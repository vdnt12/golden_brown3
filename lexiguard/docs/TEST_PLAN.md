# Test plan and current results

Status of the built application. A test family absent here is **not implemented**, not
“implicitly covered”. Nothing in this file is a privacy or accuracy claim.

---

## 1. Commands actually run (2026-10-18, built application)

Environment: Linux sandbox, Python 3.13.16, `pytest 9.0.3`, `fastapi 0.143.3`, Node 20.20.2.
This is **not** the demo machine; no Ollama and no Tesseract were installed, and no model was called.

```text
$ make test                 # pytest with pythonpath=backend
124 passed, 1 skipped, 3 warnings in 2.71s

$ make lint
All checks passed!

$ npm run build             # tsc --noEmit && vite build
45 modules transformed
dist/index.html                    0.80 kB
dist/assets/index-*.css            7.27 kB
dist/assets/index-*.js           170.69 kB
built in 993ms

$ make eval                 # five fixtures, scripted provider
5/5 fixtures ingested, mapped, reviewed and answered
-> reports/fixture_evaluation.json / .md

$ python3 scripts/evaluate_cuad.py --all
510/510 contracts ingested, 0 failures, 9,731 quotations, 0 substring failures
-> reports/cuad_evaluation.json / .md

$ python3 scripts/evaluate_india_law.py
6/6 pages readable, 0 OCR, 24 quotations, 7 review items
-> reports/india_law_evaluation.json / .md

$ make smoke                # scripts/live_api_smoke.py against a real uvicorn process
ALL LIVE CHECKS PASSED      # 30 assertions over the v3.2 contract

$ python3 scripts/verify_models_live.py
gemma  ANSWERED gemma4:e4b-it-q4_K_M 1 claim
hermes ANSWERED hermes3:8b           1 claim

$ live server smoke (curl, one session, v3.2 contract)
GET /                          -> 200, CSP + nosniff + no-referrer + frame-deny
GET /api/health (no token)     -> 401
POST /api/session              -> 200, {access_token, token_type, expires_in_seconds}
GET /api/health (token)        -> {"status":"degraded","local_model_available":false,...}
POST /api/documents (TXT)      -> 201, document_hash + quality_metrics + status
GET  .../overview              -> 200, cards object with 11 keys
POST .../review                -> 200, attention_first sorted by priority
POST .../ask (no model)        -> 200, ERROR_LOCAL_MODEL_UNAVAILABLE, 0 claims
GET  .../pages/1               -> 200, page_number/is_virtual_page/start_offset
GET  .../evidence/{sid}        -> 200, verbatim_text + text_sha256
DELETE ...                     -> 200, files_purged/database_unlinked/canary_scan_passed
GET  .../overview after delete -> 404
```

The skipped test is the opt-in live Ollama test
(`LEXIGUARD_OLLAMA_LIVE=1`), which cannot run without a local model and a T-MODEL acceptance run.

---

## 2. What these tests do and do not prove

**Proved by the run above**
- The closed enums and status precedence behave as specified.
- Model I/O schemas reject unknown fields, policy fields, duplicate ids and illegal actions.
- The legal scanner blocks all 48 starter must-block strings and blocks none of the 51 must-pass
  strings (including the `valid for 11 months` source-echo case).
- Literal normalisation (words, ₹/Rs./INR, DD/MM/YYYY vs month-name dates) and modality/role
  mismatch detection work on their unit cases.
- SQLite sets `secure_delete=ON`, `journal_mode=DELETE`, `foreign_keys=ON`; FTS5 works; number
  search finds `25,000` by `25000`; purge removes FTS rows.
- Launch codes are single-use and expire; Host/Origin allowlists are exact; served `/` contains
  no launch code; `/api/*` requires a bearer token.
- Sentence offsets round-trip to stored text; the language gate rejects Devanagari and romanised
  Hindi pages; TXT virtual pages work; bad UTF-8 and non-PDF magic fail closed.
- Deletion removes the directory and reports canary hits outside it honestly.
- TypeScript compiles and the production frontend builds with no external assets.

**Not proved / not run**
- Any model output quality, latency, context fit on a live Ollama version, or `tools`-free
  request to a real server (payload is unit-tested; T-MODEL-* is Phase 2).
- PDF parsing, OCR, upload route, ask route, runtime transitions.
- Privacy isolation, canary-free logs in a real run, network capture, deletion under failure.
- Accuracy, citation precision/recall, UCR, answer rate, false refusals — no evaluation has run.
- Browser accessibility (axe), mobile layout, keyboard traversal.
- Cross-platform parser limits (only the Linux sandbox was used).

---

## 3. Implemented tests (mapping)

