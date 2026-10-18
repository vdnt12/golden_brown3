
"""Upload validation by content, not by filename (Guide 6.1).

Accepts .pdf and .txt only; checks size, magic bytes and UTF-8 decodability.
The display name is sanitised and used for UI display only -- never as a path.
Rejections carry a stable code so the UI and tests can assert on them.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from app.config import Settings

PDF_MAGIC = b"%PDF-"


class UploadRejection(StrEnum):
    EMPTY = "EMPTY_FILE"
    TOO_LARGE = "FILE_TOO_LARGE"
    BAD_EXTENSION = "UNSUPPORTED_EXTENSION"
    BAD_MAGIC = "NOT_A_PDF"
    BAD_ENCODING = "TXT_NOT_UTF8"


class UploadRejected(ValueError):
    def __init__(self, code: UploadRejection, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}".strip(": "))
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class UploadInspection:
    kind: str  # "pdf" | "txt"
    size_bytes: int
    display_name: str


_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


def sanitise_display_name(filename: str | None) -> str:
    if not filename:
        return "document"
    name = Path(filename.replace("\\", "/")).name
    name = _CONTROL.sub("", name).strip()
    if not name:
        return "document"
    return name[:120]


def inspect_upload(filename: str | None, data: bytes, settings: Settings) -> UploadInspection:
    if not data:
        raise UploadRejected(UploadRejection.EMPTY)
    if len(data) > settings.max_upload_bytes:
        raise UploadRejected(UploadRejection.TOO_LARGE, f">{settings.max_upload_bytes} bytes")

    suffix = Path(filename or "").suffix.lower()
    if suffix not in {".pdf", ".txt"}:
        raise UploadRejected(UploadRejection.BAD_EXTENSION, suffix or "(none)")

    if suffix == ".pdf":
        if not data.startswith(PDF_MAGIC):
            raise UploadRejected(UploadRejection.BAD_MAGIC)
        kind = "pdf"
    else:
        try:
            data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise UploadRejected(UploadRejection.BAD_ENCODING) from exc
        kind = "txt"

    return UploadInspection(kind=kind, size_bytes=len(data), display_name=sanitise_display_name(filename))
