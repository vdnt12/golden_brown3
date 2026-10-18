
"""Silence gate: NOT_LOCATED only after adequate coverage (Guide 7.4).

Any missing precondition returns INSUFFICIENT_EVIDENCE instead. Unread pages
forbid NOT_LOCATED entirely, because the topic could live there.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from app.core.enums import ResponseStatus


class SilenceReason(StrEnum):
    OK = "OK"
    UNREAD_PAGES = "UNREAD_PAGES"
    UNSUPPORTED_LANGUAGE = "UNSUPPORTED_LANGUAGE"
    LOW_COVERAGE = "LOW_COVERAGE"
    LEXICON_NOT_RUN = "LEXICON_NOT_RUN"
    LEXICAL_NOT_RUN = "LEXICAL_NOT_RUN"
    HEADINGS_NOT_RUN = "HEADINGS_NOT_RUN"
    CROSSREFS_NOT_RUN = "CROSSREFS_NOT_RUN"
    INCORPORATED_MATERIAL_NOT_CHECKED = "INCORPORATED_MATERIAL_NOT_CHECKED"


@dataclass(frozen=True)
class SilenceEvidence:
    page_count: int
    unread_pages: int = 0
    unsupported_language_pages: int = 0
    coverage_ok: bool = True
    lexicon_checked: bool = False
    lexical_checked: bool = False
    headings_checked: bool = False
    crossrefs_checked: bool = False
    incorporated_material_checked: bool = False


@dataclass(frozen=True)
class SilenceDecision:
    allowed: bool
    status: ResponseStatus
    reason: SilenceReason
    details: tuple[str, ...] = field(default_factory=tuple)


def evaluate_silence(evidence: SilenceEvidence) -> SilenceDecision:
    blockers: list[SilenceReason] = []

    if evidence.unread_pages > 0:
        blockers.append(SilenceReason.UNREAD_PAGES)
    if evidence.unsupported_language_pages > 0:
        blockers.append(SilenceReason.UNSUPPORTED_LANGUAGE)
    if not evidence.coverage_ok:
        blockers.append(SilenceReason.LOW_COVERAGE)

    procedure = [
        (SilenceReason.LEXICON_NOT_RUN, evidence.lexicon_checked),
        (SilenceReason.LEXICAL_NOT_RUN, evidence.lexical_checked),
        (SilenceReason.HEADINGS_NOT_RUN, evidence.headings_checked),
        (SilenceReason.CROSSREFS_NOT_RUN, evidence.crossrefs_checked),
        (SilenceReason.INCORPORATED_MATERIAL_NOT_CHECKED, evidence.incorporated_material_checked),
    ]
    blockers.extend(reason for reason, done in procedure if not done)

    if blockers:
        return SilenceDecision(
            allowed=False,
            status=ResponseStatus.INSUFFICIENT_EVIDENCE,
            reason=blockers[0],
            details=tuple(reason.value for reason in blockers),
        )
    return SilenceDecision(
        allowed=True,
        status=ResponseStatus.NOT_LOCATED,
        reason=SilenceReason.OK,
    )