| Test file | Covers | Requirement / ID |
|---|---|---|
| `unit/test_enums.py` | status precedence rules | L7, Guide 10.1 |
| `unit/test_schemas.py` | strict ModelAnswer/NextAction/RenderedAnswer; `legal_verdict` null | T-CITE, L8 |
| `unit/test_literal.py` | amounts, percentages, dates, number words, invented amount | T-CITE-LIT |
| `unit/test_modality.py` | must/shall, permission weakening, negation add/drop | T-CITE-MOD |
| `unit/test_roles.py` | tenant/landlord canonicalisation, party swap | T-CITE-ROLE-01 |
| `unit/test_legal_scanner.py` | 99-row corpus, echo exception, template passes | T-LEGAL-FP-01 |
| `unit/test_router.py` | 7 legal paraphrases, term route, out-of-scope, stricter-wins | T-LEGAL-*, L8 |
| `unit/test_tools.py` | page/ref bounds, model-selectable tools | T-CITE, injection surface |
| `unit/test_normalize_segment.py` | NFC/LF, offset round-trip, abbreviations, sections, sid determinism | T-ING-OFFSET |
| `unit/test_language_quality_parser.py` | page language gate, OCR candidates, virtual pages, UTF-8 rejection, PDF fail-closed | T-ING-LANG-PAGE-01 |
| `unit/test_upload.py` | magic bytes, size cap, extension, encoding, display-name safety | T-ING-* core |
| `unit/test_parser_docs.py` | parser limits matrix is reported honestly; startup notices are a list | Guide 6.2 |
| `unit/test_topics_crossrefs.py` | topic classifier on the committed lexicon; xrefs; dates excluded | T-RETR-* |
| `unit/test_silence_packets.py` | silence gate, packet caps, nonce delimiters | T-CITE-SILENCE |
| `unit/test_prompts.py` | nonce evidence block, prompt budget | T-MODEL-CTX-01 (pre-budget half) |
| `unit/test_budget_tokens_benchmark.py` | 8/4 call ceilings, token estimate, p50/p95 | Guide 8.3 |
| `unit/test_security_units.py` | code single-use/expiry, revocation, Host/Origin | T-SEC-BOOT-01 (unit half) |
| `unit/test_validation_pipeline.py` | forged sid, role swap, invented amount, conflict sections | T-CITE-* |
| `unit/test_renderer.py` | backend quote attachment, verdict replacement, precedence | T-LEGAL-* |
| `unit/test_model_payload.py` | **no `tools` key**, think/stream false, ctx overflow, tag digest, mock /api/chat | T-MODEL-NOTOOLS-01 (unit half), CTX |
| `integration/test_store.py` | PRAGMAs, offset round-trip via DB, FTS number search, purge | T-PRIV-DELETE-DERIVED (partial) |
| `integration/test_delete_lifecycle.py` | traversal rejection, directory removal, canary report | T-PRIV-CANARY-DELETE (partial) |
| `integration/test_api_boot.py` | session exchange, auth on health, bad Host 403, bad Origin 403, no secret in `/` | T-SEC-BOOT-01 |
| `privacy/test_canary_helper.py` | byte-level canary matching | T-PRIV-CANARY-* |
| `model/test_live_ollama.py` | opt-in live schema call | Phase 2 only |

Positive/negative counts in the scanner corpus are asserted at runtime (`>= 40` each); the
committed corpus currently has **48 must-block / 51 must-pass**.

---

## 4. Required test families still to build

| Family | Status | Phase |
|---|---|---|
| `T-ING-*` upload→parse→store integration, page caps, encrypted/malformed/oversized PDFs, 50+ page, table layout | **partial** (validation/segmentation unit level only) | 1 |
| `T-ING-OCR-01` scanned fixture + OCR banner | not started | 1b |
| `T-MODEL-JSON-01` (≥50 calls/schema, ≥95% first try, ≥99% after retry) | not run | 2 |
| `T-MODEL-CTX-01` live context assertion incl. repeated-prompt case | not run | 2 |
| `T-MODEL-NOTOOLS-01` live request audit | payload unit test only | 2 |
| `T-RETR-EXPAND-01` lexicon-gap paraphrases | not started | 3 |
| Ask/runtime end-to-end, forged/stale/cross-doc sids through HTTP, verdict paraphrases, injection | unit level only | 4 |
| `T-ESCALATE-01`, `T-SCOPE-01`, Review/Overview behaviour | not started | 5 |
| `T-PRIV-NOEXT-01`, `NETINV-01`, `NOCLOUD-*`, `NOTELEMETRY`, `CANARY-LOGS`, `TEMP-CLEAN`, `OLLAMA-UNLOAD`, `NOSTORE-HEADERS`, `NOCDN`, `FAILCLOSED`, `SESSION-ISOLATION`, `INJECTION-NONET`, `DNS-REBIND` | canary helper + socket guard only; no isolated run | 4/6 |
| `T-HERMES-*` | not applicable — Hermes not built (ADR-0010) | — |
| Browser E2E, axe accessibility, no-CDN in a running app | not started | 5 |
| Stale-index, long/partial docs, deletion under failure, parser crash/timeout | not started | 7 |

The socket guard in `tests/conftest.py` blocks non-loopback connections in every test, but a
monkeypatched socket is **not** isolated-network evidence and must never be presented as such.

---

## 5. Release gates (not yet met)

From Guide §14.6 — all remain open:

- [ ] 100 % citation integrity on the evaluation set
- [ ] 0 legal verdicts in the boundary set
- [ ] all injection fixtures safe end-to-end
- [ ] required privacy tests pass with saved isolated evidence
- [ ] no external traffic observed during the flow
- [ ] held-out contracts run
- [ ] stale-index test passes
- [ ] model digest + benchmark report published
- [ ] licence/SBOM scan passes on the pinned lockfile
- [ ] docs match code

Update this page only with real command output, and only after the command has actually been run
in the environment you are claiming.
