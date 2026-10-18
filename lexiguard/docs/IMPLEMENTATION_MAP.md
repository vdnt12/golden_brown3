# Implementation map

What exists, what is tested, and what remains. Status is based on commands that were actually run
(see `TEST_PLAN.md` §1), not on files existing.

Status key: **done** = implemented and covered by a passing test or a committed run; **partial** =
implemented but an important case is unexercised; **seam** = deliberate failure point; **not built**
= intentionally absent.

Last updated: 2026-10-18.

---

## 1. Backend

| Module | Key symbols | Status | Evidence |
|---|---|---|---|
| `core/enums.py` | `PointKind`, `Route`, `Classification`, `ResponseStatus`, `MissingInfoCode`, `RunPath`, `resolve_status` | **done** | `test_enums`, precedence unit test |
| `core/limits.py` | `RunBudget`, `BudgetExceeded` | **done** | `test_budget_tokens_benchmark`; used by runtime |
| `core/textmetrics.py` | `estimate_tokens`, `fits_context` | **done** | `test_budget_tokens_benchmark` |
| `schemas/model_io.py` | `ModelAnswer` (empty list allowed), `ModelPoint`, `RouterProposal`, `NextAction` | **done** | `test_schemas` |
| `schemas/response.py` | `RenderedAnswer`, `Claim`, `EvidenceItem`, `MapCard`, `OverviewResponse`, `ReviewResponse`, `UploadResponse`, `QualityMetrics`, `EvidenceResponse`, `DeletionResponse` | **done** | `test_schemas`, E2E |
| `security/*` | launch codes, host/origin allowlists, CSP, no-store | **done** | `test_security_units`, `test_api_boot`; live curl headers |
| `api/session.py` | `POST /api/session` | **done** | `test_api_boot`, E2E session exchange |
| `api/health.py` | `GET /api/health` (runtime capabilities, pinned tag/digest) | **done** | `test_api_boot`; live curl |
| `api/documents.py` | upload/list/delete/pages/image | **done** | E2E (TXT + PDF + PNG + 404 after delete) |
| `api/ask.py` | ask (per-request model alias) | **done** | E2E fail-closed path; fixture evaluation; stub-Ollama roundtrip for both families |
| `api/review.py`, `api/overview.py` | review (`attention_first`) / overview (`cards` object) | **done** | E2E; 5 fixtures; CUAD ×510 |
| `api/evidence.py` | one stored sentence + `text_sha256` | **done** | E2E quote → page check |
| `ingest/pipeline.py` | `ingest_document`, `IngestError`, `IngestResult` | **done** | E2E TXT + PDF |
| `ingest/worker.py` | child-process PDF extract/render, limits, PNG encoder | **done** | `test_parser_docs`; PDF page image 200 |
| `ingest/parser.py` | TXT virtual pages, PDF parse, render | **done** | `test_language_quality_parser`, E2E |
| `ingest/ocr.py` | Tesseract subprocess, availability probe | **partial** | Code path present; Tesseract absent in this environment |
| `ingest/quality.py`, `ingest/language.py` | coverage/garble, no-ML language gate | **done** | `test_language_quality_parser` |
| `store/*` | schema, DB, row helpers, FTS5, deletion | **done** | `test_store`, `test_delete_lifecycle` |
| `retrieval/lexical.py` | FTS query, chunk search with page numbers | **done** | `test_store` |
| `retrieval/concepts.py` | 11-concept matcher (`CORE_TEN`), label→concept index | **done** | overview on 5 fixtures; CUAD ×510 |
| `retrieval/vagueness.py`, `conflicts.py` | vague terms, money/time, conflict detection | **done** | `test_…`; conflict fixture → 2 CONFLICT items |
| `retrieval/expansion.py`, `topics.py`, `crossrefs.py` | topic expansion, clause map | **done** | fixture refinement path |
| `retrieval/packets.py` | bounded packet with deterministic selection | **done** | `test_silence_packets`; runtime uses `dropped` |
| `agent/router.py` | deterministic pre-route | **done** | `test_router`; LEGAL_LIMIT observed |
| `agent/toolbox.py` | five bounded tools, provenance registration | **done** | runtime path; `test_tools` |
| `agent/prompts.py` | nonce-delimited evidence, no filenames | **done** | `test_prompts` |
| `agent/runtime.py` | `BoundedAgentRuntime`, `AskContext` | **done** (scripted model) | fixture evaluation, E2E fail-closed |
| `model/ollama_native.py` | native `/api/chat`, JSON schema, digest, `assert_context_fits` | **partial** | Payload unit-tested; real HTTP against a stub daemon; no live model |
| `model/factory.py` | provider construction, availability probe, allowlist | **done** | `/api/models`; 422 on unknown tag |
| `model/gateway.py` | Hermes **Agent framework** refusal | **done (refusal)** | ADR-0010; Hermes models run through `ollama_native` (ADR-0011) |
| `validation/*` | provenance, literal, modality, roles, claim support, legal policy, renderer | **done** | `test_validation_pipeline`, `test_literal`, `test_modality`, `test_roles`, `test_legal_scanner` |
| `services/answer.py` | ask use case + run ledger | **done** | fixture evaluation |
| `services/overview.py` | 11-card map keyed by label | **done** | E2E; 5 fixtures |
| `services/review.py` | `attention_first` with priority 1–5 + professional questions | **done** | conflict fixture → 8 items |
| `services/silence_context.py` | coverage, incorporated material, silence decision | **done** | absent-topic run → `NOT_LOCATED` |
| `services/glossary_service.py` | curated glossary lookup | **done** | term question → glossary explanation |
| `services/documents.py` | list/read page/read evidence/render/delete orchestration | **done** | E2E |
| `cli.py` | `ask`, `documents`, `delete`, `models` with exit codes 0/1/2/3 | **done** | `make ask`, `make models`; fail-closed run |

