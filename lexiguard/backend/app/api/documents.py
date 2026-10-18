"""Document lifecycle endpoints.

Upload validates by content, parses in a child process, segments, stores and
indexes. Delete removes app-controlled data and returns a verification report
that never claims forensic erasure.
"""
from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import Response

from app.api._deps import map_data_error, not_found, provider_of, settings_of
from app.ingest.pipeline import IngestError, ingest_document, warning_code
from app.schemas.response import (
    DeletionResponse,
    DocumentListResponse,
    ExtractionWarning,
    PageResponse,
    QualityMetrics,
    UploadResponse,
)
from app.services import documents as documents_service
from app.services.documents import DocumentGone
from app.services.lifecycle import InvalidDocumentId
from app.store.repo import DocumentNotFound

router = APIRouter()

MAX_UPLOAD_MB = 20


@router.post("/api/documents", status_code=201, response_model=UploadResponse)
def upload_document(request: Request, file: UploadFile = File(...)) -> UploadResponse:  # noqa: B008
    settings = settings_of(request)
    data = file.file.read()
    try:
        result = ingest_document(filename=file.filename, data=data, settings=settings)
    except IngestError as exc:
        status = 413 if exc.code == "FILE_TOO_LARGE" else 422
        raise HTTPException(status_code=status, detail={"code": exc.code, "message": exc.message}) from exc
    created_at = ""
    for existing in documents_service.list_documents(settings):
        if existing.document_id == result.document_id:
            created_at = existing.created_at
            break
    return UploadResponse(
        document_id=result.document_id,
        document_hash=result.sha256,
        display_name=result.display_name,
        source_kind=result.source_kind,
        page_count=result.page_count,
        readable_pages=result.readable_pages,
        quality_metrics=QualityMetrics(
            pages_read=result.readable_pages,
            ocr_used=bool(result.ocr_pages),
            language_detected=result.language_detected,
            garble_ratio=result.garble_ratio,
            hidden_text_detected=result.hidden_text_detected,
        ),
        extraction_warnings=[
            ExtractionWarning(
                code=warning_code(message),
                message=message,
                ocr_derived=warning_code(message) == "OCR_DERIVED",
            )
            for message in result.warnings
        ],
        status="READY" if not result.unread_pages else "PARTIAL",
        created_at=created_at,
    )


@router.get("/api/documents", response_model=DocumentListResponse)
def list_documents(request: Request) -> DocumentListResponse:
    settings = settings_of(request)
    return DocumentListResponse(documents=documents_service.list_documents(settings))


@router.delete("/api/documents/{document_id}", response_model=DeletionResponse)
def delete_document(document_id: str, request: Request) -> DeletionResponse:
    settings = settings_of(request)
    try:
        return documents_service.delete_document(
            settings, document_id, provider=provider_of(request)
        )
    except (DocumentNotFound, InvalidDocumentId, DocumentGone) as exc:
        raise not_found() from exc


@router.get("/api/documents/{document_id}/pages/{page}", response_model=PageResponse)
def get_page(document_id: str, page: int, request: Request) -> PageResponse:
    settings = settings_of(request)
    try:
        return documents_service.read_page(settings, document_id, page)
    except (DocumentNotFound, InvalidDocumentId, DocumentGone) as exc:
        raise map_data_error(exc) from exc


@router.get("/api/documents/{document_id}/pages/{page}/image")
def get_page_image(document_id: str, page: int, request: Request) -> Response:
    settings = settings_of(request)
    try:
        png = documents_service.page_image(settings, document_id, page)
    except (DocumentNotFound, InvalidDocumentId, DocumentGone) as exc:
        raise map_data_error(exc) from exc
    return Response(content=png, media_type="image/png")
