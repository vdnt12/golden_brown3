
"""Normalisation contract (Guide 5.2).

All offsets in the application refer to THIS normalized page text, never to raw
PDFium indices. The stored sentence text must round-trip: page.text[start:end]
== sentence.text.
"""
from __future__ import annotations

import re
import unicodedata


def normalize_text(raw: str) -> str:
    if not raw:
        return ""
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    text = unicodedata.normalize("NFC", text)
    for space in ("\u00a0", "\u2007", "\u202f", "\u2028", "\u2029"):
        text = text.replace(space, " " if space != "\u2028" else "\n")
    lines = [re.sub(r"[ \t\f\v]+", " ", line).rstrip() for line in text.split("\n")]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return f"{text}\n" if text else ""


def slice_roundtrip(page_text: str, start: int, end: int) -> str:
    return page_text[start:end]
