# LexiGuard — final repository structure

This is the complete target tree for the **finished application** (v3.1), not just what exists today.
Every path the final app needs appears here exactly once, with its responsibility.

**How to read it**

- A `[P1]` … `[P9]` marker at the start of a line’s comment means **the capability arrives in that
  phase**. Usually the file does not exist yet; for a seam that already exists
  (`ingest/parser.py`, `agent/runtime.py`, …) the marker names the phase that fills it in.
- A line with no marker exists in the repository today in its current form.
- Nothing in this file is a claim that a planned feature works. Current verified state is in
  [`docs/TEST_PLAN.md`](docs/TEST_PLAN.md) §1; module status is in
  [`docs/IMPLEMENTATION_MAP.md`](docs/IMPLEMENTATION_MAP.md).

**Where the built app differs from this target tree (2026-10-18):** the whole runtime path
(`ingest/`, `store/`, `retrieval/`, `agent/`, `validation/`, `services/`, `api/`, frontend) is
implemented. Still absent, and honestly not needed to run the app today:

| Planned path | Why it is absent |
|---|---|
| `store/relationships.py` | Relationship graph was folded into the concept matcher and conflict detector |
| `scripts/generate_fixtures.py` | Fixtures were authored directly and committed, including three derived PDFs |
| `tests/integration/test_{upload,ask,review_overview}_flow.py` | Consolidated into `tests/integration/test_end_to_end.py` |
| `tests/privacy/*`, `tests/e2e/*` | Privacy capture and browser E2E are not built (see `docs/LIMITATIONS.md`) |
| `tests/model/test_{schema_reliability,context_budget,no_tools_live}.py` | Need a live Ollama; the opt-in live test is the only placeholder |
| `CHANGELOG.md`, `pnpm-lock.yaml`, `reports/env.json` | Not produced; SBOM/env recording happens on the demo machine |

**Root name:** `lexiguard/` (the upstream repo may keep its original name `golden_brown1/`; the
package name stays `app`, the distribution name stays `lexiguard`).

---

## 1. The tree

