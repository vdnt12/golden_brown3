# AGENTS.md — rules for coding agents

You are working on LexiGuard, a privacy-first local legal-document triage application. The design
authority is `docs/SOLUTION_GUIDE_v3.md`; the implementation map is `docs/IMPLEMENTATION_MAP.md`.
Read `STRUCTURE.md` before touching code.

**First rule: do not claim work that has not run.** No “passing”, “verified”, “private”,
“accurate”, “fetched”, “deleted” or “benchmarked” statement may appear unless the command was
executed in this environment and its output is quoted. The application is built end to end and
covered by tests, but **no live model call and no privacy capture exist**, so accuracy, latency and
“nothing leaves the machine” remain unproven claims. `docs/LIMITATIONS.md` is the list of what is
not known yet.

## Non-negotiable invariants

1. The model never supplies quotes, page numbers, section numbers, evidence ids, statuses,
   missing-information decisions or legal verdicts. `ModelAnswer` is
   `{points:[{point_id, kind, text, sids}]}`; unknowns are rejected.
2. The backend renders every quotation from stored sentence text. Never re-wrap, trim, “fix” or
   paraphrase a quotation in the UI.
3. `legal_verdict` is always `null`. Legal conclusions degrade to `LEGAL_LIMIT` with neutral
   templates; never give advice, predictions or reassurance.
4. Requests to Ollama use native `/api/chat`, `stream:false`, `think:false`, a simple app-owned
   JSON Schema, fixed seed, `temperature:0`, `num_ctx:8192`, and **never a `tools` key**.
5. Retrieval is lexical (SQLite FTS5) with a rental-topic lexicon. Do not add vector stores,
   `torch`, embeddings, hosted APIs, telemetry or analytics to the default build.
6. No CDN or inline script/style; CSP `default-src 'self'`. No browser storage of document data.
7. Loopback bind only. Exact Host allowlist. Origin allowlist on writes. Bearer on every
   `/api/*` route, including health. No wildcard CORS.
8. Fail closed. Missing evidence → `INSUFFICIENT_EVIDENCE`; absence requires the silence gate;
   any validation failure drops the claim rather than softening it.
9. Deletion is “app-controlled files removed and verified”, never “forensic erasure”.
10. Never weaken: validator, citations, legal policy, privacy tests, deletion, fail-closed
    behaviour, or honest limitations.

## Commands that must stay green

```bash
PYTHONPATH=backend python3 -m pytest          # currently 111 passed, 1 skipped
python3 -m ruff check backend tests scripts   # currently clean
npm run build                                 # currently succeeds
```

If a change makes one of these fail, fix it or revert; do not edit the assertion to match broken
behaviour, and do not mark the release ready.

## Where to work

- Contracts: `backend/app/core/enums.py`, `schemas/*` — change here first.
- Validation: `backend/app/validation/*` — add tests before behaviour.
- Storage: `backend/app/store/*` — keep `secure_delete=ON`, DELETE journal, no WAL, FTS5.
- API: `backend/app/api/*` — authenticated stubs return `501` until their phase.
- UI: `frontend/src/*` — no `dangerouslySetInnerHTML`, no storage APIs, no inline styles.

## Docs discipline

- A behaviour change updates the matching doc in the same commit: `ARCHITECTURE.md`,
  `DATA_FLOW.md`, `IMPLEMENTATION_MAP.md`, `TEST_PLAN.md`, `LIMITATIONS.md`.
- Numbers go into `TEST_PLAN.md` only with the exact command and date.
- A decision that changes an invariant needs an ADR in `docs/adr/` and an update to the guide
  reference — never a silent divergence.

## Stop and ask before

- adding a dependency that is AGPL/GPL, a model runtime, a vector DB, or anything that phones home;
- changing a hard limit (8 tool calls, 4 model calls, 2 loops, 12 chunks, 2.5K-token packet,
  500-character question) without an ADR;
- changing deletion semantics or privacy wording;
- claiming a privacy/accuracy result.
