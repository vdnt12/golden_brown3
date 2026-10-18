
"""Fixed, read-only, document-bound tools (Guide 2.2).

Seven tools exist. Only five are model-selectable through NextAction;
get_evidence and get_document_map are runtime-initiated. No tool accepts a
document_id: the document is bound out-of-band in DocumentContext.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.schemas.model_io import NextAction


class ToolName(StrEnum):
    SEARCH_DOCUMENT = "search_document"
    GET_EVIDENCE = "get_evidence"
    GET_PAGE = "get_page"
    GET_SECTION = "get_section"
    GET_DOCUMENT_MAP = "get_document_map"
    FIND_RELATED_CLAUSES = "find_related_clauses"
    CHECK_DOCUMENT_SILENCE = "check_document_silence"


MODEL_SELECTABLE: frozenset[ToolName] = frozenset(
    {
        ToolName.SEARCH_DOCUMENT,
        ToolName.GET_PAGE,
        ToolName.GET_SECTION,
        ToolName.FIND_RELATED_CLAUSES,
        ToolName.CHECK_DOCUMENT_SILENCE,
    }
)

ACTION_TO_TOOL: dict[str, ToolName] = {
    "SEARCH": ToolName.SEARCH_DOCUMENT,
    "GET_SECTION": ToolName.GET_SECTION,
    "GET_PAGE": ToolName.GET_PAGE,
    "FIND_RELATED": ToolName.FIND_RELATED_CLAUSES,
    "CHECK_SILENCE": ToolName.CHECK_DOCUMENT_SILENCE,
}

MAX_QUERY_CHARS = 120


class ToolRejected(Exception):
    pass


@dataclass(frozen=True)
class ToolContext:
    document_id: str
    page_count: int
    known_refs: frozenset[str]


def validate_next_action(action: NextAction, context: ToolContext) -> ToolName:
    """Validate an untrusted NextAction before any tool executes (Guide 2.3)."""
    if action.query is not None and len(action.query) > MAX_QUERY_CHARS:
        raise ToolRejected("query over length cap")
    if action.action == "ANSWER":
        raise ToolRejected("ANSWER is not a tool call")
    if action.action == "GET_PAGE" and (
        action.page is None or not (1 <= action.page <= context.page_count)
    ):
        raise ToolRejected("page outside document")
    if action.action == "FIND_RELATED" and (
        action.ref is None or action.ref not in context.known_refs
    ):
        raise ToolRejected("ref was not returned earlier in this run")
    tool = ACTION_TO_TOOL[action.action]
    if tool not in MODEL_SELECTABLE:
        raise ToolRejected("tool is not model-selectable")
    return tool
