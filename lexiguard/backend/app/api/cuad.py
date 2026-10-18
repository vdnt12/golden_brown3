"""GET /api/documents/{document_id}/cuad -> CUAD Atticus contract analysis."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from app.api._deps import map_data_error, settings_of
from app.services.cuad_service import analyze_cuad
from app.services.lifecycle import InvalidDocumentId
from app.store.repo import DocumentNotFound

router = APIRouter()


@router.get("/api/documents/{document_id}/cuad")
def get_cuad_analysis(document_id: str, request: Request) -> dict[str, Any]:
    settings = settings_of(request)
    try:
        return analyze_cuad(settings, document_id)
    except (DocumentNotFound, LookupError, FileNotFoundError, InvalidDocumentId) as exc:
        raise map_data_error(exc) from exc
