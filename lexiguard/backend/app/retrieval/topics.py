
"""Versioned rental-topic lexicon (Guide 7.1).

The lexicon aids retrieval; it is not a legal taxonomy and never a judgment.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml


@lru_cache(maxsize=16)
def load_topics(path: str | Path) -> dict[str, list[str]]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    topics: dict[str, list[str]] = {}
    for entry in payload.get("topics", []):
        name = str(entry["name"]).strip().lower()
        synonyms = [str(s).strip().lower() for s in entry.get("synonyms", [])]
        topics[name] = sorted(set(synonyms), key=len, reverse=True)
    return topics


def classify_topics(query: str, topics: dict[str, list[str]]) -> list[str]:
    text = query.lower()
    matches: list[tuple[int, str]] = []
    for name, synonyms in topics.items():
        score = sum(1 for synonym in synonyms if synonym and synonym in text)
        if score:
            matches.append((score, name))
    matches.sort(key=lambda item: (-item[0], item[1]))
    return [name for _, name in matches]
