
"""Canary scanning for privacy evidence (Guide 11.4).

Returns path names only -- never file contents. Raw loopback payloads are never
captured or committed; only counts and non-loopback destinations belong in a
privacy report.
"""
from __future__ import annotations

from pathlib import Path


def canary_present(data: bytes, canaries: list[str]) -> bool:
    return any(canary and canary.encode("utf-8") in data for canary in canaries)


def scan_for_canaries(paths: list[Path], canaries: list[str]) -> list[str]:
    """Return app-controlled file paths containing any canary string."""
    hits: list[str] = []
    for root in paths:
        root = Path(root)
        if root.is_file():
            files = [root]
        elif root.is_dir():
            files = [path for path in root.rglob("*") if path.is_file()]
        else:
            continue
        for file in files:
            try:
                data = file.read_bytes()
            except OSError:
                continue
            if canary_present(data, canaries):
                hits.append(str(file))
    return hits
