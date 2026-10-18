
"""FTS5/BM25 retrieval (Guide 7.1).

Queries are tokenised and quoted; FTS operators from user text are never passed
through. Results are capped at max_chunks_per_call (default 12).
"""
from __future__ import annotations

import re
import sqlite3

_TOKEN = re.compile(r"[A-Za-z0-9\u00c0-\u024f\u20b9]+")


def fts_tokens(query: str) -> list[str]:
    return [token for token in _TOKEN.findall(query) if token]


def fts_match_query(query: str, *, mode: str = "or") -> str:
    tokens = fts_tokens(query)
    if not tokens:
        raise ValueError("empty search query")
    operator = " AND " if mode == "and" else " OR "
    return operator.join(f'"{token}"' for token in tokens)


def search_chunks(
    connection: sqlite3.Connection,
    doc_id: str,
    query: str,
    *,
    limit: int = 12,
    mode: str = "or",
) -> list[sqlite3.Row]:
    if limit < 1 or limit > 12:
        raise ValueError("chunk cap is 12")
    match = fts_match_query(query, mode=mode)
    return list(
        connection.execute(
            """
            SELECT c.ev_id, c.doc_id, c.page_no, c.section, c.heading, c.char_start,
                   c.char_end, c.text, c.sentence_ids, bm25(chunks_fts) AS rank
            FROM chunks_fts
            JOIN chunks c ON c.rowid = chunks_fts.rowid
            WHERE chunks_fts MATCH ? AND c.doc_id = ?
            ORDER BY rank
            LIMIT ?
            """,
            (match, doc_id, limit),
        )
    )


def search_sections(
    connection: sqlite3.Connection, doc_id: str, query: str, *, limit: int = 12
) -> list[str]:
    """Return section labels whose heading matches the query (heading search)."""
    tokens = fts_tokens(query)
    if not tokens:
        return []
    sections: list[str] = []
    for row in connection.execute(
        "SELECT DISTINCT section FROM chunks WHERE doc_id = ? AND section IS NOT NULL",
        (doc_id,),
    ):
        label = str(row["section"]).lower()
        if any(token.lower() in label for token in tokens):
            sections.append(str(row["section"]))
    return sections[:limit]
