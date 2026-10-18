
"""Page rows: normalised text is the single source for offsets and viewer text."""
from __future__ import annotations

import hashlib
import sqlite3


def insert_page(
    connection: sqlite3.Connection,
    *,
    doc_id: str,
    page_no: int,
    text: str,
    flags: str = "[]",
    printed_label: str | None = None,
) -> None:
    connection.execute(
        "INSERT INTO pages (doc_id, page_no, printed_label, text, text_hash, flags) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (doc_id, page_no, printed_label, text, hashlib.sha256(text.encode()).hexdigest(), flags),
    )


def get_page(connection: sqlite3.Connection, doc_id: str, page_no: int) -> sqlite3.Row | None:
    return connection.execute(
        "SELECT * FROM pages WHERE doc_id = ? AND page_no = ?", (doc_id, page_no)
    ).fetchone()
