# Contribution notes

## What was built by whom

**Scaffold status: no external contributions yet.** This document is a template that must be
filled with real names, dates and PR links; do not present placeholders as a history.

| Area | Owner (fill in) | First commit | Review |
|---|---|---|---|
| Architecture / contracts | | | |
| Ingestion / parser | | | |
| Retrieval / agent runtime | | | |
| Validation / legal policy | | | |
| Privacy / threat model | | | |
| Frontend / accessibility | | | |
| Evaluation / fixtures | | | |

## Rules for contributors

1. Read `STRUCTURE.md`, `docs/ARCHITECTURE.md` and `docs/THREAT_MODEL.md` first.
2. Do not add network calls, telemetry, CDNs, cloud models or browser storage for document data.
   CI and review enforce this; a PR that needs an exception needs an ADR.
3. Never let model output set quotes, page numbers, sections, evidence ids, statuses or verdicts.
4. Add or update a test for every behaviour change; run `make test` and `make lint`.
5. Update docs in the same PR. A feature without a limit statement is incomplete.
6. Do not claim privacy, accuracy or performance results that are not in `reports/` for that
   release.
7. Keep the default install lightweight: no `torch`, no dense embeddings, no PyMuPDF.
8. Use synthetic fixtures only; never commit a real agreement or personal data.

## Hacktoberfest

The project is submitted to the ZeroDay OSS Hacktoberfest 2026 open-source track (Problem
Statement 2). Hacktoberfest PRs follow the same rules; meaningful contributions include tests,
accessibility fixes, documentation of limits, lexicon coverage and parser robustness — not
drive-by formatting.

## Commit and PR conventions

- Conventional commit prefixes (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
- One logical change per PR; describe user-visible effects and new limits.
- PR template asks for: privacy impact, legal-boundary impact, tests run (exact commands), docs
  updated, and whether any claim in the README changes.
- Review checklist mirrors `AGENTS.md`.

## Rehearsal evidence (fill in Phase 9)

| Rehearsal | Date | Duration | Steps passed | Issues found |
|---|---|---:|---|---|
| Dry run on demo hardware | | | | |
| Second run with a fresh profile | | | | |
