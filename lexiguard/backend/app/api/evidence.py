"""GET /api/documents/{id}/evidence/{evidence_id} -> one stored sentence, verbatim.

`evidence_id` is the `sid` carried in every citation. The response carries a
SHA-256 of the exact text returned, so a reader can verify that what the UI
shows is what the database holds. No model output, scores or prompts.
"""
from __future__ import annotations

from fastapi import APIRouter, Request

from app.api._deps import map_data_error, settings_of
from app.schemas.response import EvidenceResponse
from app.services.documents import read_evidence
from app.services.lifecycle import InvalidDocumentId
from app.store.repo import DocumentNotFound

router = APIRouter()


@router.get(
    "/api/documents/{document_id}/evidence/{evidence_id}",
    response_model=EvidenceResponse,
)
def evidence(document_id: str, evidence_id: str, request: Request) -> EvidenceResponse:
    settings = settings_of(request)
    try:
        return read_evidence(settings, document_id, evidence_id)
    except (DocumentNotFound, LookupError, FileNotFoundError, InvalidDocumentId) as exc:
        raise map_data_error(exc) from exc