```text
lexiguard/
│
├── README.md                                  # what it is, honest claim table, quickstart, map
├── STRUCTURE.md                               # this file: final tree + phase deltas
├── TASKS.md                                   # phase tracker; only verified command output
├── AGENTS.md                                  # rules for coding agents (invariants, stop conditions)
├── CONTRIBUTING.md                            # contribution rules, Hacktoberfest note
├── CODE_OF_CONDUCT.md                         # Contributor Covenant summary
├── LICENSE                                    # Apache-2.0 canonical text
├── NOTICE                                     # attribution + third-party notices (PDFium, Tesseract)
├── CHANGELOG.md                               # [P9] release notes, one section per tagged release
├── Makefile                                   # setup · demo · isolated-demo · test · lint · frontend
├── Dockerfile                                 # app image; privacy proof runs with --network none
├── .dockerignore                              # [P6] excludes data/, reports/, node_modules
├── .gitignore                                 # excludes data/, weights, dist, venvs, caches, uploads
├── .editorconfig                              # LF, UTF-8, 4/2 space rules
├── pyproject.toml                             # deps, setuptools, pytest/ruff/mypy config
├── requirements.lock                          # [P9] fully pinned Python deps for releases
├── package.json                               # frontend manifest + build scripts
├── package-lock.json                          # npm lockfile (committed for reproducible builds)
├── tsconfig.json                              # strict TypeScript
├── vite.config.ts                             # root=frontend, /api proxy → 127.0.0.1:8765
│
├── .github/
│   ├── workflows/
│   │   └── ci.yml                             # backend tests+ruff, licence gate, frontend build, no-CDN grep
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   └── feature_request.yml
│   ├── PULL_REQUEST_TEMPLATE.md               # privacy/legal/test/docs checklist
│   └── labeler.yml                            # [P9] area labels for triage
│
├── backend/
│   └── app/
│       ├── __init__.py
│       ├── __main__.py                        # launcher: prints one-time #k= URL, runs uvicorn on loopback
│       ├── main.py                            # app factory: Host/Origin/auth middleware, CSP, static mount
│       ├── config.py                          # Settings (env prefix LEXIGUARD_): caps, paths, model tag
│       │
│       ├── core/                              # closed vocabulary + budgets (no I/O)
│       │   ├── __init__.py
│       │   ├── enums.py                       # PointKind, Route, Classification, ResponseStatus, precedence
│       │   ├── limits.py                      # RunBudget: 8 tool / 4 model calls / 2 loops / wall clock
│       │   └── textmetrics.py                 # conservative token estimate (chars ÷ 3.2)
│       │
│       ├── schemas/                           # strict wire contracts (extra="forbid")
│       │   ├── __init__.py
│       │   ├── model_io.py                    # ModelAnswer, ModelPoint, RouterProposal, NextAction
│       │   └── response.py                    # RenderedAnswer, Claim, EvidenceItem, MissingInformation, RunMeta
│       │
│       ├── security/                          # localhost hardening
│       │   ├── __init__.py
│       │   ├── tokens.py                      # 256-bit single-use launch codes, in-memory sessions
│       │   ├── hosts.py                       # exact Host allowlist (DNS-rebinding resistance)
│       │   ├── origin.py                      # exact Origin allowlist on state-changing requests
│       │   └── headers.py                     # CSP baseline, nosniff, no-referrer, frame deny, no-store
│       │
│       ├── api/                               # HTTP only: parse, authorise, delegate, shape errors
│       │   ├── __init__.py
│       │   ├── _deps.py                       # shared route helpers: settings, not-found mapping
│       │   ├── session.py                     # POST /api/session          (code → bearer token)
│       │   ├── health.py                      # GET  /api/health           (booleans only, auth required)
│       │   ├── documents.py                   # POST/GET /api/documents, DELETE /{id}, GET pages (+image)
│       │   ├── ask.py                         # POST /api/documents/{id}/ask
│       │   ├── review.py                      # POST /api/documents/{id}/review
│       │   ├── overview.py                    # GET  /api/documents/{id}/overview
│       │   ├── evidence.py                    # GET  /api/documents/{id}/evidence/{ev}
│       │   ├── models.py                      # GET  /api/models             (allowlist + availability)
│       │   └── _deps.py                       # shared request deps: settings, provider, error mapping
│       │
│       ├── ingest/                            # file → pages → sentences → chunks
│       │   ├── __init__.py
│       │   ├── upload.py                      # magic bytes, size cap, UTF-8 validity, safe display name
│       │   ├── normalize.py                   # NFC, CRLF→LF, whitespace policy (offset source of truth)
│       │   ├── segment.py                     # sentence spans + section detection, offsets round-trip
│       │   ├── language.py                    # per-page English gate (script ratio + function words)
│       │   ├── quality.py                     # coverage, garble ratio, OCR-candidate flags
│       │   ├── parser.py                      # TXT virtual pages exist; [P1] adds PDF text extraction + page render
│       │   ├── worker.py                      # [P1] PDF child process: rlimits, timeout, output cap
│       │   └── ocr.py                         # [P1b] Tesseract fallback, page-scoped, quality-triggered
│       │
│       ├── store/                             # the only module that touches SQLite
│       │   ├── __init__.py
│       │   ├── schema.sql                     # document · pages · sentences · chunks · clauses · relationships · run_ledger · FTS5
│       │   ├── db.py                          # connection, PRAGMAs, schema apply, FTS5 probe
│       │   ├── documents.py                   # document rows, hashes, counters
│       │   ├── pages.py                       # page text, page hash, method/flags
│       │   ├── sentences.py                   # sid/offset rows (citation unit)
│       │   ├── chunks.py                      # evidence rows (retrieval unit) + number index column
│       │   ├── clauses.py                     # [P3] clause map persistence
│       │   ├── relationships.py               # [P3] deterministic / model-suggested links
│       │   ├── ledger.py                      # [P4] run_ledger rows: ids, counts, codes — never text
│       │   ├── fts.py                         # index/purge/rebuild, quoted query helper
│       │   └── delete.py                      # directory removal + verification + report
│       │
│       ├── retrieval/                         # lexical-first, bounded
│       │   ├── __init__.py
│       │   ├── lexical.py                     # quoted FTS5 query, BM25, 12-chunk cap
│       │   ├── topics.py                      # rental + jurisdiction topic classifier
│       │   ├── crossrefs.py                   # clause / schedule / subject-to extraction
│       │   ├── clause_map.py                  # section grouping exists; [P3] adds persistence
│       │   ├── silence.py                     # NOT_LOCATED gate (coverage + language + topics)
│       │   └── packets.py                     # nonce-delimited packets, 2,500-token cap
│       │
│       ├── agent/                             # deterministic control, model only proposes
│       │   ├── __init__.py
│       │   ├── router.py                      # pre-router + stricter-wins merge with proposals
│       │   ├── tools.py                       # 7 read-only tools, 5 model-selectable, argument bounds
│       │   ├── prompts.py                     # system prompt, evidence block, prompt pre-budget
│       │   ├── runtime.py                     # states + budget exist; [P4] fills the transitions
│       │   ├── limits.py                      # re-exports of RunBudget pieces
│       │   └── schemas.py                     # re-exports of model I/O schemas
│       │
│       ├── model/                             # one local provider, no fallback
│       │   ├── __init__.py
│       │   ├── factory.py                     # provider construction + /api/tags availability probe
│       │   ├── registry.py                    # three allowlisted tags + aliases (ADR-0011)
│       │   ├── provider.py                    # LLMProvider protocol (answer / route / expand / next_action / unload)
│       │   ├── ollama_native.py               # /api/chat payload guard, retry, ctx check, unload
│       │   └── gateway.py                     # Hermes gateway refusal (ADR-0010)
│       │
│       ├── validation/                        # model answer → accepted points or nothing
│       │   ├── __init__.py
│       │   ├── provenance.py                  # per-run sid registry (cross-doc/stale rejection)
│       │   ├── literal.py                     # numbers, amounts, percentages, dates (no unit conversion)
│       │   ├── modality.py                    # must/shall/may/not, negation add/drop
│       │   ├── roles.py                       # tenant/landlord canonicalisation + checks
│       │   ├── claim_support.py               # kind-specific support (STATED/RESTATEMENT/…)
│       │   ├── pipeline.py                    # validate_model_answer → accepted / rejected points
│       │   ├── legal_policy.py                # verdict/advice scanner + source-echo exception
│       │   └── renderer.py                    # backend-owned quotes/pages/sections + final scan + status
│       │
│       └── services/                          # use-case orchestration (no HTTP, no SQL)
│           ├── __init__.py
│           ├── lifecycle.py                   # doc-id validation, path safety, delete orchestration
│           ├── documents.py                   # list / read page / read evidence / render / delete
│           ├── answer.py                      # [P4] ask use case: retrieve → model → validate → render
│           ├── review.py                      # [P5] attention list + escalation assembly
│           ├── overview.py                    # [P5] document map assembly for the overview panel
│           ├── silence_context.py             # coverage, incorporated material, silence decision
│           ├── glossary_service.py            # curated glossary lookup + fixed disclaimer
│           ├── privacy.py                     # canary byte scan (reports paths, never content)
│           └── benchmark.py                   # p50/p95 latency summary
│       ├── cli.py                             # ask / documents / delete / models (exit 0/1/2/3)
│
├── frontend/
│   ├── index.html                             # module script only; no inline script/style
│   ├── public/
│   │   └── favicon.svg
│   └── src/
│       ├── main.tsx                           # React root
│       ├── App.tsx                            # launch-code bootstrap → ready / error state
│       ├── api/
│       │   ├── session.ts                     # fragment → POST /api/session → memory token
│       │   └── client.ts                      # typed fetch, Bearer, no-store, ApiError
│       ├── components/
│       │   ├── UploadPanel.tsx                # file input, size/type checks, ingest result
│       │   ├── AskPanel.tsx                   # question ≤500 chars + suggestions
│       │   ├── AnswerView.tsx                 # claims by class + ledger details, no chain-of-thought
│       │   ├── DocumentMap.tsx                # 11 cards from the `cards` object, with warnings
│       │   ├── ModelPicker.tsx                # explicit model selection; unavailable tags disabled
│       │   ├── ReviewPanel.tsx                # attention items + questions to ask a professional
│       │   ├── SourceQuote.tsx                # immutable quotation channel; opens the page viewer
│       │   ├── PageViewer.tsx                 # stored page text with highlight + rendered page image
│       │   ├── StatusBadge.tsx                # text-only status labels (no colour-only meaning)
│       │   ├── PrivacyBanner.tsx              # “Local by default” wording, honest about evidence
│       │   └── DeleteDialog.tsx               # typed confirmation + deletion report
│       ├── pages/
│       │   └── HomePage.tsx                   # documents, tabs, workspace, page viewer
│       ├── styles/
│       │   └── app.css                        # bundled system fonts, focus-visible, reduced motion
│       └── types/
│           └── api.ts                         # RenderedAnswer mirror (legal_verdict: null)
│
├── lexicons/
│   ├── rental_topics.yaml                     # 15 topics + regional synonyms (versioned)
│   ├── jurisdiction_topics.yaml               # 8 local-law topics + caution label
│   └── escalation_templates.yaml              # neutral “questions to bring” + mandatory footer
│
├── glossary/
│   └── rental_terms.yaml                      # 20 curated entries; reviewed: false
│
├── fixtures/
│   ├── README.md                              # provenance table, canaries, hashes, licences
│   ├── synthetic_rental_simple.txt
│   ├── synthetic_rental_indian_style.txt
│   ├── synthetic_rental_conflict.txt
│   ├── synthetic_rental_ambiguous.txt
│   ├── synthetic_rental_injection.txt
│   ├── pdf/                                   # [P1] small synthetic PDFs, deterministically built
│   │   ├── README.md                          # generator command + SHA-256 per file
│   │   ├── simple_one_page.pdf
│   │   ├── two_column_table.pdf
│   │   ├── scanned_page.pdf                   # [P1b] image-only → OCR path
│   │   ├── encrypted.pdf                      # must fail closed
│   │   ├── malformed.pdf                      # truncated structure, must fail closed
│   │   └── devanagari_page.pdf                # language gate must exclude it
│   └── generated/                             # [P1] long_50_pages.pdf etc.; rebuilt on demand, git-ignored
│
├── questions/
│   ├── schema.json                            # JSON Schema for ground-truth rows
│   ├── development.jsonl                      # 12 drafts now; [P3] fills to ≥114 annotated rows
│   └── heldout/
│       └── README.md                          # rules; rows authored after freeze, never read by code
│
├── scripts/
│   ├── setup_local.sh                         # Ollama ≥0.21.1 check, pulls, install, frontend build
│   ├── verify_model_tags.py                   # writes reports/env.json; fails on missing/moved tag
│   ├── verify_licenses.py                     # AGPL/GPL/unknown gate; LGPL warning
│   ├── benchmark_model.py                     # Day-0 + model comparison, real measurements only
│   ├── benchmark_retrieval.py                 # retrieval recall/latency; exits 2 until Phase 3/6
│   ├── run_isolated_demo.sh                   # isolated privacy flow; exits 2 until Phase 6
│   ├── generate_sbom.sh                       # CycloneDX or pip-list fallback + licence report
│   └── generate_fixtures.py                   # [P1] deterministic PDF fixture builder
│
├── tests/
│   ├── conftest.py                            # autouse non-loopback socket guard; shared fixtures
│   ├── data/
│   │   └── scanner_corpus.jsonl               # 48 must-block / 51 must-pass rows
│   ├── unit/
│   │   ├── test_enums.py
│   │   ├── test_schemas.py
│   │   ├── test_literal.py
│   │   ├── test_modality.py
│   │   ├── test_roles.py
│   │   ├── test_legal_scanner.py
│   │   ├── test_router.py
│   │   ├── test_tools.py
│   │   ├── test_normalize_segment.py
│   │   ├── test_language_quality_parser.py
│   │   ├── test_upload.py
│   │   ├── test_parser_docs.py
│   │   ├── test_topics_crossrefs.py
│   │   ├── test_silence_packets.py
│   │   ├── test_prompts.py
│   │   ├── test_budget_tokens_benchmark.py
│   │   ├── test_security_units.py
│   │   ├── test_validation_pipeline.py
│   │   ├── test_renderer.py
│   │   ├── test_model_payload.py
│   │   ├── test_clause_map.py                 # [P3] section grouping, xref persistence
│   │   ├── test_answer_service.py             # [P4] retrieve→model→validate→render with a fake provider
│   │   └── test_review_overview.py            # [P5] attention list, escalation, document map
│   ├── integration/
│   │   ├── test_store.py                      # PRAGMAs, FTS, offset round-trip via DB
│   │   ├── test_delete_lifecycle.py           # traversal, removal, canary report
│   │   ├── test_api_boot.py                   # session, auth, Host, Origin, no secret in HTML
│   │   ├── test_upload_flow.py                # [P1] TXT/PDF upload → pages → sentences → delete
│   │   ├── test_ask_flow.py                   # [P4] HTTP ask with a fake provider + real validator
│   │   └── test_review_overview_flow.py       # [P5] review + overview over HTTP
│   ├── security/
│   │   ├── README.md                          # planned suite; boot tests live in integration/
│   │   ├── test_session_isolation.py          # [P4] two sessions cannot see each other’s data
│   │   ├── test_dns_rebind.py                 # [P4] rebound Host rejected even with a token
│   │   ├── test_headers_live.py               # [P4] CSP/no-store asserted on live responses
│   │   └── test_failclosed.py                 # [P4] parser crash, model timeout, bad JSON
│   ├── privacy/
│   │   ├── test_canary_helper.py
│   │   ├── negative_control.py                # target 192.0.2.1; must be detected, else inconclusive
│   │   ├── test_network_inventory.py          # [P6] attempt-visible capture inside isolation
│   │   ├── test_logs_and_temp_clean.py        # [P6] canaries absent from logs/temp after delete
│   │   └── test_deletion_under_failure.py     # [P7]
│   ├── model/
│   │   ├── test_live_ollama.py                # opt-in: LEXIGUARD_OLLAMA_LIVE=1
│   │   ├── test_schema_reliability.py         # [P2] ≥50 calls/schema; first-try and after-retry
│   │   ├── test_context_budget.py             # [P2] prompt_eval+eval < num_ctx, repeated prompt
│   │   └── test_no_tools_live.py              # [P2] server-side request audit: no `tools` key
│   └── e2e/
│       ├── README.md
│       ├── test_ui_flow.py                    # [P5] Playwright (pytest): upload → ask → delete
│       └── test_accessibility.py              # [P5] axe + keyboard traversal
│
├── docs/
│   ├── SOLUTION_GUIDE_v3.md                   # design authority
│   ├── MASTER_IMPLEMENTATION_PROMPT_v3.txt
│   ├── REVIEW_FINDINGS_v3.md
│   ├── ARCHITECTURE.md                        # components, boundaries, lifecycle, limits
│   ├── DATA_FLOW.md                           # sequences, data objects, retention, failure map
│   ├── IMPLEMENTATION_MAP.md                  # module-by-module status + next tasks
│   ├── PRD.md                                 # product brief, journeys, non-goals
│   ├── REQUIREMENTS.md                        # L1–L10 / S1–S10 traceability
│   ├── TEST_PLAN.md                           # test IDs, what exists, commands actually run
│   ├── PRIVACY.md                             # inventory, canaries, evidence procedure, wording
│   ├── THREAT_MODEL.md                        # adversaries, boundaries, residual risk
│   ├── SECURITY.md                            # reporting, hardening, CSP, parser limits
│   ├── MODEL.md                               # model contract, budgets, failure mapping
│   ├── MODEL_SETUP.md                         # Day-0 gate + environment record template
│   ├── MODEL_LICENSE.md                       # Gemma licence text to be pasted when pinned
│   ├── MODEL_BENCHMARK.md                     # method + empty result tables
│   ├── EVALUATION.md                          # precommitted targets, protocol
│   ├── DATASET_NOTES.md                       # fixtures, questions, provenance, risks
│   ├── OPEN_SOURCE.md                         # dependency licences and reuse rules
│   ├── CONTRIBUTION.md                        # ownership table + rehearsal log
│   ├── LIMITATIONS.md                         # what does not work / is not measured
│   ├── DEVELOPMENT.md                         # setup, commands, debugging, phase entry points
│   ├── DEMO.md                                # five-minute runbook + fallbacks
│   ├── architecture-overview.html             # self-contained visual map (no external assets)
│   └── adr/
│       ├── README.md                          # index + conventions
│       ├── 0001-local-first-loopback.md
│       ├── 0002-ollama-native-json-schema.md
│       ├── 0003-model-proposes-backend-renders.md
│       ├── 0004-lexical-first-retrieval.md
│       ├── 0005-per-document-sqlite.md
│       ├── 0006-no-entailment-dense-default.md
│       ├── 0007-legal-boundary-policy.md
│       ├── 0008-fail-closed-status-precedence.md
│       ├── 0009-privacy-claim-gating.md
│       ├── 0010-hermes-not-built.md
│       └── 0011-…                             # new decisions only, numbered sequentially
│
└── reports/
    ├── .gitkeep
    ├── samples/README.md                      # only real, produced reports may be added
    ├── privacy/
    │   ├── README.md                          # evidence rules; no raw loopback payloads
    │   └── <release>/                         # [P6] env, attempts log, negative control, canaries
    ├── eval/                                  # [P6] per-question results + aggregate metrics
    │   └── <release>/results.json
    ├── bench/                                 # [P2] benchmark_model.py output
    │   └── <model>-<date>.json
    ├── env.json                               # [P2] verify_model_tags.py output (versions/digests)
    └── sbom/                                  # [P9] generate_sbom.sh output, git-ignored
```

