
"""Sentence and clause segmentation (Guide 6.6).

Line-based so every sentence offset round-trips exactly into stored page text:
    page_text[sentence.char_start:sentence.char_end] == sentence.text
Heading lines set the section label and are not emitted as sentences.
Lines are split into sentences with protections for Rs., No., e.g., i.e.,
decimals, dates and common abbreviations. Sentences never span a line break in
this scaffold version; wrapped clauses become separate segments. That limit is
recorded in docs/LIMITATIONS.md and mitigated at Phase 1 when paragraph layout
is normalised.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_PROTECT = "\x01"

_ABBREV = re.compile(
    r"\b(?:Rs|No|no|Nos|e\.g|i\.e|Mr|Mrs|Ms|Dr|vs|etc|Ltd|Pvt|Co|Corp|Smt|Shri|Sr|Jr|Cl)\.(?=\s|$)",
)
_DECIMAL = re.compile(r"(?<=\d)\.(?=\d)")
_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\u2018\u201c])")
_NUMBERED_HEADING = re.compile(r"^(?P<label>\d+(?:\.\d+)*)[.)]?\s+(?P<title>[A-Z(][^\n]{0,70})$")
_CAPS_HEADING = re.compile(r"^[A-Z][A-Z0-9 ,.&()/'-]{3,70}$")


@dataclass(frozen=True)
class SentenceRecord:
    sid: str
    page: int
    section: str | None
    char_start: int
    char_end: int
    text: str
    heading: str | None = None


def _protect(text: str) -> str:
    """Replace abbreviation/decimal periods with a non-boundary character."""
    chars = list(text)
    for match in _ABBREV.finditer(text):
        chars[match.end() - 1] = _PROTECT
    for match in _DECIMAL.finditer(text):
        chars[match.start()] = _PROTECT
    return "".join(chars)


def split_sentences_with_spans(text: str) -> list[tuple[int, int, str]]:
    """Split one line/paragraph into trimmed (start, end, sentence) spans."""
    if not text.strip():
        return []
    protected = _protect(text)
    spans: list[tuple[int, int, str]] = []
    cursor = 0
    for match in _BOUNDARY.finditer(protected):
        spans.append((cursor, match.start()))
        cursor = match.end()
    spans.append((cursor, len(text)))

    cleaned: list[tuple[int, int, str]] = []
    for start, end in spans:
        raw = text[start:end]
        stripped = raw.strip()
        if not stripped:
            continue
        offset = raw.find(stripped)
        s = start + offset
        e = s + len(stripped)
        for piece_start, piece_end in _cap_length(text, s, e):
            cleaned.append((piece_start, piece_end, text[piece_start:piece_end]))
    return cleaned


def _cap_length(text: str, start: int, end: int, cap: int = 1000) -> list[tuple[int, int]]:
    if end - start <= cap:
        return [(start, end)]
    pieces: list[tuple[int, int]] = []
    cursor = start
    while end - cursor > cap:
        window = text[cursor : cursor + cap]
        split_at = window.rfind(" ")
        if split_at <= 0:
            split_at = cap
        pieces.append((cursor, cursor + split_at))
        cursor = cursor + split_at
        while cursor < end and text[cursor] == " ":
            cursor += 1
    if cursor < end:
        pieces.append((cursor, end))
    return pieces


def heading_label(line: str) -> str | None:
    """Return the section label for a heading line (e.g. "2" or "DEPOSIT")."""
    stripped = line.strip()
    match = _NUMBERED_HEADING.match(stripped)
    if match and not stripped.endswith("."):
        return match.group("label")
    if _CAPS_HEADING.match(stripped) and len(stripped.split()) <= 8:
        return stripped[:40]
    return None


def heading_title(line: str) -> str | None:
    """Return the human title of a heading line (e.g. "Rent and escalation")."""
    stripped = line.strip()
    match = _NUMBERED_HEADING.match(stripped)
    if match and not stripped.endswith("."):
        title = match.group("title").strip().rstrip(":-").strip()
        return title[:80] or None
    if _CAPS_HEADING.match(stripped) and len(stripped.split()) <= 8:
        return stripped.title()[:80]
    return None


def segment_page(page_no: int, text: str, *, start_index: int = 1) -> list[SentenceRecord]:
    records: list[SentenceRecord] = []
    section: str | None = None
    heading: str | None = None
    counter = start_index
    cursor = 0
    for line in text.split("\n"):
        label = heading_label(line) if line.strip() else None
        if label:
            section = label
            heading = heading_title(line) or label
        else:
            for start, end, sentence in split_sentences_with_spans(line):
                records.append(
                    SentenceRecord(
                        sid=f"s_{counter:04d}",
                        page=page_no,
                        section=section,
                        char_start=cursor + start,
                        char_end=cursor + end,
                        text=sentence,
                        heading=heading,
                    )
                )
                counter += 1
        cursor += len(line) + 1  # newline consumed by split()
    return records


def segment_pages(pages: list[tuple[int, str]]) -> list[SentenceRecord]:
    records: list[SentenceRecord] = []
    for page_no, text in pages:
        records.extend(segment_page(page_no, text, start_index=len(records) + 1))
    return records
