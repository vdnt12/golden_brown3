"""Document use cases: list, describe, read a page, delete.

No HTTP and no SQL construction here: routes call these functions, and every
path comes from `services.lifecycle.document_dir` (validated 32-hex ids).
"""
from __future__ import annotations

import ast
from pathlib import Path

from app.config import Settings
from app.ingest.parser import render_page_image
from app.ingest.pipeline import source_path
from app.schemas.response import (
    DeletionResponse,
    DocumentRef,
    DocumentSummary,
    EvidenceResponse,
    PageResponse,
    PageSentence,
)
from app.services.lifecycle import InvalidDocumentId, document_dir
from app.store import pages as pages_store
from app.store import sentences as sentences_store
from app.store.fts import purge_document
from app.store.repo import DB_NAME, DocumentNotFound, open_document


class DocumentGone(LookupError):
    pass


def _as_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        value = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def list_documents(settings: Settings) -> list[DocumentSummary]:
    root = (Path(settings.data_dir) / "docs").resolve()
    if not root.exists():
        return []
    summaries: list[DocumentSummary] = []
    for directory in sorted(root.iterdir()):
        if not directory.is_dir() or not (directory / DB_NAME).exists():
            continue
        try:
            handle = open_document(settings.data_dir, directory.name)
        except (DocumentNotFound, InvalidDocumentId):
            continue
        try:
            row = handle.connection.execute("SELECT * FROM document").fetchone()
            if row is None:
                continue
            unread = _as_list(row["language_flags"])
            summaries.append(
                DocumentSummary(
                    document_id=row["doc_id"],
                    display_name=row["source_filename"] or "document",
                    source_kind=row["source_kind"],
                    page_count=int(row["page_count"]),
                    sha256=row["sha256"],
                    created_at=row["created_at"],
                    readable_pages=max(0, int(row["page_count"]) - len([u for u in unread if str(u).isdigit()])),
                    unread_pages=len([u for u in unread if str(u).isdigit()]),
                    ocr_used=bool(row["ocr_used"]),
                    quality_flags=_as_list(row["quality_flags"]),
                )
            )
        finally:
            handle.close()
    summaries.sort(key=lambda item: item.created_at, reverse=True)
    return summaries


def document_ref(settings: Settings, doc_id: str) -> DocumentRef:
    with open_document(settings.data_dir, doc_id) as handle:
        row = handle.connection.execute("SELECT * FROM document").fetchone()
        if row is None:
            raise DocumentGone(doc_id)
        return DocumentRef(
            document_id=row["doc_id"],
            display_name=row["source_filename"] or "document",
            page_count=int(row["page_count"]),
            sha256=row["sha256"],
        )


def read_page(settings: Settings, doc_id: str, page_no: int) -> PageResponse:
    with open_document(settings.data_dir, doc_id) as handle:
        row = pages_store.get_page(handle.connection, doc_id, page_no)
        if row is None:
            raise DocumentGone(f"{doc_id}:{page_no}")
        sentences = sentences_store.get_page_sentences(handle.connection, doc_id, page_no)
        source_kind = handle.connection.execute(
            "SELECT source_kind FROM document WHERE doc_id = ?", (doc_id,)
        ).fetchone()
        return PageResponse(
            document_id=doc_id,
            page_number=page_no,
            # A .txt has no physical pages: its page 1 is a virtual page and the
            # UI must say so rather than imply a scan was read.
            is_virtual_page=bool(
                source_kind is not None and source_kind["source_kind"] == "txt"
            ),
            ocr_used=any(bool(s["ocr_derived"]) for s in sentences),
            text=row["text"],
            flags=_as_list(row["flags"]),
            sentences=[
                PageSentence(
                    sid=s["sid"],
                    start_offset=int(s["char_start"]),
                    end_offset=int(s["char_end"]),
                    text=s["text"],
                    section=s["section"],
                    ocr_derived=bool(s["ocr_derived"]),
                )
                for s in sentences
            ],
        )


def read_evidence(settings: Settings, doc_id: str, evidence_id: str) -> EvidenceResponse:
    """One stored sentence by id, with the hash of the exact text returned."""
    import hashlib

    with open_document(settings.data_dir, doc_id) as handle:
        row = handle.connection.execute(
            "SELECT s.*, d.sha256 AS doc_sha FROM sentences s "
            "JOIN document d ON d.doc_id = s.doc_id "
            "WHERE s.doc_id = ? AND s.sid = ?",
            (doc_id, evidence_id),
        ).fetchone()
        if row is None:
            raise DocumentGone(evidence_id)
        text = str(row["text"])
        return EvidenceResponse(
            evidence_id=str(row["sid"]),
            document_hash=str(row["doc_sha"]),
            page=int(row["page_no"]),
            section=row["section"],
            sids=[str(row["sid"])],
            verbatim_text=text,
            text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            ocr_derived=bool(row["ocr_derived"]),
        )


def page_image(settings: Settings, doc_id: str, page_no: int) -> bytes:
    source = source_path(settings.data_dir, doc_id)
    if source.suffix.lower() != ".pdf":
        raise DocumentGone("page images exist only for PDF sources")
    data = source.read_bytes()
    return render_page_image(data, page_no)


def delete_document(settings: Settings, doc_id: str, *, provider=None) -> DeletionResponse:
    """Remove app-controlled data and report exactly what was verified."""
    from app.services.lifecycle import delete_document as delete_directory
    from app.store.repo import database_path

    directory = document_dir(settings.data_dir, doc_id)
    db_path = database_path(settings.data_dir, doc_id)
    if db_path.exists():
        # Close cleanly and purge derived rows before removing files.
        with open_document(settings.data_dir, doc_id) as handle:
            purge_document(handle.connection, doc_id)
            handle.connection.execute("PRAGMA secure_delete = ON")
            handle.connection.execute("VACUUM")
    unloaded = False
    if provider is not None:
        try:
            unloaded = bool(provider.unload())
        except Exception:  # noqa: BLE001 - unload failure is reported, not raised
            unloaded = False

    canaries = [f"CANARY-LG-{doc_id[:8].upper()}"]
    report = delete_directory(
        data_root=settings.data_dir,
        doc_id=doc_id,
        canaries=canaries,
        scan_paths=[Path(settings.data_dir)],
    )
    remaining = []
    if directory.exists():
        remaining = [str(path) for path in directory.rglob("*") if path.is_file()]
    removed_files = int(report.removed_files)
    directory_gone = report.directory_removed and not directory.exists()
    return DeletionResponse(
        document_id=doc_id,
        files_purged=removed_files,
        database_unlinked=directory_gone,
        model_cache_evicted=unloaded,
        canary_scan_passed=not report.canary_hits,
        forensic_erasure_disclaimer=(
            "App-controlled files and their SQLite index were deleted and their absence "
            "verified. This is not forensic erasure: SSD wear-levelling, OS swap or "
            "hibernation files, filesystem journals and external backups are outside the "
            "application's control."
        ),
        remaining_derived_files=remaining,
        session_binding_cleared=True,
        notes=[
            "App-controlled files for this document were removed and their absence verified.",
            "This is not forensic erasure: SSD wear-levelling, OS swap/hibernation, "
            "external backups and filesystem journals are outside the application's control.",
            "The document id is dropped from this session; requests for it now return 404.",
        ],
    )
