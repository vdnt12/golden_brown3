"""Bounded state machine (Guide 8.3). THE ONLY RUNTIME.

    RECEIVE -> CLASSIFY -> PLAN -> RETRIEVE -> ANALYZE -> VALIDATE -> RESPOND

Rules enforced here, not in prompts:
  * deterministic routing first; the model may propose only when the router is
    unsure, and a proposal can never downgrade a legal limitation;
  * one model call on the fast path, at most one refinement round, ceiling 4;
  * at most 8 tool calls and 2 retrieval loops, enforced by RunBudget;
  * every rejected point is dropped; nothing is silently softened;
  * statuses and missing-information codes are computed here, never by a model.

Hermes is not part of this runtime (ADR-0010).
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.agent import toolbox
from app.agent.prompts import PromptRecord, build_answer_messages
from app.agent.router import RouteDecision, pre_route
from app.config import Settings
from app.core.enums import (
    Classification,
    MissingInfoCode,
    PointKind,
    ResponseStatus,
    Route,
    RunPath,
    resolve_status,
)
from app.core.limits import BudgetExceeded, RunBudget
from app.lexicon_paths import RENTAL_TOPICS
from app.model.provider import LLMProvider
from app.retrieval.packets import PacketItem, PacketTooLarge, build_packet
from app.retrieval.topics import classify_topics, load_topics
from app.schemas.model_io import ModelAnswer, ModelPoint
from app.schemas.response import (
    Claim,
    DocumentRef,
    EscalationQuestion,
    EvidenceItem,
    ExtractionWarning,
    GeneralExplanation,
    MissingInformation,
    RenderedAnswer,
    RunMeta,
)
from app.services import silence_context
from app.services.glossary_service import DISCLAIMER, find_entry
from app.validation.legal_policy import LEGAL_LIMIT_TEXT
from app.validation.pipeline import ValidationOutcome, validate_model_answer
from app.validation.provenance import Evidence, ProvenanceRegistry
from app.validation.renderer import render_claim

TERM_ALIASES = {
    "lock in": "lock_in",
    "lock-in": "lock_in",
    "security deposit": "deposit",
    "advance rent": "deposit",
    "notice period": "notice",
    "early termination": "termination",
}

MAX_HITS = 5
STOPWORDS = frozenset(
    ["a", "an", "and", "are", "as", "at", "be", "been", "being", "between", "by", "can", "could", "did", "do", "does", "for", "from", "had", "has", "have", "how", "i", "if", "in", "into", "is", "it", "its", "may", "me", "must", "my", "no", "not", "of", "on", "or", "our", "shall", "should", "so", "than", "that", "the", "their", "them", "then", "there", "these", "they", "this", "those", "to", "under", "was", "we", "were", "what", "when", "where", "which", "who", "why", "will", "with", "would", "you", "your", "agreement", "document", "says", "say", "said", "mention", "mean", "meaning"]
)

_CONTENT_WORD_RE = re.compile(r"[a-z]{3,}")


def _content_terms(question: str) -> set[str]:
    return set(_CONTENT_WORD_RE.findall(question.lower())) - STOPWORDS


MAX_PACKET_ITEMS = 12


class ProviderFailure(RuntimeError):
    """The local model is missing, unreachable, or produced unusable output."""


class DocumentContext(Protocol):
    """Everything one run needs; built by services.answer from the store."""

    doc_id: str
    sha256: str
    page_count: int
    display_name: str
    unread_pages: list[int]
    ocr_pages: list[int]
    settings: Settings


@dataclass
class AskContext:
    doc_id: str
    sha256: str
    page_count: int
    display_name: str
    connection: Any
    settings: Settings
    provider: LLMProvider | None
    model_tag: str | None = None
    unread_pages: list[int] = field(default_factory=list)
    ocr_pages: list[int] = field(default_factory=list)
    allow_fallback: bool = False


@dataclass
class _Run:
    decision: RouteDecision
    budget: RunBudget
    registry: ProvenanceRegistry
    path: RunPath = RunPath.FAST
    tool_names: list[str] = field(default_factory=list)
    codes: list[str] = field(default_factory=list)


class BoundedAgentRuntime:
    """Execute one question against one document and return a RenderedAnswer."""

    def __init__(self, context: AskContext) -> None:
        self.context = context
        self.settings = context.settings
        self.run: _Run = _Run(
            decision=pre_route("", max_chars=self.settings.max_question_chars),
            budget=RunBudget(
                max_tool_calls=self.settings.max_tool_calls,
                max_model_calls=self.settings.max_model_calls,
                max_retrieval_loops=self.settings.max_retrieval_loops,
                wall_clock_s=self.settings.model_timeout_s * 4,
            ),
            registry=ProvenanceRegistry(
                document_id=context.doc_id, document_sha256=context.sha256
            ),
        )

    # ------------------------------------------------------------------ entry
    def answer(self, question: str) -> RenderedAnswer:
        started = time.monotonic()
        text = (question or "").strip()
        self.run.decision = pre_route(text, max_chars=self.settings.max_question_chars)

        if not text:
            return self._simple(
                ResponseStatus.OUT_OF_SCOPE,
                "Ask a question about the document you uploaded.",
                started,
            )
        if len(text) > self.settings.max_question_chars:
            return self._simple(
                ResponseStatus.OUT_OF_SCOPE,
                f"Questions are limited to {self.settings.max_question_chars} characters.",
                started,
            )

        route = self.run.decision.route
        try:
            if route is Route.LEGAL_CONCLUSION:
                return self._legal_limit(started)
            if route is Route.EXTERNAL_LAW_REQUIRED:
                return self._legal_limit(started, external_law=True)
            if route is Route.TERM_EXPLANATION:
                return self._term_answer(text, started)
            return self._evidence_answer(text, started)
        except BudgetExceeded as exc:
            self.run.codes.append(str(exc))
            return self._simple(
                ResponseStatus.ERROR_PROCESSING,
                "This question exceeded the run budget before an answer could be validated.",
                started,
            )
        except ProviderFailure as exc:
            self.run.codes.append(f"PROVIDER_FAILURE:{type(exc).__name__}")
            return self._simple(
                ResponseStatus.ERROR_LOCAL_MODEL_UNAVAILABLE,
                (
                    "The local model could not be reached or could not produce a valid "
                    "answer. GBDoc does not fall back to a remote service, so nothing "
                    "is answered instead. Start Ollama and the pinned Gemma tag, then retry."
                ),
                started,
                recommend_review=True,
            )

    # ------------------------------------------------------------- legal route
    def _legal_limit(self, started: float, *, external_law: bool = False) -> RenderedAnswer:
        hits = self._search_for_legal(started)
        claims = [
            Claim(
                claim_id=f"claim_{index:03d}",
                text="The agreement says:",
                classification=Classification.DIRECT,
                evidence=[self._item(evidence)],
            )
            for index, evidence in enumerate(hits[:2], start=1)
        ]
        escalation = [
            EscalationQuestion(
                question=(
                    "Ask a qualified lawyer whether this wording meets the legal requirements "
                    "where the property is located, and what your position is under it."
                ),
                topics=["legal_boundary"],
                evidence=[self._item(e) for e in hits[:1]],
            )
        ]
        answer = (
            "Whether the law requires or prohibits something cannot be established from the "
            "document alone, and GBDoc does not research current law. That needs a "
            "qualified lawyer where the property is located."
            if external_law
            else LEGAL_LIMIT_TEXT
        )
        return self._render(
            statuses=[ResponseStatus.LEGAL_LIMIT],
            answer=answer,
            claims=claims,
            escalation=escalation,
            recommend_review=True,
            external_law=external_law,
            started=started,
        )

    def _search_for_legal(self, started: float) -> list[Evidence]:
        """Quote the wording under discussion, without answering the legal question."""
        for query in ("termination notice deposit rent", "agreement"):
            try:
                hits = self._search(query, limit=3)
            except BudgetExceeded:
                return []
            if hits:
                return hits
        return []

    # -------------------------------------------------------------- term route
    def _term_answer(self, question: str, started: float) -> RenderedAnswer:
        topic = self._term_topic(question)
        entry = find_entry(topic) if topic else None
        if entry is not None:
            explanation = GeneralExplanation(
                entry_id=entry.entry_id,
                term=entry.term,
                definition=entry.definition,
                disclaimer=DISCLAIMER,
            )
            definition = entry.definition
            term_label = entry.term
        else:
            explanation = GeneralExplanation(
                entry_id="no_entry",
                term=topic or "term",
                definition=(
                    "This term is not in GBDoc's curated glossary, so no general "
                    "definition is given here. GBDoc does not improvise legal definitions "
                    "from model memory."
                ),
                disclaimer=DISCLAIMER,
            )
            definition = explanation.definition
            term_label = topic or "this term"

        hits = self._search(topic or question, limit=3)
        claims = [
            Claim(
                claim_id=f"claim_{index:03d}",
                text=f"In your document, {term_label} appears here:",
                classification=Classification.DIRECT,
                evidence=[self._item(evidence)],
            )
            for index, evidence in enumerate(hits[:2], start=1)
        ]
        status = ResponseStatus.ANSWERED if claims else ResponseStatus.LIMITED
        return self._render(
            statuses=[status],
            answer=f"{definition} This is a general definition, not legal advice.",
            claims=claims,
            general_explanations=[explanation],
            started=started,
        )

    # ---------------------------------------------------------- evidence route
    def _evidence_answer(self, question: str, started: float) -> RenderedAnswer:
        is_statutory_query = bool(
            re.search(
                r"\b(?:section\s+\d+|indian\s+contract\s+act|transfer\s+of\s+property|registration\s+act|easements?\s+act|statut(?:e|ory)|supreme\s+court|open\s+india\s+law)\b",
                question,
                re.IGNORECASE,
            )
        )
        hits = self._retrieve(question)
        if (not hits or is_statutory_query) and getattr(self.context, "allow_fallback", False):
            from app.services import open_india_law
            law_results = open_india_law.search_primary_law(question)
            if law_results["sections"] or law_results["judgments"]:
                return self._render_india_law_answer(question, law_results, started)
        if not hits:
            return self._no_evidence(question, started)

        packet_items = [
            PacketItem(
                ev_id=evidence.sid,
                sid=evidence.sid,
                page=evidence.page,
                section=evidence.section,
                text=evidence.quote,
            )
            for evidence in hits[:MAX_PACKET_ITEMS]
        ]
        try:
            packet = build_packet(packet_items)
        except PacketTooLarge:
            self.run.codes.append("PACKET_TOO_LARGE")
            return self._simple(
                ResponseStatus.ERROR_PROCESSING,
                "The evidence for this question exceeded the packet budget. "
                "Try a narrower question.",
                started,
            )

        if self.context.provider is None:
            if not getattr(self.context, "allow_fallback", False):
                raise ProviderFailure("no local model configured")
            outcome = self._synthesize_outcome(packet.items)
            return self._render_outcome(
                question,
                outcome,
                started,
                points_returned=outcome.returned,
                had_hits=bool(hits),
            )

        messages = build_answer_messages(
            question,
            [
                PromptRecord(
                    sid=item.sid,
                    page=item.page,
                    section=item.section,
                    text=item.text,
                )
                for item in packet.items
            ],
            max_prompt_tokens=3_000,
        )
        try:
            outcome = self._analyse(messages)
        except ProviderFailure:
            if not getattr(self.context, "allow_fallback", False):
                raise
            outcome = self._synthesize_outcome(packet.items)

        return self._render_outcome(
            question,
            outcome,
            started,
            points_returned=outcome.returned,
            had_hits=bool(hits),
        )

    def _retrieve(self, question: str) -> list[Evidence]:
        hits = self._relevant(self._search(question, limit=MAX_HITS), question)
        if hits:
            return hits
        # One bounded refinement round: lexical expansion from the topic lexicon.
        self.run.budget.spend_retrieval_loop()
        self.run.path = RunPath.REFINEMENT
        expanded = self._expand(question)
        if expanded != question:
            return self._relevant(self._search(expanded, limit=MAX_HITS), expanded)
        return []

    def _relevant(self, hits: list[Evidence], query: str) -> list[Evidence]:
        """Drop hits that do not contain a meaningful word from the question.

        Lexical search in OR mode will happily return "sublet the premises" for
        "pets". Sending that to the model wastes the packet budget, and treating it
        as evidence would make an honest "not located" impossible. A hit survives
        only if it contains at least one content word (or a lexicon term) from the
        question. This is deliberately conservative: fewer hits, never invented
        relevance.
        """
        terms = _content_terms(query) | set(toolbox.topic_terms(query))
        if not terms:
            return hits
        kept = [hit for hit in hits if any(term in hit.quote.lower() for term in terms)]
        if len(kept) != len(hits):
            self.run.codes.append("OFF_TOPIC_HITS_DROPPED")
        return kept

    def _search(self, query: str, *, limit: int = MAX_HITS) -> list[Evidence]:
        self.run.budget.assert_deadline()
        self.run.budget.spend_tool_call()
        result = toolbox.search_document(
            self.context.connection,
            self.context.doc_id,
            query,
            self.run.registry,
            limit=limit,
        )
        self.run.tool_names.append(result.tool)
        deduped: dict[str, Evidence] = {item.sid: item for item in result.evidence}
        return list(deduped.values())

    def _expand(self, question: str) -> str:
        topics = load_topics(RENTAL_TOPICS)
        matched = classify_topics(question, topics)
        terms: list[str] = []
        for topic in matched[:2]:
            terms.extend(topics.get(topic, [])[:2])
        return " ".join([question, *terms]) if terms else question

    def _analyse(self, messages: list[dict[str, str]]) -> ValidationOutcome:
        assert self.context.provider is not None
        self.run.budget.spend_model_call()
        try:
            answer: ModelAnswer = self.context.provider.answer_from_evidence(messages=messages)
        except Exception as exc:  # noqa: BLE001 - any provider failure is fail-closed
            raise ProviderFailure(str(exc)) from exc
        outcome = validate_model_answer(answer, self.run.registry)
        self.run.codes.extend(outcome.codes)
        return outcome

    def _synthesize_outcome(self, items: list[PacketItem]) -> ValidationOutcome:
        points: list[ModelPoint] = []
        for index, item in enumerate(items[:2], start=1):
            points.append(
                ModelPoint(
                    point_id=f"pt_{index}",
                    kind=PointKind.STATED,
                    text=item.text,
                    sids=[item.sid],
                )
            )
        answer = ModelAnswer(points=points)
        outcome = validate_model_answer(answer, self.run.registry)
        self.run.codes.extend(outcome.codes)
        return outcome

    # --------------------------------------------------------------- rendering
    def _render_outcome(
        self,
        question: str,
        outcome: ValidationOutcome,
        started: float,
        *,
        points_returned: int,
        had_hits: bool,
    ) -> RenderedAnswer:
        buckets: dict[PointKind, list[Claim]] = {
            PointKind.STATED: [],
            PointKind.RESTATEMENT: [],
            PointKind.INTERPRETATION: [],
            PointKind.CONCERN: [],
            PointKind.AMBIGUITY: [],
            PointKind.CONFLICT: [],
            PointKind.GENERAL_EXPLANATION: [],
        }
        statuses: list[ResponseStatus] = []
        counter = 0

        for point in outcome.accepted:
            counter += 1
            evidence = outcome.evidence.get(point.point_id, [])
            claim = render_claim(point, evidence, counter, self.context.sha256)
            if point.kind in (PointKind.STATED, PointKind.RESTATEMENT):
                buckets[point.kind].append(claim)
                statuses.append(ResponseStatus.ANSWERED)
            elif point.kind is PointKind.INTERPRETATION or point.kind is PointKind.CONCERN:
                buckets[point.kind].append(claim)
                statuses.append(ResponseStatus.LIMITED)
            elif point.kind is PointKind.AMBIGUITY:
                buckets[point.kind].append(claim)
                statuses.append(ResponseStatus.AMBIGUOUS)
            elif point.kind is PointKind.CONFLICT:
                sections = {item.section or f"page{item.page}" for item in evidence}
                if len(sections) < 2:
                    self.run.codes.append("CONFLICT_NEEDS_TWO_SECTIONS")
                    continue
                buckets[point.kind].append(claim)
                statuses.append(ResponseStatus.CONFLICTING)

        if not statuses:
            # Absence is only claimable when retrieval also came back empty AND the
            # silence gate passes. A silent model over real hits is "insufficient
            # evidence", never "not located".
            return self._no_evidence(
                question, started, had_evidence=points_returned > 0 or had_hits
            )

        if outcome.rejected:
            statuses.append(ResponseStatus.LIMITED)

        return self._render(
            statuses=statuses,
            answer=self._answer_sentence(buckets),
            claims=buckets[PointKind.STATED] + buckets[PointKind.RESTATEMENT],
            interpretations=buckets[PointKind.INTERPRETATION],
            concerns=buckets[PointKind.CONCERN],
            ambiguities=buckets[PointKind.AMBIGUITY],
            conflicts=buckets[PointKind.CONFLICT],
            started=started,
        )

    def _answer_sentence(self, buckets: dict[PointKind, list[Claim]]) -> str:
        parts: list[str] = []
        if buckets[PointKind.STATED] or buckets[PointKind.RESTATEMENT]:
            parts.append("Here is what the readable text says, with the passage quoted below.")
        if buckets[PointKind.INTERPRETATION]:
            parts.append("The reading below is labelled as an interpretation, not as fact.")
        if buckets[PointKind.AMBIGUITY]:
            parts.append("Parts of the wording are unclear; the quoted passage is shown.")
        if buckets[PointKind.CONFLICT]:
            parts.append("Two passages appear to disagree; both are quoted so you can compare them.")
        if buckets[PointKind.CONCERN]:
            parts.append("One or more passages are flagged for attention.")
        return " ".join(parts) or "No supported point could be rendered from the retrieved evidence."

    def _no_evidence(
        self, question: str, started: float, *, had_evidence: bool = False
    ) -> RenderedAnswer:
        """Absence is only claimed when the silence gate allows it.

        `had_evidence=True` means retrieval found text but no model point survived
        validation. That is not silence: the text exists, so the honest status is
        INSUFFICIENT_EVIDENCE, never NOT_LOCATED.
        """
        decision = silence_context.decide(
            self.context.connection,
            self.context.doc_id,
            lexicon_checked=True,
            lexical_checked=True,
            headings_checked=True,
            crossrefs_checked=True,
        )
        topics = toolbox.topic_terms(question)
        if had_evidence:
            status = ResponseStatus.INSUFFICIENT_EVIDENCE
            code = MissingInfoCode.CONTEXT_REQUIRED
            message = (
                "I found related passages but could not validate a supported statement "
                "against them, so nothing is asserted. Try naming the clause or the exact "
                "figure you are asking about."
            )
        elif self.context.unread_pages:
            status = ResponseStatus.INSUFFICIENT_EVIDENCE
            code = MissingInfoCode.UNREAD_LANGUAGE
            message = (
                "Some pages could not be read, so GBDoc cannot say whether this topic "
                "appears there. No absence claim is made."
            )
        elif decision.allowed and topics:
            status = ResponseStatus.NOT_LOCATED
            code = MissingInfoCode.TOPIC_NOT_LOCATED
            message = (
                "I could not find this topic in the readable text I checked. That does not "
                "mean it is allowed or prohibited, and it does not mean the agreement is "
                "silent outside the pages I could read."
            )
        elif decision.allowed:
            status = ResponseStatus.OUT_OF_SCOPE
            code = MissingInfoCode.CONTEXT_REQUIRED
            message = (
                "That does not look like a question about this rental agreement. Try asking "
                "about rent, deposit, notice, lock-in, maintenance or termination."
            )
        else:
            status = ResponseStatus.INSUFFICIENT_EVIDENCE
            code = MissingInfoCode.CONTEXT_REQUIRED
            message = (
                "There is not enough reliable evidence to answer this, and GBDoc will not "
                "guess. Try naming the clause or topic you mean."
            )
        return self._render(
            statuses=[status],
            answer=message,
            missing_information=[MissingInformation(code=code, message=message, searches=topics)],
            started=started,
        )

    def _render_india_law_answer(
        self,
        question: str,
        results: dict[str, Any],
        started: float,
    ) -> RenderedAnswer:
        claims: list[Claim] = []
        general_explanations: list[GeneralExplanation] = []
        counter = 0

        for sec in results.get("sections", [])[:2]:
            counter += 1
            cid = f"cl_{counter}"
            sid = f"law-{sec['section_id']}"
            quote = sec["text"][:380]
            claim = Claim(
                claim_id=cid,
                text=f"Under {sec['act_name']} ({sec['section_number']}: {sec['title']}): {sec['text']}",
                classification=Classification.DIRECT,
                evidence=[
                    EvidenceItem(
                        sid=sid,
                        page=1,
                        section=f"{sec['act_name']}, {sec['section_number']}",
                        quote=quote,
                        ocr_derived=False,
                        document_sha256=self.context.sha256,
                    )
                ],
            )
            claims.append(claim)
            general_explanations.append(
                GeneralExplanation(
                    entry_id=f"expl_{counter}",
                    term=f"{sec['section_number']} ({sec['title']})",
                    definition=f"Primary legislation published under official authority ({sec['gazette_ref']}). Source: {sec['source_url']}",
                    source="glossary",
                    disclaimer="Official primary law sourced from Open India Law (GBDoc dataset).",
                )
            )

        for j in results.get("judgments", [])[:1]:
            counter += 1
            cid = f"cl_{counter}"
            sid = f"law-{j['judgment_id']}"
            claim = Claim(
                claim_id=cid,
                text=f"{j['court']} in {j['case_name']} ({j['citation']}): {j['holding']} (Ratio: {j['ratio_decidendi']})",
                classification=Classification.SUPPORTED,
                evidence=[
                    EvidenceItem(
                        sid=sid,
                        page=1,
                        section=j["citation"],
                        quote=j["quote"][:380],
                        ocr_derived=False,
                        document_sha256=self.context.sha256,
                    )
                ],
            )
            claims.append(claim)

        answer_lead = (
            "Based on the official Open India Law primary dataset, here are the applicable statutory provisions and authoritative judicial holdings:"
        )

        return self._render(
            statuses=[ResponseStatus.ANSWERED],
            answer=answer_lead,
            claims=claims,
            general_explanations=general_explanations,
            external_law=True,
            started=started,
        )

    def _render(
        self,
        *,
        statuses: list[ResponseStatus],
        answer: str,
        claims: list[Claim] | None = None,
        interpretations: list[Claim] | None = None,
        concerns: list[Claim] | None = None,
        ambiguities: list[Claim] | None = None,
        conflicts: list[Claim] | None = None,
        general_explanations: list[GeneralExplanation] | None = None,
        missing_information: list[MissingInformation] | None = None,
        escalation: list[EscalationQuestion] | None = None,
        recommend_review: bool = False,
        external_law: bool = False,
        started: float,
    ) -> RenderedAnswer:
        duration_ms = int((time.monotonic() - started) * 1000)
        meta = RunMeta(
            route=self.run.decision.route,
            path=self.run.path,
            provider="ollama" if self.context.provider is not None else "none",
            model_tag=self.context.model_tag
            or getattr(self.context.provider, "model", None)
            or self.settings.model_tag,
            model_digest=self.settings.model_digest,
            duration_ms=duration_ms,
            tool_calls=min(self.run.budget.tool_calls, 8),
            model_calls=min(self.run.budget.model_calls, 4),
            retrieval_loops=min(self.run.budget.retrieval_loops, 2),
            chunks_considered=len(self.run.registry.all_sids()),
            validation_codes=sorted(set(self.run.codes)),
            sids_exposed=self.run.registry.all_sids()[:24],
        )
        return RenderedAnswer(
            status=resolve_status(statuses),
            answer=answer,
            claims=claims or [],
            interpretations=interpretations or [],
            concerns=concerns or [],
            ambiguities=ambiguities or [],
            conflicts=conflicts or [],
            general_explanations=general_explanations or [],
            missing_information=missing_information or [],
            extraction_warnings=self._warnings(),
            jurisdiction_flags=[],
            escalation=escalation or [],
            external_law_required=external_law,
            recommend_professional_review=recommend_review,
            legal_verdict=None,
            document=DocumentRef(
                document_id=self.context.doc_id,
                display_name=self.context.display_name,
                page_count=self.context.page_count,
                sha256=self.context.sha256,
            ),
            run_meta=meta,
        )

    def _simple(
        self,
        status: ResponseStatus,
        message: str,
        started: float,
        *,
        recommend_review: bool = False,
    ) -> RenderedAnswer:
        return self._render(
            statuses=[status],
            answer=message,
            recommend_review=recommend_review,
            started=started,
        )

    def _warnings(self) -> list[ExtractionWarning]:
        warnings: list[ExtractionWarning] = []
        if self.context.unread_pages:
            warnings.append(
                ExtractionWarning(
                    code="UNREAD_LANGUAGE",
                    message=(
                        "Pages "
                        + ", ".join(str(p) for p in self.context.unread_pages)
                        + " are not in English or could not be read; they were not analysed."
                    ),
                )
            )
        if self.context.ocr_pages:
            warnings.append(
                ExtractionWarning(
                    code="OCR_DERIVED",
                    message=(
                        "Pages "
                        + ", ".join(str(p) for p in self.context.ocr_pages)
                        + " were read with OCR. Check the page image before relying on a quotation."
                    ),
                    ocr_derived=True,
                )
            )
        return warnings

    def _item(self, evidence: Evidence) -> EvidenceItem:
        return EvidenceItem(
            sid=evidence.sid,
            page=evidence.page,
            section=evidence.section,
            quote=evidence.quote,
            ocr_derived=evidence.ocr_derived,
            document_sha256=evidence.document_sha256 or self.context.sha256,
        )

    def _term_topic(self, question: str) -> str | None:
        lowered = question.lower()
        for alias, canonical in TERM_ALIASES.items():
            if alias in lowered:
                return canonical
        match = re.search(
            r"(?:what\s+does|meaning\s+of|what\s+is\s+(?:a|an))\s+[\"']?([a-z][a-z \-]{1,40})",
            lowered,
        )
        if match:
            return match.group(1).strip().rstrip("?").strip()
        return None
