"""Typed parser failures. Every one maps to a controlled API error, never a 500."""
from __future__ import annotations


class ParserError(RuntimeError):
    """Base class for controlled parser failures."""


class ParserUnavailable(ParserError):
    """The parser dependency (pypdfium2 / Tesseract) is not installed."""


class PdfEncryptedError(ParserError):
    """The PDF needs a password; GBDoc never asks for or stores one."""


class PdfMalformedError(ParserError):
    """The PDF could not be opened or rendered by PDFium."""


class ParserTimeoutError(ParserError):
    """The parser child process exceeded its wall-clock budget."""


class ParserLimitError(ParserError):
    """The document exceeded page, size or output caps."""


class OcrUnavailable(ParserError):
    """Tesseract is not installed or produced no usable text."""
