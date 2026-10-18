"""
Backend-owned rendered response (Guide 10.2 / Appendix A3, extended for v3.2).

Only the renderer constructs this object. `legal_verdict` is permanently null;
a model cannot set it because it has no field for it and unknown keys are
rejected on the model side.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import (
    Classification,
    MissingInfoCode,
    ResponseStatus,
    Route,
    RunPath,
)


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sid: str
    page: int = Field(ge=1)
    section: str | None = None
    quote: str = Field(min_length=1)
    ocr_derived: bool = False
    document_sha256: str | None = Field(default=None, min_length=64, max_length=64)


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str
    text: str = Field(min_length=1, max_length=1000)
    classification: Classification
    evidence: list[EvidenceItem] = Field(min_length=1)


class GeneralExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entry_id: str
    term: str
    definition: str
    source: Literal["glossary"] = "glossary"
    disclaimer: str = "General definition, not from your document, and not legal advice."


class MissingInformation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: MissingInfoCode
    message: str = Field(min_length=1)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    searches: list[str] = Field(default_factory=list)


class ExtractionWarning(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    page: int | None = Field(default=None, ge=1)
    ocr_derived: bool = False


class JurisdictionFlag(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: str
    label: str = "May depend on local law -- confirm locally."
    evidence: list[EvidenceItem] = Field(min_length=1)


class EscalationQuestion(BaseModel):
    """A neutral question to take to a qualified professional (PRD FR-008)."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=600)
    topics: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class DocumentRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    display_name: str
    page_count: int = Field(ge=1)
    sha256: str = Field(min_length=64, max_length=64)


class RunMeta(BaseModel):
    """Why-this-answer ledger metadata. Never chain-of-thought or raw prompts."""

    model_config = ConfigDict(extra="forbid")

    route: Route
    path: RunPath
    provider: str = "unknown"
    model_tag: str | None = None
    model_digest: str | None = None
    duration_ms: int = Field(ge=0)
    tool_calls: int = Field(ge=0, le=8)
    model_calls: int = Field(ge=0, le=4)
    retrieval_loops: int = Field(ge=0, le=2, default=0)
    chunks_considered: int = Field(ge=0, default=0)
    validation_codes: list[str] = Field(default_factory=list)
    sids_exposed: list[str] = Field(default_factory=list)


class RenderedAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ResponseStatus
    answer: str = ""
    claims: list[Claim] = Field(default_factory=list)
    interpretations: list[Claim] = Field(default_factory=list)
    concerns: list[Claim] = Field(default_factory=list)
    ambiguities: list[Claim] = Field(default_factory=list)
    conflicts: list[Claim] = Field(default_factory=list)
    general_explanations: list[GeneralExplanation] = Field(default_factory=list)
    missing_information: list[MissingInformation] = Field(default_factory=list)
    extraction_warnings: list[ExtractionWarning] = Field(default_factory=list)
    jurisdiction_flags: list[JurisdictionFlag] = Field(default_factory=list)
    escalation: list[EscalationQuestion] = Field(default_factory=list)
    external_law_required: bool = False
    recommend_professional_review: bool = False
    legal_verdict: Literal[None] = None
    document: DocumentRef | None = None
    run_meta: RunMeta | None = None


# ---------------------------------------------------------------------------
# Document-map / review / lifecycle payloads (PRD FR-004, FR-007, FR-012)
#
# Shapes here follow the v3.2 API contract. Extra fields are additive and only
# exist where the UI or an audit needs them; no field is ever optional in a way
# that would let the backend omit a limitation.
# ---------------------------------------------------------------------------


class CardEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sid: str
    page: int = Field(ge=1)
    section: str | None = None
    quote: str = Field(min_length=1)
    ocr_derived: bool = False


class MapCard(BaseModel):
    """One concept card. The key of the `cards` object is the display label."""

    model_config = ConfigDict(extra="forbid")

    status: str  # CardStatus value; str keeps the UI forward-compatible
    summary: str = ""
    evidence: list[CardEvidence] = Field(default_factory=list)
    note: str = ""


class OverviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document: DocumentRef
    cards: dict[str, MapCard]
    warnings: list[ExtractionWarning] = Field(default_factory=list)


class ReviewAttentionItem(BaseModel):
    """One attention-first review entry. Never a score, never a verdict."""

    model_config = ConfigDict(extra="forbid")

    category: str  # CONFLICT | AMBIGUITY | FINANCIAL | JURISDICTION | OTHER
    priority: int = Field(ge=1, le=5)
    title: str
    reason: str
    citations: list[CardEvidence] = Field(default_factory=list)
    order_reason: str = ""  # why this position, in plain language


class ProfessionalQuestion(BaseModel):
    """A neutral question to put to a qualified professional (PRD FR-008)."""

    model_config = ConfigDict(extra="forbid")

    topic: str
    prompt: str = Field(min_length=1)


class ReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document: DocumentRef
    review_status: str  # CLEAR | ATTENTION | NOT_ASSESSED
    attention_first: list[ReviewAttentionItem] = Field(default_factory=list)
    questions_for_professional: list[ProfessionalQuestion] = Field(default_factory=list)
    disclaimer: str = (
        "This is a review aid, not a legal assessment, risk score or advice. "
        "Items are ordered for reading convenience only."
    )


class DocumentSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    display_name: str
    source_kind: Literal["pdf", "txt"]
    page_count: int = Field(ge=1)
    sha256: str = Field(min_length=64, max_length=64)
    created_at: str
    readable_pages: int = Field(ge=0)
    unread_pages: int = Field(ge=0)
    ocr_used: bool = False
    quality_flags: list[str] = Field(default_factory=list)


class DocumentListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    documents: list[DocumentSummary]


class QualityMetrics(BaseModel):
    """What was actually measured while extracting, not a confidence score."""

    model_config = ConfigDict(extra="forbid")

    pages_read: int = Field(ge=0)
    ocr_used: bool
    language_detected: str  # "en" | "mixed" | "unknown"
    garble_ratio: float = Field(ge=0.0, le=1.0)
    hidden_text_detected: bool


class UploadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    document_hash: str = Field(min_length=64, max_length=64)
    display_name: str
    source_kind: Literal["pdf", "txt"]
    page_count: int = Field(ge=1)
    readable_pages: int = Field(ge=0)
    quality_metrics: QualityMetrics
    extraction_warnings: list[ExtractionWarning] = Field(default_factory=list)
    status: Literal["READY", "PARTIAL"]
    created_at: str = ""


class PageSentence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sid: str
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)
    text: str
    section: str | None = None
    ocr_derived: bool = False


class PageResponse(BaseModel):
    """`text` is included beyond the minimum contract: the viewer renders it."""

    model_config = ConfigDict(extra="forbid")

    document_id: str
    page_number: int = Field(ge=1)
    is_virtual_page: bool
    ocr_used: bool
    text: str
    flags: list[str] = Field(default_factory=list)
    sentences: list[PageSentence] = Field(default_factory=list)


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    document_hash: str = Field(min_length=64, max_length=64)
    page: int = Field(ge=1)
    section: str | None = None
    sids: list[str] = Field(min_length=1)
    verbatim_text: str = Field(min_length=1)
    text_sha256: str = Field(min_length=64, max_length=64)
    ocr_derived: bool = False


class DeletionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    files_purged: int = Field(ge=0)
    database_unlinked: bool
    model_cache_evicted: bool
    canary_scan_passed: bool
    forensic_erasure_disclaimer: str
    remaining_derived_files: list[str] = Field(default_factory=list)
    session_binding_cleared: bool = True
    notes: list[str] = Field(default_factory=list)
