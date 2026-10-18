# LexiGuard

**Private, evidence-backed triage of rental and leave-and-licence agreements — local-first, working build.**

LexiGuard reads an English rental or leave-and-licence agreement on your own machine, explains what
the readable text says, quotes the exact sentence and page, and says plainly when something cannot be
found, is ambiguous, or needs a qualified lawyer. It never gives a legal verdict.

> **Where this build stands (2026-10-18).** Every route is implemented and the whole
> upload → document map → ask → review → delete flow runs, against the v3.2 JSON contract below.
> The pipeline was exercised on **510/510 CUAD contracts** (0 ingest failures, 9,731 quotations with
> 0 substring failures) and on an **Indian tenancy-law PDF** (6/6 pages, 0 OCR). Both model families
> — Gemma and Hermes — are wired through one adapter and one validator. **No live model ran in the
> build environment** (no GPU, no Ollama daemon), so model quality, latency and answer accuracy are
> *not measured*; the ask route was exercised with a scripted provider and with a stub Ollama
> runtime, and with no provider at all it fails closed with `ERROR_LOCAL_MODEL_UNAVAILABLE`.
> There is no isolated-network capture yet, so "nothing leaves the machine" remains a design goal
> with implemented safeguards, not a verified privacy result. Read the claims table before
> repeating anything you see elsewhere.

## What works

- **Ingest** — PDF (parsed in a child process with resource limits) and TXT, up to 20 MB / 300 pages.
  Pages → sentences with stable ids and exact character offsets → chunks, stored in a per-document
  SQLite database with FTS5 and `secure_delete=ON`.
- **Quality and language gates** — unreadable pages and non-Latin-script pages are recorded as flags
  and surfaced in the UI instead of being silently ignored.
- **OCR hook** — scanned pages are sent to a local Tesseract binary *only if installed*; OCR text is
  labelled as OCR everywhere it appears. Not available in the build environment, so unverified.
- **Document map** — 11 concept cards (Parties, Term, Rent, Deposit, Notice, Lock-in, Penalties,
  Restrictions, Maintenance, Disputes, Pets) keyed by name, each with
  `FOUND` / `NOT_LOCATED` / `NOT_ASSESSED` / `INSUFFICIENT_EVIDENCE` and up to three quotations.
- **Ask** — deterministic routing first (fact lookup, term, out-of-scope, legal boundary), then lexical
  retrieval, one bounded refinement, a bounded evidence packet, one local model call, and full backend
  validation. Quotations, page numbers, sections and status are rendered by the backend from stored
  sentences; the model never emits them.
- **Review** — attention-first ordering: conflicts → ambiguity attached to money/time/termination →
  money clauses → jurisdiction cautions → coverage. Every item carries its quotation. Nothing is
  scored.
- **Delete** — removes the document directory, index, text and rendered pages, verifies the absence
  with canary strings, and reports exactly what was and was not removed. No claim of forensic erasure.
- **Session security** — one-time launch code in the URL fragment, exchanged for an in-memory bearer
  token; exact `Host` allowlist, `Origin` checks on state-changing requests, CSP and `no-store`.
- **Two model families, one contract** — `gemma` (`gemma4:e4b-it-q4_K_M`, default),
  `gemma-e2b` (`gemma4:e2b-it-q4_K_M`) and `hermes` (`hermes3:8b`). The caller selects explicitly;
  there is no automatic fallback and no silent substitution (ADR-0011). Every answer records
  `run_meta.model_tag`.
- **Quality metrics on upload** — pages read, OCR used, detected language, worst-page garble ratio,
  and a hidden-text heuristic are returned with every document rather than buried in logs.

## What is and is not verified

| Claim | Status (2026-10-18) | Evidence |
|---|---|---|
| Upload → map → ask → review → delete works | **Yes**, without a live model | `tests/integration/test_end_to_end.py` (6 tests) |
| Citations are verbatim stored sentences | **Yes for the renderer and validator**; backend builds every quote from the database and rejects invented figures (`LITERAL_NOT_IN_SOURCE`) and unexposed ids (`SID_NOT_EXPOSED_IN_RUN`) | `reports/fixture_evaluation.md`, validator unit tests |
| Legal questions are refused, not answered | **Yes** — deterministic legal-boundary route returns `LEGAL_LIMIT` with neutral escalation questions | fixture run, `agent/router` tests |
| Absence is not invented | **Yes** — `NOT_LOCATED` requires empty retrieval *and* a passing silence gate; if the topic appears but the model stays silent the status is `INSUFFICIENT_EVIDENCE` | `services/silence_context.py`, `_relevant()` + fixture run (2/5 fixtures show the distinction) |
| On-device / nothing leaves the machine | **Design goal. Not verified.** Host/Origin/CSP and loopback-only binding are implemented and tested; no packet capture exists | `docs/PRIVACY.md` |
| Model quality, latency, context fit | **Not measured.** No live Ollama in the build environment | — |
| OCR quality | **Not measured.** Tesseract was not installed, so `ocr_available` reported `false` | — |
| Glossary reviewed by a lawyer | **No.** 20 curated entries, `reviewed: false` | `glossary/rental_terms.yaml` |
| CUAD ingestion at scale | **Yes** — 510/510 contracts, 0 failures, 9,731 quotations, 0 substring failures | `reports/cuad_evaluation.md` |
| Concept map on real contracts | **Yes, with a caveat** — 95.7–99.8 % map recall and 0.2–2.9 % false silence across six concepts; individual-span recall is much lower (Parties 2.4 %) | same |
| Indian tenancy-law PDF path | **Yes for parsing/language gate** — 6/6 pages readable, 0 OCR, 24/24 quotations; the source is a policy brief, not an agreement | `reports/india_law_evaluation.md` |
| Gemma **and** Hermes reachable through the app | **Transport proven, quality not measured** — both tags answered through the HTTP API against a stub runtime | `reports/model_roundtrip.md`, `tests/integration/test_provider_http_roundtrip.py` |
| Tests / lint / build | `pytest` → **124 passed, 1 skipped** (skip = opt-in live-Ollama test); `ruff check` → clean; `npm run build` → 45 modules | commands below |

