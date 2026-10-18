"""Sentence rows: stable sids and offsets into normalised page text (Guide 5.2)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class SentenceInsert:
    sid: str
    page_no: int
    section: str | None
    char_start: int
    char_end: int
    text: str
    ocr_derived: bool = False
    heading: str | None = None


def insert_sentences(connection: sqlite3.Connection, doc_id: str, rows: list[SentenceInsert]) -> None:
    connection.executemany(
        "INSERT INTO sentences (sid, doc_id, page_no, section, heading, char_start, char_end, "
        "text, ocr_derived) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                r.sid,
                doc_id,
                r.page_no,
                r.section,
                r.heading,
                r.char_start,
                r.char_end,
                r.text,
                int(r.ocr_derived),
            )
            for r in rows
        ],
    )
    connection.commit()


def get_sentence(connection: sqlite3.Connection, doc_id: str, sid: str) -> sqlite3.Row | None:
    return connection.execute(
        "SELECT * FROM sentences WHERE doc_id = ? AND sid = ?", (doc_id, sid)
    ).fetchone()


def get_sentences(connection: sqlite3.Connection, doc_id: str, sids: list[str]) -> list[sqlite3.Row]:
    if not sids:
        return []
    placeholders = ",".join("?" for _ in sids)
    rows = list(
        connection.execute(
            f"SELECT * FROM sentences WHERE doc_id = ? AND sid IN ({placeholders})",
            (doc_id, *sids),
        )
    )
    order = {sid: index for index, sid in enumerate(sids)}
    rows.sort(key=lambda row: order.get(row["sid"], 0))
    return rows


def get_page_sentences(connection: sqlite3.Connection, doc_id: str, page_no: int) -> list[sqlite3.Row]:
    return list(
        connection.execute(
            "SELECT * FROM sentences WHERE doc_id = ? AND page_no = ? ORDER BY char_start",
            (doc_id, page_no),
        )
    )


def all_sentences(connection: sqlite3.Connection, doc_id: str) -> list[sqlite3.Row]:
    return list(
        connection.execute(
            "SELECT * FROM sentences WHERE doc_id = ? ORDER BY page_no, char_start", (doc_id,)
        )
    )


def count_sentences(connection: sqlite3.Connection, doc_id: str) -> int:
    row = connection.execute(
        "SELECT COUNT(*) AS n FROM sentences WHERE doc_id = ?", (doc_id,)
    ).fetchone()
    return int(row["n"])
