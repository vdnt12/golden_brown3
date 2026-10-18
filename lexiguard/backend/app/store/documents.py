
"""Document rows. Filenames are display metadata only and never become paths."""
from __future__ import annotations

import sqlite3
from datetime import UTC, datetime


def create_document(
    connection: sqlite3.Connection,
    *,
    doc_id: str,
    sha256: str,
    source_filename: str | None,
    source_kind: str,
    page_count: int,
    parser_version: str,
    language_flags: str = "[]",
    quality_flags: str = "[]",
    ocr_used: bool = False,
    model_tag: str | None = None,
    model_digest: str | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO document (doc_id, sha256, source_filename, source_kind, page_count,
                              parser_version, language_flags, quality_flags, ocr_used,
                              created_at, model_tag, model_digest)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            doc_id,
            sha256,
            source_filename,
            source_kind,
            page_count,
            parser_version,
            language_flags,
            quality_flags,
            int(ocr_used),
            datetime.now(UTC).isoformat(timespec="seconds"),
            model_tag,
            model_digest,
        ),
    )
    connection.commit()


def get_document(connection: sqlite3.Connection, doc_id: str) -> sqlite3.Row | None:
    return connection.execute("SELECT * FROM document WHERE doc_id = ?", (doc_id,)).fetchone()


def list_documents(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    return list(
        connection.execute(
            "SELECT doc_id, source_kind, page_count, quality_flags, created_at "
            "FROM document ORDER BY created_at DESC"
        )
    )
