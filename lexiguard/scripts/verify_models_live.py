#!/usr/bin/env python3
"""Demonstrate both model families through the real HTTP API, against a stub runtime.

The stub implements Ollama's `/api/tags` and `/api/chat` contract and echoes one
evidence sentence. It is **not** a language model and produces no reasoning. The
purpose is to prove the full application path (session -> upload -> ask -> render)
works for both `gemma` and `hermes` selections, with the backend enforcing the
schema and the quotations.

A real run against Gemma/Hermes inference requires Ollama on the demo machine:

    OLLAMA_NO_CLOUD=1 ollama serve
    ollama pull gemma4:e4b-it-q4_K_M
    ollama pull hermes3:8b
    python3 scripts/verify_models_live.py --real

`--real` skips the stub and talks to the daemon on 127.0.0.1:11434.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "synthetic_rental_conflict.txt"
QUESTION = "What notice period applies if I want to leave?"
ORIGIN = {"Origin": "http://127.0.0.1:8765"}
EVIDENCE_LINE = re.compile(r"^\[(s_\d{4,8})\] p\d+ s[^:]*: (.+)$", re.MULTILINE)


class Stub(BaseHTTPRequestHandler):
    tags = ["gemma4:e4b-it-q4_K_M", "hermes3:8b"]

    def do_GET(self):  # noqa: N802
        self._json({"models": [{"name": tag, "digest": "stub", "size": 1} for tag in self.tags]})

    def do_POST(self):  # noqa: N802
        if self.path != "/api/chat":
            # /api/generate?keep_alive=0 is the unload request; acknowledge it.
            self._json({"done": True})
            return
        length = int(self.headers.get("content-length") or 0)
        request = json.loads(self.rfile.read(length) or b"{}")
        user = next(m["content"] for m in request["messages"] if m["role"] == "user")
        matches = EVIDENCE_LINE.findall(user)
        keyword = "notice" if "notice" in user.lower() else "rent"
        chosen = next(((sid, text) for sid, text in matches if keyword in text.lower()), None)
        points = []
        if chosen:
            points.append(
                {
                    "point_id": "p1",
                    "kind": "STATED",
                    "text": chosen[1].strip()[:600],
                    "sids": [chosen[0]],
                }
            )
        self._json(
            {
                "message": {"role": "assistant", "content": json.dumps({"points": points})},
                "prompt_eval_count": 1200,
                "eval_count": 80,
                "done": True,
            }
        )

    def _json(self, payload):
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


def run(base_url: str, *, real: bool) -> list[dict]:
    results: list[dict] = []
    for alias in ("gemma", "hermes"):
        settings = Settings(
            data_dir=pathlib.Path(tempfile.mkdtemp()),
            ollama_url=base_url,
            launch_code_ttl_s=3600,
        )
        app = create_app(settings)
        client = TestClient(app, base_url="http://127.0.0.1:8765")
        token = client.post(
            "/api/session", json={"launch_code": app.state.launch_code}, headers=ORIGIN
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}", **ORIGIN}
        upload = client.post(
            "/api/documents",
            headers=headers,
            files={"file": (FIXTURE.name, FIXTURE.read_bytes(), "text/plain")},
        )
        document_id = upload.json()["document_id"]
        response = client.post(
            f"/api/documents/{document_id}/ask",
            headers=headers,
            json={"question": QUESTION, "model": alias},
        )
        payload = response.json()
        results.append(
            {
                "alias": alias,
                "http_status": response.status_code,
                "inference": "real Ollama" if real else "stub runtime (not a model)",
                "status": payload["status"],
                "answer": payload["answer"],
                "claims": [
                    {
                        "text": claim["text"],
                        "quote": claim["evidence"][0]["quote"],
                        "page": claim["evidence"][0]["page"],
                        "sid": claim["evidence"][0]["sid"],
                    }
                    for claim in payload["claims"]
                ],
                "model_tag": payload["run_meta"]["model_tag"],
                "model_calls": payload["run_meta"]["model_calls"],
                "tool_calls": payload["run_meta"]["tool_calls"],
                "validation_codes": payload["run_meta"]["validation_codes"],
                "legal_verdict": payload["legal_verdict"],
            }
        )
        client.delete(f"/api/documents/{document_id}", headers=headers)
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--real", action="store_true", help="use a real Ollama on 127.0.0.1:11434")
    args = parser.parse_args()

    server = None
    if args.real:
        base_url = "http://127.0.0.1:11434"
        results = run(base_url, real=True)
    else:
        server = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        try:
            results = run(base_url, real=False)
        finally:
            server.shutdown()

    lines = [
        "# Model round-trip through the application",
        "",
        f"Generated by `scripts/verify_models_live.py` at {_now()}.",
        "",
    ]
    if not args.real:
        lines += [
            "**The inference runtime here is a stub, not a language model.** It implements",
            "Ollama's `/api/tags` and `/api/chat` contract and echoes one evidence sentence.",
            "These rows prove the transport, schema enforcement, provenance checks and",
            "rendering for both model families; they say nothing about answer quality.",
            "Run with `--real` on a machine with Ollama for genuine inference.",
            "",
        ]
    lines += [
        "`OFF_TOPIC_HITS_DROPPED` is a retrieval note, not a validation failure: lexical hits",
        "that share no content word with the question are filtered before the packet is built.",
        "",
        f"Question: *{QUESTION}*",
        "",
        "| Selection | Model tag recorded | HTTP | Status | Claims | Model calls | Validation codes |",
        "|---|---|---:|---|---:|---:|---|",
    ]
    for row in results:
        codes = ", ".join(row["validation_codes"]) or "—"
        lines.append(
            f"| {row['alias']} | `{row['model_tag']}` | {row['http_status']} | {row['status']} | "
            f"{len(row['claims'])} | {row['model_calls']} | {codes} |"
        )
    for row in results:
        lines += ["", f"## {row['alias']} — {row['model_tag']}", ""]
        lines.append(row["answer"])
        for claim in row["claims"]:
            lines += ["", f'> "{claim["quote"]}"', f'> — p.{claim["page"]} ({claim["sid"]})']
        lines += ["", f"`legal_verdict`: {row['legal_verdict']}"]
    (ROOT / "reports" / "model_roundtrip.md").write_text("\n".join(lines) + "\n")
    (ROOT / "reports" / "model_roundtrip.json").write_text(json.dumps(results, indent=2) + "\n")
    for row in results:
        print(row["alias"], row["status"], row["model_tag"], len(row["claims"]), row["validation_codes"])
    return 0


def _now() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())
