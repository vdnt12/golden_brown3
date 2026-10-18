
"""Untrusted model I/O schemas.

ModelAnswer may contain content only: no quotes, pages, sections, statuses,
policy flags or verdicts. Unknown keys are rejected at every level. The simple
JSON Schema sent to Ollama is derived from these models but never trusted;
Pydantic validation is the real gate (Guide 3.2a, 8.4).
"""
from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.enums import PointKind, Route

SID_PATTERN = re.compile(r"^s_\d{4,8}$")
POINT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,16}$")


class ModelPoint(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    point_id: str = Field(min_length=1, max_length=16)
    kind: PointKind
    text: str = Field(min_length=1, max_length=600)
    sids: list[str] = Field(default_factory=list, max_length=6)

    @field_validator("point_id")
    @classmethod
    def _point_id_shape(cls, value: str) -> str:
        if not POINT_ID_PATTERN.fullmatch(value):
            raise ValueError("point_id must be a short identifier")
        return value

    @field_validator("sids")
    @classmethod
    def _sids_shape(cls, value: list[str]) -> list[str]:
        for sid in value:
            if not SID_PATTERN.fullmatch(sid):
                raise ValueError(f"invalid sid format: {sid!r}")
        if len(set(value)) != len(value):
            raise ValueError("duplicate sid in point")
        return value

    @model_validator(mode="after")
    def _citation_requirement(self) -> ModelPoint:
        # GENERAL_EXPLANATION must not cite document sentences; every other
        # kind needs at least one sid here (section-level checks come later).
        if self.kind is PointKind.GENERAL_EXPLANATION:
            if self.sids:
                raise ValueError("GENERAL_EXPLANATION must not cite document sids")
        elif not self.sids:
            raise ValueError(f"{self.kind} requires at least one sid")
        return self


class ModelAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # An empty list is a valid, useful answer: it means "the evidence does not
    # support any point". The runtime then applies the silence gate instead of
    # treating the reply as a provider failure.
    points: list[ModelPoint] = Field(default_factory=list, max_length=12)

    @model_validator(mode="after")
    def _unique_point_ids(self) -> ModelAnswer:
        ids = [p.point_id for p in self.points]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate point_id")
        return self


class RouterProposal(BaseModel):
    """Advice only; the backend merges it with the deterministic route."""

    model_config = ConfigDict(extra="forbid")

    proposed_route: Route
    topics: list[str] = Field(default_factory=list, max_length=5)
    needs_clarification: bool = False

    @field_validator("topics")
    @classmethod
    def _topic_shape(cls, value: list[str]) -> list[str]:
        for topic in value:
            if not re.fullmatch(r"[a-z0-9 _-]{2,40}", topic):
                raise ValueError(f"invalid topic label: {topic!r}")
        return value


class NextActionActionSpelling(str):
    pass


class NextAction(BaseModel):
    """Flat refinement action executed by LexiGuard code, not Ollama tools[].

    (Guide 2.3 / Appendix A4.) Never add a `tools` key to an Ollama request.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    action: str = Field(pattern=r"^(SEARCH|GET_SECTION|GET_PAGE|FIND_RELATED|CHECK_SILENCE|ANSWER)$")
    query: str | None = Field(default=None, max_length=120)
    topic: str | None = Field(default=None, max_length=40)
    ref: str | None = Field(default=None, max_length=32)
    page: int | None = Field(default=None, ge=1)
    section: str | None = Field(default=None, max_length=40)

    @model_validator(mode="after")
    def _required_fields(self) -> NextAction:
        required = {
            "SEARCH": ("query",),
            "GET_SECTION": ("section",),
            "GET_PAGE": ("page",),
            "FIND_RELATED": ("ref",),
            "CHECK_SILENCE": ("topic",),
            "ANSWER": (),
        }[self.action]
        for name in required:
            if getattr(self, name) in (None, ""):
                raise ValueError(f"{self.action} requires {name}")
        return self
