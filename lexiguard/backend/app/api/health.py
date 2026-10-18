"""GET /api/health: runtime capability, token-protected.

v3.2 exposes the pinned model tag and digest so a reviewer can confirm which
weights are in use. It still exposes no paths, prompts, documents or
environment values.
"""
from __future__ import annotations

from fastapi import APIRouter, Request

from app.api._deps import settings_of
from app.ingest.pipeline import PARSER_VERSION
from app.model.factory import model_available, model_inventory

router = APIRouter()


@router.get("/api/health")
def health(request: Request) -> dict[str, object]:
    settings = settings_of(request)
    available = model_available(settings)
    return {
        "status": "ok" if available else "degraded",
        "local_model_available": available,
        "model_tag": settings.model_tag,
        "model_digest": settings.model_digest or None,
        "parser_engine": f"pypdfium2 ({PARSER_VERSION})",
        "storage_backend": "sqlite-fts5",
        # Additive: the picker needs per-model availability and OCR status.
        "models": {str(row["alias"]): bool(row["available"]) for row in model_inventory(settings)},
        "ocr_available": __import__("app.ingest.ocr", fromlist=["ocr_available"]).ocr_available(),
        "history_enabled": settings.history_enabled,
    }
