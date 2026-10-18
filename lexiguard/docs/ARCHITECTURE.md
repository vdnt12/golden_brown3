# LexiGuard architecture

**Status of this document:** design + implemented reality as of 2026-10-18. Implementation
authority is [`SOLUTION_GUIDE_v3.md`](SOLUTION_GUIDE_v3.md); this file is the navigable map of it.
Read [`../STRUCTURE.md`](../STRUCTURE.md) for the annotated file tree and
[`IMPLEMENTATION_MAP.md`](IMPLEMENTATION_MAP.md) for module-by-module status.

- All routes are implemented: upload, list, delete, pages/text, pages/image, ask, review, overview,
  evidence, health, session.
- The full upload → map → ask → review → delete flow is exercised by
  `tests/integration/test_end_to_end.py` (6 tests) with no live model.
- The validator was exercised with a scripted provider (`scripts/evaluate_fixtures.py`); a live
  Gemma run, latency measurement and privacy evidence remain outstanding.

---

## 1. Invariants that shape every module

1. **The model proposes; code decides.** The model returns content points with sentence ids
   only (`ModelAnswer`). Deterministic code owns routes, statuses, quotes, pages, sections,
   validation, legal policy, missing-information decisions and rendering.
2. **Quotes are immutable and backend-rendered.** A displayed quotation is a byte-for-byte
   slice of LexiGuard-normalised, stored text, shown in a separate `SourceQuote` channel.
3. **Everything is local by default.** FastAPI binds `127.0.0.1`; Ollama is called on
   `127.0.0.1:11434`; there is no cloud fallback, CDN, telemetry or browser persistence.
4. **Fail closed.** A claim that cannot be validated is dropped, not repaired. An operation that
   cannot complete returns a controlled status, never a guess.
5. **Hard caps are code, not prompt suggestions.** Tool calls, model calls, retrieval loops,
   chunks, packet size, question length, upload size and wall-clock budget are enforced in
   Python (see §9).
6. **Absence needs proof.** `NOT_LOCATED` requires adequate coverage, supported language and
   every silence-gate check; otherwise the status is `INSUFFICIENT_EVIDENCE`.
7. **One runtime.** The bounded state machine is the only agent runtime. The Hermes Agent framework is not built
   (ADR-0010); constructing the gateway fails closed.

---

## 2. System context

```text
┌──────────────────────────── Browser (same origin) ────────────────────────────┐
│ React + Vite + TypeScript SPA · all assets bundled · no CDN                   │
│ launch URL: http://127.0.0.1:<port>/#k=<one-time code>                        │
│ code ──POST /api/session──► bearer token held in JS memory only               │
└───────────────────────────────────┬───────────────────────────────────────────┘
                                    │ /api/*  Bearer · exact Host · Origin on writes
┌───────────────────────────────────▼───────────────────────────────────────────┐
│ FastAPI on 127.0.0.1 (also serves frontend/dist on the same origin)            │
│                                                                               │
│  security/  tokens · hosts · origin · headers (CSP, no-store)                 │
│  api/       session · health · documents · ask · review · overview · evidence │
│                                                                               │
│  ┌──────────────┐    ┌───────────────────────────────┐    ┌────────────────┐  │
│  │ ingest/      │    │ agent/ (bounded runtime)      │    │ model/         │  │
│  │ upload       │    │ RECEIVE → CLASSIFY → PLAN →   │    │ LLMProvider    │  │
│  │ worker (pdf) │    │ RETRIEVE → ANALYZE → VALIDATE │    │ OllamaNative   │  │
│  │ normalize    │    │ → RESPOND                     │    │ no tools[]     │  │
│  │ segment      │    │ 7 tools · RunBudget 8/4/2     │    │ 1 format retry │  │
│  │ quality/lang │    └───────────────┬───────────────┘    └───────┬────────┘  │
│  └──────┬───────┘                    │                            │           │
│         │                  ┌─────────▼─────────┐         127.0.0.1:11434       │
│         │                  │ retrieval/        │                  │           │
│         │                  │ FTS5/BM25 · topic │                  ▼           │
│         │                  │ lexicon · xrefs · │          Ollama + Gemma 4    │
│         │                  │ clause map ·      │          (local process)     │
│         │                  │ silence gate ·    │                              │
│         │                  │ packets           │                              │
│         │                  └─────────┬─────────┘                              │
│  ┌──────▼────────────────────────────▼─────────────────────────────────────┐  │
│  │ store/  data/docs/<doc_id>/doc.sqlite3  (SQLite + FTS5, secure_delete)  │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  validation/  provenance → citation → literal/modality/roles → legal scanner  │
│               → renderer (backend-owned RenderedAnswer)                       │
│  services/    document lifecycle/delete · canary scan · benchmark summaries   │
└───────────────────────────────────────────────────────────────────────────────┘
```

