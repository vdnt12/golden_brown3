#!/usr/bin/env python3
"""Download CUAD v1 (CC BY 4.0) with a pinned hash.

The 40 MB JSON is intentionally not committed. The manifest in
`datasets/manifest.json` records source, licence and hash so the evaluation is
reproducible without shipping third-party data in the repository.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGET = ROOT / "datasets" / "cuad" / "CUAD_v1.json"
URL = "https://huggingface.co/datasets/theatticusproject/cuad/resolve/main/CUAD_v1/CUAD_v1.json"
EXPECTED = "ed0b77d85bdf4014d7495800e8e4a70565b48ee6f8a2e5dca9cf8655dbf10eae"


def main() -> int:
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    if not TARGET.exists():
        print(f"downloading {URL}")
        with urllib.request.urlopen(URL, timeout=120) as response:  # noqa: S310
            TARGET.write_bytes(response.read())
    digest = hashlib.sha256(TARGET.read_bytes()).hexdigest()
    print(f"sha256: {digest}")
    if digest != EXPECTED:
        print("HASH MISMATCH: refusing to use this file.", file=sys.stderr)
        return 2
    manifest = {
        "cuad": {
            "name": "CUAD v1",
            "url": URL,
            "license": "CC BY 4.0",
            "sha256": digest,
            "bytes": TARGET.stat().st_size,
            "used_for": "deterministic pipeline validation: ingestion, quotation integrity, "
            "concept coverage on lawyer-annotated clause spans",
        }
    }
    (ROOT / "datasets" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
