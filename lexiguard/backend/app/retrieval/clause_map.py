
"""Deterministic clause map from segmented sentences (Guide 7.3).

Grouping only: it does not interpret, rank or judge clauses.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.ingest.segment import SentenceRecord


@dataclass(frozen=True)
class ClauseEntry:
    label: str
    page: int
    sid_first: str
    sid_last: str
    sentence_count: int


@dataclass
class ClauseMap:
    entries: list[ClauseEntry] = field(default_factory=list)

    def labels(self) -> list[str]:
        return [entry.label for entry in self.entries]


def build_clause_map(sentences: list[SentenceRecord]) -> ClauseMap:
    grouped: dict[tuple[str, int], list[SentenceRecord]] = {}
    for sentence in sentences:
        if sentence.section is None:
            continue
        grouped.setdefault((sentence.section, sentence.page), []).append(sentence)

    entries: list[ClauseEntry] = []
    for (label, page), group in sorted(
        grouped.items(), key=lambda item: (item[0][1], item[1][0].char_start)
    ):
        entries.append(
            ClauseEntry(
                label=label,
                page=page,
                sid_first=group[0].sid,
                sid_last=group[-1].sid,
                sentence_count=len(group),
            )
        )
    return ClauseMap(entries=entries)
