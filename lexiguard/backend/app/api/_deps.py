"""Shared route helpers: settings, data access errors, honest error bodies."""
from __future__ import annotations

from fastapi import HTTPException, Request

from app.config import Settings
from app.model.factory import build_provider
from app.model.registry import UnknownModel, resolve_model
from app.services.lifecycle import InvalidDocumentId
from app.store.repo import DocumentNotFound


def settings_of(request: Request) -> Settings:
    return request.app.state.settings


def provider_of(request: Request):
    return getattr(request.app.state, "provider", None)


def provider_for(request: Request, model: str | None):
    """Resolve a model alias/tag to a provider, reusing the startup default.

    Raises UnknownModel for anything outside the allowlist (mapped to 422 by the
    route) and returns None when the local runtime cannot construct a provider.
    """
    settings = settings_of(request)
    try:
        tag = resolve_model(settings, model)
    except UnknownModel as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if tag == settings.model_tag:
        return provider_of(request), tag
    try:
        return build_provider(settings, tag), tag
    except Exception:  # noqa: BLE001 - unavailable runtime is a normal, reported state
        return None, tag


def not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="Document not found.")


def map_data_error(exc: Exception) -> HTTPException:
    if isinstance(exc, (DocumentNotFound, InvalidDocumentId, LookupError, FileNotFoundError)):
        return not_found()
    return HTTPException(status_code=500, detail="The request could not be completed.")
