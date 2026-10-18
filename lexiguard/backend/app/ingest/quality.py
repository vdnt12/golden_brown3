
"""Per-page extraction quality gate (Guide 6.4).

The report records page coverage and OCR candidates. Warnings are surfaced in
the UI; they never silently disappear. Hidden-text detection is a heuristic and
is labelled as such (Phase 1 work).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PageQuality:
    page_no: int
    char_count: int
    image_only: bool
    garble_ratio: float
    flags: tuple[str, ...] = ()


@dataclass
class QualityReport:
    pages: list[PageQuality] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def readable_pages(self) -> int:
        return sum(1 for p in self.pages if not p.image_only)

    @property
    def coverage(self) -> float:
        return (self.readable_pages / self.page_count) if self.page_count else 0.0

    @property
    def coverage_ok(self) -> bool:
        return self.coverage >= 0.95

    def ocr_candidates(self) -> list[int]:
        return [p.page_no for p in self.pages if p.image_only or "LOW_TEXT" in p.flags]


def assess_page(page_no: int, text: str) -> PageQuality:
    stripped = text.strip()
    char_count = len(stripped)
    garble = 0.0
    if stripped:
        bad = sum(1 for ch in stripped if ch == "\ufffd" or (ord(ch) < 32 and ch not in "\n\t"))
        garble = bad / len(stripped)
    flags: list[str] = []
    if char_count < 40:
        flags.append("LOW_TEXT")
    if garble > 0.01:
        flags.append("GARBLED_TEXT")
    if char_count == 0:
        flags.append("EMPTY_PAGE")
    return PageQuality(
        page_no=page_no,
        char_count=char_count,
        image_only=char_count < 40,
        garble_ratio=garble,
        flags=tuple(flags),
    )


def assess_pages(pages: list[tuple[int, str]]) -> QualityReport:
    report = QualityReport(pages=[assess_page(no, text) for no, text in pages])
    low = [p.page_no for p in report.pages if p.image_only]
    if low:
        report.warnings.append(
            "Pages with little or no extractable text: " + ", ".join(str(n) for n in low)
            + ". OCR (local Tesseract) is required before those pages can be analysed."
        )
    if not report.coverage_ok:
        report.warnings.append(
            "Text coverage is below 95%; absence claims (NOT_LOCATED) are disabled."
        )
    return report