---

## 2. Runtime data (never in git)

Created at run time under the app data directory; excluded by `.gitignore` as `data/`.

```text
data/
└── docs/
    └── <doc_id>/                        # 32 lowercase hex chars, generated server-side
        ├── source.<ext>                 # the uploaded file, unchanged
        ├── doc.sqlite3                  # pages, sentences, chunks, clauses, FTS, run ledger
        └── pages/
            └── <page_no>.png            # lazily rendered, only when a page image is requested
```

Deleting a document removes `data/docs/<doc_id>/` as a unit, then verifies absence and scans for
canaries. Paths are built only from validated ids — never from a filename or user input.

---

## 3. Generated / ignored, never committed

| Path | Why it is excluded |
|---|---|
| `node_modules/`, `frontend/dist/`, `.vite/` | npm install + build reproduce them |
| `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `.coverage` | tool caches |
| `.venv/`, `build/`, `dist/`, `*.egg-info/` | local environment / packaging |
| `data/` | runtime documents and per-document databases |
| `fixtures/generated/` | long/derived fixtures rebuilt by `scripts/generate_fixtures.py` |
| `reports/sbom/`, `reports/privacy/*/raw/` | large artifacts and raw capture |
| `models/`, `*.gguf`, `*.safetensors` | model weights are pulled by Ollama, never vendored |
| `*.pdf` outside `fixtures/` | any user document |
| `.env*`, `*.pem`, `*.key`, `secrets/` | credentials |

---

## 4. What appears in each phase (delta view)

| Phase | New paths |
|---|---|
| **Now (v3.2 build)** | Everything untagged above — 94 backend modules, 17 frontend files, full ingest/store/retrieval/validation/services/API, 11-card map, dual-model allowlist, 5 synthetic fixtures + CUAD + PRS brief data paths, 27 test modules, 23 docs, 11 ADRs |
| **P1** | `ingest/parser.py` PDF path, `ingest/worker.py`, `scripts/generate_fixtures.py`, `fixtures/pdf/*` (except scanned), `tests/integration/test_upload_flow.py` |
| **P1b** | `ingest/ocr.py` OCR path, `fixtures/pdf/scanned_page.pdf` |
| **P2** | `tests/model/test_{schema_reliability,context_budget,no_tools_live}.py`, `reports/env.json`, `reports/bench/` |
| **P3** | `store/clauses.py`, `store/relationships.py`, `retrieval/clause_map.py` persistence, `tests/unit/test_clause_map.py`, annotated `questions/development.jsonl` |
| **P4** | `services/answer.py`, `agent/{toolbox,runtime}.py`, `store/ledger.py`, `model/factory.py`, `api/*` routes, `tests/integration/test_end_to_end.py`; `ScaffoldNotice.tsx` removed |
| **P5** | `services/{review,overview,silence_context}.py`, `frontend/src/components/{DocumentMap,ReviewPanel,PageViewer}.tsx`, `scripts/evaluate_fixtures.py` |
| **P6** | `scripts/run_isolated_demo.sh` real flow, `tests/privacy/test_{network_inventory,logs_and_temp_clean}.py`, `reports/privacy/<release>/`, `reports/eval/<release>/`, `.dockerignore` |
| **P7** | `tests/privacy/test_deletion_under_failure.py`, hardening fixes |
| **P9** | `CHANGELOG.md`, `requirements.lock`, `.github/labeler.yml`, `reports/sbom/` |

---

## 5. Layering rules the structure encodes

Dependencies point **downward only**; a lower layer never imports an upper one.

```text
api/          HTTP: parse, authorise, delegate, shape errors        (no SQL, no prompts)
  ↓
services/     use cases: lifecycle, answer, review, overview        (no HTTP, no SQL)
  ↓
agent/        control flow + budgets ──► retrieval/  ingest/  validation/  model/
  ↓
store/        the only module that opens SQLite                     (no FastAPI, no model)
  ↓
core/ + schemas/ + config        closed vocabulary and contracts    (no I/O)
```

- `security/` is used by `api/` and `main.py` only.
- `validation/` may read schemas and stored sentences; it never calls the model or the network.
- `model/` never imports `store/`; it receives already-bounded prompt material.
- `frontend/` holds presentation only: no business rules, no legal wording, no status logic.
- Data files (`lexicons/`, `glossary/`) are read-only inputs, loaded through typed loaders.

---

## 5b. Tree vs. current build

The tree above is the target layout with phase tags. As of 2026-10-18 the
application is built, with these known gaps between the tree and the files on disk:

| In the tree | Status |
|---|---|
| `store/relationships.py`, `store/clauses.py` | `clauses.py` exists and is used; `relationships.py` is not built (cross-reference expansion is lexical) |
| `tests/model/test_{schema_reliability,context_budget,no_tools_live}.py` | Replaced by `tests/integration/test_provider_http_roundtrip.py` (real HTTP against a stub daemon). Live-model tests remain opt-in and were not run |
| `scripts/generate_fixtures.py` | Fixtures are committed as-is; the PDFs are small and synthetic |
| `components/ScaffoldNotice.tsx` | Deleted in P4, as planned |
| `services/benchmark.py` | Present; `scripts/benchmark_retrieval.py` still exits non-zero (not implemented) |

Everything else in the tree exists. `datasets/` and `backend/app/cli.py` were added
after this tree was written (see §6b).

---

## 6. Deviations from Guide §4 (with reasons)

| Guide §4 | Here | Why |
|---|---|---|
| `pnpm-lock.yaml` | `package-lock.json` (npm) | npm is already in use and verified; one lockfile, committed. Switching adds no value. |
| `uv.lock` | `pyproject.toml` now, `requirements.lock` at release | Keeps the scaffold installable with plain pip; a pinned lockfile is a Phase 9 release requirement (S3). |
| `backend/app/api/{documents,ask,review,overview,evidence,health}.py` | adds `session.py` | Launch-code exchange needs its own unauthenticated-but-Origin-checked route. |
| — | `core/`, `schemas/`, `validation/{modality,roles,pipeline}.py` | The closed vocabulary, wire contracts and per-check modules are real trust boundaries; splitting them keeps tests honest. |
| `retrieval/` has no packet module | `retrieval/packets.py` | Packet construction is where the token cap and nonce delimiters live; it is testable in isolation. |
| `services/{lifecycle,privacy,benchmark}.py` | adds `answer.py`, `review.py`, `overview.py` | Keeps routes thin and makes the ask/review/overview use cases testable without HTTP. |
| — | `store/{clauses,relationships,ledger}.py` | Tables already exist in `schema.sql`; each needs a single owning accessor. |
| “generated PDFs … fixtures” | `fixtures/pdf/` committed small files + `fixtures/generated/` ignored | Small synthetic PDFs must be reproducible for judges; 50-page/derived files are rebuilt on demand. |
| Frontend `src/{app,api,components,pages,styles,types}/` | `App.tsx` + those folders | Same intent; named entry file keeps Vite’s default simple. |
| One pinned model family | `model/registry.py` + three allowlisted tags (`gemma`, `gemma-e2b`, `hermes`) | Turn-5 requirement to run both families; see ADR-0011. Same adapter, prompt, validator; no fallback. |
| — | `backend/app/cli.py` | `ask` / `documents` / `delete` / `models` with stable exit codes (0 answer, 1 ingest, 2 model unavailable, 3 usage) so the pipeline is scriptable without a browser. |
| — | `datasets/` + `scripts/fetch_{cuad,india_law}.py` | Public-data verification needs pinned hashes and a recorded list of unreachable sources; raw downloads stay out of git. |

---

## 6b. Contract drift fixed in turn 5

The v3.2 API contract replaced the earlier payload shapes. This is the migration table:

| Surface | Before | Now |
|---|---|---|
| Session | `{code}` → `{token, expires_in}` | `{launch_code}` → `{access_token, token_type, expires_in_seconds}` |
| Health | booleans only | `status`, `local_model_available`, `model_tag`, `model_digest`, `parser_engine`, `storage_backend` (+ per-model map) |
| Upload | document summary | `document_hash`, `quality_metrics{pages_read, ocr_used, language_detected, garble_ratio, hidden_text_detected}`, `extraction_warnings`, `status` |
| Delete | `directory_removed`, `canary_hits`, `forensic_erasure` | `files_purged`, `database_unlinked`, `model_cache_evicted`, `canary_scan_passed`, `forensic_erasure_disclaimer` |
| Overview | `cards` array | `cards` **object** keyed by label, 11 keys including Pets |
| Review | `items` + `escalation` | `review_status`, `attention_first[{category, priority, title, reason, citations}]`, `questions_for_professional[{topic, prompt}]` |
| Pages | `page_no`, `char_start/char_end` | `page_number`, `is_virtual_page`, `ocr_used`, `start_offset`/`end_offset` |
| Evidence | `text`, `page_text` | `evidence_id`, `document_hash`, `sids[]`, `verbatim_text`, `text_sha256` |

`legal_verdict` remains `null` in every version.

---

## 7. Where each concern lives

| You want to change… | Start in | Then update |
|---|---|---|
| What the model may return | `backend/app/schemas/model_io.py` | `docs/MODEL.md`, prompt, tests |
| Legal-boundary wording / scanner rules | `backend/app/validation/legal_policy.py` | scanner corpus, `docs/LIMITATIONS.md` |
| Status or route behaviour | `backend/app/core/enums.py`, `backend/app/agent/router.py` | `docs/ARCHITECTURE.md` §7, tests |
| Retrieval ranking and caps | `backend/app/retrieval/{lexical,packets}.py` | `docs/ARCHITECTURE.md` §9 |
| Database schema | `backend/app/store/schema.sql`, `db.py` | `docs/DATA_FLOW.md` §8 + migration note |
| Upload/parse limits | `backend/app/ingest/{upload,parser,worker}.py` | `docs/SECURITY.md`, limits table |
| Privacy wording | `docs/PRIVACY.md`, `frontend/src/components/PrivacyBanner.tsx` | any stronger wording requires committed capture evidence |
| Adding a glossary term | `glossary/rental_terms.yaml` | rerun scanner corpus (term must pass) |
| Wiring a phase | `docs/IMPLEMENTATION_MAP.md` | `TASKS.md` with real command output |

---

## 8. Non-negotiables when editing

- The model never supplies quotes, pages, sections, evidence ids, statuses or legal verdicts.
- Never send `tools` to Ollama, never use `/v1`, never add a cloud fallback.
- Never add a CDN, inline script/style, telemetry, or browser storage for document data.
- Never claim a privacy or accuracy result before the matching report exists for that release.
- Every displayed factual point cites a stored sentence; quotations are never edited.
- Hard caps change only with an ADR and updated tests.
