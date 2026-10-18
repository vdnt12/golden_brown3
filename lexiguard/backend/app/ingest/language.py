
"""Per-page language gate without ML dependencies (Guide 6.4, T5).

Rules:
  (a) share of letters outside the Latin script > 15 %  -> UNREAD (non-Latin)
  (b) pages with >= 40 tokens whose common-English function-word share is
      < 8 % -> UNREAD (inconclusive / likely romanised non-English)
  (c) pages under 40 tokens inherit document language unless (a) fails
Unread pages are excluded from retrieval and disable NOT_LOCATED decisions.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

_LATIN = re.compile(r"[A-Za-z\u00c0-\u024f]")
_LETTER = re.compile(r"[^\W\d_]", re.UNICODE)
_WORD = re.compile(r"[A-Za-z']+")

ENGLISH_FUNCTION_WORDS = frozenset(
    {
        "the", "a", "an", "and", "or", "of", "to", "in", "on", "at", "by", "for",
        "with", "from", "as", "is", "are", "was", "were", "be", "been", "being",
        "shall", "will", "would", "may", "might", "must", "can", "could", "should",
        "that", "this", "these", "those", "it", "its", "not", "no", "any", "all",
        "if", "then", "than", "so", "such", "he", "she", "they", "them", "his",
        "her", "their", "you", "your", "we", "our", "i", "has", "have", "had",
        "do", "does", "did", "here", "there", "which", "who", "whom", "when",
        "where", "how", "what", "into", "upon", "under", "over", "after", "before",
    }
)

NON_LATIN_THRESHOLD = 0.15
FUNCTION_WORD_THRESHOLD = 0.08
MIN_TOKENS = 40


class PageLanguage(StrEnum):
    ENGLISH = "ENGLISH"
    UNREAD_LANGUAGE = "UNREAD_LANGUAGE"
    NO_TEXT = "NO_TEXT"


@dataclass(frozen=True)
class LanguageVerdict:
    page_no: int
    language: PageLanguage
    non_latin_ratio: float
    function_word_ratio: float
    token_count: int
    reason: str


def non_latin_letter_ratio(text: str) -> float:
    letters = _LETTER.findall(text)
    if not letters:
        return 0.0
    non_latin = sum(1 for ch in letters if not _LATIN.fullmatch(ch))
    return non_latin / len(letters)


def english_function_word_ratio(text: str) -> tuple[float, int]:
    words = [w.lower() for w in _WORD.findall(text)]
    if not words:
        return 0.0, 0
    hits = sum(1 for w in words if w in ENGLISH_FUNCTION_WORDS)
    return hits / len(words), len(words)


def classify_page(page_no: int, text: str) -> LanguageVerdict:
    letters = _LETTER.findall(text)
    if not letters:
        return LanguageVerdict(page_no, PageLanguage.NO_TEXT, 0.0, 0.0, 0, "no letters")

    latin_ratio = 1.0 - non_latin_letter_ratio(text)
    function_ratio, tokens = english_function_word_ratio(text)

    if latin_ratio < (1.0 - NON_LATIN_THRESHOLD):
        return LanguageVerdict(
            page_no,
            PageLanguage.UNREAD_LANGUAGE,
            non_latin_letter_ratio(text),
            function_ratio,
            tokens,
            "more than 15% of letters are outside the Latin script",
        )

    if tokens >= MIN_TOKENS and function_ratio < FUNCTION_WORD_THRESHOLD:
        return LanguageVerdict(
            page_no,
            PageLanguage.UNREAD_LANGUAGE,
            non_latin_letter_ratio(text),
            function_ratio,
            tokens,
            "English function-word share below 8% (possibly romanised non-English)",
        )

    return LanguageVerdict(
        page_no, PageLanguage.ENGLISH, non_latin_letter_ratio(text), function_ratio, tokens, "ok"
    )
