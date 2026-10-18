"""POST /api/documents/{id}/review -> deterministic, attention-first review."""
from __future__ import annotations

from fastapi import APIRouter, Request

from app.api._deps import map_data_error, settings_of
from app.schemas.response import ReviewResponse
from app.services.lifecycle import InvalidDocumentId
from app.services.review import build_review

router = APIRouter()


@router.post("/api/documents/{document_id}/review", response_model=ReviewResponse)
def review(document_id: str, request: Request) -> ReviewResponse:
    settings = settings_of(request)
    try:
        return build_review(settings, document_id)
    except (LookupError, FileNotFoundError, InvalidDocumentId) as exc:
        raise map_data_error(exc) from exc