Optional Phase 8 (not built): a second *agent framework* such as Hermes would sit behind the same gateway and the same seven
tools; see ADR-0010.

---

## 3. Trust boundaries

| Data / component | Trust | Consequence |
|---|---|---|
| Uploaded PDF/TXT, OCR text, headers, footnotes, tables, metadata, filenames | **Untrusted** | Never treated as instructions; nonce-delimited evidence; metadata and filenames never enter prompts |
| `ModelAnswer`, `RouterProposal`, `NextAction` | **Untrusted** | Strict Pydantic validation; unknown keys rejected; can only propose content |
| Tool arguments | **Untrusted** | Allowlist, page/ref bounds, length caps, call caps in code |
| Browser/API input | **Untrusted** | Size/type/magic checks, 500-char question cap, strict schemas |
| FastAPI process, validator, renderer, SQLite files | **Trusted application code** | Single trust anchor; every response passes through it |
| Parser | **Semi-trusted child process** | Isolated from API memory; limits + timeout; parent re-validates output |
| Ollama + Gemma | **Untrusted supplier** | Output validated; local-only URL enforced; no tools API |
| Local same-user malware | **Out of scope** | Stated in `THREAT_MODEL.md`; the launch-code design removes the easy token leak from served HTML |

---

## 4. Component responsibilities

### 4.1 `app/security/`
- `tokens.py` — one-time launch codes (256-bit, single-use, 60 s), bearer session tokens held in
  process memory, constant-time comparison. Implemented + tested.
- `hosts.py` — exact Host allowlist (`127.0.0.1:<port>`, `localhost:<port>`). Implemented + tested.
- `origin.py` — exact Origin allowlist on state-changing requests. Implemented + tested.
- `headers.py` — CSP baseline, `nosniff`, `no-referrer`, frame deny, `no-store` for API responses.
  Implemented + tested through the API boot tests.

### 4.2 `app/api/`
| Route | Phase | Behaviour |
|---|---|---|
| `POST /api/session` | 1 | Single-use launch code → in-memory bearer token |
| `GET /api/health` | 1 | Boolean flags only (`api`, `store_ready`, `model_available`, `ocr_available`, `history_enabled`), token required |
| `POST /api/documents` | 1 | Upload → ingest (child-process PDF parse, quality/language gates, OCR hook) → 201 summary |
| `GET /api/documents` | 1 | List stored documents (no paths, no hashes of other docs) |
| `DELETE /api/documents/{id}` | 1 | Delete + canary verification + honest report |
| `GET /api/documents/{id}/pages/{n}` (+`/image`) | 1/4 | Stored page text with sentence offsets; PNG render for PDFs |
| `POST …/ask` | 4 | Deterministic route → retrieval → bounded packet → one model call → validation → rendered answer |
| `POST …/review` | 5 | Attention-ordered review + escalation questions |
| `GET …/overview` | 5 | 11-card map with evidence, keyed by label |
| `GET …/evidence/{sid}` | 4 | One stored sentence, verbatim, with its page text |

### 4.3 `app/ingest/`
- `upload.py` — magic-byte/size/encoding validation, display-name sanitisation. Implemented + tested.
- `normalize.py` — CRLF→LF, NFC, whitespace policy; offsets refer to this text. Implemented + tested.
- `segment.py` — line-based sentence segmentation with abbreviation/decimal protection and
  section tracking; every sentence offset round-trips. Implemented + tested (line-based limit in
  `LIMITATIONS.md`).
- `language.py` — no-ML page gate: >15 % non-Latin letters → unread; ≥40 tokens and <8 % English
  function words → unread. Implemented + tested.
- `quality.py` — per-page coverage/garble/OCR-candidate report. Implemented + tested.
- `parser.py` — TXT into virtual pages (~3,000 chars) and PDF via a child process (pypdfium2),
  both implemented + tested.
