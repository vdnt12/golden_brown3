"""Upload -> pages -> sentences -> chunks -> SQLite, with quality and language gates.

Deterministic end to end. The only optional non-deterministic step is OCR, and
it is applied page-by-page only where the quality gate says the page has no
usable text, and only when Tesseract is installed locally.

Guarantees:
  * every page keeps its normalised text; every sentence offset round-trips
  * unreadable pages are flagged and excluded from retrieval
  * chunks carry page and section so the renderer can cite them
  * no path is ever derived from the uploaded filename
"""
from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass, field
from pathlib import Path

from app.config import Settings
from app.ingest import ocr as ocr_module
from app.ingest.language import PageLanguage, classify_page
from app.ingest.normalize import normalize_text
from app.ingest.parser import (
    DecodeError,
    ParsedDocument,
    ParserError,
    parse_pdf_bytes,
    parse_txt_bytes,
    render_page_image,
)
from app.ingest.quality import QualityReport, assess_pages
from app.ingest.segment import SentenceRecord, segment_pages
from app.ingest.upload import UploadInspection, inspect_upload, sanitise_display_name
from app.retrieval.clause_map import build_clause_map
from app.services.lifecycle import document_dir
from app.store import chunks as chunks_store
from app.store import documents as documents_store
from app.store import fts
from app.store import pages as pages_store
from app.store import sentences as sentences_store
from app.store.clauses import replace_clause_map
from app.store.db import init_db

PARSER_VERSION = "lexiguard-parser/1.0"
CHUNK_TARGET_CHARS = 700
CHUNK_MAX_SENTENCES = 6


