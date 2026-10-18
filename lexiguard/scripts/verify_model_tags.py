
#!/usr/bin/env python3
"""Verify pinned Ollama tags and record digests in reports/env.json.

Fails with a clear error if a required tag is missing. Reads only loopback.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

OLLAMA = "http://127.0.0.1:11434"
REQUIRED = ["gemma4:e4b-it-q4_K_M", "gemma4:e2b-it-q4_K_M"]


def get_json(path: str) -> dict:
    with urllib.request.urlopen(f"{OLLAMA}{path}", timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    try:
        version = get_json("/api/version")
        tags = get_json("/api/tags")
    except Exception as exc:  # noqa: BLE001 - report the exact failure
        print(f"ERROR: cannot reach Ollama on loopback: {exc}", file=sys.stderr)
        print("Start it with: OLLAMA_NO_CLOUD=1 ollama serve", file=sys.stderr)
        return 1

    by_name = {
        (model.get("name") or model.get("model")): model
        for model in tags.get("models", [])
    }
    missing = [tag for tag in REQUIRED if tag not in by_name]
    if missing:
        print(f"ERROR: missing Ollama tags: {missing}", file=sys.stderr)
        for tag in missing:
            print(f"  ollama pull {tag}", file=sys.stderr)
        return 1

    payload = {
        "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "ollama_version": version.get("version"),
        "required_tags": {
            tag: {
                "digest": by_name[tag].get("digest"),
                "size_bytes": by_name[tag].get("size"),
            }
            for tag in REQUIRED
        },
        "note": "Digests move. Re-run after any model or Ollama upgrade.",
    }
    out = Path("reports/env.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    for tag in REQUIRED:
        print(f"  {tag}: {by_name[tag].get('digest')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
