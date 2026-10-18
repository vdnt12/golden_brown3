"""GET /api/documents/{id}/overview -> evidence-gated Document Map (11 cards)."""
from __future__ import annotations

from fastapi import APIRouter, Request

from app.api._deps import map_data_error, settings_of
from app.schemas.response import OverviewResponse
from app.services.lifecycle import InvalidDocumentId
from app.services.overview import build_overview

router = APIRouter()


@router.get("/api/documents/{document_id}/overview", response_model=OverviewResponse)
def overview(document_id: str, request: Request) -> OverviewResponse:
    settings = settings_of(request)
    try:
        return build_overview(settings, document_id)
    except (LookupError, FileNotFoundError, InvalidDocumentId) as exc:
        raise map_data_error(exc) from exc