class IngestError(RuntimeError):
    """Upload rejected or document unreadable; carries a stable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


# Stable codes for extraction warnings, so a client can branch on them without
# parsing prose. Anything unrecognised becomes EXTRACTION_NOTE rather than
# disappearing.
WARNING_CODES: tuple[tuple[str, str], ...] = (
    ("Local OCR is not installed", "OCR_UNAVAILABLE"),
    ("OCR-derived text", "OCR_DERIVED"),
    ("OCR failed on page", "OCR_FAILED"),
    ("Unsupported or inconclusive language", "UNREAD_LANGUAGE"),
    ("Pages with little or no extractable text", "LOW_TEXT"),
    ("Text coverage is below 95%", "LOW_COVERAGE"),
    ("garble", "GARBLED_TEXT"),
    ("Encrypted", "ENCRYPTED"),
    ("truncated", "TRUNCATED"),
)

ZERO_WIDTH = frozenset("\u200b\u200c\u200d\ufeff\u00ad")
# Invisible-text render mode (Tr 3) only appears literally when a content stream
# is uncompressed. A negative therefore does not prove absence; see docs.
INVISIBLE_TEXT_MARKERS = (b"/Tr 3", b"/Tr3", b"/Tr 3 ")


def warning_code(message: str) -> str:
    lowered = message.lower()
    for needle, code in WARNING_CODES:
        if needle.lower() in lowered:
            return code
    return "EXTRACTION_NOTE"


def detect_hidden_text(text: str, data: bytes, kind: str) -> bool:
    """Best-effort hidden-text heuristic (zero-width run or invisible render mode).

    This is a heuristic, not a guarantee: compressed PDF content streams and
    white-on-white text drawn with normal render mode are not visible to it.
    """
    if sum(1 for ch in text if ch in ZERO_WIDTH) >= 5:
        return True
    return bool(kind == "pdf" and any(marker in data for marker in INVISIBLE_TEXT_MARKERS))


@dataclass
class IngestResult:
    document_id: str
    display_name: str
    source_kind: str
    sha256: str
    page_count: int
    sentence_count: int
    chunk_count: int
    readable_pages: int
    unread_pages: list[int] = field(default_factory=list)
    ocr_pages: list[int] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    quality_flags: list[str] = field(default_factory=list)
    garble_ratio: float = 0.0
    hidden_text_detected: bool = False
    language_detected: str = "en"


def new_document_id() -> str:
    return secrets.token_hex(16)


def _parse(data: bytes, kind: str, settings: Settings) -> ParsedDocument:
    if kind == "pdf":
        try:
            return parse_pdf_bytes(
                data, max_pages=settings.max_pages, timeout_s=settings.parser_timeout_s
            )
        except ParserError as exc:
            raise IngestError(type(exc).__name__.upper(), str(exc)) from exc
    try:
        return parse_txt_bytes(data)
    except DecodeError as exc:
        raise IngestError("TXT_NOT_UTF8", str(exc)) from exc


def _apply_ocr(
    parsed: ParsedDocument,
    data: bytes,
    quality: QualityReport,
    settings: Settings,
    warnings: list[str],
) -> list[int]:
    """OCR only flagged pages, only locally, only if Tesseract exists."""
    candidates = [
        page_no
        for page_no in quality.ocr_candidates()
        if page_no <= settings.max_pages
    ][: ocr_module.MAX_OCR_PAGES]
    if not candidates:
        return []
    if not ocr_module.ocr_available():
        warnings.append(
            "Local OCR is not installed, so image-only pages were left unread. "
            "Install Tesseract and re-upload to analyse those pages."
        )
        return []

    ocr_pages: list[int] = []
    for page_no in candidates:
        if parsed.source_kind != "pdf":
            continue
        try:
            png = render_page_image(data, page_no)
            text = ocr_module.ocr_png_bytes(png)
        except Exception as exc:  # noqa: BLE001 - OCR must never kill the ingest
            warnings.append(f"OCR failed on page {page_no}: {type(exc).__name__}")
            continue
        for index, page in enumerate(parsed.pages):
            if page.page_no == page_no:
                parsed.pages[index] = type(page)(
                    page_no=page_no, text=normalize_text(text), virtual=False
                )
                break
        ocr_pages.append(page_no)
    if ocr_pages:
        warnings.append(
            "OCR-derived text on pages " + ", ".join(str(n) for n in ocr_pages)
            + ". OCR is best-effort: check the page image."
        )
    return ocr_pages


def _chunk_sentences(sentences: list[SentenceRecord]) -> list[chunks_store.ChunkInsert]:
    chunks: list[chunks_store.ChunkInsert] = []
    buffer: list[SentenceRecord] = []
    size = 0
    counter = 1

    def flush() -> None:
        nonlocal buffer, size, counter
        if not buffer:
            return
        first, last = buffer[0], buffer[-1]
        chunks.append(
            chunks_store.ChunkInsert(
                ev_id=f"ev_{counter:04d}",
                page_no=first.page,
                section=first.section,
                heading=first.heading or first.section,
                char_start=first.char_start,
                char_end=last.char_end,
                text=" ".join(record.text for record in buffer),
                sentence_ids=[record.sid for record in buffer],
            )
        )
        counter += 1
        buffer, size = [], 0

    for sentence in sentences:
        same_page = not buffer or buffer[-1].page == sentence.page
        same_section = not buffer or buffer[-1].section == sentence.section
        if not same_page or not same_section:
            flush()
        if len(buffer) >= CHUNK_MAX_SENTENCES or (
            size + len(sentence.text) > CHUNK_TARGET_CHARS and buffer
        ):
            flush()
        buffer.append(sentence)
        size += len(sentence.text) + 1
    flush()
    return chunks


def ingest_document(
    *,
    filename: str | None,
    data: bytes,
    settings: Settings,
    ocr_allowed: bool = True,
) -> IngestResult:
    from app.ingest.upload import UploadRejected

    try:
        inspection: UploadInspection = inspect_upload(filename, data, settings)
    except UploadRejected as exc:
        raise IngestError(exc.code.value, str(exc)) from exc

    display_name = sanitise_display_name(filename)
    parsed = _parse(data, inspection.kind, settings)
    if not parsed.pages:
        raise IngestError("NO_PAGES", "the document contains no readable pages")

    warnings: list[str] = list(parsed.warnings)
    quality = assess_pages([(page.page_no, page.text) for page in parsed.pages])
    ocr_pages = (
        _apply_ocr(parsed, data, quality, settings, warnings) if ocr_allowed else []
    )
    if ocr_pages:
        # Re-assess after OCR so coverage and warnings reflect the final text.
        quality = assess_pages([(page.page_no, page.text) for page in parsed.pages])
    warnings.extend(quality.warnings)

    language = {
        page.page_no: classify_page(page.page_no, page.text) for page in parsed.pages
    }
    unread_pages = sorted(
        page_no
        for page_no, verdict in language.items()
        if verdict.language is not PageLanguage.ENGLISH
    )
    if unread_pages:
        warnings.append(
            "Unsupported or inconclusive language on pages "
            + ", ".join(str(n) for n in unread_pages)
            + ". Those pages are excluded from analysis; absence claims are disabled."
        )

    readable = [
        page for page in parsed.pages if page.page_no not in set(unread_pages)
    ]
    sentences = segment_pages([(page.page_no, page.text) for page in readable])
    if not sentences:
        raise IngestError(
            "NO_READABLE_TEXT",
            "no English sentences could be segmented from the readable pages",
        )

    all_text = "\n".join(page.text for page in parsed.pages)
    hidden_text = detect_hidden_text(all_text, data, inspection.kind)
    if hidden_text:
        warnings.append(
            "Possible hidden or invisible text was detected (zero-width characters or an "
            "invisible text layer). It is included in the text below; treat it with suspicion."
        )
    garble_ratio = max((page.garble_ratio for page in quality.pages), default=0.0)
    if unread_pages and not readable:
        language_detected = "unknown"
    elif unread_pages:
        language_detected = "mixed"
    else:
        language_detected = "en"

    doc_id = new_document_id()
    sha256 = hashlib.sha256(data).hexdigest()
    directory = document_dir(settings.data_dir, doc_id)
    directory.mkdir(parents=True, exist_ok=True)

    suffix = ".pdf" if inspection.kind == "pdf" else ".txt"
    (directory / f"source{suffix}").write_bytes(data)

    connection = init_db(directory / "doc.sqlite3")
    try:
        quality_flags = sorted({flag for page in quality.pages for flag in page.flags})
        documents_store.create_document(
            connection,
            doc_id=doc_id,
            sha256=sha256,
            source_filename=display_name,
            source_kind=inspection.kind,
            page_count=len(parsed.pages),
            parser_version=PARSER_VERSION,
            language_flags=repr(unread_pages),
            quality_flags=repr(quality_flags),
            ocr_used=bool(ocr_pages),
            model_tag=settings.model_tag,
            model_digest=settings.model_digest,
        )
        for page in parsed.pages:
            flags = [flag for flag in quality.pages if flag.page_no == page.page_no]
            pages_store.insert_page(
                connection,
                doc_id=doc_id,
                page_no=page.page_no,
                text=page.text,
                flags=repr(flags[0].flags if flags else []),
                printed_label=None,
            )
        sentences_store.insert_sentences(
            connection,
            doc_id,
            [
                sentences_store.SentenceInsert(
                    sid=sentence.sid,
                    page_no=sentence.page,
                    section=sentence.section,
                    char_start=sentence.char_start,
                    char_end=sentence.char_end,
                    text=sentence.text,
                    ocr_derived=sentence.page in set(ocr_pages),
                    heading=sentence.heading,
                )
                for sentence in sentences
            ],
        )
        chunk_list = _chunk_sentences(sentences)
        chunks_store.insert_chunks(connection, doc_id, chunk_list)
        fts.rebuild(connection)
        replace_clause_map(connection, doc_id, build_clause_map(sentences))
        connection.commit()
    finally:
        connection.close()

    return IngestResult(
        document_id=doc_id,
        display_name=display_name,
        source_kind=inspection.kind,
        sha256=sha256,
        page_count=len(parsed.pages),
        sentence_count=len(sentences),
        chunk_count=len(_chunk_sentences(sentences)),
        readable_pages=len(readable),
        unread_pages=unread_pages,
        ocr_pages=ocr_pages,
        warnings=sorted(set(warnings)),
        quality_flags=sorted({flag for page in quality.pages for flag in page.flags}),
        garble_ratio=round(garble_ratio, 4),
        hidden_text_detected=bool(hidden_text),
        language_detected=language_detected,
    )


def source_path(data_root: str | Path, doc_id: str) -> Path:
    directory = document_dir(data_root, doc_id)
    for name in ("source.pdf", "source.txt"):
        candidate = directory / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(doc_id)
