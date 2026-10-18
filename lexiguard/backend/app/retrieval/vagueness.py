"""Vague-wording and money/time detection for the Review view (FR-004, FR-007).

Heuristic only. Every hit is a *candidate* for a human to look at, never a
finding of unfairness or illegality. The UI shows the quotation and says so.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

VAGUE_TERMS: tuple[str, ...] = (
    "reasonable",
    "promptly",
    "as soon as possible",
    "from time to time",
    "market rate",
    "prevailing rate",
    "usual",
    "customary",
    "adequate",
    "sufficient",
    "material",
    "substantial",
    "good faith",
    "at the discretion",
    "sole discretion",
    "approximately",
    "similar",
)

MONEY_RE = re.compile(r"(?:rs\.?|inr|₹|\$)\s?[\d,]+(?:\.\d+)?", re.IGNORECASE)
TIME_RE = re.compile(
    r"\b(?:\d{1,2}|one|two|three|five|seven|ten|fifteen|thirty|sixty)\s*"
    r"(?:days?|weeks?|months?|years?)\b",
    re.IGNORECASE,
)
PENALTY_RE = re.compile(
    r"\b(?:penalt\w*|forfeit\w*|deduct\w*|late\s+fee|interest\s+at|lock[-\s]?in)\b",
    re.IGNORECASE,
)
TERMINATION_RE = re.compile(
    r"\b(?:terminat\w*|notice|vacat\w*|evict\w*|surrender)\b", re.IGNORECASE
)
OBLIGATION_RE = re.compile(r"\b(?:shall|must|agrees?\s+to|undertakes?)\b", re.IGNORECASE)


@dataclass(frozen=True)
class VagueHit:
    sid: str
    term: str
    text: str


def find_vague(sentences: list[tuple[str, str]]) -> list[VagueHit]:
    hits: list[VagueHit] = []
    for sid, text in sentences:
        lowered = text.lower()
        for term in VAGUE_TERMS:
            if term in lowered:
                hits.append(VagueHit(sid=sid, term=term, text=text))
                break
    return hits


def has_money(text: str) -> bool:
    return bool(MONEY_RE.search(text))


def has_time(text: str) -> bool:
    return bool(TIME_RE.search(text))


def has_penalty(text: str) -> bool:
    return bool(PENALTY_RE.search(text))


def has_termination(text: str) -> bool:
    return bool(TERMINATION_RE.search(text))


def has_obligation(text: str) -> bool:
    return bool(OBLIGATION_RE.search(text))
