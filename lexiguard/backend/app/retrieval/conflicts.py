"""Candidate conflict detection (FR-004, FR-007).

A candidate conflict is reported only when two *different* stored sentences,
from *different* sections, attach *different* values to the same concept --
for example a notice clause saying 30 days in section 4 and 60 days in
section 9. This is a reading aid: the UI shows both quotations and states that
whether the clauses actually conflict needs a human (or a lawyer) to decide.

No model is involved, and nothing here produces a legal conclusion.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.retrieval.concepts import CORE_TEN, Concept, compiled_patterns
from app.retrieval.vagueness import MONEY_RE, TIME_RE

CONFLICT_CONCEPTS = ("rent", "deposit", "notice", "lock_in", "term", "penalties")


@dataclass(frozen=True)
class Sentence:
    sid: str
    page: int
    section: str | None
    text: str


@dataclass(frozen=True)
class ConflictCandidate:
    concept: str
    label: str
    left: Sentence
    right: Sentence
    values: tuple[str, ...]
    explanation: str = (
        "Two sections attach different values to the same topic. Whether this is a "
        "real inconsistency depends on the rest of the agreement and on local law; "
        "show both passages to a qualified professional."
    )


@dataclass
class ConflictReport:
    candidates: list[ConflictCandidate] = field(default_factory=list)


def _values(text: str) -> set[str]:
    values: set[str] = set()
    for match in MONEY_RE.findall(text):
        values.add(re.sub(r"\s+", "", match).lower().replace(",", ""))
    for match in TIME_RE.findall(text):
        values.add(re.sub(r"\s+", " ", match).lower())
    return values


def _section_key(sentence: Sentence) -> str:
    return sentence.section or f"page:{sentence.page}"


def _matching(concept: Concept, sentences: list[Sentence]) -> list[Sentence]:
    patterns = compiled_patterns(concept)
    return [s for s in sentences if any(p.search(s.text) for p in patterns)]


def detect_conflicts(sentences: list[Sentence]) -> ConflictReport:
    report = ConflictReport()
    for key in CONFLICT_CONCEPTS:
        concept = next((c for c in CORE_TEN if c.key == key), None)
        if concept is None:
            continue
        candidates = _matching(concept, sentences)
        for index, left in enumerate(candidates):
            values_left = _values(left.text)
            if not values_left:
                continue
            for right in candidates[index + 1 :]:
                if _section_key(left) == _section_key(right):
                    continue
                values_right = _values(right.text)
                if not values_right:
                    continue
                if values_left & values_right:
                    continue
                differing = tuple(sorted(values_left | values_right))
                if len(differing) < 2:
                    continue
                report.candidates.append(
                    ConflictCandidate(
                        concept=concept.key,
                        label=concept.label,
                        left=left,
                        right=right,
                        values=differing,
                    )
                )
                break
            if len(report.candidates) >= 6:
                return report
    return report
