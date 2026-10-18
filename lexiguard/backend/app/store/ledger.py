"""Run ledger rows: identifiers and counts only, never question/answer text."""
from __future__ import annotations

import json
import secrets
import sqlite3


def new_run_id() -> str:
    return secrets.token_hex(8)


def record_run(
    connection: sqlite3.Connection,
    *,
    doc_id: str,
    route: str,
    status: str,
    path: str,
    tool_names: list[str],
    tool_calls: int,
    model_calls: int,
    sids_exposed: list[str],
    validation_codes: list[str],
    duration_ms: int,
    run_id: str | None = None,
) -> str:
    run_id = run_id or new_run_id()
    connection.execute(
        """
        INSERT INTO run_ledger (run_id, doc_id, route, status, path, tool_names, tool_calls,
                                model_calls, sids_exposed, validation_codes, duration_ms)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            doc_id,
            route,
            status,
            path,
            json.dumps(sorted(set(tool_names))),
            tool_calls,
            model_calls,
            json.dumps(sorted(set(sids_exposed))),
            json.dumps(sorted(set(validation_codes))),
            duration_ms,
        ),
    )
    connection.commit()
    return run_id


def list_runs(connection: sqlite3.Connection, doc_id: str, limit: int = 20) -> list[sqlite3.Row]:
    return list(
        connection.execute(
            "SELECT * FROM run_ledger WHERE doc_id = ? ORDER BY rowid DESC LIMIT ?",
            (doc_id, limit),
        )
    )
