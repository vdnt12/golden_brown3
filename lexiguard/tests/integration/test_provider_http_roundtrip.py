"""End-to-end HTTP round-trip through the real Ollama adapter, with a stub server.

The stub is **not** a language model: it echoes an evidence sentence that the
backend exposed, exactly as a compliant model is asked to do. This test proves
the transport, JSON-schema request shape, response parsing, context check,
validation and rendering work for both supported model families (Gemma and
Hermes) without downloading several gigabytes.
"""
from __future__ import annotations

import json
import pathlib
import re
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from app.config import Settings
from app.ingest.pipeline import ingest_document
from app.model.ollama_native import OllamaNativeProvider
from app.model.registry import availability
from app.services.answer import answer_question

FIXTURES = pathlib.Path(__file__).resolve().parents[2] / "fixtures"
EVIDENCE_LINE = re.compile(r"^\[(s_\d{4,8})\] p\d+ s[^:]*: (.+)$", re.MULTILINE)


class _StubHandler(BaseHTTPRequestHandler):
    tags: list[str] = []

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        if self.path != "/api/tags":
            self.send_error(404)
            return
        payload = {
            "models": [{"name": tag, "digest": "stub" + tag[:8], "size": 1} for tag in self.tags]
        }
        self._json(payload)

    def do_POST(self) -> None:  # noqa: N802 - http.server API
        if self.path != "/api/chat":
            self.send_error(404)
            return
        length = int(self.headers.get("content-length") or 0)
        request = json.loads(self.rfile.read(length) or b"{}")
        assert "tools" not in request, "the adapter must never send an Ollama tools array"
        user = next(
            (message["content"] for message in request["messages"] if message["role"] == "user"),
            "",
        )
        match = EVIDENCE_LINE.search(user)
        if not match:
            content = json.dumps({"points": []})
        else:
            sid, text = match.group(1), match.group(2).strip()
            content = json.dumps(
                {
                    "points": [
                        {
                            "point_id": "p1",
                            "kind": "STATED",
                            "text": text[:600],
                            "sids": [sid],
                        }
                    ]
                }
            )
        self._json(
            {
                "model": request.get("model"),
                "message": {"role": "assistant", "content": content},
                "prompt_eval_count": 900,
                "eval_count": 120,
                "done": True,
            }
        )

    def _json(self, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args) -> None:  # silence the stub
        return


@pytest.fixture()
def stub_server():
    _StubHandler.tags = ["gemma4:e4b-it-q4_K_M", "hermes3:8b"]
    server = ThreadingHTTPServer(("127.0.0.1", 0), _StubHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=2)


@pytest.mark.parametrize(
    ("tag", "expected_model_calls"),
    [("gemma4:e4b-it-q4_K_M", 1), ("hermes3:8b", 1)],
)
def test_both_model_families_answer_through_http(stub_server, tag, expected_model_calls):
    settings = Settings(data_dir=pathlib.Path(tempfile.mkdtemp()), ollama_url=stub_server)
    result = ingest_document(
        filename="synthetic_rental_simple.txt",
        data=(FIXTURES / "synthetic_rental_simple.txt").read_bytes(),
        settings=settings,
    )
    provider = OllamaNativeProvider(base_url=stub_server, model=tag, seed=42)
    answer = answer_question(
        settings,
        result.document_id,
        "What is the monthly rent?",
        provider=provider,
        model_tag=tag,
    )
    assert answer.status.value == "ANSWERED", answer.run_meta
    assert answer.claims
    assert answer.run_meta is not None
    assert answer.run_meta.model_tag == tag
    assert answer.run_meta.model_calls == expected_model_calls
    rejected = {
        code
        for code in answer.run_meta.validation_codes
        if code not in {"OFF_TOPIC_HITS_DROPPED"}
    }
    assert rejected == set(), answer.run_meta.validation_codes
    # The quote must come from the stored sentence, verbatim.
    claim = answer.claims[0]
    assert claim.evidence[0].quote in claim.text or claim.text in claim.evidence[0].quote


def test_availability_reports_both_tags(stub_server):
    settings = Settings(data_dir=pathlib.Path(tempfile.mkdtemp()), ollama_url=stub_server)
    rows = {row["alias"]: row for row in availability(settings)}
    assert rows["gemma"]["available"] is True
    assert rows["hermes"]["available"] is True
    assert rows["gemma-e2b"]["available"] is False  # not in the stub's tag list
