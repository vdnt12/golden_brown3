"""Document Map — the evidence-gated 11-card overview (PRD §3.2, FR-004, FR-007).

Every card is built from stored sentences. A card is:
  FOUND                 at least one stored sentence matched the concept
  NOT_ASSESSED          unread (unsupported-language or unreadable) pages exist
  NOT_LOCATED           nothing matched and the silence gate allowed the claim
  INSUFFICIENT_EVIDENCE nothing matched and silence was not permitted

An empty card never means "this provision is legally absent".
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from app.config import Settings
from app.core.enums import CardStatus, MissingInfoCode
from app.retrieval.concepts import CORE_TEN, Concept
from app.schemas.response import (
    CardEvidence,
    DocumentRef,
    ExtractionWarning,
    MapCard,
    OverviewResponse,
)
from app.services import silence_context
from app.store import sentences as sentences_store
from app.store.repo import open_document

MAX_CARD_EVIDENCE = 3
MAX_SUMMARY_CHARS = 240


@dataclass(frozen=True)
class _Sentence:
    sid: str
    page: int
    section: str | None
    text: str


def load_sentences(connection: sqlite3.Connection, doc_id: str) -> list[_Sentence]:
    return [
        _Sentence(
            sid=row["sid"],
            page=int(row["page_no"]),
            section=row["section"],
            text=row["text"],
        )
        for row in sentences_store.all_sentences(connection, doc_id)
    ]


def _evidence(sentence: _Sentence, ocr_pages: set[int]) -> CardEvidence:
    return CardEvidence(
        sid=sentence.sid,
        page=sentence.page,
        section=sentence.section,
        quote=sentence.text,
        ocr_derived=sentence.page in ocr_pages,
    )


def _summary(matches: list[_Sentence]) -> str:
    text = matches[0].text.strip()
    if len(text) <= MAX_SUMMARY_CHARS:
        return text
    return text[: MAX_SUMMARY_CHARS - 1].rstrip() + "…"


def build_card(
    concept: Concept,
    sentences: list[_Sentence],
    *,
    silence_allowed: bool,
    unread: int,
    ocr_pages: set[int],
) -> MapCard:
    import re

    patterns = [re.compile(pattern, re.IGNORECASE) for pattern in concept.patterns]
    matches = [s for s in sentences if any(p.search(s.text) for p in patterns)]

    if matches:
        return MapCard(
            status=CardStatus.FOUND.value,
            summary=_summary(matches),
            evidence=[_evidence(s, ocr_pages) for s in matches[:MAX_CARD_EVIDENCE]],
            note=concept.hint,
        )
    if unread:
        return MapCard(
            status=CardStatus.NOT_ASSESSED.value,
            note=(
                f"{unread} page(s) could not be read, so this concept could not be "
                "searched everywhere. Not a statement that it is absent."
            ),
        )
    if silence_allowed:
        return MapCard(
            status=CardStatus.NOT_LOCATED.value,
            note=(
                "Not located in the readable text that was checked. This does not mean "
                "it is allowed or prohibited."
            ),
        )
    return MapCard(
        status=CardStatus.INSUFFICIENT_EVIDENCE.value,
        note="Could not be searched reliably enough to make any statement.",
    )


def build_overview(settings: Settings, doc_id: str) -> OverviewResponse:
    with open_document(settings.data_dir, doc_id) as handle:
        document = handle.connection.execute(
            "SELECT * FROM document WHERE doc_id = ?", (doc_id,)
        ).fetchone()
        if document is None:
            raise LookupError(doc_id)
        sentences = load_sentences(handle.connection, doc_id)
        unread = silence_context.unread_pages(handle.connection, doc_id)
        decision = silence_context.decide(handle.connection, doc_id)
        ocr_pages = {
            int(row["page_no"])
            for row in handle.connection.execute(
                "SELECT DISTINCT page_no FROM sentences WHERE doc_id = ? AND ocr_derived = 1",
                (doc_id,),
            )
        }

    # The contract is an object keyed by the concept label, in the PRD's order.
    # A dict (not a list) makes a dropped concept structurally impossible: the
    # cardinality is asserted below rather than left to rendering.
    cards: dict[str, MapCard] = {}
    for concept in CORE_TEN:
        card = build_card(
            concept,
            sentences,
            silence_allowed=decision.allowed,
            unread=len(unread),
            ocr_pages=ocr_pages,
        )
        if concept.label in cards:  # pragma: no cover - guards config drift
            raise RuntimeError(f"duplicate concept label: {concept.label}")
        cards[concept.label] = card
    expected = {concept.label for concept in CORE_TEN}
    if set(cards) != expected:  # pragma: no cover - guards config drift
        raise RuntimeError(f"document map is incomplete: {expected - set(cards)}")

    warnings: list[ExtractionWarning] = []
    if unread:
        warnings.append(
            ExtractionWarning(
                code=MissingInfoCode.UNREAD_LANGUAGE.value,
                message=(
                    "Pages " + ", ".join(str(n) for n in unread) + " are not in English or "
                    "could not be read. They are excluded from analysis."
                ),
            )
        )
    if ocr_pages:
        warnings.append(
            ExtractionWarning(
                code="OCR_DERIVED",
                message="Some quotations come from OCR. Check the page image before relying on them.",
                ocr_derived=True,
            )
        )
    if not decision.allowed:
        warnings.append(
            ExtractionWarning(
                code="SILENCE_GATE_BLOCKED",
                message=(
                    "Absence claims are disabled for this document ("
                    + decision.reason.value
                    + "): cards without evidence say 'insufficient evidence', not 'absent'."
                ),
            )
        )

    return OverviewResponse(
        document=DocumentRef(
            document_id=doc_id,
            display_name=document["source_filename"] or "document",
            page_count=int(document["page_count"]),
            sha256=document["sha256"],
        ),
        cards=cards,
        warnings=warnings,
    )
