
"""SQLite connection policy and schema bootstrap (Guide 0.3, 5.1).

* secure_delete=ON on every connection
* journal_mode=DELETE (rollback journal; never WAL)
* foreign_keys=ON
* FTS5 presence checked with a probe; startup fails with a clear message
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).with_name("schema.sql")
_SCHEMA_SQL = SCHEMA_PATH.read_text(encoding="utf-8")


class FTS5UnavailableError(RuntimeError):
    pass


def connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA secure_delete = ON")
    connection.execute("PRAGMA journal_mode = DELETE")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def assert_fts5(connection: sqlite3.Connection) -> None:
    try:
        connection.execute("CREATE VIRTUAL TABLE IF NOT EXISTS _lexiguard_fts5_probe USING fts5(x)")
        connection.execute("DROP TABLE IF EXISTS _lexiguard_fts5_probe")
    except sqlite3.OperationalError as exc:  # pragma: no cover - depends on build
        raise FTS5UnavailableError(
            "This Python's SQLite build has no FTS5. Install a build with FTS5 enabled."
        ) from exc


def init_db(db_path: str | Path) -> sqlite3.Connection:
    connection = connect(db_path)
    assert_fts5(connection)
    connection.executescript(_SCHEMA_SQL)
    connection.commit()
    return connection


def pragma_report(connection: sqlite3.Connection) -> dict[str, object]:
    def one(sql: str) -> object:
        row = connection.execute(sql).fetchone()
        return row[0] if row else None

    return {
        "secure_delete": one("PRAGMA secure_delete"),
        "journal_mode": one("PRAGMA journal_mode"),
        "foreign_keys": one("PRAGMA foreign_keys"),
    }
