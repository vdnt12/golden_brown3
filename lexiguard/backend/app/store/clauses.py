"""Clause-map persistence (deterministic grouping only)."""
from __future__ import annotations

import json
import sqlite3

from app.retrieval.clause_map import ClauseMap


def replace_clause_map(connection: sqlite3.Connection, doc_id: str, clause_map: ClauseMap) -> None:
    connection.execute("DELETE FROM clauses WHERE doc_id = ?", (doc_id,))
    connection.executemany(
        "INSERT INTO clauses (clause_id, doc_id, label, heading, page_no, topics) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        # Clause labels repeat in real contracts (two "Notices" headings, a heading
        # that reappears per page). The id must be positional, not label-based.
        [
            (
                f"{doc_id}:{index:04d}:{entry.label}"[:200],
                doc_id,
                entry.label[:200],
                entry.label[:200],
                entry.page,
                json.dumps([]),
            )
            for index, entry in enumerate(clause_map.entries)
        ],
    )
    connection.commit()


def list_clauses(connection: sqlite3.Connection, doc_id: str) -> list[sqlite3.Row]:
    return list(
        connection.execute(
            "SELECT * FROM clauses WHERE doc_id = ? ORDER BY page_no", (doc_id,)
        )
    )
