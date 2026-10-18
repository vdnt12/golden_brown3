"""Chunk/evidence rows and their searchable numeric column."""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

_NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def number_index_text(text: str) -> str:
    """Normalise numbers for FTS matching; no unit conversion."""
    tokens: set[str] = set()
    for raw in _NUM_RE.findall(text):
        cleaned = raw.replace(",", "")
        if cleaned.endswith(".0"):
            cleaned = cleaned[:-2]
        tokens.add(cleaned)
    return " ".join(sorted(tokens))


@dataclass(frozen=True)
class ChunkInsert:
    ev_id: str
    section: str | None
    heading: str | None
    char_start: int
    char_end: int
    text: str
    sentence_ids: list[str]
    page_no: int = 1


def insert_chunk(connection: sqlite3.Connection, doc_id: str, chunk: ChunkInsert) -> None:
    connection.execute(
        "INSERT INTO chunks (ev_id, doc_id, page_no, section, heading, char_start, char_end, "
        "text, numbers, sentence_ids) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            chunk.ev_id,
            doc_id,
            chunk.page_no,
            chunk.section,
            chunk.heading,
            chunk.char_start,
            chunk.char_end,
            chunk.text,
            number_index_text(chunk.text),
            ",".join(chunk.sentence_ids),
        ),
    )


def insert_chunks(
    connection: sqlite3.Connection, doc_id: str, chunks: list[ChunkInsert]
) -> None:
    connection.executemany(
        "INSERT INTO chunks (ev_id, doc_id, page_no, section, heading, char_start, char_end, "
        "text, numbers, sentence_ids) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                c.ev_id,
                doc_id,
                c.page_no,
                c.section,
                c.heading,
                c.char_start,
                c.char_end,
                c.text,
                number_index_text(c.text),
                ",".join(c.sentence_ids),
            )
            for c in chunks
        ],
    )
    connection.commit()


def get_chunk(connection: sqlite3.Connection, doc_id: str, ev_id: str) -> sqlite3.Row | None:
    return connection.execute(
        "SELECT * FROM chunks WHERE doc_id = ? AND ev_id = ?", (doc_id, ev_id)
    ).fetchone()


def count_chunks(connection: sqlite3.Connection, doc_id: str) -> int:
    row = connection.execute(
        "SELECT COUNT(*) AS n FROM chunks WHERE doc_id = ?", (doc_id,)
    ).fetchone()
    return int(row["n"])


def all_chunks(connection: sqlite3.Connection, doc_id: str) -> list[sqlite3.Row]:
    return list(
        connection.execute(
            "SELECT * FROM chunks WHERE doc_id = ? ORDER BY page_no, char_start", (doc_id,)
        )
    )
