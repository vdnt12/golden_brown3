
"""Deterministic cross-reference extraction (Guide 7.1 step 3).

Clause numbers, schedules/annexures and "subject to" references are expanded by
code, not by the model. Dates such as 01.11.2026 are not clause references.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("clause", re.compile(r"\bclause\s+(\d+(?:\.\d+)*)", re.I)),
    ("schedule", re.compile(r"\b(?:schedule|annexure|appendix)\s+([A-Z0-9]{1,4}|[IVX]{1,6})\b", re.I)),
    ("subject_to", re.compile(r"\bsubject\s+to\s+(?:clause\s+)?(\d+(?:\.\d+)*)", re.I)),
    ("in_accordance", re.compile(r"\bin\s+accordance\s+with\s+(?:clause\s+)?(\d+(?:\.\d+)*)", re.I)),
)


@dataclass(frozen=True)
class CrossRef:
    kind: str
    ref: str
    phrase: str


def extract_crossrefs(text: str) -> list[CrossRef]:
    seen: set[tuple[str, str]] = set()
    refs: list[CrossRef] = []
    for kind, pattern in _PATTERNS:
        for match in pattern.finditer(text):
            ref = match.group(1)
            key = (kind, ref.lower())
            if key in seen:
                continue
            seen.add(key)
            refs.append(CrossRef(kind=kind, ref=ref, phrase=match.group(0)))
    return refs
