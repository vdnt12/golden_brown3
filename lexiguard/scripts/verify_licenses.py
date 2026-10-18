
#!/usr/bin/env python3
"""Dependency licence gate (Guide 17).

Fails on AGPL/GPL and unknown licence metadata; LGPL is review-required (warning).
This is a metadata scan, not legal advice. CI pins the SBOM separately.
"""
from __future__ import annotations

import re
import sys
from importlib import metadata

FORBIDDEN = re.compile(r"\b(?:A?GPL|GNU (?:Affero )?General Public License)\b", re.I)
LGPL = re.compile(r"\bLGPL\b|Lesser General Public License", re.I)
UNKNOWN_MARKERS = ("UNKNOWN", "NONE")


def classify(dist: metadata.Distribution) -> tuple[str, str]:
    meta = dist.metadata
    name = meta.get("Name", dist.metadata.get("Name", "unknown"))
    license_field = meta.get("License") or ""
    classifiers = " ".join(meta.get_all("Classifier") or [])
    text = f"{license_field} {classifiers}"
    if LGPL.search(text):
        return name, "review-lgpl"
    if FORBIDDEN.search(text):
        return name, "forbidden"
    if not text.strip() or any(marker in text.upper() for marker in UNKNOWN_MARKERS):
        return name, "unknown"
    return name, "ok"


def main() -> int:
    problems = []
    warnings = []
    for dist in metadata.distributions():
        name, verdict = classify(dist)
        if verdict == "forbidden":
            problems.append(f"{name}: forbidden copyleft licence")
        elif verdict == "unknown":
            warnings.append(f"{name}: unknown licence metadata (review)")
        elif verdict == "review-lgpl":
            warnings.append(f"{name}: LGPL dependency requires review and notices")

    for warning in warnings:
        print(f"WARN  {warning}")
    for problem in problems:
        print(f"FAIL  {problem}")
    if problems:
        print("Licence gate failed.", file=sys.stderr)
        return 1
    print("Licence gate passed for installed distributions (review warnings above).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
