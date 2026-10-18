
-- Per-document database. Created once per data/docs/<doc_id>/doc.sqlite3.
-- PRAGMAs are applied per connection in app/store/db.py:
--   secure_delete=ON, journal_mode=DELETE (no WAL), foreign_keys=ON.
-- Run history contains no question, answer or evidence text by default.

CREATE TABLE IF NOT EXISTS document (
    doc_id          TEXT PRIMARY KEY,
    sha256          TEXT NOT NULL,
    source_filename TEXT,
    source_kind     TEXT NOT NULL CHECK (source_kind IN ('pdf', 'txt')),
    page_count      INTEGER NOT NULL CHECK (page_count >= 1),
    parser_version  TEXT NOT NULL,
    language_flags  TEXT NOT NULL DEFAULT '[]',
    quality_flags   TEXT NOT NULL DEFAULT '[]',
    ocr_used        INTEGER NOT NULL DEFAULT 0 CHECK (ocr_used IN (0, 1)),
    created_at      TEXT NOT NULL,
    model_tag       TEXT,
    model_digest    TEXT
);

CREATE TABLE IF NOT EXISTS pages (
    doc_id        TEXT NOT NULL REFERENCES document(doc_id) ON DELETE CASCADE,
    page_no       INTEGER NOT NULL CHECK (page_no >= 1),
    printed_label TEXT,
    text          TEXT NOT NULL,
    text_hash     TEXT NOT NULL,
    flags         TEXT NOT NULL DEFAULT '[]',
    PRIMARY KEY (doc_id, page_no)
);

CREATE TABLE IF NOT EXISTS sentences (
    sid         TEXT NOT NULL,
    doc_id      TEXT NOT NULL REFERENCES document(doc_id) ON DELETE CASCADE,
    page_no     INTEGER NOT NULL,
    section     TEXT,
    heading     TEXT,
    char_start  INTEGER NOT NULL CHECK (char_start >= 0),
    char_end    INTEGER NOT NULL CHECK (char_end >= char_start),
    text        TEXT NOT NULL,
    ocr_derived INTEGER NOT NULL DEFAULT 0 CHECK (ocr_derived IN (0, 1)),
    PRIMARY KEY (doc_id, sid),
    UNIQUE (doc_id, page_no, char_start, char_end),
    FOREIGN KEY (doc_id, page_no) REFERENCES pages(doc_id, page_no) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chunks (
    ev_id        TEXT NOT NULL,
    doc_id       TEXT NOT NULL REFERENCES document(doc_id) ON DELETE CASCADE,
    page_no      INTEGER NOT NULL DEFAULT 1,
    section      TEXT,
    heading      TEXT,
    char_start   INTEGER NOT NULL,
    char_end     INTEGER NOT NULL,
    text         TEXT NOT NULL,
    numbers      TEXT NOT NULL DEFAULT '',
    sentence_ids TEXT NOT NULL,
    PRIMARY KEY (doc_id, ev_id)
);

CREATE TABLE IF NOT EXISTS clauses (
    clause_id TEXT PRIMARY KEY,
    doc_id    TEXT NOT NULL REFERENCES document(doc_id) ON DELETE CASCADE,
    label     TEXT,
    heading   TEXT,
    page_no   INTEGER,
    topics    TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS relationships (
    rel_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id        TEXT NOT NULL REFERENCES document(doc_id) ON DELETE CASCADE,
    source_clause TEXT NOT NULL,
    target_clause TEXT NOT NULL,
    rel_type      TEXT NOT NULL,
    origin        TEXT NOT NULL CHECK (origin IN ('deterministic', 'model_suggested'))
);

-- Run ledger: identifiers and counts only; no question/answer/evidence text.
CREATE TABLE IF NOT EXISTS run_ledger (
    run_id           TEXT PRIMARY KEY,
    doc_id           TEXT NOT NULL REFERENCES document(doc_id) ON DELETE CASCADE,
    route            TEXT,
    status           TEXT,
    path             TEXT,
    tool_names       TEXT NOT NULL DEFAULT '[]',
    tool_calls       INTEGER NOT NULL DEFAULT 0,
    model_calls      INTEGER NOT NULL DEFAULT 0,
    sids_exposed     TEXT NOT NULL DEFAULT '[]',
    validation_codes TEXT NOT NULL DEFAULT '[]',
    duration_ms      INTEGER
);

-- External-content FTS index over chunks. `numbers` stores normalised numeric
-- tokens so "Rs. 25,000/-", "25000" and the digits in "25,000" match each other.
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    text,
    heading,
    numbers,
    content = 'chunks',
    content_rowid = 'rowid',
    tokenize = 'unicode61 remove_diacritics 2'
);

CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, text, heading, numbers)
    VALUES (new.rowid, new.text, new.heading, new.numbers);
END;

CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, text, heading, numbers)
    VALUES ('delete', old.rowid, old.text, old.heading, old.numbers);
END;

CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, text, heading, numbers)
    VALUES ('delete', old.rowid, old.text, old.heading, old.numbers);
    INSERT INTO chunks_fts(rowid, text, heading, numbers)
    VALUES (new.rowid, new.text, new.heading, new.numbers);
END;

CREATE INDEX IF NOT EXISTS idx_sentences_page ON sentences(doc_id, page_no, char_start);
CREATE INDEX IF NOT EXISTS idx_chunks_page ON chunks(doc_id, page_no);
