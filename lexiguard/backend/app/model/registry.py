"""The set of local models this build may call.

Hermes here means the **Hermes model family served by Ollama**, not the Hermes
Agent framework. Both families go through the same native `/api/chat` JSON
schema path and the same backend validation; no model is trusted with quotes,
pages, sections or statuses. (ADR-0011.)

Only tags listed here can be selected. A client cannot ask the server to load an
arbitrary model from the registry or the internet.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings


class UnknownModel(ValueError):
    """Raised when a request names a model this build does not support."""


@dataclass(frozen=True)
class ModelSpec:
    alias: str
    tag: str
    label: str
    role: str  # primary | low-memory | alternate


def model_specs(settings: Settings) -> list[ModelSpec]:
    return [
        ModelSpec(
            alias="gemma",
            tag=settings.model_tag,
            label="Gemma 4 E4B (primary)",
            role="primary",
        ),
        ModelSpec(
            alias="gemma-e2b",
            tag=settings.model_alt_tag,
            label="Gemma 4 E2B (low memory)",
            role="low-memory",
        ),
        ModelSpec(
            alias="hermes",
            tag=settings.hermes_model_tag,
            label="Hermes (alternate local model)",
            role="alternate",
        ),
    ]


def resolve_model(settings: Settings, value: str | None) -> str:
    """Accept an alias or an exact configured tag; return the tag."""
    if not value:
        return settings.model_tag
    needle = value.strip()
    for spec in model_specs(settings):
        if needle == spec.alias or needle == spec.tag:
            return spec.tag
    raise UnknownModel(f"unsupported model: {needle}")


def alias_for_tag(settings: Settings, tag: str) -> str:
    for spec in model_specs(settings):
        if spec.tag == tag:
            return spec.alias
    return tag


def installed_tags(settings: Settings, *, timeout_s: float = 2.0) -> set[str] | None:
    """Return tags reported by local Ollama, or None when it cannot be reached."""
    import httpx

    try:
        response = httpx.get(f"{settings.ollama_url}/api/tags", timeout=timeout_s)
    except Exception:  # noqa: BLE001 - unreachable is a normal state
        return None
    if response.status_code != 200:
        return None
    try:
        payload = response.json()
    except ValueError:
        return None
    tags: set[str] = set()
    for model in payload.get("models", []):
        name = str(model.get("name") or model.get("model") or "").strip()
        if name:
            tags.add(name)
    return tags


def availability(settings: Settings) -> list[dict[str, object]]:
    tags = installed_tags(settings)
    rows: list[dict[str, object]] = []
    for spec in model_specs(settings):
        present = bool(tags is not None and spec.tag in tags)
        rows.append(
            {
                "alias": spec.alias,
                "tag": spec.tag,
                "label": spec.label,
                "role": spec.role,
                "available": present,
                "ollama_reachable": tags is not None,
                "default": spec.tag == settings.model_tag,
            }
        )
    return rows
