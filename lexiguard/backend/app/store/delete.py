
"""Verified directory deletion (Guide 5.3).

Distinguishes app-controlled file removal from forensic erasure. Canaries are
searched for in app-controlled logs/temp paths; hits are reported, never hidden.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from app.services.privacy import scan_for_canaries


@dataclass
class DeletionReport:
    directory: str
    directory_removed: bool
    canary_hits: list[str] = field(default_factory=list)
    removed_files: int = 0
    remaining_derived_files: list[str] = field(default_factory=list)
    forensic_erasure: bool = False
    notes: list[str] = field(default_factory=list)


def delete_document_directory(
    document_dir: Path,
    *,
    canaries: list[str] | None = None,
    scan_paths: list[Path] | None = None,
) -> DeletionReport:
    doc_dir = document_dir.resolve()
    # Count first: after rmtree there is nothing left to count, and a delete
    # report that cannot say how many files went is not verifiable.
    removed_files = (
        sum(1 for path in doc_dir.rglob("*") if path.is_file()) if doc_dir.exists() else 0
    )
    shutil.rmtree(doc_dir, ignore_errors=True)
    removed = not doc_dir.exists()
    hits: list[str] = []
    if canaries and scan_paths:
        hits = scan_for_canaries(scan_paths, canaries)
    report = DeletionReport(
        directory=str(doc_dir),
        directory_removed=removed,
        canary_hits=hits,
        removed_files=removed_files if removed else 0,
        forensic_erasure=False,
        notes=[
            "App-controlled files were removed and their absence verified.",
            "This is not forensic erasure: SSD wear-levelling, OS swap/hibernation "
            "and external backups are outside the application's control.",
        ],
    )
    if canaries:
        report.notes.append(
            "Canary scan covers app-controlled paths supplied by the caller only."
        )
    return report
