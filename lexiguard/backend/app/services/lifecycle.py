
"""Document deletion coordinator (Guide 5.3).

Validates the server-generated document id, resolves the path only under
data/docs/, and refuses traversal. Removal and canary verification happen in
store.delete; this service owns path safety.
"""
from __future__ import annotations

import re
from pathlib import Path

from app.store.delete import DeletionReport, delete_document_directory

DOC_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


class InvalidDocumentId(ValueError):
    pass


def document_dir(data_root: str | Path, doc_id: str) -> Path:
    if not DOC_ID_PATTERN.fullmatch(doc_id):
        raise InvalidDocumentId("document id must be 32 lowercase hex characters")
    base = (Path(data_root) / "docs").resolve()
    candidate = (base / doc_id).resolve()
    if candidate.parent != base:
        raise InvalidDocumentId("resolved path escapes the documents directory")
    return candidate


def delete_document(
    *,
    data_root: str | Path,
    doc_id: str,
    canaries: list[str] | None = None,
    scan_paths: list[Path] | None = None,
) -> DeletionReport:
    target = document_dir(data_root, doc_id)
    return delete_document_directory(target, canaries=canaries, scan_paths=scan_paths)
