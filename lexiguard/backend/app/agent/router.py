
"""Deterministic pre-router plus a stricter-wins merge (Guide 8.2).

The pre-router owns the legal-boundary, term, silence and scope decisions. A
model may only propose a route for cases the pre-router leaves uncertain, and
the proposal can never downgrade a legal limitation into an ordinary answer.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.enums import Route
from app.schemas.model_io import RouterProposal

LEGAL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:is|are|was|were)\s+(?:(?:this|that)\s+(?:agreement|contract|clause|term|notice)|this|it|the\s+(?:agreement|contract|clause|term|notice))"
        r"\s+(?:legally\s+)?(?:valid|invalid|enforceable|unenforceable|legal|illegal|lawful|"
        r"unlawful|binding|void)\b",
        re.I,
    ),
    re.compile(r"\b(?:enforceable|unenforceable)\b", re.I),
    re.compile(r"\bhold\s+up\s+in\s+court\b", re.I),
    re.compile(r"\b(?:throw|kick)\s+(?:me|you|us|them)\s+out\b", re.I),
    re.compile(r"\bcan\s+(?:i|we|they|you)\s+(?:sue|be\s+sued)\b", re.I),
    re.compile(r"\b(?:allowed|permitted|required)\s+by\s+law\b", re.I),
    re.compile(r"\b(?:against|under)\s+the\s+law\b", re.I),
    re.compile(r"\b(?:validity|enforceability|legality)\s+of\b", re.I),
    re.compile(r"\bwill\s+(?:i|we|they|you)\s+(?:win|lose)\b", re.I),
    re.compile(r"\bis\s+it\s+legal\b", re.I),
    re.compile(r"\bdo\s+i\s+have\s+to\s+(?:leave|move\s+out|vacate|pay)\b", re.I),
    re.compile(r"\bcan\s+(?:the\s+)?landlord\s+(?:evict|throw|lock)\b", re.I),
    re.compile(r"\bwhat\s+does\s+the\s+law\s+say\b", re.I),
)

TERM_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bwhat\s+does\s+[\"']?([a-z][a-z \-]{1,40})[\"']?\s+mean\b", re.I),
    re.compile(r"\bmeaning\s+of\s+[\"']?([a-z][a-z \-]{1,40})[\"']?\s*\??$", re.I),
    re.compile(r"\bwhat\s+is\s+(?:a|an)\s+[\"']?([a-z][a-z \-]{1,40})[\"']?\s*\??$", re.I),
)

SILENCE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bdoes\s+(?:the\s+)?(?:agreement|contract|document|it)\s+(?:mention|say\s+anything\s+about|contain|include)\b", re.I),
    re.compile(r"\bis\s+there\s+(?:a|any)\s+clause\s+(?:about|on|for)\b", re.I),
)

CONFLICT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:conflict|conflicting|inconsistent|contradict|contradiction)\w*\b", re.I),
    re.compile(r"\b(?:ambiguous|ambiguity|unclear|two\s+different)\b", re.I),
)

DOCUMENT_MAP_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:summarise|summarize|summary|overview)\b", re.I),
    re.compile(r"\b(?:key|main)\s+(?:terms|points|obligations)\b", re.I),
    re.compile(r"\bwhat\s+(?:are\s+)?my\s+(?:rights|obligations)\b", re.I),
)

REVIEW_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\breview\b", re.I),
    re.compile(r"\bcheck\s+(?:the|this)\s+(?:agreement|contract|document)\b", re.I),
    re.compile(r"\banything\s+(?:i\s+should|unusual|concerning)\b", re.I),
    re.compile(r"\bred\s+flags?\b", re.I),
)

STRICT_ROUTES: frozenset[Route] = frozenset(
    {Route.LEGAL_CONCLUSION, Route.EXTERNAL_LAW_REQUIRED, Route.OUT_OF_SCOPE}
)


@dataclass(frozen=True)
class RouteDecision:
    route: Route
    reason: str
    confident: bool


def pre_route(question: str, *, max_chars: int = 500) -> RouteDecision:
    text = question.strip()
    if not text:
        return RouteDecision(Route.OUT_OF_SCOPE, "empty question", True)
    if len(text) > max_chars:
        return RouteDecision(Route.OUT_OF_SCOPE, "question over length cap", True)

    if any(p.search(text) for p in LEGAL_PATTERNS):
        return RouteDecision(Route.LEGAL_CONCLUSION, "legal conclusion / outcome paraphrase", True)
    if any(p.search(text) for p in TERM_PATTERNS):
        return RouteDecision(Route.TERM_EXPLANATION, "definition question", True)
    if any(p.search(text) for p in CONFLICT_PATTERNS):
        return RouteDecision(Route.AMBIGUITY_OR_CONFLICT, "ambiguity or conflict wording", True)
    if any(p.search(text) for p in SILENCE_PATTERNS):
        return RouteDecision(Route.DOCUMENT_SILENCE_CHECK, "explicit absence question", True)
    if any(p.search(text) for p in REVIEW_PATTERNS):
        return RouteDecision(Route.REVIEW_SCAN, "review request", True)
    if any(p.search(text) for p in DOCUMENT_MAP_PATTERNS):
        return RouteDecision(Route.DOCUMENT_MAP, "document map request", True)

    return RouteDecision(Route.FACT_LOOKUP, "default deterministic route", False)


def merge_route(decision: RouteDecision, proposal: RouterProposal | None) -> RouteDecision:
    """Stricter route wins; a proposal can never downgrade a strict decision."""
    if proposal is None:
        return decision
    if decision.route in STRICT_ROUTES and decision.confident:
        return decision
    if proposal.proposed_route in STRICT_ROUTES:
        return RouteDecision(
            proposal.proposed_route, "model proposed a stricter route", True
        )
    if decision.confident:
        return decision
    return RouteDecision(proposal.proposed_route, "model proposal for an uncertain route", True)
