
"""Pattern-based legal-verdict scanner (Guide 9.3, 9.3a).

Scans assistant-authored text only. Immutable source quotations are rendered in
a separate channel and are never scanned or rewritten.

Three rule groups:
  1. verdict predicates applied to the agreement/clause/party;
  2. outcome predictions and advice;
  3. source-echo exception: a flagged word also present in the cited source
     sentence, with matching following context, is allowed for STATED and
     RESTATEMENT points only.

The starter test corpus lives in tests/data/scanner_corpus.jsonl. The Guide
requires >= 40 must-block and >= 40 must-pass strings before release; the
starter set is smaller and marked accordingly in TEST_PLAN.md.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.enums import PointKind

CODE_VERDICT_BLOCKED = "LEGAL_VERDICT_REPLACED"

LEGAL_LIMIT_TEXT = (
    "I can explain what this document says and where it says it. I cannot assess "
    "whether it meets legal requirements or predict how a disagreement would be "
    "resolved. That needs a qualified lawyer."
)

REVIEW_SUGGESTION = (
    "Consider asking a qualified lawyer experienced in tenancy matters where the "
    "property is located."
)

# Longer alternatives before their suffixes; word boundaries keep "invalid"
# from matching "valid", but explicit ordering is still safer.
_VERDICT_ALT = (
    r"unenforceable|unconscionable|unlawful|illegal|invalid|voidable|"
    r"enforceable|lawful|legally binding|binding|valid|void|legal|fair|unfair"
)
_VERDICT = rf"(?:{_VERDICT_ALT})"
_COPULA = r"(?:is|are|was|were|be|seems?|appears?|remains?|becomes?|be held|be deemed)"
_TARGET = (
    r"(?:this|that|it|the agreement|the contract|the clause|the term|the provision|"
    r"the notice|the document|the landlord|the tenant|the licensor|the licensee)"
)
_NON_LEGAL_NOUN = (
    r"(?!(?:\s+(?:advice|information|requirement|requirements|obligation|obligations|"
    r"right|rights|heir|heirs|purpose|purposes|proceedings|proceeding|representative|"
    r"counsel|framework|regime|jurisdiction|system|laws)\b))"
)

RE_VERDICT_TARGETED = re.compile(
    rf"\b{_TARGET}\b[^.!?\n]{{0,60}}?\b{_COPULA}\b\s*(?:not\s+)?{_VERDICT}\b{_NON_LEGAL_NOUN}", re.I
)
RE_VERDICT_COPULA = re.compile(
    rf"\b(?:is|are|was|were)\s+(?:clearly|plainly|obviously|therefore|thus|hence|likely|probably)?\s*"
    rf"(?:not\s+)?{_VERDICT}\b{_NON_LEGAL_NOUN}",
    re.I,
)
RE_AGAINST_LAW = re.compile(
    r"\b(?:against\s+the\s+law|violates\s+(?:the\s+)?law|illegal\s+under|"
    r"contrary\s+to\s+law)\b",
    re.I,
)
RE_HEADLINE_VERDICT = re.compile(
    r"^\s*(?:not\s+)?(?:unenforceable|unconscionable|unlawful|illegal|invalid|void|"
    r"enforceable|lawful|valid|legal|fair|unfair)(?:\s+(?:clause|agreement|contract|term))?\s*[.!]?\s*$",
    re.I,
)

RE_OUTCOME = re.compile(
    r"\b(?:you|they|he|she|the\s+(?:landlord|tenant|owner|lessee|lessor|licensee|licensor))"
    r"\s+(?:will|would|can|could|cannot|can't|may|might)\s+(?:legally\s+)?"
    r"(?:win|lose|sue|be\s+sued|evict|be\s+evicted|throw\s+[a-z\s]{0,20}out|"
    r"take\s+possession|keep\s+the\s+deposit)\b"
    r"|\bwill\s+(?:hold\s+up|stand)\s+in\s+court\b"
    r"|\b(?:court|tribunal)\w*\s+(?:would|will|must)\s+(?:find|hold|decide|rule|agree)\b"
    r"|\bpolice\s+(?:will|can|must)\s+(?:remove|evict|throw)\b",
    re.I,
)
RE_ADVICE = re.compile(
    r"\byou\s+should\s+(?:not\s+)?sign\b"
    r"|\b(?:safe|fine|okay|ok)\s+to\s+sign\b"
    r"|\bno\s+need\s+(?:for\s+a\s+(?:lawyer|solicitor)|to\s+consult\s+(?:a\s+)?(?:lawyer|solicitor))\b"
    r"|\byou\s+should\s+not\s+worry\b"
    r"|\byou\s+can\s+(?:refuse|withhold|stop\s+paying)\b"
    r"|\b(?:standard|normal|typical|usual|market)\s+practice\b"
    r"|\b(?:is|seems|appears|looks)\s+(?:un)?reasonable\b"
    r"|\byou\s+(?:have|are\s+entitled)\s+to\s+(?:stay|remain|refuse)\b",
    re.I,
)

_VERDICT_WORD_RE = re.compile(rf"\b(?:{_VERDICT_ALT})\b", re.I)


@dataclass(frozen=True)
class ScanResult:
    blocked: bool
    rule: str = ""
    matched: str = ""
    code: str = ""

    @property
    def ok(self) -> bool:
        return not self.blocked


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _echo_allowed(
    text: str,
    match: re.Match[str],
    kind: PointKind | None,
    source_text: str,
) -> bool:
    """Source-echo exception (Guide 9.3a rule 3).

    Only STATED/RESTATEMENT points may echo a flagged word, and only when the
    word plus its immediately following word also appears in the cited source
    (e.g. "valid for 11 months"). A bare verdict with no following context is
    never allowed, even if the word appears somewhere in the source.
    """
    if kind not in (PointKind.STATED, PointKind.RESTATEMENT):
        return False
    verdict = _VERDICT_WORD_RE.search(match.group(0))
    if verdict is None:
        return False
    word = verdict.group(0).lower()
    after = text[match.end():].lstrip()
    next_word = re.match(r"[A-Za-z]+", after)
    if next_word is None:
        return False  # bare verdict -> block
    key = f"{word} {next_word.group(0).lower()}"
    return bool(re.search(rf"\b{re.escape(key)}\b", _normalise(source_text)))


def scan_text(
    text: str,
    *,
    kind: PointKind | None = None,
    source_text: str = "",
) -> ScanResult:
    """Return ScanResult(blocked=True) if assistant text contains a legal verdict."""
    if not text or not text.strip():
        return ScanResult(blocked=False)

    for pattern, rule in (
        (RE_VERDICT_TARGETED, "VERDICT_TARGETED"),
        (RE_VERDICT_COPULA, "VERDICT_COPULA"),
        (RE_HEADLINE_VERDICT, "VERDICT_HEADLINE"),
    ):
        match = pattern.search(text)
        if match and not _echo_allowed(text, match, kind, source_text):
            return ScanResult(
                blocked=True,
                rule=rule,
                matched=match.group(0),
                code=CODE_VERDICT_BLOCKED,
            )

    for pattern, rule in (
        (RE_AGAINST_LAW, "AGAINST_LAW"),
        (RE_OUTCOME, "OUTCOME_PREDICTION"),
        (RE_ADVICE, "ADVICE_OR_JUDGEMENT"),
    ):
        match = pattern.search(text)
        if match:
            return ScanResult(
                blocked=True,
                rule=rule,
                matched=match.group(0),
                code=CODE_VERDICT_BLOCKED,
            )

    return ScanResult(blocked=False)


def safe_text(
    text: str,
    *,
    kind: PointKind | None = None,
    source_text: str = "",
) -> tuple[str, ScanResult]:
    """Return (text-or-template, ScanResult). Blocked text is replaced."""
    result = scan_text(text, kind=kind, source_text=source_text)
    if result.blocked:
        return LEGAL_LIMIT_TEXT, result
    return text, result
