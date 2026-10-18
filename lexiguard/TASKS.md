# Task tracker

Phase order is fixed: 0 → 1 → 1b → 2 → 3 → 4 (+T8) → 6 → 5 → 7 → 8 → 9. Evaluation (6) runs
before UI polish (5) on purpose.

**Legend:** ✅ done and verified by a command · 🟡 partially done · ⬜ not started · 🚫 deliberately
not built.

---

## Phase status

| Phase | Scope | Status | Evidence |
|---|---|---|---|
| 0 | Repo scaffold, docs, ADRs, CI, setup scripts, licence gate | 🟡 | Tree + docs exist; workflow written but never run on GitHub; setup script not executed against Ollama |
| 1 | PDF child process, upload/list/delete routes, per-document DB, verified deletion | ✅ | `test_end_to_end.py` uploads TXT and PDF, renders a page image, deletes and verifies 404 |
| 1b | Local OCR fallback + OCR banner | 🟡 | Tesseract integration is real; Tesseract absent in the build environment, so it is unexercised |
| 2 | Ollama acceptance (`T-MODEL-JSON-01`, `CTX-01`, `NOTOOLS-01`), Day-0 timing, digests | 🟡 | Adapter exercised over real HTTP against a stub daemon for both families (`tests/integration/test_provider_http_roundtrip.py`); no live inference |
| 3 | FTS population, cross-reference expansion, silence wiring, question annotations | ✅ | Ingest rebuilds FTS; overview and silence gate exercised on 5 fixtures |
| 4 | Runtime transitions, ask route, end-to-end validator, injection fixtures through HTTP | ✅ (scripted model) | `scripts/evaluate_fixtures.py`; ask route returns fail-closed error with no provider |
| 6 | Evaluation, isolated-network privacy evidence, negative control, benchmarks | 🟡 | Fixtures + CUAD (510 contracts) + India brief evaluated; no live-model evaluation, no privacy capture |
| 5 | Overview/Review routes, UI panels, accessibility (axe), mobile | 🟡 | All routes and UI panels built and used in the E2E test; no axe or mobile pass |
| 7 | Hardening: stale index, parser crash/timeout, partial documents, adversarial files | 🟡 | Parser limits, malformed/encrypted errors and injection fixture exist; fuzzing not done |
| 8 | ADR-0010 (Hermes Agent framework not built) + ADR-0011 (both model families selectable) | ✅ | ADR-0010, ADR-0011; `model/gateway.py` still fails closed; Hermes models served by the same adapter |
| 9 | Submission: S1–S10 pack, demo rehearsal, SBOM, release notes | ⬜ | — |

---

## What is actually verified today (2026-10-18)

| Command | Result |
|---|---|
| `make test` | **124 passed, 1 skipped** (skip = opt-in live Ollama test) |
| `make lint` | **All checks passed** |
| `npm run build` | **success** — `tsc --noEmit` + Vite (45 modules, 171 kB JS) |
| `make eval` | 5/5 fixtures ingest, map, review and answer; report in `reports/fixture_evaluation.md` |
| `python3 scripts/evaluate_cuad.py --all` | 510/510 contracts, 0 failures, 9,731 quotations, 0 substring failures, 3,715 review items |
| `python3 scripts/evaluate_india_law.py` | 6/6 pages readable, 0 OCR, 24/24 quotations, 7 review items |
| `python3 scripts/verify_models_live.py` | `gemma` and `hermes` both `ANSWERED` through the HTTP API against a stub runtime, 1 model call each |
| live server smoke (`curl`) | token-protected routes 401 without bearer; upload TXT → 201 with `quality_metrics`; overview `cards` object with 11 keys; review `attention_first` sorted by priority; ask with no model → `ERROR_LOCAL_MODEL_UNAVAILABLE`; delete → `files_purged`/`database_unlinked`/`forensic_erasure_disclaimer` |

What is **not** verified: any live model call, OCR accuracy, answer accuracy on real tenancy
agreements, privacy isolation, browser accessibility, CI on GitHub.

---

## Next tasks (in order)

1. **Phase 2.0 — Day-0 gate** on a machine with Ollama: record version and model digest in
   `docs/MODEL_SETUP.md`; run `scripts/benchmark_model.py`; choose E4B or E2B by measured latency.
2. **Phase 2.1 — live acceptance:** ≥50 schema-valid calls, the repeated-identical-prompt context
   test, and a request audit proving no `tools` key.
3. **Phase 6.1 — live evaluation:** run the documented question set against the pinned model and
   fill the empty rows in `docs/EVALUATION.md` §5. Do not fill them from the scripted run.
4. **Phase 6.2 — privacy evidence:** isolated-network demo, attempt-visible capture and negative
   control per `reports/privacy/README.md`.
5. **Phase 5.1 — accessibility:** axe CI plus a keyboard-only pass over upload, ask, review, delete.
6. **Phase 7.1 — hardening:** fuzz the parser with truncated/odd PDFs; test stale-index behaviour
   after a re-upload of an edited file.
7. **Phase 9 — submission pack:** S1–S10, SBOM, demo rehearsal, release notes.

---

## Open decisions / blockers

| Item | Owner | Needed by | Note |
|---|---|---|---|
| Confirm the submission deadline (ask organisers once) | team | before scheduling Phase 6 | Freeze = deadline − 3 days; do not invent one |
| Day-0 hardware gate | team | before Phase 1 | E4B p50 > ~60 s → E2B; neither < ~120 s → stop |
| Held-out fixture author | team | before Phase 6 | Must not write lexicons/prompts |
| CI actually executed on a branch | team | Phase 0 exit | Workflow file exists; no run recorded |
| OCR availability on demo machine | team | Phase 1b | Tesseract + language data |

---

## Changelog

| Date | Change |
|---|---|
| 2026-10-18 | Scaffold created: backend contracts + primitives, UI shell, tests green, docs 0001–0010, docs map |
| 2026-10-18 | `STRUCTURE.md` rewritten as the final-application tree with per-line phase markers `[P1]`…`[P9]` and layering rules |
| 2026-10-18 | Application built: ingest (PDF child process, OCR hook), store, retrieval, agent runtime, all routes, full React UI; 117 tests green; fixture evaluation committed |
| 2026-10-18 | Turn 5: CUAD ingestion fixed (`clause_id` collision) → 510/510; concept patterns widened; conflict spam capped; India brief pipeline; CLI (`app.cli ask/models`); **API migrated to the v3.2 contract** (session/health/upload/delete/ask/overview/review/pages/evidence); 11 concept cards incl. Pets; dual-model allowlist + ADR-0011; 124 tests green |
