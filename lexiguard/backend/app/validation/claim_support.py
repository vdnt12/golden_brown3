
"""Kind-specific claim checks (Guide 9.1 stage 4).

These checks prove citation integrity and catch invented figures, swapped
parties and flipped modality. They do not prove semantic faithfulness; that
limit is stated in LIMITATIONS.md and measured by the human-labelled UCR.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.enums import PointKind
from app.schemas.model_io import ModelPoint
from app.validation.literal import missing_literals
from app.validation.modality import check_modality
from app.validation.provenance import Evidence
from app.validation.roles import check_roles

CODE_SID_NOT_EXPOSED = "SID_NOT_EXPOSED_IN_RUN"
CODE_STATED_NOT_EXTRACTIVE = "STATED_NOT_EXTRACTIVE"
CODE_CONFLICT_NEEDS_TWO_SECTIONS = "CONFLICT_NEEDS_TWO_SECTIONS"
CODE_GENERAL_HAS_DOCUMENT_FACTS = "GENERAL_EXPLANATION_HAS_DOCUMENT_FACTS"
_DIGIT_RE = re.compile(r"\d")


@dataclass(frozen=True)
class Violation:
    code: str
    point_id: str
    detail: str = ""


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def check_point(
    point: ModelPoint,
    evidence: list[Evidence],
    exposed_sids: set[str],
) -> list[Violation]:
    """Return violations for one point. Any violation drops the point."""
    violations: list[Violation] = []
    pid = point.point_id

    for sid in point.sids:
        if sid not in exposed_sids:
            violations.append(Violation(CODE_SID_NOT_EXPOSED, pid, sid))

    sources = [item.quote for item in evidence]

    if point.kind is PointKind.GENERAL_EXPLANATION:
        if point.sids:
            violations.append(Violation(CODE_SID_NOT_EXPOSED, pid, "general explanation cites sids"))
        if _DIGIT_RE.search(point.text):
            violations.append(Violation(CODE_GENERAL_HAS_DOCUMENT_FACTS, pid))
        return violations

    if not evidence:
        violations.append(Violation(CODE_SID_NOT_EXPOSED, pid, "no evidence resolved"))
        return violations

    if point.kind is PointKind.STATED and _normalise(point.text) not in _normalise(
        " ".join(sources)
    ):
        violations.append(Violation(CODE_STATED_NOT_EXTRACTIVE, pid))

    if point.kind is PointKind.RESTATEMENT:
        for literal in missing_literals(point.text, sources):
            violations.append(Violation(literal.code, pid, literal.literal))
        for modality in check_modality(point.text, sources):
            violations.append(Violation(modality.code, pid, modality.detail))
        for role in check_roles(point.text, sources):
            violations.append(Violation(role.code, pid, role.role))

    if point.kind is PointKind.CONFLICT:
        distinct = {item.section if item.section else f"page:{item.page}" for item in evidence}
        if len(distinct) < 2:
            violations.append(Violation(CODE_CONFLICT_NEEDS_TWO_SECTIONS, pid))

    return violations
