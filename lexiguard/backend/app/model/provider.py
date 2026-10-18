
"""LLMProvider: the only way application code talks to a model (Guide 3.4)."""
from __future__ import annotations

from typing import Protocol

from app.schemas.model_io import ModelAnswer, NextAction, RouterProposal


class LLMProvider(Protocol):
    """Narrow, typed interface. No arbitrary URLs or models are exposed to clients."""

    def answer_from_evidence(
        self,
        *,
        messages: list[dict[str, str]],
    ) -> ModelAnswer:
        ...

    def route_proposal(self, *, question: str) -> RouterProposal | None:
        ...

    def expand_query(self, *, question: str, topic: str | None) -> list[str] | None:
        ...

    def next_action(
        self,
        *,
        question: str,
        evidence_block: str,
        known_refs: list[str],
        page_count: int,
    ) -> NextAction:
        ...

    def unload(self) -> bool:
        ...
