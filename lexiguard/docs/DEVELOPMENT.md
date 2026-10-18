# Development guide

## Prerequisites

| Tool | Version | Why |
|---|---|---|
| Python | ≥ 3.11 (tested 3.13.16) | Backend, scripts |
| Node.js / npm | ≥ 20 (tested 20.20.2 / 10.8.2) | Frontend build |
| Ollama | ≥ 0.21.1 | Local model (`think:false` + `format`) |
| SQLite | ≥ 3.35, FTS5 | Storage/search (3.46.1 tested) |
| Tesseract | optional | OCR fallback only (Phase 1b) |

## Setup

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
npm install
npm run build                 # tsc --noEmit && vite build

ollama serve                  # terminal 1 (OLLAMA_NO_CLOUD=1)
ollama pull gemma4:e4b-it-q4_K_M
python3 scripts/verify_model_tags.py

make run                      # terminal 2
```

`make setup` performs the setup steps that can be automated; `make demo` builds the UI and starts
the API.

## Commands that exist today

| Command | What it does | Verified |
|---|---|---|
| `PYTHONPATH=backend python3 -m pytest` | 111 passed, 1 skipped (opt-in live Ollama) | 2026-10-18 |
| `python3 -m ruff check backend tests scripts` | lint | passes |
| `npm run build` | typecheck + production build | passes |
| `make run` | starts API on 127.0.0.1:8765 | smoke-tested with curl |
| `make test`, `make lint`, `make backend`, `make frontend` | wrappers | same as above |
| `make isolated-demo` | **intentionally exits 2** until Phase 6 | by design |
| `python3 scripts/benchmark_retrieval.py` | exits 2 until Phase 3/6 | by design |

`make isolated-demo` failing is deliberate: no isolation report exists, so the target must not
pretend to produce one.

## Daily loop

1. Read the phase you are in (`TASKS.md`) and the module status (`IMPLEMENTATION_MAP.md`).
2. Change one layer at a time. Contracts first: enums → schemas → validator → renderer → runtime.
3. Add a test that fails before the change and passes after it. Prefer fail-closed assertions.
4. Run `make test && make lint` and, for UI changes, `npm run build`.
5. Update the docs and the limits table in the same commit.

## Coding standards

- Python 3.11+, type hints, `from __future__ import annotations`, ruff defaults (line length 100),
  mypy on the strict-ish default profile.
- Pydantic models: `extra="forbid"`, explicit length caps, enums for closed sets.
- No floating URLs or model names; configuration comes from `Settings` only.
- No user input in paths; `doc_id` is validated with `^[0-9a-f]{32}$`.
- Frontend: no inline styles/scripts, no storage APIs, no `dangerouslySetInnerHTML` on model or
  document text; render quotes as text nodes.

## Where to start per phase

| Phase | First files |
|---|---|
| 1 | `ingest/parser.py` (PDF child process), `api/documents.py`, `store/*` wiring |
| 1b | `ingest/ocr.py`, quality banner in UI |
| 2 | `model/ollama_native.py` live acceptance, `MODEL_SETUP.md` |
| 3 | `retrieval/{lexical,crossrefs,silence}.py`, questions/annotations |
| 4 | `agent/runtime.py`, `api/ask.py`, end-to-end validator tests |
| 5 | `api/review.py`, `api/overview.py`, UI panels, axe CI |
| 6 | `scripts/benchmark_model.py`, `run_isolated_demo.sh`, `reports/privacy/` |
| 7 | hardening tests (stale index, crash, timeout, partial doc) |

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `OllamaUnavailable` | server not running / wrong port | `OLLAMA_NO_CLOUD=1 ollama serve` |
| `ContextOverflowError` | packet + prompt ≥ `num_ctx` | reduce packet cap; don't silently truncate quotes |
| `ERROR_LOCAL_MODEL_UNAVAILABLE` on ask | no local model running | start Ollama and pull the pinned tag |
| `403` on any Host | exact allowlist | use `127.0.0.1:<port>` or `localhost:<port>` |
| Frontend cannot reach API | Vite proxy / origin | ensure `vite.config.ts` proxies `/api`; no CORS |
| `secure_delete` missing | non-standard SQLite build | tests fail loudly; do not bypass |
