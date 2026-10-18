"""Review view: attention-first, never a score (PRD FR-004, FR-007, FR-012).

Order (fixed by the PRD):
  1 CONFLICT      candidate clause conflicts (two sections, different values)
  2 AMBIGUITY     vague wording attached to money, time or termination
  3 FINANCIAL     payment / forfeiture / deduction / penalty / lock-in wording
  4 JURISDICTION  topics that may depend on local law (caution only)
  5 OTHER         remaining noteworthy wording, incl. unread-language coverage

Every item carries the stored quotation(s) it came from, and an `order_reason`
that explains its position in plain language. Nothing is scored, ranked by
risk, or turned into a legal conclusion.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from functools import lru_cache

import yaml

from app.config import Settings
from app.lexicon_paths import ESCALATION_TEMPLATES, JURISDICTION_TOPICS
from app.retrieval.conflicts import Sentence, detect_conflicts
from app.retrieval.vagueness import (
    PENALTY_RE,
    find_vague,
    has_money,
    has_penalty,
    has_termination,
    has_time,
)
from app.schemas.response import (
    CardEvidence,
    DocumentRef,
    ProfessionalQuestion,
    ReviewAttentionItem,
    ReviewResponse,
)
from app.services import silence_context
from app.store import sentences as sentences_store
from app.store.repo import open_document

# Reading order fixed by the PRD. The number is part of the payload so a client
# cannot re-sort by risk, and so the order survives serialisation.
CATEGORY_PRIORITY: dict[str, int] = {
    "CONFLICT": 1,
    "AMBIGUITY": 2,
    "FINANCIAL": 3,
    "JURISDICTION": 4,
    "OTHER": 5,
}


@dataclass(frozen=True)
class _Item:
    """Internal review finding, before it is given a priority."""

    category: str
    title: str
    detail: str
    order_reason: str
    evidence: list[CardEvidence]


@dataclass(frozen=True)
class _Row:
    sid: str
    page: int
    section: str | None
    text: str


def _load_sentences(connection: sqlite3.Connection, doc_id: str) -> list[_Row]:
    return [
        _Row(
            sid=row["sid"],
            page=int(row["page_no"]),
            section=row["section"],
            text=row["text"],
        )
        for row in sentences_store.all_sentences(connection, doc_id)
    ]


def _evidence(row: _Row, ocr_pages: set[int]) -> CardEvidence:
    return CardEvidence(
        sid=row.sid,
        page=row.page,
        section=row.section,
        quote=row.text,
        ocr_derived=row.page in ocr_pages,
    )


@dataclass(frozen=True)
class _JurisdictionTopic:
    name: str
    patterns: tuple[str, ...]


@lru_cache(maxsize=1)
def _jurisdiction_topics() -> list[_JurisdictionTopic]:
    payload = yaml.safe_load(JURISDICTION_TOPICS.read_text(encoding="utf-8")) or {}
    topics: list[_JurisdictionTopic] = []
    for raw in payload.get("topics", []):
        name = str(raw.get("name", "")).strip()
        covers = [str(item).lower() for item in raw.get("covers", [])]
        if not name:
            continue
        words = {name.replace("_", " "), *covers}
        patterns = tuple(sorted(words))
        topics.append(_JurisdictionTopic(name=name, patterns=patterns))
    return topics


@lru_cache(maxsize=1)
def _templates() -> dict[str, str]:
    payload = yaml.safe_load(ESCALATION_TEMPLATES.read_text(encoding="utf-8")) or {}
    return {str(k): str(v) for k, v in (payload.get("templates") or {}).items()}


def _section(section: str | None, page: int) -> str:
    return section if section else f"page {page}"


def build_review(settings: Settings, doc_id: str) -> ReviewResponse:
    items: list[_Item] = []

    with open_document(settings.data_dir, doc_id) as handle:
        document = handle.connection.execute(
            "SELECT * FROM document WHERE doc_id = ?", (doc_id,)
        ).fetchone()
        if document is None:
            raise LookupError(doc_id)
        rows = _load_sentences(handle.connection, doc_id)
        unread = silence_context.unread_pages(handle.connection, doc_id)
        ocr_pages = {
            int(row["page_no"])
            for row in handle.connection.execute(
                "SELECT DISTINCT page_no FROM sentences WHERE doc_id = ? AND ocr_derived = 1",
                (doc_id,),
            )
        }

    by_sid = {row.sid: row for row in rows}
    templates = _templates()

    # 1 -- candidate conflicts -------------------------------------------------
    conflict_report = detect_conflicts(
        [Sentence(sid=r.sid, page=r.page, section=r.section, text=r.text) for r in rows]
    )
    # Two candidates per concept is enough to show the disagreement; a discursive
    # document can otherwise produce a wall of near-identical "rent" candidates.
    per_concept: dict[str, int] = {}
    for candidate in conflict_report.candidates:
        left = by_sid.get(candidate.left.sid)
        right = by_sid.get(candidate.right.sid)
        if left is None or right is None:
            continue
        if per_concept.get(candidate.label, 0) >= 2:
            continue
        per_concept[candidate.label] = per_concept.get(candidate.label, 0) + 1
        items.append(
            _Item(
                category="CONFLICT",
                title=f"Possible conflicting {candidate.label.lower()} wording",
                detail=(
                    f"Section {_section(left.section, left.page)} and section "
                    f"{_section(right.section, right.page)} attach different values "
                    f"({', '.join(candidate.values)}) to the same topic. Whether these "
                    "clauses really conflict needs a human reading; both passages are quoted."
                ),
                order_reason=(
                    "Listed first: two passages that appear to disagree are the most "
                    "useful thing to read before signing."
                ),
                evidence=[_evidence(left, ocr_pages), _evidence(right, ocr_pages)],
            )
        )

    # 2 -- ambiguity about money, time or termination --------------------------
    vague_hits = find_vague([(row.sid, row.text) for row in rows])
    ambiguity_count = 0
    for hit in vague_hits:
        row = by_sid.get(hit.sid)
        if row is None:
            continue
        if not (has_money(row.text) or has_time(row.text) or has_termination(row.text)):
            continue
        ambiguity_count += 1
        items.append(
            _Item(
                category="AMBIGUITY",
                title=f"Vague wording: “{hit.term}”",
                detail=(
                    f"The wording “{hit.term}” is not defined in the agreement. It "
                    "attaches to money, a deadline or termination, so its practical "
                    "meaning may only be settled between the parties (or locally)."
                ),
                order_reason=(
                    "Listed after conflicts: vague wording is common, but matters most "
                    "where it touches money, deadlines or ending the tenancy."
                ),
                evidence=[_evidence(row, ocr_pages)],
            )
        )
        if ambiguity_count >= 4:
            break

    # 3 -- financial obligations ----------------------------------------------
    financial_count = 0
    for row in rows:
        if not has_penalty(row.text):
            continue
        financial_count += 1
        matched = PENALTY_RE.search(row.text)
        keyword = matched.group(0).lower() if matched else "payment"
        items.append(
            _Item(
                category="FINANCIAL",
                title=f"Money clause mentioning “{keyword}”",
                detail=(
                    "This passage attaches a payment, deduction, forfeiture, penalty or "
                    "lock-in consequence. It is quoted below so the amount and the trigger "
                    "can be checked together."
                ),
                order_reason=(
                    "Listed after ambiguity: a stated financial consequence is easier to "
                    "read than vague wording, but still worth confirming."
                ),
                evidence=[_evidence(row, ocr_pages)],
            )
        )
        if financial_count >= 4:
            break

    # 4 -- jurisdiction-flagged topics ----------------------------------------
    jurisdiction_count = 0
    for topic in _jurisdiction_topics():
        for row in rows:
            lowered = row.text.lower()
            if any(pattern and pattern in lowered for pattern in topic.patterns):
                jurisdiction_count += 1
                items.append(
                    _Item(
                        category="JURISDICTION",
                        title=f"May depend on local law: {topic.name.replace('_', ' ')}",
                        detail=(
                            "This passage covers a topic whose effect commonly depends on "
                            "local law. GBDoc does not state what local law requires."
                        ),
                        order_reason=(
                            "Listed after the document's own wording: local-law questions "
                            "need someone qualified in the relevant place."
                        ),
                        evidence=[_evidence(row, ocr_pages)],
                    )
                )
                break
        if jurisdiction_count >= 3:
            break

    # 5 -- coverage -----------------------------------------------------------
    if unread:
        items.append(
            _Item(
                category="OTHER",
                title="Some pages could not be read",
                detail=(
                    "Pages " + ", ".join(str(n) for n in unread) + " are not in English or "
                    "contain no extractable text, so they were not reviewed. Categories "
                    "that depend on them are marked not assessed rather than clear."
                ),
                order_reason="Listed last: it qualifies everything above rather than adding a finding.",
                evidence=[],
            )
        )

    questions = build_escalation(items, rows, templates, ocr_pages)

    attention_first = [
        ReviewAttentionItem(
            category=item.category,
            priority=CATEGORY_PRIORITY.get(item.category, 5),
            title=item.title,
            reason=item.detail,
            order_reason=item.order_reason,
            citations=item.evidence,
        )
        for item in items
    ]
    # Stable sort: within a category, findings stay in document/discovery order.
    attention_first.sort(key=lambda entry: entry.priority)

    if unread:
        review_status = "NOT_ASSESSED"
    elif attention_first:
        review_status = "ATTENTION"
    else:
        review_status = "CLEAR"

    return ReviewResponse(
        document=DocumentRef(
            document_id=doc_id,
            display_name=document["source_filename"] or "document",
            page_count=int(document["page_count"]),
            sha256=document["sha256"],
        ),
        review_status=review_status,
        attention_first=attention_first,
        questions_for_professional=questions,
    )


def build_escalation(
    items: list[_Item],
    rows: list[_Row],
    templates: dict[str, str],
    ocr_pages: set[int],
) -> list[ProfessionalQuestion]:
    """Turn the top findings into neutral questions, each backed by a quotation."""
    questions: list[ProfessionalQuestion] = []
    seen: set[str] = set()

    for item in items:
        if not item.evidence:
            continue
        template = templates.get(item.category.lower())
        if not template:
            continue
        first = item.evidence[0]
        key = f"{item.category}:{first.sid}"
        if key in seen:
            continue
        seen.add(key)
        topic = item.title.split(":", 1)[-1].strip() if ":" in item.title else item.title
        if item.category == "CONFLICT" and len(item.evidence) >= 2:
            second = item.evidence[1]
            body = template.format(
                section_a=_section(first.section, first.page),
                page_a=first.page,
                quote_a=_short(first.quote),
                section_b=_section(second.section, second.page),
                page_b=second.page,
                quote_b=_short(second.quote),
            )
        else:
            body = template.format(
                section=_section(first.section, first.page),
                page=first.page,
                quote=_short(first.quote),
                topic=topic.lower(),
            )
        questions.append(
            ProfessionalQuestion(
                topic=item.category.lower(),
                prompt=" ".join(body.split()),
            )
        )
        if len(questions) >= 4:
            break

    if not questions and rows:
        # Nothing specific to escalate; ask the one question that always applies.
        questions.append(
            ProfessionalQuestion(
                topic="general",
                prompt=(
                    "Ask a qualified lawyer to read this agreement with you before you sign: "
                    "which obligations bind me, what happens if I leave early, and what does "
                    "local law require for deposits and notice?"
                ),
            )
        )
    return questions


def _short(text: str, limit: int = 160) -> str:
    cleaned = " ".join(text.split())
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 1].rstrip() + "…"
