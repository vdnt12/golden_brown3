"""Execution of the seven read-only, document-bound tools (Guide 2.2).

Only these functions touch retrieval. Each one returns `Evidence` records taken
from stored text and registers them in the run's provenance registry, so every
sentence the model may cite is a sentence the backend itself handed over.

No tool accepts a document id from the model: the document is bound when the
run starts.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from app.retrieval.crossrefs import extract_crossrefs
from app.retrieval.lexical import search_chunks
from app.retrieval.topics import classify_topics
from app.services import silence_context
from app.store import sentences as sentences_store
from app.validation.provenance import Evidence, ProvenanceRegistry

MAX_SENTENCES_PER_HIT = 2


@dataclass(frozen=True)
class ToolResult:
    tool: str
    evidence: list[Evidence]
    query: str = ""
    note: str = ""


def _evidence_for_chunk(
    connection: sqlite3.Connection,
    doc_id: str,
    chunk,
    *,
    limit: int = MAX_SENTENCES_PER_HIT,
) -> list[Evidence]:
    sids = [sid for sid in str(chunk["sentence_ids"]).split(",") if sid]
    rows = sentences_store.get_sentences(connection, doc_id, sids)
    evidence: list[Evidence] = []
    for row in rows[:limit]:
        evidence.append(
            Evidence(
                sid=row["sid"],
                page=int(row["page_no"]),
                section=row["section"],
                quote=row["text"],
                ocr_derived=bool(row["ocr_derived"]),
            )
        )
    return evidence


def search_document(
    connection: sqlite3.Connection,
    doc_id: str,
    query: str,
    registry: ProvenanceRegistry,
    *,
    limit: int = 6,
) -> ToolResult:
    rows = search_chunks(connection, doc_id, query, limit=min(limit, 12))
    evidence: list[Evidence] = []
    for row in rows:
        evidence.extend(_evidence_for_chunk(connection, doc_id, row))
    registry.register(evidence)
    return ToolResult(tool="search_document", evidence=evidence, query=query)


def get_page(
    connection: sqlite3.Connection,
    doc_id: str,
    page_no: int,
    registry: ProvenanceRegistry,
    *,
    limit: int = 6,
) -> ToolResult:
    rows = sentences_store.get_page_sentences(connection, doc_id, page_no)[:limit]
    evidence = [
        Evidence(
            sid=row["sid"],
            page=int(row["page_no"]),
            section=row["section"],
            quote=row["text"],
            ocr_derived=bool(row["ocr_derived"]),
        )
        for row in rows
    ]
    registry.register(evidence)
    return ToolResult(tool="get_page", evidence=evidence, query=f"page {page_no}")


def get_section(
    connection: sqlite3.Connection,
    doc_id: str,
    section: str,
    registry: ProvenanceRegistry,
    *,
    limit: int = 8,
) -> ToolResult:
    rows = connection.execute(
        "SELECT * FROM sentences WHERE doc_id = ? AND section = ? ORDER BY page_no, char_start LIMIT ?",
        (doc_id, section, limit),
    )
    evidence = [
        Evidence(
            sid=row["sid"],
            page=int(row["page_no"]),
            section=row["section"],
            quote=row["text"],
            ocr_derived=bool(row["ocr_derived"]),
        )
        for row in rows
    ]
    registry.register(evidence)
    return ToolResult(tool="get_section", evidence=evidence, query=f"section {section}")


def find_related_clauses(
    connection: sqlite3.Connection,
    doc_id: str,
    ref: str,
    registry: ProvenanceRegistry,
    *,
    limit: int = 6,
) -> ToolResult:
    """Deterministic cross-reference expansion for a clause/schedule reference."""
    rows = connection.execute(
        "SELECT text FROM sentences WHERE doc_id = ? AND section = ? LIMIT 8", (doc_id, ref)
    ).fetchall()
    phrases = [row["text"] for row in rows]
    refs: list[str] = []
    for phrase in phrases:
        refs.extend(r.ref for r in extract_crossrefs(phrase))
    evidence: list[Evidence] = []
    for target in refs[:2]:
        rows = connection.execute(
            "SELECT * FROM sentences WHERE doc_id = ? AND section = ? LIMIT ?",
            (doc_id, target, limit),
        ).fetchall()
        for row in rows:
            evidence.append(
                Evidence(
                    sid=row["sid"],
                    page=int(row["page_no"]),
                    section=row["section"],
                    quote=row["text"],
                    ocr_derived=bool(row["ocr_derived"]),
                )
            )
    registry.register(evidence)
    return ToolResult(tool="find_related_clauses", evidence=evidence, query=f"ref {ref}")


def check_document_silence(
    connection: sqlite3.Connection, doc_id: str, topic: str
) -> tuple[ToolResult, bool]:
    """Return the tool result and whether a NOT_LOCATED claim is permitted."""
    decision = silence_context.decide(connection, doc_id)
    note = "allowed" if decision.allowed else decision.reason.value
    return (
        ToolResult(tool="check_document_silence", evidence=[], query=topic, note=note),
        decision.allowed,
    )


def topic_terms(question: str) -> list[str]:
    from app.lexicon_paths import RENTAL_TOPICS
    from app.retrieval.topics import load_topics

    topics = load_topics(RENTAL_TOPICS)
    return classify_topics(question, topics)
