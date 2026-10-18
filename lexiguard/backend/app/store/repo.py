"""Per-document database handle.

`data/docs/<doc_id>/doc.sqlite3` is opened once per request, used through the
small store functions, and always closed. Paths are built only from a validated
32-hex document id (services.lifecycle.document_dir).
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from app.services.lifecycle import document_dir
from app.store.db import init_db

DB_NAME = "doc.sqlite3"


class DocumentNotFound(LookupError):
    pass


def database_path(data_root: str | Path, doc_id: str) -> Path:
    return document_dir(data_root, doc_id) / DB_NAME


@dataclass
class DocumentHandle:
    doc_id: str
    directory: Path
    connection: sqlite3.Connection

    @property
    def sha256(self) -> str:
        row = self.connection.execute(
            "SELECT sha256 FROM document WHERE doc_id = ?", (self.doc_id,)
        ).fetchone()
        return str(row["sha256"]) if row else ""

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> DocumentHandle:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def open_document(data_root: str | Path, doc_id: str) -> DocumentHandle:
    directory = document_dir(data_root, doc_id)
    path = directory / DB_NAME
    if not path.exists():
        raise DocumentNotFound(doc_id)
    connection = init_db(path)
    row = connection.execute("SELECT 1 FROM document WHERE doc_id = ?", (doc_id,)).fetchone()
    if row is None:
        connection.close()
        raise DocumentNotFound(doc_id)
    return DocumentHandle(doc_id=doc_id, directory=directory, connection=connection)
