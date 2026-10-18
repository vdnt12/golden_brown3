#!/usr/bin/env python3
"""End-to-end smoke test of the running application over real HTTP.

Starts `python -m app` on a free loopback port with a throwaway data directory,
redeems the one-time launch code, then walks the whole v3.2 contract:
session -> health -> models -> upload -> overview -> pages -> evidence -> review
-> ask -> delete.

It asserts field names and invariants, not values, so it keeps working as the
pipeline changes; the ask route is expected to fail closed when no Ollama daemon
is running. Exits non-zero on the first failed check.

    python3 scripts/live_api_smoke.py
"""
from __future__ import annotations

import contextlib
import os
import pathlib
import re
import signal
import socket
import subprocess
import sys
import time

import httpx

ROOT = pathlib.Path(__file__).resolve().parents[1]
LOG = pathlib.Path("/tmp/lexiguard_launcher.log")
DATA_DIR = "/tmp/lexiguard_smoke_data"
ORIGIN_HOST = "127.0.0.1"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind((ORIGIN_HOST, 0))
        return int(sock.getsockname()[1])


def start_server() -> tuple[subprocess.Popen, str, str]:
    LOG.write_text("")
    handle = LOG.open("w")
    port = free_port()
    env = dict(
        os.environ,
        PYTHONPATH=str(ROOT / "backend"),
        LEXIGUARD_DATA_DIR=DATA_DIR,
        LEXIGUARD_PORT=str(port),
    )
    subprocess.run(["rm", "-rf", DATA_DIR], check=False)
    proc = subprocess.Popen(
        [sys.executable, "-m", "app"],
        cwd=ROOT,
        env=env,
        stdout=handle,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    deadline = time.time() + 30
    while time.time() < deadline:
        time.sleep(0.2)
        text = LOG.read_text()
        match = re.search(r"(http://127\.0\.0\.1:\d+)/#k=([A-Za-z0-9_-]+)", text)
        if match:
            return proc, match.group(1), match.group(2)
    raise SystemExit("launcher did not print a one-time URL within 30 s")


def stop_server(proc: subprocess.Popen) -> None:
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait(timeout=10)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        with contextlib.suppress(ProcessLookupError):
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)


def check(name: str, ok: bool, detail: object = "") -> None:
    print(("PASS " if ok else "FAIL ") + name + (f" :: {detail}" if detail != "" else ""))
    if not ok:
        raise SystemExit(1)


def run(client: httpx.Client, code: str) -> None:
    for _ in range(100):
        try:
            unauthenticated = client.get("/api/health")
            break
        except httpx.ConnectError:
            time.sleep(0.2)
    else:
        raise SystemExit("server never accepted a connection")

    check("health unauthenticated -> 401", unauthenticated.status_code == 401)
    session = client.post("/api/session", json={"launch_code": code})
    check("session", session.status_code == 200, session.text[:80])
    token = session.json()
    check(
        "session fields",
        set(token) == {"access_token", "token_type", "expires_in_seconds"},
        token.keys(),
    )
    check("token_type bearer", token["token_type"] == "bearer")
    client.headers["Authorization"] = f"Bearer {token['access_token']}"

    health = client.get("/api/health").json()
    check(
        "health v3.2",
        {
            "status",
            "local_model_available",
            "model_tag",
            "model_digest",
            "parser_engine",
            "storage_backend",
        }
        <= set(health),
        health,
    )
    check(
        "model unavailability reported honestly",
        health["local_model_available"] is False and health["status"] == "degraded",
    )

    models = client.get("/api/models").json()["models"]
    check(
        "three allowlisted models",
        [row["alias"] for row in models] == ["gemma", "gemma-e2b", "hermes"],
        [row["alias"] for row in models],
    )
    unknown = client.post(
        "/api/documents/x/ask", json={"question": "rent?", "model": "llama3:70b"}
    )
    check("unknown model -> 422", unknown.status_code == 422, unknown.status_code)

    fixture = ROOT / "fixtures" / "synthetic_rental_simple.txt"
    upload = client.post(
        "/api/documents",
        files={"file": (fixture.name, fixture.read_bytes(), "text/plain")},
    )
    check("upload 201", upload.status_code == 201, upload.text[:120])
    document = upload.json()
    check(
        "upload contract",
        {
            "document_id",
            "document_hash",
            "page_count",
            "quality_metrics",
            "extraction_warnings",
            "status",
        }
        <= set(document),
        sorted(document),
    )
    check(
        "quality metrics",
        {"pages_read", "ocr_used", "language_detected", "garble_ratio", "hidden_text_detected"}
        == set(document["quality_metrics"]),
        document["quality_metrics"],
    )
    check("document hash is sha256", len(document["document_hash"]) == 64)

    doc_id = document["document_id"]
    overview = client.get(f"/api/documents/{doc_id}/overview").json()
    check(
        "overview cards object with 11 keys",
        isinstance(overview["cards"], dict) and len(overview["cards"]) == 11,
        list(overview["cards"])[:3],
    )
    check("card shape", {"status", "summary", "evidence"} <= set(overview["cards"]["Rent"]))

    page = client.get(f"/api/documents/{doc_id}/pages/1").json()
    check(
        "page contract",
        {"page_number", "is_virtual_page", "ocr_used", "sentences"} <= set(page),
    )
    sentence = page["sentences"][0]
    check(
        "offset round-trip",
        page["text"][sentence["start_offset"] : sentence["end_offset"]] == sentence["text"],
    )

    evidence = client.get(f"/api/documents/{doc_id}/evidence/{sentence['sid']}").json()
    check(
        "evidence contract",
        {
            "evidence_id",
            "document_hash",
            "page",
            "section",
            "sids",
            "verbatim_text",
            "text_sha256",
        }
        <= set(evidence),
        sorted(evidence),
    )
    check(
        "evidence hash matches text",
        len(evidence["text_sha256"]) == 64 and evidence["verbatim_text"] == sentence["text"],
    )

    review = client.post(f"/api/documents/{doc_id}/review").json()
    check(
        "review contract",
        {"review_status", "attention_first", "questions_for_professional"} <= set(review),
    )
    priorities = [item["priority"] for item in review["attention_first"]]
    check("review sorted by priority", priorities == sorted(priorities), priorities)

    answer = client.post(
        f"/api/documents/{doc_id}/ask", json={"question": "What is the monthly rent?"}
    ).json()
    check("ask fails closed", answer["status"] == "ERROR_LOCAL_MODEL_UNAVAILABLE", answer["status"])
    check("no fabricated claim", answer["claims"] == [] and answer["legal_verdict"] is None)
    check(
        "model tag recorded",
        answer["run_meta"]["model_tag"] == "gemma4:e4b-it-q4_K_M",
        answer["run_meta"]["model_tag"],
    )

    deletion = client.delete(f"/api/documents/{doc_id}").json()
    check(
        "delete contract",
        {
            "files_purged",
            "database_unlinked",
            "model_cache_evicted",
            "canary_scan_passed",
            "forensic_erasure_disclaimer",
        }
        <= set(deletion),
        sorted(deletion),
    )
    check("files actually purged", deletion["files_purged"] >= 2, deletion["files_purged"])
    check("database unlinked", deletion["database_unlinked"] is True)
    check(
        "after delete -> 404",
        client.get(f"/api/documents/{doc_id}/overview").status_code == 404,
    )


def main() -> int:
    proc, base_url, code = start_server()
    try:
        with httpx.Client(
            base_url=base_url,
            headers={"Origin": base_url},
            timeout=30,
        ) as client:
            run(client, code)
    finally:
        stop_server(proc)
    print("\nALL LIVE CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
