"""Provider construction and availability probes.

Every provider is the same loopback Ollama adapter; the difference is the model
tag. There is no cloud fallback: if the local runtime is down the caller returns
ERROR_LOCAL_MODEL_UNAVAILABLE (ADR-0002, ADR-0010, ADR-0011).
"""
from __future__ import annotations

from app.config import Settings
from app.model.ollama_native import OllamaNativeProvider
from app.model.registry import availability, installed_tags, resolve_model


def build_provider(
    settings: Settings, model_tag: str | None = None
) -> OllamaNativeProvider:
    tag = resolve_model(settings, model_tag)
    return OllamaNativeProvider(
        base_url=settings.ollama_url,
        model=tag,
        num_ctx=settings.num_ctx,
        seed=settings.seed,
        temperature=settings.temperature,
        timeout_s=settings.model_timeout_s,
    )


def model_available(settings: Settings, *, timeout_s: float = 2.0) -> bool:
    """True only when the default tag is installed locally. Booleans only."""
    tags = installed_tags(settings, timeout_s=timeout_s)
    return bool(tags is not None and settings.model_tag in tags)


def model_inventory(settings: Settings) -> list[dict[str, object]]:
    return availability(settings)