These rows change only when a committed report or a command's output supports the change.

## Quickstart

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
npm install

PYTHONPATH=backend python3 -m pytest          # 124 passed, 1 skipped
ruff check backend tests scripts              # clean
npm run build                                 # typecheck + production build
PYTHONPATH=backend python3 -m app             # http://127.0.0.1:8765
```

The launcher prints a one-time URL such as `http://127.0.0.1:8765/#k=…`. The code lives in the URL
fragment (never sent to the server), is exchanged for an in-memory token, and expires in 60 seconds.
Open it in a browser on the same machine.

To use the model path you need a local Ollama with the pinned tags:

```bash
OLLAMA_NO_CLOUD=1 ollama serve
ollama pull gemma4:e4b-it-q4_K_M   # default
ollama pull gemma4:e2b-it-q4_K_M   # low-memory option
ollama pull hermes3:8b             # optional second family
```

`GET /api/health` reports `local_model_available: false` and `GET /api/models` marks each tag
unavailable when the daemon or the model is missing. The ask route then returns
`ERROR_LOCAL_MODEL_UNAVAILABLE` rather than guessing or switching model.

Optional OCR (scanned PDFs):

```bash
# Debian/Ubuntu
sudo apt install tesseract-ocr
```

Without it, image-only pages are stored as `UNREADABLE_PAGE` flags and reported as not assessed.

## API contract (v3.2)

All routes are same-origin, token-protected except `POST /api/session`, and reject unknown fields.

| Route | Request | Response |
|---|---|---|
| `POST /api/session` | `{launch_code}` | `{access_token, token_type, expires_in_seconds}` |
| `GET /api/health` | — | `{status, local_model_available, model_tag, model_digest, parser_engine, storage_backend, …}` |
| `GET /api/models` | — | allowlisted tags with per-tag availability |
| `POST /api/documents` | multipart `file` | `{document_id, document_hash, page_count, quality_metrics{pages_read, ocr_used, language_detected, garble_ratio, hidden_text_detected}, extraction_warnings, status}` |
| `GET /api/documents` | — | `{documents[]}` for the session |
| `GET …/{id}/overview` | — | `{document, cards{Parties…Pets: {status, summary, evidence[]}}, warnings}` |
| `POST …/{id}/ask` | `{question, model?}` | `RenderedAnswer` with `claims[{claim_id, text, classification, evidence[{sid, page, section, quote, ocr_derived}]}]` |
| `POST …/{id}/review` | — | `{review_status, attention_first[{category, priority, title, reason, citations}], questions_for_professional[{topic, prompt}]}` |
| `GET …/{id}/pages/{n}` | — | `{page_number, is_virtual_page, ocr_used, sentences[{sid, start_offset, end_offset, text}]}` |
| `GET …/{id}/evidence/{eid}` | — | `{evidence_id, document_hash, page, section, sids[], verbatim_text, text_sha256}` |
| `DELETE …/{id}` | — | `{files_purged, database_unlinked, model_cache_evicted, canary_scan_passed, forensic_erasure_disclaimer, …}` |

`legal_verdict` is `null` in the schema, not merely unset: the model output type has no field for it,
and the renderer is the only code that builds an answer.

## Reproduce the evaluations

```bash
# 1. Synthetic fixtures + validator behaviour (scripted provider, not a model)
python3 scripts/evaluate_fixtures.py --json reports/fixture_evaluation.json \
                                     --md   reports/fixture_evaluation.md

# 2. CUAD v1 (downloads 40 MB, CC BY 4.0) — 510 contracts
python3 scripts/fetch_cuad.py
python3 scripts/evaluate_cuad.py --all

# 3. Indian tenancy-law PDF (PRS brief, 446 KB)
python3 scripts/fetch_india_law.py
python3 scripts/evaluate_india_law.py

# 4. Both model families through the HTTP API (stub runtime unless --real)
python3 scripts/verify_models_live.py          # or --real with Ollama running
```

