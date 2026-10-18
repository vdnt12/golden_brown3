
"""Obligation-strength and negation checks (Guide 9.2).

Catches "may" restated as "must", "shall not" restated as "shall", and added or
dropped negation. Conservative: a mismatch fails the point closed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_OBLIGATION = re.compile(
    r"\b(?:must|shall|has\s+to|have\s+to|is\s+required\s+to|are\s+required\s+to)\b", re.I
)
_PERMISSION = re.compile(
    r"\b(?:may|is\s+permitted\s+to|are\s+permitted\s+to|can|is\s+entitled\s+to)\b", re.I
)
_NEGATION = re.compile(r"\b(?:not|no|never|cannot|can't)\b", re.I)

CODE_OBLIGATION_ADDED = "MODALITY_OBLIGATION_ADDED"
CODE_PERMISSION_WEAKENED = "MODALITY_WEAKENED"
CODE_NEGATION_ADDED = "NEGATION_ADDED"
CODE_NEGATION_DROPPED = "NEGATION_DROPPED"


@dataclass(frozen=True)
class ModalityViolation:
    code: str
    detail: str


def check_modality(claim_text: str, source_texts: list[str]) -> list[ModalityViolation]:
    claim = claim_text.lower()
    source = " ".join(source_texts).lower()
    violations: list[ModalityViolation] = []

    claim_obligation = bool(_OBLIGATION.search(claim))
    source_obligation = bool(_OBLIGATION.search(source))
    claim_permission = bool(_PERMISSION.search(claim))
    source_permission = bool(_PERMISSION.search(source))
    claim_negation = bool(_NEGATION.search(claim))
    source_negation = bool(_NEGATION.search(source))

    if claim_obligation and not (source_obligation or source_permission):
        violations.append(ModalityViolation(CODE_OBLIGATION_ADDED, "obligation not present in source"))

    if claim_permission and not claim_obligation and source_obligation and not source_permission:
        violations.append(ModalityViolation(CODE_PERMISSION_WEAKENED, "permission replaces an obligation"))

    if claim_negation and not source_negation:
        violations.append(ModalityViolation(CODE_NEGATION_ADDED, "negation added"))

    if source_negation and not claim_negation:
        violations.append(ModalityViolation(CODE_NEGATION_DROPPED, "negation dropped"))

    return violations
