"""Curated glossary access (FR-003).

Definitions are team-written, not lawyer-reviewed, and are always presented as a
*general* definition separate from anything found in the user's document. When a
term has no curated entry, the caller must say so rather than let the model
improvise a legal definition.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

GLOSSARY_PATH = Path(__file__).resolve().parents[3] / "glossary" / "rental_terms.yaml"

DISCLAIMER = "General definition, not from your document, and not legal advice."


@dataclass(frozen=True)
class GlossaryEntry:
    entry_id: str
    term: str
    definition: str
    aliases: tuple[str, ...] = ()


def _load(path: Path) -> tuple[str, list[GlossaryEntry]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    version = str(payload.get("version", "unversioned"))
    entries: list[GlossaryEntry] = []
    for index, raw in enumerate(payload.get("entries", []), start=1):
        term = str(raw.get("term", "")).strip()
        definition = str(raw.get("definition", "")).strip()
        if not term or not definition:
            continue
        aliases = tuple(str(a).strip().lower() for a in raw.get("aliases", []) if str(a).strip())
        entries.append(
            GlossaryEntry(
                entry_id=str(raw.get("id") or f"term_{index:03d}"),
                term=term,
                definition=definition,
                aliases=aliases,
            )
        )
    return version, entries


@lru_cache(maxsize=1)
def glossary() -> tuple[str, tuple[GlossaryEntry, ...]]:
    version, entries = _load(GLOSSARY_PATH)
    return version, tuple(entries)


def _normalise(text: str) -> str:
    return re.sub(r"[\s_-]+", " ", text.strip().lower()).strip("\"'` ")


def find_entry(term: str) -> GlossaryEntry | None:
    needle = _normalise(term)
    if not needle:
        return None
    _, entries = glossary()
    for entry in entries:
        if _normalise(entry.term) == needle:
            return entry
    for entry in entries:
        if needle in {_normalise(alias) for alias in entry.aliases}:
            return entry
    for entry in entries:
        if needle and needle in _normalise(entry.term):
            return entry
    return None


def all_terms() -> list[str]:
    _, entries = glossary()
    return [entry.term for entry in entries]
