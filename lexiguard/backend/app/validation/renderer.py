
"""Backend-owned renderer (Guide 9.1 stage 7, 10.2).

Every displayed factual point is assembled here from validated points and
stored evidence. The model never supplies quotes, pages, sections or statuses.
The final answer text is scanned once more; a hit replaces the text with the
limitation template and forces a LEGAL_LIMIT status at the caller.
"""
from __future__ import annotations

from app.core.enums import (
    Classification,
    PointKind,
    ResponseStatus,
)
from app.schemas.model_io import ModelPoint
from app.schemas.response import (
    Claim,
    EvidenceItem,
    RenderedAnswer,
    RunMeta,
)
from app.validation.legal_policy import LEGAL_LIMIT_TEXT, scan_text
from app.validation.provenance import Evidence

KIND_TO_CLASSIFICATION: dict[PointKind, Classification] = {
    PointKind.STATED: Classification.DIRECT,
    PointKind.RESTATEMENT: Classification.SUPPORTED,
    PointKind.INTERPRETATION: Classification.INTERPRETIVE,
    PointKind.AMBIGUITY: Classification.AMBIGUOUS,
    PointKind.CONFLICT: Classification.CONFLICTING,
    PointKind.CONCERN: Classification.SUPPORTED,
}


def render_claim(
    point: ModelPoint,
    evidence: list[Evidence],
    claim_number: int,
    document_sha256: str | None = None,
) -> Claim:
    return Claim(
        claim_id=f"claim_{claim_number:03d}",
        text=point.text,
        classification=KIND_TO_CLASSIFICATION[point.kind],
        evidence=[
            EvidenceItem(
                sid=item.sid,
                page=item.page,
                section=item.section,
                quote=item.quote,
                ocr_derived=item.ocr_derived,
                document_sha256=item.document_sha256 or document_sha256,
            )
            for item in evidence
        ],
    )


def finalise_answer_text(text: str) -> tuple[str, bool]:
    """Scan the composed answer; return (safe_text, blocked)."""
    result = scan_text(text)
    if result.blocked:
        return LEGAL_LIMIT_TEXT, True
    return text, False


def build_rendered_answer(
    *,
    statuses: list[ResponseStatus],
    answer: str,
    claims: list[Claim] | None = None,
    interpretations: list[Claim] | None = None,
    concerns: list[Claim] | None = None,
    ambiguities: list[Claim] | None = None,
    conflicts: list[Claim] | None = None,
    general_explanations: list | None = None,
    missing_information: list | None = None,
    extraction_warnings: list | None = None,
    jurisdiction_flags: list | None = None,
    external_law_required: bool = False,
    recommend_professional_review: bool = False,
    run_meta: RunMeta | None = None,
) -> RenderedAnswer:
    safe_answer, blocked = finalise_answer_text(answer)
    if blocked:
        statuses = [*statuses, ResponseStatus.LEGAL_LIMIT]
        answer = LEGAL_LIMIT_TEXT
    else:
        answer = safe_answer

    # Status precedence is resolved here, never by the model.
    from app.core.enums import resolve_status

    status = resolve_status(statuses) if statuses else ResponseStatus.ANSWERED

    return RenderedAnswer(
        status=status,
        answer=answer,
        claims=claims or [],
        interpretations=interpretations or [],
        concerns=concerns or [],
        ambiguities=ambiguities or [],
        conflicts=conflicts or [],
        general_explanations=general_explanations or [],
        missing_information=missing_information or [],
        extraction_warnings=extraction_warnings or [],
        jurisdiction_flags=jurisdiction_flags or [],
        external_law_required=external_law_required,
        recommend_professional_review=recommend_professional_review,
        legal_verdict=None,
        run_meta=run_meta,
    )
