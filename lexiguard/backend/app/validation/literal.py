
"""Conservative literal normalisation for RESTATEMENT checks (Guide 9.2).

Equivalence only -- never unit conversion. "sixty (60)" -> N:60, "Rs. 25,000/-"
and "INR 25000" -> AMT:25000, "01/11/2026" and "1 November 2026" ->
DATE:2026-11-01. If equivalence cannot be established safely, the claim fails
closed in claim_support.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

CODE_LITERAL_MISSING = "LITERAL_NOT_IN_SOURCE"

_ONES = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
}
_TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}
_NUMBER_WORDS = set(_ONES) | set(_TENS) | {"hundred", "and"}
_NUM_WORDS_ALT = (
    "zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    "thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
    "twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred"
)
_NUM_SEQ_RE = re.compile(
    rf"\b(?:{_NUM_WORDS_ALT})(?:[\s-]+(?:and[\s-]+)?(?:{_NUM_WORDS_ALT}))*\b",
    re.I,
)

_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12, "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}


@dataclass(frozen=True)
class LiteralViolation:
    code: str
    literal: str


def _parse_number_words(words: list[str]) -> int | None:
    total = 0
    current = 0
    for word in words:
        word = word.lower()
        if word == "and":
            continue
        if word == "hundred":
            current = max(1, current) * 100
        elif word in _TENS:
            current += _TENS[word]
        elif word in _ONES:
            current += _ONES[word]
        else:
            return None
    total += current
    return total


def words_to_digits(text: str) -> str:
    """Replace runs of English number words with digits (best effort).

    Conservative direction: matching more literals can only cause a claim to be
    dropped, never an unsupported claim to pass.
    """

    def replace(match: re.Match[str]) -> str:
        words = [w for w in re.split(r"[\s-]+", match.group(0).lower()) if w]
        value = _parse_number_words(words)
        return match.group(0) if value is None else str(value)

    return _NUM_SEQ_RE.sub(replace, text)


def _canon_number(raw: str) -> str:
    cleaned = raw.replace(",", "")
    if "." in cleaned:
        cleaned = cleaned.rstrip("0").rstrip(".") if "." in cleaned else cleaned
    try:
        value = float(cleaned)
    except ValueError:
        return raw
    if value.is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _date_token(year: int, month: int, day: int) -> str | None:
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None
    return f"DATE:{year:04d}-{month:02d}-{day:02d}"


_DATE_DMY_RE = re.compile(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})\b")
_DATE_DMY_TEXT_RE = re.compile(
    r"\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|"
    r"September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|"
    r"Sep|Sept|Oct|Nov|Dec)\s+(\d{4})\b",
    re.I,
)
_DATE_MDY_TEXT_RE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|"
    r"October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
    r"\s+(\d{1,2}),?\s+(\d{4})\b",
    re.I,
)
_CURRENCY_RE = re.compile(r"(?:\bRs\.?|\bINR|₹)\s*(\d[\d,]*(?:\.\d{1,2})?)\s*(?:/-)?", re.I)
_PERCENT_RE = re.compile(r"\b(\d+(?:\.\d+)?)\s*(?:%|percent\b)", re.I)
_PLAIN_NUM_RE = re.compile(r"\b\d[\d,]*(?:\.\d+)?\b")

_DATE_PATTERNS = (
    (
        _DATE_DMY_RE,
        lambda m: _date_token(
            int(m.group(3)) + (2000 if len(m.group(3)) == 2 else 0),
            int(m.group(2)),
            int(m.group(1)),
        ),
    ),
    (
        _DATE_DMY_TEXT_RE,
        lambda m: _date_token(int(m.group(3)), _MONTHS[m.group(2).lower()], int(m.group(1))),
    ),
    (
        _DATE_MDY_TEXT_RE,
        lambda m: _date_token(int(m.group(3)), _MONTHS[m.group(1).lower()], int(m.group(2))),
    ),
)


def extract_literals(text: str) -> set[str]:
    """Return the normalised literal set (amounts, numbers, dates, percentages)."""
    work = words_to_digits(text)
    found: set[str] = set()

    def remove(span: tuple[int, int]) -> None:
        nonlocal work
        start, end = span
        work = work[:start] + (" " * (end - start)) + work[end:]

    # Dates: DD/MM/YYYY (also DD-MM-YYYY and DD.MM.YYYY), 1 November 2026,
    # November 1, 2026. Spans are blanked so their parts are not re-read.
    for pattern, builder in _DATE_PATTERNS:
        for match in list(pattern.finditer(work)):
            token = builder(match)
            if token:
                found.add(token)
                remove(match.span())

    # Currency amounts (Rs., INR, ₹, optional /-). No unit conversion.
    for match in list(_CURRENCY_RE.finditer(work)):
        found.add(f"AMT:{_canon_number(match.group(1))}")
        remove(match.span())

    # Percentages.
    for match in list(_PERCENT_RE.finditer(work)):
        found.add(f"PCT:{_canon_number(match.group(1))}")
        remove(match.span())

    # Remaining plain numbers.
    for match in _PLAIN_NUM_RE.finditer(work):
        found.add(f"N:{_canon_number(match.group(0))}")

    return found


def missing_literals(claim_text: str, source_texts: list[str]) -> list[LiteralViolation]:
    claim_literals = extract_literals(claim_text)
    source_literals: set[str] = set()
    for source in source_texts:
        source_literals |= extract_literals(source)
    return [
        LiteralViolation(code=CODE_LITERAL_MISSING, literal=literal)
        for literal in sorted(claim_literals - source_literals)
    ]