- `worker.py` — platform limits matrix and honest startup notices; subprocess supervisor is Phase 1.
- `ocr.py` — Tesseract availability seam; OCR is Phase 1b.

### 4.4 `app/store/`
SQLite schema (`schema.sql`), connection policy (`db.py`: `secure_delete=ON`,
`journal_mode=DELETE`, `foreign_keys=ON`, FTS5 probe), row helpers for documents/pages/sentences/
chunks, FTS triggers over `chunks`, purge helper, and verified directory deletion.
Implemented + tested.

### 4.5 `app/retrieval/`
- `lexical.py` — FTS5 tokenisation/quoting, BM25 search capped at 12 chunks. Implemented + tested.
- `topics.py` — versioned lexicon loader/classifier. Implemented + tested.
- `crossrefs.py` — clause/schedule/subject-to extraction. Implemented + tested.
- `clause_map.py` — section grouping from sentence records. Implemented + tested.
- `silence.py` — silence gate returning `NOT_LOCATED` only when every precondition holds.
  Implemented + tested.
- `packets.py` — nonce-delimited packets, 12-chunk and ~2,500-token caps. Implemented + tested.

### 4.6 `app/agent/`
- `router.py` — deterministic pre-router for legal paraphrases, terms, ambiguity, silence,
  document map, review, scope; stricter-wins merge. Implemented + tested.
- `tools.py` — seven tools, five model-selectable; `NextAction` validation against page/ref caps.
  Implemented + tested.
- `prompts.py` — system prompt, nonce-delimited evidence blocks, prompt token pre-budget.
  Implemented + tested.
- `runtime.py` — states/transitions and budget wiring; transition bodies are Phase 4 (raises
  explicitly).
- `limits.py` — budget re-exports.

### 4.7 `app/model/`
- `provider.py` — narrow `LLMProvider` protocol.
- `ollama_native.py` — payload builder (`/api/chat`, `think:false`, `stream:false`, `num_ctx`,
  seed 7, temperature 0, **never `tools`**), context post-check, `/api/tags` parsing, one
  format-retry then fail closed. Implemented + tested with a mock transport.
  Route proposal / expansion / NextAction calls are Phase 4 seams.
- `gateway.py` — refuses construction (Hermes Agent framework not built).
- `registry.py` / `factory.py` — allowlisted model tags (`gemma`, `gemma-e2b`, `hermes`), availability probe, no fallback (ADR-0011).

### 4.8 `app/validation/`
| Stage | Module | Scaffold status |
|---|---|---|
| Schema | `schemas/model_io.py` | Implemented + tested |
| Provenance | `provenance.py` | Implemented + tested |
| Citation rendering | `renderer.py` | Implemented + tested |
| Literal/number/date checks | `literal.py` | Implemented + tested |
| Modality/negation | `modality.py` | Implemented + tested |
| Role check (T7) | `roles.py` | Implemented + tested |
| Kind-specific support | `claim_support.py` | Implemented + tested |
| Pipeline orchestration | `pipeline.py` | Implemented + tested |
| Legal scanner | `legal_policy.py` | Implemented + tested against a 99-row starter corpus |
| Optional entailment | — | Not built (Tier 2) |

Validation order is fixed: **schema → provenance → citation rendering → kind-specific checks →
optional entailment (off) → legal scanner → renderer**. The scanner runs on assistant-authored
text; quotations are never altered.

### 4.9 `app/services/`

| Module | Responsibility |
|---|---|
| `lifecycle.py` | document-id validation, directory removal, canary scan, verification |
| `documents.py` | list/open/read page/render page/delete orchestration |
| `answer.py` | assembles `AskContext`, runs `BoundedAgentRuntime`, writes the run ledger |
| `overview.py` | 11-card map with FOUND / NOT_LOCATED / NOT_ASSESSED / INSUFFICIENT_EVIDENCE |
| `review.py` | attention-ordered review + escalation questions |
| `glossary_service.py` | curated glossary lookup and disclaimers |
| `silence_context.py` | unread pages, coverage, incorporated-material checks, silence decision |

### 4.10 `agent/`
`router.py` (deterministic pre-route), `toolbox.py` (five bounded tools, every returned sentence
registered in `ProvenanceRegistry`), `prompts.py` (nonce-delimited evidence, no filenames),
`runtime.py` (`BoundedAgentRuntime`: budget, one refinement, validation, rendering).

