"""Concept lexicons and sentence matching (PRD §3.2, FR-004, FR-007).

The v3.2 contract fixes eleven cards, in this order: Parties, Term, Rent, Deposit,
Notice, Lock-in, Penalties, Restrictions, Maintenance, Disputes, Pets.

A card is only ever "FOUND" when a stored sentence matches one of the concept's
patterns. Nothing here infers a legal conclusion: matches are *candidates* that
the backend renders with their quotation, and the UI labels them as such.

Targets are English rental and leave-and-licence wording. Patterns are
case-insensitive and deliberately broad; precision comes from validation and
from the human review of the fixtures, not from this table.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

MAX_EVIDENCE_PER_CONCEPT = 3


@dataclass(frozen=True)
class Concept:
    key: str
    label: str
    patterns: tuple[str, ...]
    hint: str


CORE_TEN: tuple[Concept, ...] = (
    Concept(
        key="parties",
        label="Parties",
        patterns=(
            r"\b(?:landlord|lessor|licensor|owner|tenant|lessee|licensee|licensor)\b",
            r"\bbetween\b[^.\n]{0,120}\band\b",
            r"\bby\s+and\s+between\b",
            r"\bin\s+witness\s+whereof\b",
        ),
        hint="Who the agreement names as the parties.",
    ),
    Concept(
        key="term",
        label="Term",
        patterns=(
            r"\b(?:term|period of|commenc\w*|renew\w*|expir\w*|valid\s+for)\b",
            r"\b(?:month|year)s?\s+(?:from|of|beginning)\b",
        ),
        hint="When the agreement starts, ends and whether it renews.",
    ),
    Concept(
        key="rent",
        label="Rent",
        patterns=(
            r"\brent\b",
            r"\b(?:monthly|per\s+month|rental\s+value)\b",
            r"\b(?:rental\s+agreement|lease\s+rent|licence\s+fee)\b",
        ),
        hint="Amount, due date and escalation of the rent.",
    ),
    Concept(
        key="deposit",
        label="Deposit",
        patterns=(
            r"\b(?:security\s+)?deposit\b",
            r"\badvance\b",
            r"\brefund\w*\b",
        ),
        hint="What is held, when it is returned and what may be deducted.",
    ),
    Concept(
        key="notice",
        label="Notice",
        patterns=(
            r"\bnotice\b",
            r"\b(?:days|months?)\s+(?:written\s+)?notice\b",
        ),
        hint="How much notice either side must give.",
    ),
    Concept(
        key="lock_in",
        label="Lock-in",
        patterns=(
            r"\block[-\s]?in\b",
            r"\bminimum\s+(?:stay|period)\b",
        ),
        hint="Any minimum period before the tenancy can end.",
    ),
    Concept(
        key="penalties",
        label="Penalties",
        patterns=(
            r"\bpenalt\w*\b",
            r"\bliquidated\s+damages?\b",
            r"\bforfeit\w*\b",
            r"\bdeduct\w*\b",
            r"\blate\s+(?:fee|payment|charge)\b",
            r"\binterest\b",
        ),
        hint="Charges, forfeiture or deductions the agreement allows.",
    ),
    Concept(
        key="restrictions",
        label="Restrictions",
        patterns=(
            r"\b(?:shall|must)\s+not\b",
            r"\bprohibit\w*\b",
            r"\b(?:sublet\w*|assignment|guests?|alteration)\b",
        ),
        hint="What the agreement says the tenant must not do.",
    ),
    Concept(
        key="maintenance",
        label="Maintenance",
        patterns=(
            r"\b(?:repair\w*|maintain\w*|maintenance|upkeep|whitewash|painting)\b",
        ),
        hint="Who is responsible for repairs and upkeep.",
    ),
    Concept(
        key="disputes",
        label="Disputes",
        patterns=(
            r"\b(?:dispute|jurisdiction|court|arbitrat\w*|tribunal|venue)\b",
            r"\bgoverning\s+law\b",
            r"\bgoverned\s+by\b",
            r"\blaws\s+of\s+(?:the\s+)?(?:state|country|republic|province|territory)\b",
        ),
        hint="Where disputes are said to be handled and which law governs.",
    ),
    Concept(
        key="pets",
        label="Pets",
        patterns=(
            r"\bpets?\b",
            r"\b(?:animals?|livestock|dogs?|cats?)\b",
            r"\bno\s+pets?\b",
        ),
        hint="Whether pets are allowed, and on what conditions.",
    ),
)

CONCEPTS_BY_KEY: dict[str, Concept] = {concept.key: concept for concept in CORE_TEN}
CONCEPTS_BY_LABEL: dict[str, Concept] = {concept.label: concept for concept in CORE_TEN}
_COMPILED_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    concept.key: tuple(re.compile(pattern, re.IGNORECASE) for pattern in concept.patterns)
    for concept in CORE_TEN
}


@dataclass(frozen=True)
class ConceptMatch:
    concept: str
    sentence: str


def compiled_patterns(concept: Concept) -> tuple[re.Pattern[str], ...]:
    cached = _COMPILED_PATTERNS.get(concept.key)
    if cached is not None:
        return cached
    return tuple(re.compile(pattern, re.IGNORECASE) for pattern in concept.patterns)


def _compiled(concept: Concept) -> tuple[re.Pattern[str], ...]:
    return compiled_patterns(concept)


def match_sentences(
    concept: Concept, sentences: list[tuple[str, str]]
) -> list[tuple[str, str]]:
    """Return (sid, text) pairs whose text matches any concept pattern."""
    patterns = compiled_patterns(concept)
    hits: list[tuple[str, str]] = []
    for sid, text in sentences:
        if any(pattern.search(text) for pattern in patterns):
            hits.append((sid, text))
        if len(hits) >= MAX_EVIDENCE_PER_CONCEPT * 4:
            break
    return hits


def concept_for_topic(topic: str) -> Concept | None:
    key = topic.strip().lower().replace("-", "_").replace(" ", "_")
    if key in CONCEPTS_BY_KEY:
        return CONCEPTS_BY_KEY[key]
    for concept in CORE_TEN:
        if key.startswith(concept.key) or concept.key in key:
            return concept
    return None
