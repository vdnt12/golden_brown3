# ADR-0004 — Lexical-first retrieval with SQLite FTS5, no vector database

- **Status:** Accepted
- **Date:** 2026-10-18

## Context

The default install must be small, offline and easy to audit. Dense retrieval adds model downloads,
embedding compute and a second model whose behaviour is hard to evaluate on a small corpus.
Rental agreements are formulaic; lexical matching plus a curated topic lexicon covers most queries.

## Decision

- Retrieval is BM25 over SQLite FTS5 external-content chunks, with a quoted-term query builder and
  an allowlisted rental-topic lexicon for expansion.
- Cross-references (clause/schedule/subject-to) are extracted and expanded deterministically.
- A silence gate decides whether absence may be claimed.
- No vector store, embedding model, `torch`, FAISS or Hugging Face Hub access in the default build.

## Consequences

**Positive**: zero extra model, deterministic, fast, fully local, easy to test.

**Negative**: vocabulary mismatch can cause missed evidence; non-English and OCR-garbled text
retrieves poorly; synonym coverage is manual.

## Alternatives rejected

- Hybrid dense+lexical from day one: cost/complexity before evaluation evidence.
- Pure model long-context stuffing: exceeds context and weakens citation control.

## Follow-ups

- T6 expansion and paraphrase-twin evaluation.
- Dense retrieval only as a Tier 2 ADR with a local model, if evaluation shows a lexical ceiling.
