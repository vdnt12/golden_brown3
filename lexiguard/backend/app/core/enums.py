"""
Closed enums owned by the backend.

The model never returns any of these as policy. Route and ResponseStatus are
computed by deterministic code after validation (Guide 8.2, 10.1).

v3.2 additions: `UNSUPPORTED_LANGUAGE` (document has no readable English
pages) and `CardStatus` for document-map / review cards, where PRD FR-007
requires `NOT_ASSESSED` for pages that could not be read.
"""
from __future__ import annotations

from enum import StrEnum


class PointKind(StrEnum):
    """Permitted ModelAnswer point kinds (Guide 8.4)."""

    STATED = "STATED"
    RESTATEMENT = "RESTATEMENT"
    INTERPRETATION = "INTERPRETATION"
    CONCERN = "CONCERN"
    AMBIGUITY = "AMBIGUITY"
    CONFLICT = "CONFLICT"
    GENERAL_EXPLANATION = "GENERAL_EXPLANATION"


class Route(StrEnum):
    FACT_LOOKUP = "FACT_LOOKUP"
    MULTI_CLAUSE_ANALYSIS = "MULTI_CLAUSE_ANALYSIS"
    DOCUMENT_MAP = "DOCUMENT_MAP"
    REVIEW_SCAN = "REVIEW_SCAN"
    DOCUMENT_SILENCE_CHECK = "DOCUMENT_SILENCE_CHECK"
    AMBIGUITY_OR_CONFLICT = "AMBIGUITY_OR_CONFLICT"
    TERM_EXPLANATION = "TERM_EXPLANATION"
    LEGAL_CONCLUSION = "LEGAL_CONCLUSION"
    EXTERNAL_LAW_REQUIRED = "EXTERNAL_LAW_REQUIRED"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class Classification(StrEnum):
    """Per-point classification shown to the user (Guide 10.1)."""

    DIRECT = "DIRECT"
    SUPPORTED = "SUPPORTED"
    INTERPRETIVE = "INTERPRETIVE"
    AMBIGUOUS = "AMBIGUOUS"
    CONFLICTING = "CONFLICTING"
    GENERAL_EXPLANATION = "GENERAL_EXPLANATION"
    NOT_LOCATED = "NOT_LOCATED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class ResponseStatus(StrEnum):
    """Overall answer status. Backend-owned, never model-supplied."""

    ANSWERED = "ANSWERED"
    LIMITED = "LIMITED"
    NOT_LOCATED = "NOT_LOCATED"
    AMBIGUOUS = "AMBIGUOUS"
    CONFLICTING = "CONFLICTING"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    LEGAL_LIMIT = "LEGAL_LIMIT"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    UNSUPPORTED_LANGUAGE = "UNSUPPORTED_LANGUAGE"
    ERROR_LOCAL_MODEL_UNAVAILABLE = "ERROR_LOCAL_MODEL_UNAVAILABLE"
    ERROR_PROCESSING = "ERROR_PROCESSING"


class CardStatus(StrEnum):
    """Status of one document-map or review card (PRD FR-007)."""

    FOUND = "FOUND"
    NOT_LOCATED = "NOT_LOCATED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NOT_ASSESSED = "NOT_ASSESSED"


class MissingInfoCode(StrEnum):
    """Closed enum for backend-authored missing-information messages."""

    UNREADABLE_CONTENT = "UNREADABLE_CONTENT"
    UNREAD_LANGUAGE = "UNREAD_LANGUAGE"
    REFERENCED_MATERIAL_NOT_PROVIDED = "REFERENCED_MATERIAL_NOT_PROVIDED"
    TOPIC_NOT_LOCATED = "TOPIC_NOT_LOCATED"
    CONTEXT_REQUIRED = "CONTEXT_REQUIRED"


class RunPath(StrEnum):
    FAST = "FAST"              # exactly one answer call
    REFINEMENT = "REFINEMENT"  # one refinement call + one answer call


# Guide 10.1 precedence, extended by v3.2. ERROR_PROCESSING is placed before
# ERROR_LOCAL_MODEL_UNAVAILABLE because, when both are recorded, processing
# failed while handling the model failure. UNSUPPORTED_LANGUAGE outranks the
# legal/ambiguity statuses: if the document cannot be read, no document claim
# below it can be trusted.
STATUS_PRECEDENCE: tuple[ResponseStatus, ...] = (
    ResponseStatus.ERROR_PROCESSING,
    ResponseStatus.ERROR_LOCAL_MODEL_UNAVAILABLE,
    ResponseStatus.UNSUPPORTED_LANGUAGE,
    ResponseStatus.LEGAL_LIMIT,
    ResponseStatus.CONFLICTING,
    ResponseStatus.AMBIGUOUS,
    ResponseStatus.INSUFFICIENT_EVIDENCE,
    ResponseStatus.NOT_LOCATED,
    ResponseStatus.LIMITED,
    ResponseStatus.OUT_OF_SCOPE,
    ResponseStatus.ANSWERED,
)


def resolve_status(statuses: set[ResponseStatus] | list[ResponseStatus]) -> ResponseStatus:
    """Return the highest-precedence status present (Guide 10.1).

    OUT_OF_SCOPE applies when no higher-priority failure/limitation applies, so
    it sits above ANSWERED. An empty set raises: callers must not pass an empty
    set to mean failure.
    """
    present = set(statuses)
    for status in STATUS_PRECEDENCE:
        if status in present:
            return status
    raise ValueError("resolve_status requires at least one status")
