#!/usr/bin/env python3
"""Fetch one public Indian tenancy-law document for pipeline validation.

What is reachable from a plain sandbox and what is not (tested 2026-10-18):

  * indiacode.nic.in  -> blocked by an edge bot filter (HTML error page, curl and
                         browser UA both refused). Not downloaded.
  * mohua.gov.in      -> the Model Tenancy Act PDF paths now return 404.
  * huggingface.co/datasets/vaquill/open-india-law -> gated (HTTP 401 without a token).
  * prsindia.org      -> serves the PRS Legislative Brief on the Model Tenancy
                         Act, 2021 as a real PDF. Downloaded.

The brief is a policy summary that cites IndiaCode section numbers; it is not a
tenancy agreement, so it is used to test the PDF path, the language gate and the
concept matcher on Indian legal prose - not to claim rental accuracy.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGET_DIR = ROOT / "datasets" / "india_law"
URL = (
    "https://prsindia.org/files/bills_acts/bills_parliament/2021/"
    "Legislative%20Brief%20-%20Model%20Tenancy%20Act%202021.pdf"
)
EXPECTED = "db30e5813241f843cc34d71372677c25abd6891e0e956f99aeee035c4de4abb4"
NAME = "prs_model_tenancy_act_brief_2021.pdf"


def main() -> int:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    target = TARGET_DIR / NAME
    if not target.exists():
        request = urllib.request.Request(URL, headers={"User-Agent": "LexiGuard/0.1 (local evaluation)"})
        with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310
            target.write_bytes(response.read())
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    print(f"sha256: {digest}")
    if digest != EXPECTED:
        print("HASH MISMATCH: refusing to use this file.")
        return 2
    manifest_path = ROOT / "datasets" / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    manifest["india_law"] = {
        "name": "PRS Legislative Brief - Model Tenancy Act, 2021",
        "url": URL,
        "license": "PRS India publishes legislative briefs for public use; redistributed here for evaluation only",
        "sha256": digest,
        "bytes": target.stat().st_size,
        "used_for": "PDF parsing, language gate and concept coverage on Indian tenancy-law prose",
        "inaccessible_sources": {
            "https://www.indiacode.nic.in/bitstream/123456789/21157/1/english_16_of_2021.pdf":
                "blocked by edge bot filter (HTML error page)",
            "https://mohua.gov.in/upload/whatsnew/60b7acb90a086Model-Tenancy-Act-English-02.06.2021.pdf":
                "HTTP 404",
            "https://huggingface.co/datasets/vaquill/open-india-law":
                "gated dataset; HTTP 401 without an access token",
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
