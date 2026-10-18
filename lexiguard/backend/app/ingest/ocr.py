"""Local Tesseract OCR, page-scoped and quality-triggered (Guide 6.5).

Rules encoded here:
  * OCR only runs on pages the quality gate flagged (image-only / low text).
  * Tesseract is a local binary; nothing is downloaded while processing.
  * Every sentence derived from OCR is stored with `ocr_derived = 1`, and the UI
    must show "OCR-derived -- check the page image".
  * If Tesseract is absent the page is left unread; the document gets an
    UNREADABLE_CONTENT warning instead of a guessed transcription.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from app.ingest.errors import OcrUnavailable

MAX_OCR_PAGES = 40
OCR_TIMEOUT_S = 30.0
MIN_MEANINGFUL_CHARS = 20


def tesseract_path() -> str | None:
    return shutil.which("tesseract")


def ocr_available() -> bool:
    return tesseract_path() is not None


def ocr_png_bytes(png: bytes, *, language: str = "eng", timeout_s: float = OCR_TIMEOUT_S) -> str:
    """Run Tesseract on one page image and return its text.

    Raises OcrUnavailable when the binary or the language data is missing, so
    the caller can mark the page unread instead of pretending.
    """
    binary = tesseract_path()
    if binary is None:
        raise OcrUnavailable("Tesseract is not installed")
    with tempfile.TemporaryDirectory(prefix="lexiguard-ocr-") as tmp:
        image = Path(tmp) / "page.png"
        image.write_bytes(png)
        output_base = Path(tmp) / "out"
        try:
            completed = subprocess.run(  # noqa: S603 - fixed binary, fixed args
                [binary, str(image), str(output_base), "-l", language, "--psm", "6"],
                capture_output=True,
                timeout=timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise OcrUnavailable("Tesseract timed out") from exc
        text_file = output_base.with_suffix(".txt")
        if completed.returncode != 0 or not text_file.exists():
            raise OcrUnavailable("Tesseract failed or language data is missing")
        text = text_file.read_text(encoding="utf-8", errors="replace").strip()
    if len(text) < MIN_MEANINGFUL_CHARS:
        raise OcrUnavailable("OCR produced no usable text")
    return text


def ocr_verdict_note() -> str:
    return "OCR-derived text is best-effort: check the page image before relying on a quotation."
