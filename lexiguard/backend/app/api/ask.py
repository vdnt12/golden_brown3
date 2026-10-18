"""POST /api/documents/{id}/ask -> backend-built RenderedAnswer."""
from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

from app.api._deps import map_data_error, provider_for, settings_of
from app.schemas.response import RenderedAnswer
from app.services.answer import answer_question
from app.services.lifecycle import InvalidDocumentId

router = APIRouter()


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    question: str = Field(min_length=1, max_length=500)
    model: str | None = Field(default=None, max_length=64)
    allow_fallback: bool = Field(default=False)


@router.post("/api/documents/{document_id}/ask", response_model=RenderedAnswer)
def ask(document_id: str, body: AskRequest, request: Request) -> RenderedAnswer:
    settings = settings_of(request)
    provider, model_tag = provider_for(request, body.model)
    try:
        return answer_question(
            settings,
            document_id,
            body.question,
            provider=provider,
            model_tag=model_tag,
            allow_fallback=body.allow_fallback,
        )
    except (LookupError, FileNotFoundError, InvalidDocumentId) as exc:
        raise map_data_error(exc) from exc
