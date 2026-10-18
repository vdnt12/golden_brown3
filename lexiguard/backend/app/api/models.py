"""GET /api/models: which supported local models are installed.

Only the three allowlisted tags are reported. No file paths, no Ollama version,
no arbitrary tags from the daemon are echoed.
"""
from __future__ import annotations

from fastapi import APIRouter, Request

from app.api._deps import settings_of
from app.model.factory import model_inventory

router = APIRouter()


@router.get("/api/models")
def models(request: Request) -> dict[str, object]:
    return {"models": model_inventory(settings_of(request))}
