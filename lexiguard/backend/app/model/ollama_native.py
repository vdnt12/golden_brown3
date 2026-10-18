
"""Ollama native /api/chat adapter (Guide 3.2, 3.2a).

Hard rules encoded here:
  * POST {base}/api/chat, never /v1
  * stream=false, think=false, format=<simple app schema>
  * options: fixed seed, temperature 0, num_ctx (always sent)
  * NO `tools` key, ever (T-MODEL-NOTOOLS-01)
  * empty content is a failure even if thinking text exists
  * Pydantic validates every reply; one format-retry only; then fail closed
  * post-check prompt_eval_count + eval_count < num_ctx
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.enums import PointKind
from app.schemas.model_io import ModelAnswer

MODEL_ANSWER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "points": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "point_id": {"type": "string"},
                    "kind": {"type": "string", "enum": [k.value for k in PointKind]},
                    "text": {"type": "string"},
                    "sids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["point_id", "kind", "text", "sids"],
            },
        }
    },
    "required": ["points"],
}


class OllamaError(RuntimeError):
    pass


class ModelUnavailableError(OllamaError):
    pass


class ModelOutputError(OllamaError):
    pass


class ContextOverflowError(OllamaError):
    pass


@dataclass(frozen=True)
class ModelTagCheck:
    tag: str
    digest: str
    size_bytes: int
    matches_expected: bool


def build_chat_payload(
    *,
    model: str,
    messages: list[dict[str, str]],
    format_schema: dict[str, Any],
    seed: int = 42,
    num_ctx: int = 8192,
    temperature: float = 0.0,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "stream": False,
        "think": False,
        "messages": messages,
        "format": format_schema,
        "options": {"seed": seed, "temperature": temperature, "num_ctx": num_ctx},
    }
    if "tools" in payload:  # pragma: no cover - structural guard
        raise AssertionError("tools key must never be sent to Ollama")
    return payload


def assert_context_fits(payload: dict[str, Any], response: dict[str, Any]) -> None:
    num_ctx = int(payload["options"]["num_ctx"])
    prompt_eval = int(response.get("prompt_eval_count") or 0)
    eval_count = int(response.get("eval_count") or 0)
    if prompt_eval + eval_count >= num_ctx:
        raise ContextOverflowError(
            f"prompt_eval_count({prompt_eval}) + eval_count({eval_count}) >= num_ctx({num_ctx})"
        )


def parse_model_tags(tags_payload: dict[str, Any], tag: str) -> ModelTagCheck | None:
    for model in tags_payload.get("models", []):
        name = model.get("name") or model.get("model") or ""
        if name == tag:
            return ModelTagCheck(
                tag=name,
                digest=str(model.get("digest", "")),
                size_bytes=int(model.get("size", 0)),
                matches_expected=True,
            )
    return None


class OllamaNativeProvider:
    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "gemma4:e4b-it-q4_K_M",
        num_ctx: int = 8192,
        seed: int = 42,
        temperature: float = 0.0,
        timeout_s: float = 120.0,
        client: httpx.Client | None = None,
    ) -> None:
        if not base_url.startswith("http://127.0.0.1:"):
            raise ValueError("Ollama base URL must be loopback (127.0.0.1)")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.num_ctx = num_ctx
        self.seed = seed
        self.temperature = temperature
        self.timeout_s = timeout_s
        self._client = client or httpx.Client(timeout=timeout_s)

    def _chat(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        payload = build_chat_payload(
            model=self.model,
            messages=messages,
            format_schema=MODEL_ANSWER_SCHEMA,
            seed=self.seed,
            num_ctx=self.num_ctx,
            temperature=self.temperature,
        )
        try:
            response = self._client.post(f"{self.base_url}/api/chat", json=payload)
        except httpx.HTTPError as exc:
            raise ModelUnavailableError("local model unavailable") from exc
        if response.status_code != 200:
            raise ModelUnavailableError(f"Ollama returned status {response.status_code}")
        body = response.json()
        assert_context_fits(payload, body)
        content = (body.get("message") or {}).get("content") or ""
        if not content.strip():
            raise ModelOutputError("empty model content")
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise ModelOutputError("model content is not JSON") from exc

    def answer_from_evidence(self, *, messages: list[dict[str, str]]) -> ModelAnswer:
        try:
            raw = self._chat(messages)
            return ModelAnswer.model_validate(raw)
        except (ModelOutputError, ValidationError) as first_error:
            # Exactly one format-retry (Guide 8.3). Separate from validation retries.
            retry_messages = [
                *messages,
                {
                    "role": "user",
                    "content": (
                        "Your previous reply was not valid JSON for the required schema. "
                        "Return only the JSON object with a points array; no prose."
                    ),
                },
            ]
            try:
                raw = self._chat(retry_messages)
                return ModelAnswer.model_validate(raw)
            except (ModelOutputError, ValidationError) as second_error:
                raise ModelOutputError(
                    f"model output invalid after one format-retry ({second_error})"
                ) from first_error

    def route_proposal(self, *, question: str) -> None:
        raise NotImplementedError("Phase 4: RouterProposal call (optional, only when unsure).")

    def expand_query(self, *, question: str, topic: str | None) -> None:
        raise NotImplementedError("Phase 3/4: T6 query expansion (refinement path only).")

    def next_action(self, **kwargs: Any) -> None:
        raise NotImplementedError("Phase 4: NextAction refinement (one round maximum).")

    def unload(self) -> bool:
        """Ask Ollama to unload the model now (keep_alive: 0). Verify at Phase 2."""
        try:
            response = self._client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "keep_alive": 0},
            )
        except httpx.HTTPError:
            return False
        return response.status_code == 200