### 4.11 `frontend/`
React + Vite + TS. Launch-code bootstrap with an in-memory token, upload panel, document list,
11-card map, ask panel with typed claim sections, review panel, delete dialog with a deletion
report, and a page viewer that shows the stored page text plus the rendered PDF page. Every quote
is a button that opens that page; the token is sent as a header, never in a URL.
`tsc --noEmit && vite build` passes (44 modules). No browser E2E or axe run yet.

---

## 5. Request lifecycle (ask)

```text
RECEIVE   question (≤500 chars), document binding, session check
CLASSIFY  deterministic pre-router; optional model proposal only when unsure; stricter wins
PLAN      topic lexicon + BM25 always run first; decide fast path vs one refinement
RETRIEVE  ≤2 loops; 7 tools; ≤8 calls; ≤12 chunks/call; ≤2,500-token packets
ANALYZE   exactly one ModelAnswer call on the fast path; +1 refinement call otherwise
VALIDATE  provenance → citation → literal/modality/role → scanner; rejected points dropped
RESPOND   backend composes RenderedAnswer; status precedence; ledger metadata (no CoT)
```

Call budget (hard): fast path 3 worst case (answer + format retry + validation retry); refinement
path 4 (refinement + answer + format retry + validation retry). Wall clock = 4 × Day-0 p50, never
above the request timeout. See `SAFE_LIMITS` in `docs/ARCHITECTURE.md` §9 and `config.py`.

---

## 6. Validation and legal policy

```text
ModelAnswer ──schema──► ──provenance──► ──render citations──► ──kind checks──►
   │                         │                  │                   │
   │ unknown keys rejected   │ sid not exposed  │ quote/page from   │ literal, modality,
   │                         │ this run → drop  │ store, not model  │ role, conflict rules
   ▼                         ▼                  ▼                   ▼
 optional entailment (off) ──► legal scanner (assistant text only) ──► renderer
                                   │
                                   └─ hit → limitation template + LEGAL_LIMIT
```

Scanner rules (pattern-based, not a keyword list): targeted verdict predicates, copula verdicts,
headline verdicts, against-law phrases, outcome predictions, advice/judgement. The **source-echo
exception** applies only to `STATED`/`RESTATEMENT` points when the verdict word plus its next word
also appears in the cited source (e.g. “valid for 11 months”). A bare verdict is never allowed.
`legal_verdict` is permanently `null`.

Honest scope of these checks: they prove **citation integrity** and catch invented figures,
swapped parties and flipped modality. They do **not** prove semantic faithfulness; that is measured
by the human-labelled Unsupported Claim Rate and stated in `LIMITATIONS.md`.

---

## 7. Statuses and precedence

`ERROR_PROCESSING` > `ERROR_LOCAL_MODEL_UNAVAILABLE` > `LEGAL_LIMIT` > `CONFLICTING` >
`AMBIGUOUS` > `INSUFFICIENT_EVIDENCE` > `NOT_LOCATED` > `LIMITED` > `OUT_OF_SCOPE` > `ANSWERED`.

`OUT_OF_SCOPE` applies when no higher-priority failure/limitation applies. The two error statuses
are ordered with processing first because it means the run itself failed while handling the model
failure; recorded in `EVALUATION.md`.

Missing information uses only: `UNREADABLE_CONTENT`, `REFERENCED_MATERIAL_NOT_PROVIDED`,
`TOPIC_NOT_LOCATED` (silence gate only), `CONTEXT_REQUIRED`. Messages are backend templates.

---

## 8. Data model

```text
document ──1:N── pages ──1:N── sentences
   │                            │
   │                            └── sid ── presented in evidence packets ── cited by points
   ├──1:N── chunks ──(trigger)── chunks_fts (text, heading, numbers)
   ├──1:N── clauses
   ├──1:N── relationships (deterministic | model_suggested)
   └──1:N── run_ledger (ids, names, counts; no question/answer/evidence text)
```

Evidence identity chain: `point → sid → stored sentence → page + section + offsets → document
SHA-256`. A sid must have been returned by a tool **in that run**; existence in the database is
not enough (`ProvenanceRegistry` is per-request). Deletion removes the whole directory and
verifies absence.

