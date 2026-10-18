
"""Per-run provenance registry (Guide 9.1 stage 2).

Only evidence returned by an approved tool during THIS run for THIS document can
be cited. The registry is created per ask request and never persists. A sid is
not sufficient because it exists in the database; it must have been exposed to
the model in the current run.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Evidence:
    sid: str
    page: int
    section: str | None
    quote: str
    ocr_derived: bool = False
    document_sha256: str | None = None


class UnknownSidError(KeyError):
    pass


class ProvenanceRegistry:
    def __init__(self, document_id: str, document_sha256: str | None = None) -> None:
        self.document_id = document_id
        self.document_sha256 = document_sha256
        self._items: dict[str, Evidence] = {}

    def register(self, items: list[Evidence]) -> None:
        """Called only by the tool layer with records from the bound document."""
        for item in items:
            self._items[item.sid] = item

    def knows(self, sid: str) -> bool:
        return sid in self._items

    def evidence_for(self, sids: list[str]) -> list[Evidence]:
        missing = [sid for sid in sids if sid not in self._items]
        if missing:
            raise UnknownSidError(f"sids not returned in this run: {missing}")
        return [self._items[sid] for sid in sids]

    def all_sids(self) -> list[str]:
        return sorted(self._items)
