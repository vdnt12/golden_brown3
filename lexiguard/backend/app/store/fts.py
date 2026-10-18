
"""FTS maintenance helpers (light wrappers; queries live in app.retrieval.lexical)."""
from __future__ import annotations

import sqlite3

from app.store.chunks import ChunkInsert, insert_chunk


def index_chunk(connection: sqlite3.Connection, doc_id: str, chunk: ChunkInsert) -> None:
    insert_chunk(connection, doc_id, chunk)
    connection.commit()


def rebuild(connection: sqlite3.Connection) -> None:
    connection.execute("INSERT INTO chunks_fts(chunks_fts) VALUES ('rebuild')")
    connection.commit()


def purge_document(connection: sqlite3.Connection, doc_id: str) -> None:
    """Remove rows and FTS shadows for one document (deletion step 4)."""
    connection.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))  # triggers FTS delete
    connection.execute("DELETE FROM sentences WHERE doc_id = ?", (doc_id,))
    connection.execute("DELETE FROM clauses WHERE doc_id = ?", (doc_id,))
    connection.execute("DELETE FROM relationships WHERE doc_id = ?", (doc_id,))
    connection.execute("DELETE FROM run_ledger WHERE doc_id = ?", (doc_id,))
    connection.execute("DELETE FROM pages WHERE doc_id = ?", (doc_id,))
    connection.execute("DELETE FROM document WHERE doc_id = ?", (doc_id,))
    connection.commit()
