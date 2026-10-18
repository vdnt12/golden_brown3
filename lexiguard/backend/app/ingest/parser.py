"""Document parsing: TXT in-process, PDF in a resource-limited child process.

PDF parsing MUST run pypdfium2 out-of-process (Guide 6.2); PyMuPDF is forbidden.
TXT has no pages, so it is split into virtual pages of roughly 3,000 characters
at paragraph boundaries. Virtual pages count as physical pages for citations.

Offsets always refer to `normalize_text()` output, never to PDFium indices.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.ingest.normalize import normalize_text
from app.ingest.worker import extract_pdf, render_pdf_page

TXT_VIRTUAL_PAGE_CHARS = 3000

# Re-exported so callers import parser errors from one place.
from app.ingest.errors import (  # noqa: E402
    OcrUnavailable,
    ParserError,
    ParserLimitError,
    ParserTimeoutError,
    ParserUnavailable,
    PdfEncryptedError,
    PdfMalformedError,
)

__all__ = [
    "DecodeError",
    "ParsedDocument",
    "ParsedPage",
    "ParserError",
    "ParserLimitError",
    "ParserTimeoutError",
    "ParserUnavailable",
    "PdfEncryptedError",
    "PdfMalformedError",
    "OcrUnavailable",
    "parse_pdf_bytes",
    "parse_txt_bytes",
    "render_page_image",
    "virtual_pages",
]


class DecodeError(ValueError):
    pass


@dataclass
class ParsedPage:
    page_no: int
    text: str
    virtual: bool = False


@dataclass
class ParsedDocument:
    source_kind: str
    pages: list[ParsedPage] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def virtual_pages(text: str, limit: int = TXT_VIRTUAL_PAGE_CHARS) -> list[str]:
    paragraphs = text.split("\n\n")
    pages: list[str] = []
    current: list[str] = []
    size = 0
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if size and size + len(paragraph) + 2 > limit:
            pages.append("\n\n".join(current))
            current, size = [], 0
        if len(paragraph) > limit:
            if current:
                pages.append("\n\n".join(current))
                current, size = [], 0
            for start in range(0, len(paragraph), limit):
                pages.append(paragraph[start : start + limit])
            continue
        current.append(paragraph)
        size += len(paragraph) + 2
    if current:
        pages.append("\n\n".join(current))
    return pages


def parse_txt_bytes(data: bytes) -> ParsedDocument:
    try:
        raw = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DecodeError("TXT file is not valid UTF-8") from exc
    text = normalize_text(raw)
    if not text.strip():
        raise DecodeError("TXT file is empty after normalisation")
    pages = [
        ParsedPage(page_no=index, text=page_text, virtual=True)
        for index, page_text in enumerate(virtual_pages(text), start=1)
    ]
    warnings = ["TXT input: citations refer to virtual pages split at paragraph boundaries."]
    return ParsedDocument(source_kind="txt", pages=pages, warnings=warnings)


def parse_pdf_bytes(
    data: bytes,
    *,
    max_pages: int = 300,
    timeout_s: float = 30.0,
) -> ParsedDocument:
    result = extract_pdf(data, max_pages=max_pages, timeout_s=timeout_s)
    if not result.pages:
        raise PdfMalformedError("PDF contains no pages")
    pages = [
        ParsedPage(page_no=page.page_no, text=normalize_text(page.text), virtual=False)
        for page in result.pages
    ]
    return ParsedDocument(source_kind="pdf", pages=pages, warnings=list(result.warnings))


def render_page_image(data: bytes, page_no: int, *, scale: float = 1.6) -> bytes:
    """Render one page to PNG in the parser child process (source viewer)."""
    return render_pdf_page(data, page_no, scale=scale)