---

## 2. Frontend

| File | Purpose | Status |
|---|---|---|
| `App.tsx` | launch-code bootstrap → ready/error | **done (builds)** |
| `api/session.ts` | fragment code → `/api/session` → memory token, strips fragment | **done** |
| `api/client.ts` | typed client for every route, header-only bearer token | **done** |
| `types/api.ts` | mirrors backend schemas (snake_case) | **done** |
| `components/UploadPanel.tsx` | size/type checks, ingest result + quality metrics + warnings | **done** |
| `components/DocumentMap.tsx` | 11 cards from the `cards` object, with quotes and warnings | **done** |
| `components/AskPanel.tsx` | ≤500-char question, suggestions | **done** |
| `components/AnswerView.tsx` | typed claim sections, missing info, jurisdiction, ledger | **done** |
| `components/SourceQuote.tsx` | quote → page-viewer button | **done** |
| `components/PageViewer.tsx` | stored page text, highlighted sentence, rendered page | **done** |
| `components/ReviewPanel.tsx` | `attention_first` by priority + professional questions | **done** |
| `components/DeleteDialog.tsx` | typed confirmation + honest report | **done** |
| `components/StatusBadge.tsx` | text labels in words | **done** |
| `components/PrivacyBanner.tsx` | local-by-design wording | **done** |
| `tsc --noEmit && vite build` | type check + production build | **passes** (45 modules, 171 kB JS) |
| Browser E2E, axe CI, mobile pass | accessibility / cross-browser | **not built** |

There is no mock data path: every panel is fed by a live backend route.

---

## 3. Next three tasks

1. Live Day-0 gate on a machine with Ollama: record version + digest, run
   `scripts/benchmark_model.py`, choose E4B or E2B by measured latency.
2. Live evaluation: run the question set, fill `docs/EVALUATION.md` §5 from real output only.
3. Privacy evidence: isolated run with capture and negative control per `reports/privacy/README.md`.