Fixture results (regenerate to update):

| Fixture | Concepts found / 11 | Not located | Review items |
|---|---|---|---|
| `synthetic_rental_simple.txt` | 10 | Lock-in | 5 |
| `synthetic_rental_conflict.txt` | 9 | Lock-in, Maintenance | 8 (2 conflicts) |
| `synthetic_rental_ambiguous.txt` | 7 | Term, Lock-in, Disputes, Pets | 5 (1 ambiguity) |
| `synthetic_rental_injection.txt` | 7 | Lock-in, Penalties, Restrictions, Pets | 3 |
| `synthetic_rental_indian_style.txt` | 10 | Pets | 6 |

Those numbers describe five synthetic documents, not real contracts, and say nothing about model
accuracy. CUAD is real contracts but commercial ones; the PRS brief is a policy summary. See
[`docs/EVALUATION.md`](docs/EVALUATION.md) for what each result does and does not prove.

## Repository map

| Path | What it is |
|---|---|
| [`STRUCTURE.md`](STRUCTURE.md) | Final-app directory tree: every path, its responsibility and phase |
| [`backend/app/`](backend/app/) | FastAPI application: ingest, store, retrieval, agent, validation, services, API |
| [`frontend/src/`](frontend/src/) | React + TypeScript UI: session bootstrap, upload, map, ask, page viewer, review, delete |
| [`lexicons/`](lexicons/) | Rental topics, jurisdiction topics, escalation templates |
| [`glossary/rental_terms.yaml`](glossary/rental_terms.yaml) | 20 curated rental-term definitions, `reviewed: false` |
| [`fixtures/`](fixtures/) | Five synthetic agreements (TXT + three PDFs). Never real contracts |
| [`datasets/`](datasets/) | Manifests for CUAD v1 and the PRS brief: source, licence, SHA-256, and the sources that were unreachable |
| [`questions/development.jsonl`](questions/development.jsonl) | Development question set |
| [`tests/`](tests/) | Unit, integration and opt-in live-Ollama tests |
| [`docs/`](docs/) | Architecture, data flow, privacy, evaluation, limitations, ADRs |
| [`scripts/`](scripts/) | Launcher helpers, fixture evaluation, benchmarks, licence and model-tag checks |
| [`reports/`](reports/) | Generated evaluation output and privacy evidence procedures |

## Design in one paragraph

React + Vite + TypeScript served same-origin by FastAPI on `127.0.0.1`. The browser receives a
one-time launch code in the URL fragment and exchanges it for a memory-only bearer token. PDFs and TXT
are parsed into pages → sentences (stable ids, exact offsets) → chunks in per-document SQLite with
FTS5 and `secure_delete=ON`. A question is routed deterministically first (fact, term, scope, legal
boundary); retrieval is lexical with a rental-topic lexicon, a silence gate and a bounded evidence
packet. Gemma or Hermes (via native Ollama `/api/chat`, same adapter and prompt) only proposes points
that cite stored sentence ids; the backend validates provenance, literals, modality, roles, conflict
sections and legal-verdict language, then renders quotes, pages, sections and status itself. Anything
that fails is dropped or degraded — never guessed. `legal_verdict` is always `null`. The Hermes
*Agent framework* is deliberately not built (ADR-0010); the Hermes *model family* is selectable
(ADR-0011).

## Documents

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — components, trust boundaries, request lifecycle
- [`docs/DATA_FLOW.md`](docs/DATA_FLOW.md) — upload / ask / review / delete flows with data objects
- [`docs/MODEL_SETUP.md`](docs/MODEL_SETUP.md) — installing and pinning the local model
- [`docs/PRIVACY.md`](docs/PRIVACY.md) — network inventory, canaries, evidence procedure, wording rules
- [`docs/EVALUATION.md`](docs/EVALUATION.md) — what was measured, how, and what was not
- [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) — the honest list
- [`docs/TEST_PLAN.md`](docs/TEST_PLAN.md) — test IDs, commands, release gates
- [`docs/adr/`](docs/adr/) — decisions 0001–0011
- [`reports/fixture_evaluation.md`](reports/fixture_evaluation.md) — synthetic fixtures
- [`reports/cuad_evaluation.md`](reports/cuad_evaluation.md) — 510 real commercial contracts
- [`reports/india_law_evaluation.md`](reports/india_law_evaluation.md) — Indian policy brief (PDF path)
- [`reports/model_roundtrip.md`](reports/model_roundtrip.md) — Gemma and Hermes through the API (stub runtime)

## Context

Built for ZeroDay OSS Hacktoberfest 2026, Problem Statement 2 (Private Legal Document Triage Agent).
Target repository: `panditshubham766-dotcom/golden_brown1` (optional rename to `lexiguard`).

## Licence

Apache-2.0. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

## Not legal advice

LexiGuard output is general information about a document's wording. It is not legal advice. For
decisions about signing, disputes or rights, consult a qualified lawyer experienced in tenancy
matters in the state where the property is located.