---

## 9. Hard limits

| Limit | Value | Enforced where |
|---|---:|---|
| Upload size | 20 MiB default | `ingest/upload.py`, `config.py` |
| Pages | 300 | `config.py`; parser (Phase 1) |
| Question length | 500 chars | `api/ask.py`, `agent/router.py` |
| Tool calls / request | 8 | `core/limits.py` (`RunBudget`) |
| Model calls / question | 4 | `RunBudget` |
| Retrieval loops | 2 | `RunBudget` |
| Chunks / tool call | 12 | `retrieval/lexical.py`, `retrieval/packets.py` |
| Evidence packet | ~2,500 estimated tokens (chars ÷ 3.2) | `retrieval/packets.py`, `agent/prompts.py` |
| Prompt pre-budget | ~3,000 estimated tokens | `agent/prompts.py` |
| `num_ctx` | 8192 | `model/ollama_native.py` |
| Format retries | 1 | `model/ollama_native.py` |
| Validation attempts | 2 | Phase 4 runtime (constant exists) |
| Wall clock | 4 × Day-0 p50 | Phase 4 runtime (`RunBudget.wall_clock_s`) |

---

## 10. Privacy and localhost hardening

- Bind loopback only; no wildcard CORS; exact Host check resists DNS rebinding; Origin check on
  writes; bearer token on every `/api/*` route including health.
- Launch code in the URL fragment → `/api/session` → in-memory token. The served HTML contains no
  secret. `/` is verified in tests to contain no launch code.
- CSP: `default-src 'self'` with no inline scripts/styles; all assets bundled.
- `Cache-Control: no-store` on API responses; no localStorage/sessionStorage/IndexedDB.
- Per-document SQLite with `secure_delete=ON`, rollback journal (no WAL), history off.
- Deletion: reject new work, close handles, unload model (Phase 2 verification), remove directory,
  clear session binding, canary scan, report distinguishing app-controlled removal from forensic
  erasure.
- Evidence: no privacy claim before an isolated run with attempt-visible capture, a detected
  negative control and no raw loopback payloads. UI says “Designed for local processing” until then.

---

## 11. Where the implementation starts (build order)

1. **Phase 1** — PDF child process + upload route + per-document DB writes + delete route.
   The store, normaliser, segmenter, language/quality gates, TXT parser and deletion service are
   already tested, so this is wiring and limits, not new design.
2. **Phase 2** — Ollama adapter acceptance (`T-MODEL-JSON-01`, `CTX-01`, `NOTOOLS-01`) and
   Day-0 timing on the target machine.
3. **Phase 3** — populate FTS from segmented pages; add cross-reference expansion into retrieval;
   wire the silence gate to real coverage data.
4. **Phase 4** — runtime transitions, tools execution, ModelAnswer → validation → renderer, and
   the ask route; then the minimal UI against real routes.
5. Everything after that is Phase 6 (evaluation/privacy) before Phase 5 (UI polish), per Guide §15.

Do not reorder: evaluation before UI polish is deliberate. Do not weaken validator, citations,
legal policy, privacy tests, deletion, fail-closed behaviour or honest limitations to ship.

---

## 12. What is still deliberately not built

| Omitted | Why | Where tracked |
|---|---|---|
| Live model acceptance run and benchmark | Needs a machine with Ollama and the pinned model | `MODEL_SETUP.md`, `EVALUATION.md` |
| Privacy evidence (isolated run, capture, negative control) | Needs a live machine and the capture procedure | `PRIVACY.md`, `reports/privacy/` |
| Entailment pass, dense retrieval | Tier 2 quality work, not required for the documented behaviour | ADR-0006 |
| Hermes *Agent framework* | Not built by decision; fail-closed seam only | ADR-0010 |
| Hermes *model family* (`hermes3:8b`) | Built: same adapter, prompt and validator as Gemma, selected explicitly per request | ADR-0011 |
| Per-IP attempt throttling on `/api/session` | Single-user local tool; codes are 256-bit, single-use, 60 s | `LIMITATIONS.md` |
| Answer history | Privacy decision: no question/answer persistence | ADR-0009 |

Honesty rule for every doc in this repository: **no feature is complete because files exist, and
no test is “passing” unless its command was run.** Current command results are in `TEST_PLAN.md` §1.
