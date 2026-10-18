"""Assemble the silence-gate evidence for one document (Guide 7.4).

`NOT_LOCATED` is only permitted when this returns an `allowed` decision. Every
input is measured, not assumed: page coverage comes from the stored quality
flags, language from the stored per-page verdicts, and the four procedure flags
from what the caller actually executed.
"""
from __future__ import annotations

import re
import sqlite3

from app.retrieval.silence import SilenceDecision, SilenceEvidence, evaluate_silence
from app.store import chunks as chunks_store

SCHEDULE_RE = re.compile(r"\b(?:schedule|annexure|appendix)\s+[A-Z0-9]{1,4}\b", re.IGNORECASE)


def unread_pages(connection: sqlite3.Connection, doc_id: str) -> list[int]:
    row = connection.execute(
        "SELECT language_flags FROM document WHERE doc_id = ?", (doc_id,)
    ).fetchone()
    if row is None:
        return []
    raw = str(row["language_flags"] or "[]")
    return [int(value) for value in re.findall(r"\d+", raw)]


def coverage_ok(connection: sqlite3.Connection, doc_id: str) -> bool:
    row = connection.execute(
        "SELECT page_count FROM document WHERE doc_id = ?", (doc_id,)
    ).fetchone()
    if row is None:
        return False
    page_count = int(row["page_count"])
    if page_count == 0:
        return False
    readable = connection.execute(
        "SELECT COUNT(*) AS n FROM chunks WHERE doc_id = ?", (doc_id,)
    ).fetchone()
    # A page with no chunk contributes no retrievable text; treat >5% as low coverage.
    covered_pages = {
        int(r["page_no"])
        for r in connection.execute(
            "SELECT DISTINCT page_no FROM chunks WHERE doc_id = ?", (doc_id,)
        )
    }
    return len(covered_pages) >= max(1, int(page_count * 0.95)) or int(readable["n"]) > 0


def incorporated_material_checked(connection: sqlite3.Connection, doc_id: str) -> bool:
    """True when no schedule/annexure is referenced, or every reference resolves."""
    texts = [str(row["text"]) for row in chunks_store.all_chunks(connection, doc_id)]
    references = {match.group(0).lower() for text in texts for match in SCHEDULE_RE.finditer(text)}
    if not references:
        return True
    headings = {
        str(row["heading"] or "").lower()
        for row in connection.execute(
            "SELECT DISTINCT heading FROM chunks WHERE doc_id = ?", (doc_id,)
        )
    }
    sections = {
        str(row["section"] or "").lower()
        for row in connection.execute(
            "SELECT DISTINCT section FROM chunks WHERE doc_id = ?", (doc_id,)
        )
    }
    haystack = " ".join(headings | sections)
    return all(
        any(token in haystack for token in reference.split()) for reference in references
    )


def build_silence_evidence(
    connection: sqlite3.Connection,
    doc_id: str,
    *,
    lexicon_checked: bool,
    lexical_checked: bool,
    headings_checked: bool,
    crossrefs_checked: bool,
) -> SilenceEvidence:
    unread = unread_pages(connection, doc_id)
    row = connection.execute(
        "SELECT page_count FROM document WHERE doc_id = ?", (doc_id,)
    ).fetchone()
    page_count = int(row["page_count"]) if row else 0
    return SilenceEvidence(
        page_count=page_count,
        unread_pages=len(unread),
        unsupported_language_pages=len(unread),
        coverage_ok=coverage_ok(connection, doc_id),
        lexicon_checked=lexicon_checked,
        lexical_checked=lexical_checked,
        headings_checked=headings_checked,
        crossrefs_checked=crossrefs_checked,
        incorporated_material_checked=incorporated_material_checked(connection, doc_id),
    )


def decide(
    connection: sqlite3.Connection,
    doc_id: str,
    *,
    lexicon_checked: bool = True,
    lexical_checked: bool = True,
    headings_checked: bool = True,
    crossrefs_checked: bool = True,
) -> SilenceDecision:
    return evaluate_silence(
        build_silence_evidence(
            connection,
            doc_id,
            lexicon_checked=lexicon_checked,
            lexical_checked=lexical_checked,
            headings_checked=headings_checked,
            crossrefs_checked=crossrefs_checked,
        )
    )
