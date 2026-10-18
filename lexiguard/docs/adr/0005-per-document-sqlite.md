# ADR-0005 — Per-document SQLite with `secure_delete=ON`, DELETE journal

- **Status:** Accepted
- **Date:** 2026-10-18

## Context

Documents must be deletable as a unit, with a verifiable result and no cross-document leakage.
WAL leaves side files that complicate deletion and forensics; `secure_delete` zeroes freed pages.

## Decision

- Each document gets `data/docs/<32-hex doc_id>/` containing its source file and one SQLite DB.
- PRAGMAs on every connection: `secure_delete=ON`, `journal_mode=DELETE`, `foreign_keys=ON`,
  `synchronous=FULL`; WAL explicitly not used; no history tables.
- FTS5 external-content over `chunks`; delete triggers keep the index consistent.
- Deletion removes the directory and reports what was removed; wording never claims forensic
  erasure.

## Consequences

**Positive**: simple blast radius; deletion is a directory removal; per-document corruption is
contained.

**Negative**: no cross-document search; some duplication of schema; crash-safety depends on the
journal, not WAL concurrency.

## Alternatives rejected

- One global DB: harder to delete one document reliably and to prove removal.
- WAL: extra `-wal`/`-shm` files and checkpoint complexity at delete time.

## Follow-ups

- Startup integrity check and repair guidance.
- Test crash-during-delete and reopen behaviour (Phase 7).
