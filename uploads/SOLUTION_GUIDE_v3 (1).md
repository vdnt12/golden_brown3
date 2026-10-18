# LexiGuard — Final Solution Guide v3.0 (merged and verified)

**Product:** LexiGuard — Private, evidence-backed legal-document triage  
**Hackathon:** ZeroDay OSS Hacktoberfest 2026 · Problem Statement 2  
**Repository:** <https://github.com/panditshubham766-dotcom/golden_brown1>  
**Intended repository path:** `docs/SOLUTION_GUIDE_v3.md`  
**Specification version:** 3.1 (3.0 plus the consistency patch of 18 Oct 2026, §00 item 12; Guide v2.1 + Amendments v2.1 merged + independent audit of 18 Oct 2026; supersedes all earlier guides, amendments and prompts)  
**MVP scope:** English rental / leave-and-licence agreements in PDF or TXT; local inference; source-grounded answers; no legal verdicts.

> **Core rule:** retrieval finds evidence; local Gemma proposes structured points that cite sentence IDs; deterministic code validates and labels those points; the backend—not the model—owns final status, legal policy, missing-information decisions, citations, and rendering.

This is a build specification, not a claim that the application or its tests already exist. No privacy, accuracy, benchmark, or release gate may be described as passed until a real run produces a checked-in report.

---

## 00. What changed in v3.0 (read first)

v3.0 **merges** Guide v2.1, `AMENDMENTS_v2.1.md` (T1–T9, R1–R8) and the findings of the independent audit of 18 Oct 2026 (`docs/REVIEW_FINDINGS_v3.md`). **This file alone is the design authority.** `AMENDMENTS_v2.1.md`, `MASTER_IMPLEMENTATION_PROMPT_v2.txt` and `lexiguard_masterprompt_v2_1.txt` are superseded; do not commit them (the two prompts had opposite precedence rules). Merged amendments are tagged **[T#]/[R#]**; new audit changes are tagged **[v3]**.

[v3] changes in one list:

1. One authority and one prompt (v3 prompt = `docs/MASTER_IMPLEMENTATION_PROMPT_v3.txt`).
2. Repository baseline corrected (§0.2): the README already exists and makes claims the project cannot yet support (FAISS RAG, “verbatim citations”); Phase 0 rewrites it honestly.
3. Ollama/Gemma pins corrected from the issue pages themselves (§3.2a): minimum Ollama 0.21.1; `-qat` and `-mlx` tags excluded; no `pattern` in schemas.
4. Scope tiers, a Day-0 hardware gate and schedule scaling for an unannounced deadline (§15.1).
5. Gemma-call budget and fast path (§8.3a) so one answer is not 5–8 model calls on a laptop.
6. Verdict scanner redesigned to avoid false blocks such as “valid for 11 months” (§9.3a).
7. Over-refusal can no longer buy a good score: answer-rate and false-refusal metrics (§14.3).
8. Network evidence must show *attempts* and include a negative control; Docker `--network none` portable path (§11.4).
9. No secret in served HTML: one-time launch-code exchange (§11.3).
10. Platform matrix for parser limits; TXT virtual pages; language gate without an ML dependency; glossary is “curated”, not “reviewed”.
11. Hermes is not built by default (ADR-0010).
12. **[v3.1] Consistency patch after re-auditing v3.0 against itself:** (a) §15 heading said "do not reorder" while §15.1 runs Phase 6 before Phase 5, and Phase 5 listed Investigate, which is Tier 2; (b) the Gemma-call ceiling of 4 was arithmetically broken by "expansion *and/or* NextAction" (up to 5 calls) and had no wall-clock cap (§8.3, §8.3a); (c) a Docker container with `--network none` publishes no ports, so a host browser cannot reach its UI; the Docker target is now a headless scripted flow (§11.4, §16.1); (d) schedule scaling promised Tier 1 in 7–11 days although Tier 0 + Tier 1 is estimated at ≈9–14 focused days (§15.1); (e) the public README is wrong *today*, so the owner replaces it before any agent session instead of waiting for Phase 0 (§0.2).

---

## 0. Binding decisions and precedence

### 0.1 Authority

1. The official PS2 requirements and submission gates in the ZeroDay OSS participant guide define the hackathon obligations.
2. This Guide defines the implementation contract for this repository.
3. `docs/MASTER_IMPLEMENTATION_PROMPT_v3.txt` instructs the coding agent to implement this Guide; it must never silently override it.
4. Runtime configuration and installed-version checks determine which version-specific commands/options actually work. Record their outputs in `docs/MODEL_SETUP.md` and reports.
5. Changes to fixed decisions require an Architecture Decision Record (ADR) naming the trade-off, evidence, measurements, risks, and tests. Do not change a decision merely to make an implementation easier.

If the Guide and prompt disagree, do not code the disputed behaviour. Fix the documents first. If a library or runtime behaves differently from its documentation, fail closed, record exact versions and output, and add a detecting test before continuing.

### 0.2 Public repository baseline

At the independent re-check on 18 October 2026 the public `main` branch showed **two commits** and the root files `.gitignore`, `LICENSE` and a short `README.md`; no application source was visible and no repository topics were set. **[v3] The existing README claims a “RAG engine powered by Gemma 4 & FAISS”, “100% localhost & on-device execution” and “verbatim legal citations”.** None of that exists yet, and FAISS/dense retrieval contradicts the lexical-first decision below, so Phase 0 must replace the README with an honest status README (what exists, what is planned, what is verified). A README that claims unbuilt or unverified features is a fabrication/G3 risk. Start by cloning and inspecting the actual working tree; do not assume an existing application or claim that implementation/tests have run. Preserve and inspect the existing Apache-2.0 license rather than replacing it blindly. **[v3.1] The owner replaces the root `README.md` on `main` with the honest status README (`docs/README_REPLACEMENT.md`) before the first agent session**: the current text is public and wrong today, and a coding session may be days away. Phase 0 then keeps that README accurate; it does not wait on it. Add `NOTICE` and project files as specified below.

### 0.3 Locked decisions

| Concern | Binding decision |
|---|---|
| Frontend | React + Vite + TypeScript, production build served by FastAPI on the same origin; every font, icon and script bundled locally; no CDN; CSP `default-src 'self'`. |
| Backend | Python + FastAPI bound only to `127.0.0.1`; mandatory random bearer token on every `/api/*` request; validate Host; validate Origin on state-changing requests; no wildcard CORS. |
| Storage | One directory per document: `data/docs/<doc_id>/`; SQLite + FTS5; `PRAGMA secure_delete=ON`; rollback journal (`journal_mode=DELETE`), not WAL; answer history disabled by default. |
| PDF parser | `pypdfium2` (permitted Apache-2.0 or BSD-3-Clause options); **do not use PyMuPDF**. Parse in a child process with limits and timeout. |
| Text offsets | Offsets refer only to LexiGuard's stored normalized page text, never directly to PDFium character indices. |
| OCR | Tesseract, local only, invoked only when the page-quality gate detects image-only/low-text pages; OCR evidence is visibly labelled. |
| Project license | Apache-2.0 with root `LICENSE` and `NOTICE`; CI fails if an AGPL/GPL dependency is introduced. Model and data licenses are recorded separately. |
| Primary model | Ollama tag `gemma4:e4b-it-q4_K_M`; pin and record actual digest. No 12B/26B/31B variant, `:cloud` tag, or cloud fallback. |
| Alternative model | `gemma4:e2b-it-q4_K_M` (same quantisation family as the primary, so the E2B-vs-E4B benchmark is fair); verify availability/digest at setup. Do not silently substitute an unpinned alias. `-qat`, `-mlx`, `-nvfp4`, `-mxfp8` tags are excluded (§3.2a). |
| Inference API | Ollama ≥ 0.21.1 native `POST /api/chat` on loopback, not `/v1`; `format` is a *simple* JSON Schema and is never trusted (Pydantic always validates); `think:false`; `options.seed` fixed; `temperature:0`; `num_ctx:8192` by default; `stream:false`; **no `tools` key ever sent** [T1][T2]. Empty `message.content` is a failure even if thinking text exists. |
| Ollama process | Headless `ollama serve` with `OLLAMA_NO_CLOUD=1`; do not set `OLLAMA_DEBUG`; do not depend on the desktop tray app for the privacy demo. |
| Retrieval | Lexical-first: SQLite FTS5/BM25 + versioned rental-topic lexicon + deterministic cross-reference expansion. Dense retrieval is optional and off by default. |
| Dense retrieval | If and only if evaluation shows a measured recall improvement, add `DENSE=on` using local Ollama `/api/embed` and a pinned `nomic-embed-text` digest, with `search_document:` / `search_query:` prefixes. No `torch`, `sentence-transformers`, or Hugging Face Hub access in the default install. |
| Agent runtime | Bounded state machine is the only runtime for all gates, evaluation and demo. Tool choice is a schema-constrained `NextAction` executed by LexiGuard code (§2.3). **Hermes is not built by default** (ADR-0010, §12) [R7]. |
| Truth ownership | Deterministic code owns file handling, IDs, page/section metadata, offsets, hashes, DB, retrieval caps, citations, validation, legal policy, deletion, network policy, tool allowlists and schema validation. |

**Model-tag note [v3, verified 18 Oct 2026]:** the Ollama tags page lists `gemma4:e4b-it-q4_K_M` (6.6 GB, 128K, digest `dc35e8d9c606`) and `gemma4:e2b-it-q4_K_M` (4.6 GB, 128K, digest `b37049369adf`). Digests move; record the names and digests returned by *your* `/api/tags` and put those in every report. The setup script must stop with a clear error if a tag cannot be resolved. The official Gemma 4 model card (ai.google.dev/gemma/docs/core/model_card_4) states **Apache 2.0**; paste its licence text into `docs/MODEL_LICENSE.md` at pin time. E4B is 4.5 B effective / 8 B with embeddings, so budget for the weights *plus* KV cache.

### 0.4 Version-specific verification register

Do not invent Hermes configuration keys, minimum context settings, OCR data availability, model parameters or parser range behaviour. At setup/pin time, verify and record:

- `ollama --version`, `/api/tags` names/digests, `/api/show` model capabilities, actual `think:false` behaviour, structured-output content, `keep_alive:0` unload behaviour, `num_ctx` used per request and logs.
- Exact E2B tag/digest and quantization comparable to E4B for benchmarking.
- Gemma model license from the official Google model card.
- pypdfium2 version/license and actual extraction/highlight behaviour; text normalization and offset round-trips on representative PDFs.
- Tesseract executable and language data installed locally; no downloads during document processing.
- Hermes version, `HERMES_HOME` behaviour, session/memory/skill persistence, effective tool list at the gateway, actual `num_ctx`, network isolation, and delete wipe.
- Exact package license metadata from locked dependencies and generated SBOM.

If an item cannot be verified, disable the affected optional capability or fail closed. A web page describing an option is not proof that the installed version uses it as expected.

---

## 1. Product definition and PS2 traceability

LexiGuard helps a non-lawyer understand what an English rental agreement says, find the exact passage, identify ambiguous or potentially noteworthy wording, and recognise when the document cannot answer a question. It is a preliminary document-understanding tool, not a lawyer, legal research system, or source of legal advice.

### 1.1 MVP

Accept PDF/TXT; process locally; extract page-level text, sentences, headings and quality warnings; build a lexical index; answer questions using local Gemma; cite exact source passages; distinguish document statements from restatements, interpretations, concerns, ambiguities and conflicts; explain terms using a curated local glossary; flag topics that may depend on local law without saying what that law requires; detect missing evidence; support verified deletion; work without external networking after setup.

Topics include parties, property reference, start/end dates, term, renewal, rent and schedule, deposit/advance, utilities, repairs/maintenance, access/inspection, restrictions, guests, pets, subletting, alterations, notice, lock-in, termination, early exit, penalties, deductions, forfeiture, handover, dispute/venue wording, referenced annexures and schedules, ambiguities, conflicts and extraction quality.

### 1.2 Non-goals

- No legal validity/enforceability/legality/fairness decision or outcome prediction.
- No external-law research in the answering loop; no jurisdiction-specific conclusion from pretrained knowledge.
- No cloud model, OCR, embedding, translation, storage or telemetry service.
- No editing, negotiation, signing or automated legal action.
- Non-English content is detected and flagged `UNSUPPORTED_LANGUAGE` / `NOT_ASSESSED`; it is not silently treated as English.
- Employment contracts, legal notices and service agreements are future work, not part of the MVP claims. [R3] They must still **degrade honestly, not break**: see the document-type gate in §13.1.

### 1.3 Requirements map

| Requirement | Implementation | Evidence/test |
|---|---|---|
| L1 PDF/TXT ingestion | API upload validation and parser worker | `T-ING-*` |
| L2 local extraction and interpretation | pypdfium2/Tesseract + local Gemma/Ollama | `T-ING-*`, `T-MODEL-*` |
| L3 plain-language terms | curated `glossary/rental_terms.yaml`, `TERM_EXPLANATION` route | `T-GLOSS-*` |
| L4 rights/obligations/dates/penalties/termination | validated Document Map and Review | evaluation question set |
| L5 verifiable passages | sentence-ID provenance; backend-only quote/page/section rendering | `T-CITE-*` |
| L6 explicit vs interpretive | typed points and separately labelled UI panels | validator/UI tests |
| L7 ambiguity, silence, jurisdiction dependence | silence gate, ambiguity/conflict routing, local-law topic lexicon | evaluation tests |
| L8 limit/refuse/escalate legal conclusions | deterministic pre-router + stricter-route merge + output scanner | `T-LEGAL-*` |
| L9 privacy demonstrated | local-only services and isolated-network evidence | all `T-PRIV-*` |
| L10 meaningful Gemma + reusable open source | local Gemma central to interpretation; reproducible setup and docs | `T-MODEL-*`, CI |
| S1–S10 submission | Phase 9 checklist and reports | release checklist |

The PS2 rubric strongly rewards citation/grounding, uncertainty/refusal and demonstrated on-device privacy. These are release blockers, not features to sacrifice for interface polish.

---

## 2. System architecture

```text
Browser UI (React/Vite, same origin, in-memory token only)
  │ authenticated /api/* calls; no CDN and no persistent browser cache
  ▼
FastAPI on 127.0.0.1
  ├─ Host/Origin/token and input validation
  ├─ document lifecycle + deletion coordinator
  ├─ parser child process ── pypdfium2 ── local Tesseract only when needed
  ├─ per-document SQLite/FTS5 store + versioned lexicons + clause map
  ├─ deterministic pre-router + constrained local route proposal
  ├─ bounded AgentRuntime (default)
  │    └─ seven read-only, document-bound tools
  ├─ LLMProvider ── Ollama native /api/chat on loopback
  └─ Validator + legal scanner + policy + backend-owned renderer

Optional Phase 8 only:
  Hermes sandbox (tmpfs HERMES_HOME, no egress)
    └─ LexiGuard model gateway + the same constrained MCP tools
```

All document-bearing arrows in normal use remain local. The browser never talks directly to Ollama; only the backend/gateway does. The model receives only a bounded question and relevant, nonce-delimited evidence text. File metadata and filenames never enter the model prompt. Network isolation must include the app and Ollama in the same isolated environment so loopback remains usable while external networking is unavailable.

### 2.1 Trust boundaries

- Browser input, uploaded files, extracted text, OCR text and all model outputs are untrusted.
- The parser runs outside the API process in a resource-limited child process.
- The retrieval/tool layer is read-only, document-bound out-of-band and capped.
- Gemma output is an untrusted proposal, never a policy or truth authority.
- The validator and response renderer are trusted application code; every response passes through them.
- Hermes, if later enabled, is an untrusted planner; its effective capabilities are determined by the LexiGuard gateway and sandbox, not by its own status screen.

### 2.2 Fixed tools

Only these tools may be exposed to the bounded runtime and, if enabled, Hermes:

1. `search_document(query, topic?)`
2. `get_evidence(ev_id)`
3. `get_page(page)`
4. `get_section(label)`
5. `get_document_map()`
6. `find_related_clauses(ev_id)`
7. `check_document_silence(topic)`

The document ID is bound when the request/session starts; no tool accepts a `document_id` parameter. Validate tool names, argument schema and size in code. `validate_citation` is **not** model-callable; validation runs after every model response regardless of which tools were called. No shell, arbitrary filesystem, web, browser, messaging, remote MCP or writable document tool is allowed.

### 2.3 [T2][v3] Tool selection without Ollama `tools[]`

Do **not** send a `tools` key to Ollama. Gemma returns a small flat `NextAction` object under a simple JSON Schema (Appendix A4); **LexiGuard code** validates it, executes the tool and feeds back a bounded evidence packet. Rationale: native tool-calling with `think:false` is the path with the open empty-reply bug (Ollama #18861, open on 18 Oct 2026, reported on `gemma4:26b`; treat as applicable to the E-series until shown otherwise), and it would hand tool selection to a template we do not control. `T-MODEL-NOTOOLS-01` asserts that no request to Ollama ever contains `tools`.

Enforced in code: `action` ∈ allowlist; `ref` must be an id returned earlier in this run; `page` ∈ [1, page_count]; `query` ≤ 120 chars; every tool result is capped (12 chunks, 40 sentences and ≈2,500 estimated tokens — `get_page` and `get_section` included); ≤ 8 tool calls. `get_evidence` and `get_document_map` are runtime-initiated, not model-selectable. Planning is deterministic-first: lexicon + BM25 pre-retrieval always runs, Gemma only refines (≤ 2 loops, §8.3a).

---

## 3. Model and local inference contract

### 3.1 Models

- Primary: `gemma4:e4b-it-q4_K_M`.
- Memory-constrained alternative: `gemma4:e2b-it-q4_K_M`, only after tag verification and a documented benchmark.
- Do not use `:cloud`, remote endpoints, another model as a silent fallback, or the 12B/26B/31B family for this project.
- Pin the resolved digest; a tag alone is mutable and is insufficient for reproducibility.
- Record model name, digest, Ollama version, quantization, requested/effective context, OS, CPU/GPU, RAM/VRAM, seed, temperature, `think`, latency and peak memory for reports.

### 3.2 Native API request

Use `POST http://127.0.0.1:11434/api/chat` with `stream:false`, `think:false`, a strict JSON Schema under `format`, and `options: { seed: <fixed integer>, temperature: 0, num_ctx: 8192 }`. Use only a loopback URL. Do not parse the `thinking` channel or attempt to salvage malformed JSON. If `message.content` is missing or empty, schema validation fails, output exceeds limits, or Ollama is unavailable, return a controlled failure status. No network/cloud fallback is allowed.

The 8192-token context is the default, not a benchmark claim. Evidence packets must remain small (target ≤ about 3K tokens) to preserve headroom. Raise the context only with a measured need and recorded memory/latency evaluation. Do not assume the maximum shown for a model tag is suitable for local hardware.

### 3.2a [T1][T3][T4][v3] Schema, version and context rules (verified 18 Oct 2026)

- **Never trust server-side schema enforcement.** Always `model_validate_json` the reply. A schema-invalid reply gets at most **one** format-retry (separate from the 2 validation attempts), then fails closed.
- **Keep schemas simple:** flat objects, arrays, enums, required fields, short strings. No `pattern`, `format`, `oneOf`, deep nesting, or reliance on `additionalProperties`. Ollama #8063 (open) reports schema-invalid output on Gemma 4 e2b/e4b/12b `-qat` models, including enum violations and extra fields; the thread traced one failure to a grammar-parse error from a `\d` pattern escape.
- **Minimum Ollama version 0.21.1.** Ollama #15260 (`think:false` silently dropped `format` on Gemma 4) was fixed in 0.21.1. The version you pin is the one on which the `T-MODEL-*` tests pass, recorded in `docs/MODEL_SETUP.md`.
- **Tags:** GGUF `…-it-q4_K_M` only. **Never `-mlx`** (the MLX runner ignores `format`, #16776) and **do not benchmark `-qat`** (open #8063). This overrides Amendment T3's optional `-qat` row.
- **Context:** Ollama's default context is 4096 tokens (Ollama FAQ) and VRAM-dependent defaults can differ, so always pass `num_ctx` per request. Silent truncation drops the *start* of the prompt, i.e. the safety instructions. Guard twice: (1) pre-budget the prompt with a conservative token estimate (§8.3a); (2) after each call assert `prompt_eval_count + eval_count < num_ctx` (`T-MODEL-CTX-01`, failing with `ERROR_PROCESSING`, never truncating). `prompt_eval_count` may under-report when a prompt prefix is cached, so the test must include a repeated-identical-prompt case on the pinned version and the pre-budget stays the primary guard (verify, do not assume).
- **`T-MODEL-JSON-01` is statistical:** ≥ 50 calls per schema (router, ModelAnswer, expansion, NextAction) at temperature 0; record first-try schema-valid rate and empty-content rate. Thresholds fixed *before* the run: first-try valid ≥ 95 %, valid after the single retry ≥ 99 %, zero empty replies reaching the user. If missed, simplify the schema or change model; do not lower the threshold.
- `seed` + `temperature:0` give repeatability on the same machine and build, not bit-identical output across hardware or versions; never claim cross-hardware determinism.
- Thinking is controlled only through Ollama's `think` parameter; the Gemma 4 model card describes a thinking token in the system prompt — do not add one.

### 3.3 Ollama process and logs

For isolated demonstrations, start headless `ollama serve` with `OLLAMA_NO_CLOUD=1`; do not set `OLLAMA_DEBUG`. Verify if logs contain prompts/canaries. Do not rely on an updater/tray app. Any non-loopback connection during the normal flow fails the privacy gate. Setup-time downloads must be a separate, documented workflow; never provide private user files during setup.

### 3.4 Provider interface

Implement `LLMProvider` as a narrow interface. Its initial implementation is `OllamaNativeProvider`. Do not expose arbitrary URLs/models to the client. The provider should have typed calls for `route_proposal`, `answer_from_evidence` and optional `downgrade_entailment_check`. A route proposal is advice only; deterministic code selects final route/status.

### 3.5 [R5] Who does what (publish in `docs/MODEL.md`)

| Gemma (local, proposes) | Deterministic code (decides) |
|---|---|
| Route proposal when the pre-router is unsure; query-expansion terms (T6); `NextAction` refinement; the `text` of restatement / interpretation / ambiguity / conflict points; reading-level paraphrase of curated glossary entries; Overview card restatements | Format validation, parsing, OCR trigger, IDs, offsets, hashes, DB, retrieval, caps, silence decision, citation rendering, validation, legal policy, status/route precedence, jurisdiction and escalation panels, deletion, network policy, allowlists |

“Why this answer?” shows the loop — classify → plan → actions (names only) → analysis → validation result → path (fast/refine) → duration — never chain-of-thought. Report memory, tokens/s and p50/p95 latency for **both** E4B and E2B.

---

## 4. Repository structure

Create the following structure without committing documents, model weights, generated data, real agreements, secrets or personal data:

```text
golden_brown1/
├── README.md
├── LICENSE
├── NOTICE
├── .gitignore
├── .editorconfig
├── AGENTS.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── pyproject.toml
├── uv.lock
├── package.json
├── pnpm-lock.yaml
├── tsconfig.json
├── vite.config.ts
├── .github/
│   ├── workflows/ci.yml
│   ├── ISSUE_TEMPLATE/bug_report.yml
│   ├── ISSUE_TEMPLATE/feature_request.yml
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── labeler.yml
├── backend/
│   ├── app/main.py
│   ├── app/config.py
│   ├── app/security/{tokens,hosts,origin,headers}.py
│   ├── app/api/{documents,ask,review,overview,evidence,health}.py
│   ├── app/ingest/{upload,worker,parser,normalize,segment,quality,language,ocr}.py
│   ├── app/store/{db,documents,pages,sentences,chunks,fts,delete}.py
│   ├── app/retrieval/{lexical,topics,crossrefs,clause_map,silence}.py
│   ├── app/agent/{runtime,router,tools,limits,schemas,prompts}.py
│   ├── app/model/{provider,ollama_native,gateway}.py
│   ├── app/validation/{provenance,literal,modality,claim_support,legal_policy,renderer}.py
│   └── app/services/{lifecycle,privacy,benchmark}.py
├── frontend/
│   ├── index.html
│   └── src/{app,api,components,pages,styles,types}/
├── lexicons/
│   ├── rental_topics.yaml
│   └── jurisdiction_topics.yaml
├── glossary/
│   └── rental_terms.yaml
├── fixtures/
│   ├── README.md
│   ├── synthetic_rental_simple.txt
│   ├── synthetic_rental_indian_style.txt
│   ├── synthetic_rental_conflict.txt
│   ├── synthetic_rental_ambiguous.txt
│   ├── synthetic_rental_injection.txt
│   └── generated PDFs / scanned / table / long / malformed / language fixtures
├── questions/
│   ├── development.jsonl
│   ├── heldout/README.md
│   └── schema.json
├── scripts/
│   ├── setup_local.sh
│   ├── verify_model_tags.py
│   ├── verify_licenses.py
│   ├── run_isolated_demo.sh
│   ├── benchmark_model.py
│   ├── benchmark_retrieval.py
│   └── generate_sbom.sh
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── security/
│   ├── privacy/
│   ├── model/
│   └── e2e/
├── docs/
│   ├── SOLUTION_GUIDE_v3.md
│   ├── MASTER_IMPLEMENTATION_PROMPT_v3.txt
│   ├── PRD.md
│   ├── REQUIREMENTS.md
│   ├── ARCHITECTURE.md
│   ├── DATA_FLOW.md
│   ├── PRIVACY.md
│   ├── THREAT_MODEL.md
│   ├── SECURITY.md
│   ├── MODEL.md
│   ├── MODEL_SETUP.md
│   ├── MODEL_LICENSE.md
│   ├── MODEL_BENCHMARK.md
│   ├── EVALUATION.md
│   ├── TEST_PLAN.md
│   ├── DEMO.md
│   ├── DATASET_NOTES.md
│   ├── OPEN_SOURCE.md
│   ├── CONTRIBUTION.md
│   ├── LIMITATIONS.md
│   └── adr/0001-license.md ...
└── reports/
    ├── .gitkeep
    ├── samples/README.md
    └── privacy/README.md
```

The exact internal module split can evolve if tests stay stable, but do not combine trust boundaries just to reduce file count. **[v3] Additions:** `lexicons/escalation_templates.yaml`, `Makefile` (`setup`, `demo`, `isolated-demo`, `isolated-demo-docker`, `test`), `Dockerfile`, `docs/adr/0010-hermes-not-built.md`, `docs/REVIEW_FINDINGS_v3.md`, `fixtures/README.md` provenance table, `tests/privacy/negative_control.py`. A public repository should remain understandable and reusable, not be built around one demo file.

### 4.1 Required minimum docs in Phase 0

Create/update: `README.md`, `LICENSE`, `NOTICE`, `AGENTS.md`, `TASKS.md`, `docs/PRD.md`, `REQUIREMENTS.md`, `SOLUTION_GUIDE_v3.md`, `ARCHITECTURE.md`, `DATA_FLOW.md`, `PRIVACY.md`, `THREAT_MODEL.md`, `SECURITY.md`, `MODEL.md`, `MODEL_SETUP.md`, `MODEL_LICENSE.md`, `MODEL_BENCHMARK.md`, `EVALUATION.md`, `TEST_PLAN.md`, `DATASET_NOTES.md`, `OPEN_SOURCE.md`, `CONTRIBUTION.md`, `LIMITATIONS.md`, `DEMO.md`, and initial ADRs. No placeholder doc may claim an unperformed test passed.

---

## 5. Document lifecycle and data model

### 5.1 Directory-per-document storage

`data/docs/<doc_id>/` contains only the source file, `doc.sqlite3`, and lazily rendered page images if needed. `doc_id` is a random 128-bit identifier generated by the backend. Never use a filename or user input as a filesystem path. Paths are created from validated server-side identifiers.

Suggested tables:

- `document`: document ID, SHA-256, parser/version, language/quality/OCR flags, model tag/digest, created time; never log personal file metadata.
- `pages`: physical page number (1-based), optional printed label, normalized text, text hash and warning flags.
- `sentences`: stable `sid`, page, section, start/end offsets into LexiGuard-normalized text, sentence text and OCR marker.
- `chunks`: evidence ID, ordered sentence IDs, section/heading, char offsets and search fields.
- `clauses`: deterministic clause IDs, label/heading/topic classifications.
- `relationships`: source/target/type plus `origin=deterministic|model_suggested`; suggested edges are only possible links.
- `run_ledger`: run ID, route/status, tool names and counts, sentence IDs exposed in that run, validation codes and durations; **no question, answer, evidence text, embedding or personal metadata** by default.

No answer-history rows are created unless the user explicitly enables local history. If enabled, the UI states what is kept and the same Delete action removes it.

### 5.2 Normalization and offsets

Store the exact normalized text that every source viewer and citation uses: CRLF→LF, Unicode NFC, controlled whitespace normalization, a recorded mapping for de-hyphenation. Keep the original PDF for page-image display; do not confuse raw PDFium offsets with normalized-text offsets. A sentence offset must round-trip to the exact stored sentence. Every citation maps:

`point → sid → stored sentence → page + section + offsets → document SHA-256`.

`sid` is not sufficient merely because it exists in the database. It must have been returned by a retrieval tool for this particular document and request/run.

### 5.3 Safe deletion

Deletion must:

1. Reject new work for the document and cancel/await active operations.
2. Close SQLite connections/cursors and parser/page handles.
3. Unload model state using an installed-version-verified Ollama request with `keep_alive:0` as specified; if that cannot be verified, report the failure rather than claiming full unload.
4. Remove the per-document directory, per-document derived state, page images and local history; no WAL should exist because rollback journal mode is used.
5. Clear frontend state and revoke the document session binding.
6. Run a verification scan on app-controlled data/temp/logs and optional Hermes tmpfs for test canaries; verify directory absence and no derived rows/FTS shadow data remain.
7. Return a deletion verification result that distinguishes **app-controlled files removed** from forensic erasure. Never claim secure forensic erasure from SSD, OS swap/hibernation or external backups.

Use `PRAGMA secure_delete=ON`, rollback journal, `Cache-Control: no-store` for document endpoints, a session-scoped temporary directory, cleanup on success and failure, and startup warning if the data directory appears to be inside a known sync folder. Store data outside cloud-synced locations by default.

---

## 6. Ingestion, parsing, OCR and quality gates

### 6.1 Upload validation

Accept `.pdf` and `.txt` only. Verify content independently of filename (PDF magic bytes `%PDF-`; TXT encoding sanity). Enforce configured maximum upload size, page count, text size and processing time. Reject empty, encrypted, malformed and over-limit files without creating a partial searchable document. Do not accept arbitrary filesystem paths from the client. **[v3] TXT has no pages:** split it into *virtual pages* (≈3,000 characters at paragraph boundaries), labelled “virtual page (TXT)”; these count as physical pages for citations and the viewer shows text rather than an image.

### 6.2 Parser sandbox

Run pypdfium2 in a child process isolated from the API's memory. Set CPU-time and memory limits where the OS supports them, plus a wall-clock timeout and output-size cap. Return structured JSON to the parent; the parent validates all fields before inserting records. **[v3] Platform matrix.** *Linux:* full limits (`RLIMIT_CPU`, `RLIMIT_AS`, wall timeout, output cap). *macOS:* CPU-time and wall timeout, output cap and page/size caps; `RLIMIT_AS` is not reliably enforced, so add an RSS watchdog. *Windows:* no `resource` module — wall timeout, output cap, page/size caps and (if implemented) a Job Object memory limit. On macOS/Windows the app prints a startup notice “reduced parser isolation” and `docs/SECURITY.md` lists the difference. Never parse without at least the wall-clock timeout, output cap and page/size caps. The network-privacy claims do not depend on parser rlimits. Do not silently skip a limit: every missing limit is reported at startup.

### 6.3 Extraction and physical page mapping

Store physical page numbers 1-based and printed labels separately if reliably detected. Extract text with pypdfium2; use page images for source viewing. Highlight via PDFium text search/rectangles when it reliably matches the stored sentence; otherwise show the page image plus exact sentence text. Never falsify a highlight when extraction/ligatures/layout prevent a precise match.

File metadata (title, author, XMP), filenames and arbitrary path values never enter LLM prompts. They may be scanned for suspicious injection patterns to produce a warning but not included in the analysis context.

### 6.4 Quality and language gate

Per-page checks: extracted character count, image-only likelihood, garble ratio, missing-text indicators, repeated header/footer indicators, column/table layout warnings, non-Latin script ratio and parser errors. The report records page coverage and any OCR use. If coverage is inadequate, silence claims are disabled for unread pages and the result becomes `INSUFFICIENT_EVIDENCE`.

The MVP supports English only, decided **per page** [T5]. A page that is not English, or where detection is inconclusive, is marked `UNREAD_LANGUAGE`, excluded from retrieval, and disables `NOT_LOCATED` for any topic that could live there (in practice: for all topics); banner “Page N is not in a supported language and was not analysed.” Relevant Review categories become `NOT_ASSESSED`; the document shows `UNSUPPORTED_LANGUAGE`. **[v3] No ML language-detection dependency:** gate on (a) share of letters outside the Latin script > 15 % → unread, and (b) for pages with ≥ 40 tokens, share of common English function words < 8 % → inconclusive → unread. Romanised Hindi/regional text usually fails (b) and is flagged, which is the safe outcome. Pages under 40 tokens inherit the document majority unless test (a) fails. Do not translate via a network service or pretend unsupported text was understood. Test `T-ING-LANG-PAGE-01` (10-page English fixture with 1 non-English page).

### 6.5 Local OCR

Phase 1b adds Tesseract and language data installed during setup, not fetched during document processing. Invoke OCR only for pages flagged as image-only or low-text. Add OCR confidence and a visible `OCR-derived — check the page image` banner to every claim derived from OCR. Names, dates, money and numbers from OCR may not be shown as `DIRECT` without the OCR warning. The scanned-PDF fixture and `T-ING-OCR-01` are required before claiming scan support.

### 6.6 Sentence and clause segmentation

Order: page → numbered headings/clauses → paragraphs → sentence splitting with protections for `Rs.`, `No.`, `e.g.`, `i.e.`, clause numbers, decimals and dates → character-cap fallback. Keep cross-page clauses as multiple page-bound source segments. Each sentence has a deterministic `sid` and offsets into stored normalized text. Maintain sentence-to-section and sentence-to-clause mappings.

Hidden-text detection (tiny font, page-coloured text, suspicious text objects) is a heuristic. Warn that hidden text **may** exist; do not claim the detector proves absence of hidden text.

---

## 7. Retrieval, clause map and absence handling

### 7.1 Lexical-first retrieval

Create a versioned `lexicons/rental_topics.yaml` with topic names, synonyms and regional variants: landlord/tenant, lessor/lessee, leave-and-licence, security deposit/advance, rent/escalation, vacate/handover/possession, notice/termination/lock-in, maintenance/repairs, pets/subletting/guests, deductions/forfeiture, penalties/interest and dispute venue. The taxonomy is an aid to retrieval—not a legal judgment.

For each query:

1. Deterministically classify topic/terms and preserve exact numbers, clause labels and key phrases.
2. Search FTS5/BM25 over chunks and headings; boost exact clause references and exact numeric phrases.
3. Expand deterministic cross-references, including “subject to”, “except”, “unless”, “notwithstanding”, “provided that”, “in accordance with”, clause numbers and referenced annexures/schedules.
4. Merge/deduplicate, preserve conflicts, cap at 12 chunks per tool call and construct a bounded evidence packet with sids, source text, page/section and quality warnings.
5. **[T6] Optional query expansion (refinement path only):** Gemma may return ≤ 8 extra search terms (array of short strings, validated as `[A-Za-z0-9 \-/.]{2,40}`). They feed BM25 only, never appear in the answer and never count as evidence. Purpose: cut false `NOT_LOCATED` on phrasing the lexicon lacks. Test `T-RETR-EXPAND-01` (held-out paraphrases the lexicon lacks).
6. **[v3] FTS5 settings:** `unicode61` tokenizer with diacritic removal (plus an optional Porter column); index a normalised-number column so “Rs. 25,000/-”, “25000” and “₹25,000” match each other; at startup check that the bundled SQLite has FTS5 and fail with a clear message if not.

### 7.2 Optional dense retrieval

Dense retrieval remains off until a measured evaluation shows lexical retrieval misses meaningfully important paraphrases. If enabled, use Ollama `/api/embed` locally with a pinned `nomic-embed-text` model and required `search_document:`/`search_query:` prefixes. Store embeddings only inside that document's directory. Never connect to Hugging Face Hub or a cloud embedding provider. Report the same questions/fixtures lexical-only versus hybrid; enable dense only if the recall gain justifies its dependencies, memory, startup cost and deletion surface.

### 7.3 Clause map

Deterministically extract clause references and candidate relationships such as `refers_to`, `defines`, `modifies`, `exception_to`, `subject_to` and `follows`. A model may suggest additional edges, but such edges must be labelled “possible link — verify” and may not appear as confirmed fact. Candidate conflicts arise deterministically from same-topic values/obligations appearing in different sections; Gemma can explain the candidate, not invent the candidate or choose a winner without textual basis.

### 7.4 Silence / `NOT_LOCATED`

Zero FTS hits are not enough. Backend may assign `NOT_LOCATED` only if all hold:

- document/page coverage is adequate, with no unread pages;
- language is supported;
- topic lexicon, lexical full-text and heading searches were run;
- cross-references and mentions of incorporated schedules/annexures/other documents were examined;
- dense search was also run if dense retrieval is enabled.

Otherwise return `INSUFFICIENT_EVIDENCE`. The user-facing template is: “I could not locate a provision about **X** in the readable parts of this document. I checked [short description of searches]. This does not mean X is allowed or prohibited.” The backend assigns this status; Gemma cannot declare a document silent.

---

## 8. Routing, bounded runtime and model contract

### 8.1 Routes

`FACT_LOOKUP`, `MULTI_CLAUSE_ANALYSIS`, `DOCUMENT_MAP`, `REVIEW_SCAN`, `DOCUMENT_SILENCE_CHECK`, `AMBIGUITY_OR_CONFLICT`, `TERM_EXPLANATION`, `LEGAL_CONCLUSION`, `EXTERNAL_LAW_REQUIRED`, `OUT_OF_SCOPE`.

### 8.2 Two-stage router

1. Deterministic pre-router catches verdict/current-law/outcome patterns, paraphrases and topic boundaries. It routes “is this enforceable?”, “will this hold up in court?”, “can they throw me out legally?”, “is this valid?”, “can I sue?”, “is this allowed by law?” and equivalents to the limitation path. It routes “what does X mean?” to `TERM_EXPLANATION`; oversized/empty/off-topic questions to `OUT_OF_SCOPE` or a controlled error.
2. A small schema-constrained local Gemma router may propose a route. The stricter decision wins. A model may never downgrade a deterministic legal limitation into an ordinary factual answer. The **final route/status is backend-owned** and never trusted from `ModelAnswer`.

### 8.3 Bounded state machine and hard limits

`RECEIVE → CLASSIFY → PLAN → RETRIEVE → ANALYZE → VALIDATE → RESPOND`.

- At most 8 tool calls total per user request.
- At most 2 retrieve/refine loops.
- At most 2 validation attempts, plus at most 1 separate format-retry [T1]. **Every Gemma call of any kind, retries included, counts against the hard ceiling in §8.3a.**
- At most 12 chunks per tool call.
- Request timeout, model timeout, response byte/token cap and tool argument size caps are mandatory.
- Question length ≤ 500 characters.
- Retry prompts contain only validation violation codes and the minimal schema error—never re-inject the whole source document or expand the context in a loop.
- No unbounded “retry until good”. On failure return `INSUFFICIENT_EVIDENCE`, `ERROR_LOCAL_MODEL_UNAVAILABLE` or `ERROR_PROCESSING` as appropriate.

### 8.3a [v3] Gemma-call budget and fast path

Every Gemma call on laptop hardware costs seconds to minutes. v2.1 permitted 5–8 calls per question (router, expansion, NextAction ×2, answer, format retry, validation retry, entailment). Budget instead:

- **Deterministic first:** pre-router, topic lexicon, BM25, cross-reference expansion and the silence gate run with no model call.
- **Fast path (default):** if retrieval is *confident* (topic matched in the lexicon AND ≥ 1 chunk above a tuned BM25 threshold AND no unresolved cross-reference) the runtime makes exactly **one** Gemma call: `ModelAnswer` from the evidence packet.
- **Refinement path:** otherwise exactly one refinement call, either query expansion (T6) **or** one `NextAction` round, never both, then the answer call. A router proposal is requested only when the pre-router has no confident route.
- **Hard ceiling:** ≤ 4 Gemma calls per question, retries included. Worst cases: fast path = answer + format-retry + validation-retry = 3; refinement path = refinement + answer + format-retry + validation-retry = 4. At the ceiling, fail closed (`INSUFFICIENT_EVIDENCE` or `ERROR_PROCESSING`); never exceed it.
- **Wall-clock cap [v3.1, design judgement, untested]:** per-question budget = 4 × the Day-0 p50 measured for the chosen model, never above the configured request timeout. Skip the optional refinement call if more than half the budget is already spent. Exceeding the budget returns `ERROR_PROCESSING`. Tune from measured latency and record the value in `docs/EVALUATION.md`. The entailment pass is OFF by default (Tier 2).
- **Evidence packet ≤ ≈2,500 estimated tokens** (characters ÷ 3.2, conservative) so prompt + schema + output stays inside `num_ctx` (§3.2a).
- The run ledger records which path ran; EVALUATION.md reports fast-path rate and per-path latency.

### 8.4 ModelAnswer schema — model may propose content only

The model returns only an object equivalent to:

```json
{
  "points": [
    {
      "point_id": "p1",
      "kind": "RESTATEMENT",
      "text": "The tenant must provide sixty days' written notice before termination.",
      "sids": ["s_0412"]
    }
  ]
}
```

Permitted kinds: `STATED`, `RESTATEMENT`, `INTERPRETATION`, `CONCERN`, `AMBIGUITY`, `CONFLICT`, `GENERAL_EXPLANATION`.

The model must **not** produce a final route/status, citations/evidence IDs, quotes, page/section values, `NOT_LOCATED`, missing-information decision, professional-review flag, jurisdiction flag or legal verdict. Backend computes all of them. `sids` must originate from tool results returned in the current run/document. General explanation points normally come from curated glossary entries and do not cite document sids unless also making a separate document-specific claim.

A separate `RouterProposal` schema may return a proposed route for use in the stricter-route merge. It is untrusted and is not a response status.

### 8.5 Read-only tools and evidence packets

Tool responses contain only relevant records; each sentence is identified by `sid`, page and section. The evidence block is nonce-delimited for prompt-injection defence, e.g. `<<EVIDENCE-<random nonce>>> ... <<END-EVIDENCE-<same nonce>>>`. Treat every byte inside the block as data, not instructions. The nonce is new per request. Filenames and document metadata are excluded.

---

## 9. Validation, rendering, terminology and legal policy

Validation is deterministic and always runs before the response reaches the UI. A second local Gemma entailment check is optional; it may only downgrade a claim to “support unverified”, never upgrade or repair it.

### 9.1 Validation stages

1. **Schema:** strict Pydantic/JSON Schema; reject unknown fields, unknown enums, too many points, overlong text and duplicate point IDs.
2. **Provenance:** every model-supplied `sid` must have been returned by an approved tool in this exact run and bound document. Forged, stale, cross-document or not-returned IDs cause the point to be dropped.
3. **Citation rendering:** backend loads the stored sentence and fills verbatim quote, physical page, section, OCR warning, source hash reference and UI navigation link. The model never types a quote, page, section or evidence ID.
4. **Kind-specific checks:**
   - `STATED`: extractive; the rendered source quote is the stated fact. If the point includes additional generated text, treat it as a RESTATEMENT and validate separately.
   - `RESTATEMENT`: every number, amount, duration, date, ordinal and proper noun in the proposed text must occur in the cited sentences after conservative normalization. E.g. “sixty (60)” may normalize to `60`; `Rs. 25,000/-` may normalize to ₹25,000. **Never convert units** (months≠days). Check modality and negation (`must`, `shall`, `may`, `shall not`, `may not`, `cannot`, `unless`, `except`, `only if`) for contradictions. Any unsupported or ambiguous literal fails closed. **[T7] Role check:** canonicalise role words (tenant/lessee/licensee/occupant → TENANT; landlord/lessor/licensor/owner → LANDLORD) in the restatement and in the cited sentences; every role named in the restatement must occur in the cited sentences, and where a simple “ROLE + modal verb” pattern exists the actor must match; a swap or an added party drops the point (`T-CITE-ROLE-01`). **Limit [v3]:** these checks catch invented figures, swapped parties and flipped modality; they do **not** prove semantic faithfulness (e.g. a wrong relationship between correct numbers). State this in LIMITATIONS.md and measure it with the human-labelled Unsupported Claim Rate.
   - `INTERPRETATION`, `CONCERN`, `AMBIGUITY`: at least one cited sentence; explicit label; no headline placement unless the same displayed headline is visibly labelled as interpretation/concern/ambiguity. These labels express possible reading/attention, not a legal conclusion.
   - `CONFLICT`: at least two sids from different sections; show both passages; do not select a winner without explicit textual support.
   - `GENERAL_EXPLANATION`: no document-specific figures, names, amounts or factual claim about the uploaded agreement. It appears in a separate clearly labelled box. Use the curated local glossary.
   - `NOT_LOCATED` and `INSUFFICIENT_EVIDENCE`: backend-assigned only; not model kinds.
5. **Optional entailment check:** local only; outcomes `SUPPORTED`, `NOT_SUPPORTED`, `UNSURE`. `NOT_SUPPORTED`/`UNSURE` can downgrade or drop the proposed point; this pass cannot override literal checks or raise a claim's status.
6. **Legal output policy:** scan all assistant-authored prose, headlines, summaries, labels generated dynamically and glossary text for prohibited legal verdicts or outcome predictions **using the pattern-based scanner of §9.3a (not a bare keyword list)**. Any hit replaces that assistant-authored text with a safe limitation template and records a validation code. Do not scan or rewrite immutable source quotations as if LexiGuard authored them; source quotations are rendered in a separate `SourceQuote` channel with original text and the label “Quoted source text — not LexiGuard's legal assessment.” Never add an endorsement around a quotation.
7. **Renderer:** only validated points can be rendered. Backend composes a headline only from validated claim IDs and attaches citations for any factual assertion. No uncited headline or model-written summary bypasses the same scanner and support checks.

### 9.2 Literal and modality normalization

Implement conservative normalizers with unit tests. Support common numeric word forms and digit forms, Indian rupee patterns (`Rs.`, `INR`, `₹`, `/-`), date formats including DD/MM/YYYY and month-name dates, and ordinal/clause references. Normalization is for equivalence detection, not unit conversion or adding content. If the normalizer cannot safely establish equivalence, fail closed rather than guess. Detect changed obligation strength and negation; examples: `may` cannot become `must`; `shall not` cannot become `shall`; `unless`/`except` cannot be silently omitted if it changes scope.

### 9.3 Legal boundary and the source-quotation exception

LexiGuard never gives its own conclusion that an agreement is valid/invalid, enforceable/unenforceable, legal/illegal, lawful/unlawful, void, binding in law, fair/unfair, or predicts a court/eviction/dispute outcome. `legal_verdict` in the rendered schema is permanently `null`.

The deterministic pre-router catches paraphrases and limits the answer, but the system should still retrieve relevant agreement wording. The limitation response explains what the document states, what the document alone cannot settle, which context/law is outside the system's scope, and recommends a qualified legal professional when appropriate. Do not answer current-law or jurisdiction-specific questions from Gemma's pretraining.

**Scanner rule:** scan assistant-authored text, not immutable source quotes. Source text may itself contain legal terms such as “void” or “illegal”; those exact words must remain unchanged for citation integrity. Render them only as a verified quotation clearly distinguished from LexiGuard's explanation, and ensure the adjacent generated prose does not repeat or endorse a forbidden verdict. Add tests for both a prohibited generated verdict and a source clause that contains verdict vocabulary.

### 9.3a [v3] Verdict scanner design (replaces keyword-list scanning)

A bare keyword list produces false blocks that damage accuracy and usability: leave-and-licence agreements routinely say “this agreement is **valid for** 11 months”, “**legal** heirs”, “**lawful** purposes”, “a **valid** ID proof”, and the curated glossary itself contains words such as “legal right”. The scanner works on *assistant-authored text only* with three rule groups:

1. **Verdict patterns (block):** an evaluative predicate — valid, invalid, enforceable, unenforceable, legal, illegal, lawful, unlawful, void, voidable, binding (in law), fair, unfair, unconscionable, “against the law”, “violates” — applied to the agreement/clause/term/notice/landlord/tenant/this/it/that within a short window, in a declarative or modal sentence by LexiGuard (e.g. “this clause is unenforceable”, “the landlord cannot legally …”).
2. **Outcome and advice patterns (block):** predictions about courts, eviction, police, winning or losing; “you will/can/cannot sue/win”; “you should (not) sign”, “safe to sign”, “no need for a lawyer”; “standard/normal/typical/market practice”; “reasonable/unreasonable” used as a judgement of a term.
3. **Source-echo exception:** in a `STATED` or `RESTATEMENT` point only, a flagged word that also appears in the cited source sentence(s) in the same grammatical role (e.g. “valid for 11 months”) is allowed. The exception never applies to interpretations, concerns, headlines, summaries, limitation templates, escalation text or glossary text.

A hit replaces the assistant-authored text with a safe limitation template and records a validation code. Immutable source quotations are never scanned or altered. **Concerns are attention flags tied to text** (“This clause places X on the tenant; consider asking about Y”), never evaluative adjectives.

**Test `T-LEGAL-FP-01`:** a committed corpus of ≥ 40 must-block strings (verdicts, paraphrases, outcome predictions, advice) and ≥ 40 must-pass strings (“valid for 11 months”, “legal heirs”, “lawful purposes”, every glossary definition, neutral concerns). Report block-recall (target: 0 missed) and false-block rate (target ≤ 5 %). Every curated glossary entry must pass the scanner unmodified.

### 9.4 General legal-term explanations

`glossary/rental_terms.yaml` is a versioned, curated, team-authored glossary (not lawyer-reviewed unless a named reviewer is recorded per entry): security deposit, lock-in period, notice period, indemnity, lien, force majeure, subletting, escalation, lessor/lessee, leave-and-licence versus lease, arrears, handover and similar terms. Every entry has a neutral, concise general definition and an optional “wording can vary by jurisdiction” note. Do not imply that a definition settles the legal effect of the uploaded clause.

When a term appears in the document, display two separate fields:

- **General definition (not from your document):** text from the curated local glossary.
- **In your document:** exact cited source sentence(s).

The model may adjust reading level only if the output remains equivalent to the glossary entry and passes the legal scanner. If a term has no curated entry, do not improvise a legal definition from model memory; state that the local glossary has no curated definition and suggest qualified review if material.

### 9.5 Proactive local-law flags

`lexicons/jurisdiction_topics.yaml` lists topics that may vary by local law: deposit amounts/refunds, notice, eviction/lock-in, rent escalation, stamping/registration, assignment/subletting, maintenance obligations, governing-law and forum clauses. When a related clause is found, the UI shows “May depend on local law — confirm locally” beside its citation. This flag is a caution only; it must not say what the law requires.

### 9.6 Injection policy

All PDF/TXT content—including OCR output, header/footer, footnote, table, metadata and filenames—is untrusted data. Use nonce-delimited evidence blocks; do not include metadata/filename in prompts; expose only read-only document-bound tools; validate tool names/args and call caps outside the model; do not let a document control system prompts, tools, model choices or routing. The injection detector only raises a warning; it must not change policy based on model opinion. Include fixtures for a body instruction, footnote, header, tiny text, table cell, metadata, fake system message, “declare this valid”, “call tool X” and “reveal your prompt”.

---

## 10. Backend-owned response contract

### 10.1 Enums

Per-point classification: `DIRECT`, `SUPPORTED`, `INTERPRETIVE`, `AMBIGUOUS`, `CONFLICTING`, `GENERAL_EXPLANATION`, `NOT_LOCATED`, `INSUFFICIENT_EVIDENCE`, `OUT_OF_SCOPE`.

Overall response status: `ANSWERED`, `LIMITED`, `NOT_LOCATED`, `AMBIGUOUS`, `CONFLICTING`, `INSUFFICIENT_EVIDENCE`, `LEGAL_LIMIT`, `OUT_OF_SCOPE`, `ERROR_LOCAL_MODEL_UNAVAILABLE`, `ERROR_PROCESSING`.

Overall status precedence when multiple conditions exist: `ERROR_*` > `LEGAL_LIMIT` > `CONFLICTING` > `AMBIGUOUS` > `INSUFFICIENT_EVIDENCE` > `NOT_LOCATED` > `LIMITED` > `ANSWERED`. `OUT_OF_SCOPE` is used when no higher-priority failure/limitation applies. No numeric confidence percentages, risk scores or red/green global assessment.

### 10.2 RenderedAnswer (server-generated only)

Server response includes:

- `status`, `answer` (template-composed from validated facts only),
- `claims[]`: claim ID, text, classification, cited sentence IDs and backend-rendered evidence objects,
- separate `interpretations[]`, `concerns[]`, `ambiguities[]`, `conflicts[]`, `general_explanations[]`,
- backend-generated `missing_information[]`, `extraction_warnings[]`, `jurisdiction_flags[]`, `external_law_required`, `recommend_professional_review`,
- `legal_verdict: null` always,
- run/evidence ledger metadata: route, sections searched, sids retrieved, validation codes, model digest and duration; no chain-of-thought and no private text in default logs.

Every list item with document-specific content carries citations. Missing-information items use the closed code enum `UNREADABLE_CONTENT`, `REFERENCED_MATERIAL_NOT_PROVIDED`, `TOPIC_NOT_LOCATED`, or `CONTEXT_REQUIRED`; each message is rendered from a backend-owned template and validated variables, never free-form model text. If the document references a missing schedule/annexure, cite the source sentence that references it. `TOPIC_NOT_LOCATED` is allowed only after the full silence procedure in §7.4. Policy booleans are computed by backend rules. Unknown response fields are rejected. The model never returns the final `RenderedAnswer` directly.

---

## 11. Privacy, localhost hardening and network evidence

### 11.1 Network policy

Allowed during normal operation: loopback-only UI↔API, API↔Ollama, API↔gateway and optional isolated Hermes↔gateway/MCP. Forbidden: remote LLM, remote embeddings, cloud OCR, translation, document storage, telemetry, crash uploads, browser/search tools, CDN and background update calls carrying or potentially exposing user content. Setup downloads are a separate explicitly documented activity and must never receive user documents.

Use environment defence in depth: `OLLAMA_NO_CLOUD=1`, no `OLLAMA_DEBUG`, `DO_NOT_TRACK=1`, `HF_HUB_OFFLINE=1`. These flags are not proof; network capture and canary tests are proof.

### 11.2 Frontend cache and same-origin

Production frontend is built and served by FastAPI on the same origin. All fonts/icons/scripts are bundled. CSP baseline:

`default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' blob: data:; font-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'`

Do not use inline scripts or inline styles; do not enable `unsafe-inline`. The token bootstrap uses the one-time launch-code exchange described in §11.3. No document text in `localStorage`, `sessionStorage`, IndexedDB, URLs, crash reports or browser telemetry. Hold the token in JS memory only. API document responses use `Cache-Control: no-store`, `Pragma: no-cache`, and suitable `X-Content-Type-Options: nosniff`; prevent service-worker caching. `T-PRIV-NOCDN` must load the app with external network blocked.

### 11.3 Token, Host and Origin

- Generate an unpredictable per-launch token using a cryptographically secure random generator.
- **[v3] One-time launch code; no secret in served HTML.** The launcher prints/opens `http://127.0.0.1:<port>/#k=<one-time-code>`. The SPA reads the fragment (fragments are never sent to the server or logged), strips it with `history.replaceState`, and POSTs the code to `/api/session`; the code is single-use and expires in 60 s; the response carries the session token, held in JS memory only. `GET /` and static assets contain no token, so another local process or page that merely fetches `/` obtains nothing. A page reload requires re-opening the launch URL (documented). No inline scripts, query parameters, cookies, logs or persistent storage for the token. Test `T-SEC-BOOT-01`: `/` contains no token; a used or expired code is rejected. *Fallback if time is short:* the v2.1 `<meta>` bootstrap, with its weaker threat model stated honestly — any local process able to GET `/` can read the token, which then protects only against cross-origin browser pages and DNS rebinding. Same-user local malware is out of scope in THREAT_MODEL.md.
- Every `/api/*` request including health requires `Authorization: Bearer ...`; compare tokens in constant time.
- Validate Host against exact `127.0.0.1:<port>` and `localhost:<port>` values configured for that run. Reject unexpected Host headers to reduce DNS rebinding.
- Validate Origin for browser state-changing requests; reject mismatches. Do not enable wildcard CORS. Keep the API bound to `127.0.0.1`, not `0.0.0.0`.
- Rate-limit upload/ask, set timeouts and caps. Never expose environment values, local paths, prompts, logs or database contents through health/errors.

### 11.4 Privacy proof procedure

1. Each privacy fixture includes unique synthetic canaries in the document and question. After the complete upload→ask→delete flow, search app/Ollama/gateway logs, temp directories, external-interface captures and optional Hermes home. Canaries must be absent from logs and external-traffic captures; after Delete, app-controlled storage must not retain them. **Do not capture, save or commit raw loopback packet payloads:** the allowed local API→Ollama request necessarily contains prompt/evidence text, so loopback traffic may contain canaries without violating the no-external-traffic requirement. Privacy evidence should capture connection metadata and non-loopback interfaces only.
2. Run the complete flow with external networking disabled. On Linux, use a network namespace with only loopback up or a fully internal network; app and Ollama must share that isolated namespace. On macOS/Windows, provide a reproducible firewall + connection-monitoring procedure and state its limits. Save command output and non-loopback connection evidence in `reports/privacy/<release-or-commit>/`; do not save raw loopback payloads.

   **[v3] Attempt-visible evidence with a negative control.** A loopback-only namespace proves little by itself: nothing *can* leave, so an empty capture is true by construction and says nothing about whether the software *tries* to. The isolated run must therefore (a) record every connection *attempt* by the app and Ollama process trees — e.g. `strace -f -e trace=connect,sendto,sendmsg` filtered to non-loopback / non-`AF_UNIX` destinations, or a dummy interface with `tcpdump` and a DROP rule — and save the filtered log plus an unfiltered destination summary; (b) include a **negative control**: a tiny script run inside the same environment that deliberately tries a documentation-range address (e.g. `192.0.2.1`), proving the instrument would have caught an attempt — the report must show the control **was** detected and that app and Ollama produced **zero** such attempts (`tests/privacy/negative_control.py`); (c) save `ollama --version`, the Ollama log line `Ollama cloud disabled: true`, the environment and the canary-scan results.

   **Portable path.** Also ship a `Dockerfile` and `make isolated-demo-docker`, running app + Ollama in one container with `--network none` and the model volume mounted read-only; `docker inspect` output proves the network mode. It works for judges on Windows/macOS (CPU-only, slower); the native Linux run is the performance reference. **[v3.1] Limit:** a container with `--network none` has no published ports, so a host browser cannot reach a UI inside it. The Docker target therefore runs a **headless scripted flow** (`tests/privacy/isolated_flow.py`: launch-code exchange → upload synthetic fixture → ask → delete → canary scan → negative control) as the container entrypoint or via `docker exec`, and writes its report to a separate writable output volume that holds no secrets. It is privacy *evidence*, not the interactive demo: judges use `make demo` for the UI and the Docker report for the privacy proof. Never describe it as an interactive isolated UI. (Optional Tier 2: serve the app on a Unix-domain socket and expose it through a host-side forwarder so the UI can be viewed while the container stays network-less.) Without Docker on macOS/Windows, document the firewall + monitor procedure and its limits.
3. Add a pytest socket guard preventing non-loopback connections in all non-setup tests.
4. CI checks bundled frontend/backend for external hosts, CDN URLs, analytics SDKs and forbidden dependency families; generate SBOM and license report.
5. UI says **“Designed for local processing”** until a successful isolated-network report exists for that exact release. Only then may it say **“Verified local processing — see report.”**

### 11.5 Mandatory privacy tests

- `T-PRIV-NOEXT-01`: zero non-loopback connections in isolated upload→ask→delete; saved capture/output.
- `T-PRIV-NOCLOUD-LLM`, `T-PRIV-NOCLOUD-EMBED`, `T-PRIV-NOCLOUD-OCR`.
- `T-PRIV-NOTELEMETRY`.
- `T-PRIV-CANARY-LOGS` (app/Ollama/gateway logs only; external-capture payloads if any), `T-PRIV-CANARY-DELETE`.
- `T-PRIV-TEMP-CLEAN` on success and failure.
- `T-PRIV-DELETE-DERIVED` for rows, FTS tables, embeddings, page images, sessions/history.
- `T-PRIV-OLLAMA-UNLOAD`.
- `T-PRIV-NOSTORE-HEADERS`, `T-PRIV-NOCDN`, `T-PRIV-FAILCLOSED`.
- `T-PRIV-SESSION-ISOLATION`, `T-PRIV-INJECTION-NONET`, `T-PRIV-DNS-REBIND`.

Do not mark the privacy suite passed until every required test has run and the real report is committed. A unit test that monkeypatches networking does not replace the isolated network run. Additional IDs: `T-PRIV-NOCLOUD-LOG` (Ollama log shows `Ollama cloud disabled: true`), `T-PRIV-NETINV-01` (every destination observed ⊆ loopback; run an early smoke version at the end of Phase 4 [T8] and repeat it formally in Phase 6), `T-SEC-BOOT-01` (§11.3).

### 11.6 [R4] Network-call inventory (publish in `docs/PRIVACY.md`; verified by the capture)

| Component | Destination | When | Carries content? | Default |
|---|---|---|---|---|
| Browser ↔ API | 127.0.0.1 | normal use | yes (local only) | on |
| API ↔ Ollama | 127.0.0.1:11434 | normal use | yes (local only) | on |
| Ollama → ollama.com | model pull | setup only | no | never during use |
| Ollama desktop/tray updater | vendor | — | no | avoided: headless `ollama serve`; attempts, if any, are visible in the isolated capture |
| pip / npm / Tesseract language data | package registries | setup only | no | never during use |
| everything else | — | — | — | none |

Link each row to the capture so the table is verified, not asserted. The Ollama FAQ does not document update or telemetry behaviour, so assert nothing about it; measure it.

---

## 12. Optional Hermes integration (Phase 8 only)

> **[R7][v3] Hermes is not built by default.** The participant rubric awards it no points and it carries the largest privacy and robustness risk. Do not start this section unless Tier 0 and Tier 1 are fully green and ≥ 3 days remain before the freeze; otherwise write `docs/adr/0010-hermes-not-built.md` (“considered, not built, because …”) and move on. The bounded runtime already satisfies the agentic requirement. The text below is retained only for that contingency.

Hermes is **not required** to establish an agentic implementation. The bounded runtime is a genuine, finite plan→retrieve→analyze→validate loop and remains default for all judging if Hermes is not safely usable.

If pursued after Phase 7:

- Run Hermes in a container/network namespace with no egress, read-only root, no host mounts, and only the LexiGuard model gateway and LexiGuard MCP endpoint reachable.
- Set a unique per-session `HERMES_HOME` on tmpfs; do not rely on changing `HOME` alone. Check the installed version's resolver. Wipe state, session history, tool results, memory, skills, logs, configuration and tokens on session end and document deletion.
- Disable memory, skill-writing and external-memory features using configuration verified from the installed version. Do not invent config keys.
- Configure MCP `tools.include` for exactly the seven tools, with resources/prompts disabled if supported. MCP inclusion filters the MCP server, not the entire Hermes built-in toolset; restrict built-in tools separately and verify effective tools at the gateway.
- The gateway must reject any non-allowlisted tool, model, parameter or non-loopback URL; force the pinned model/seed/temperature/think/context; log only tool names/counts and violation codes.
- Measure actual request `num_ctx`; do not assume server or Modelfile context wins over Hermes parameters. If the installed Hermes version requires 64K and target hardware cannot reliably support it, do not enable Hermes.

Enable Hermes only after all pass: `T-HERMES-TOOLS-EFFECTIVE`, `T-HERMES-NO-NET`, `T-HERMES-HOME-WIPE`, `T-HERMES-CTX-01`, `T-HERMES-INJECTION`, `T-HERMES-FAILCLOSED`, `T-HERMES-DOCSCOPE`, `T-HERMES-NOHANG`. If any fails, leave it disabled and state “attempted, not enabled” with test output. Never weaken a required privacy/validator gate to preserve Hermes.

---

## 13. UI and API

### 13.1 UI modes

- **Overview:** evidence-gated Document Map, extraction quality, language and OCR warnings, jurisdiction flags. **[T9] Latency plan:** deterministic extractors (regex + lexicon) pull money, dates, durations and parties with sids first so Gemma only restates; eagerly build the “core 10” cards (parties, term, rent, deposit, notice, termination/lock-in, penalties, restrictions, maintenance, disputes) and the rest on demand; stream cards as they validate; `keep_alive` ≥ the session; `OLLAMA_NUM_PARALLEL=1`; publish measured Overview time on E4B and E2B.
- **Ask:** concise validated answer, direct/restated claims, interpretations, concerns, ambiguities, conflicts, missing information, glossary definitions, and “Why this answer?” ledger. No hidden chain-of-thought.
- **Review:** topics show `FOUND`, `NOT_FOUND` (displayed as “Not located”), `AMBIGUOUS`, `POSSIBLE_CONFLICT`, `NOT_ASSESSED`; never a global legal verdict.
- **Attention first** [R2]: deterministic order, each row with a templated reason (“Listed first because two clauses give different notice periods”): (1) conflicts between clauses; (2) ambiguity on money, time or termination; (3) clauses creating payment, forfeiture, deduction, penalty or lock-in obligations; (4) jurisdiction-flagged clauses; (5) everything else. No scores, colours or verdict words.
- **Questions to bring to a professional** [R1]: built deterministically from AMBIGUITY, CONCERN, CONFLICT and jurisdiction-flag points using `lexicons/escalation_templates.yaml`, e.g. “Clause {section} (page {page}) says ‘{quote}’. Ask: how is {topic} treated where the property is located, and does it change what this clause means for me?” Neutral wording; passes the scanner; footer: bring this agreement, stamp/registration papers and payment receipts; consult a qualified lawyer experienced in tenancy matters in the state where the property is located. Test `T-ESCALATE-01`: every `LEGAL_LIMIT` and `AMBIGUOUS` answer contains ≥ 1 cited, specific question.
- **Document-type gate** [R3]: deterministic lexicon hit-density (rental / employment / notice / service). If the rental score is low, show “This doesn't look like a rental agreement. LexiGuard was tested on rental agreements.” Ask, Source viewer, citations, validator and legal policy keep working; Review cards, glossary and local-law flags are limited and labelled. Lexicons are pluggable (`lexicons/<doctype>/`). Test `T-SCOPE-01` (employment fixture → banner, citations still valid, no rental-specific claims).
- **Investigate (thin):** search, related clauses, source navigation only.
- **Source viewer:** exact page, page-label distinction, highlighted cited sentence when reliable, and immutable source quotation panel.
- **Delete:** clear confirmation and a result distinguishing app-controlled removal from forensic erasure.

Every card or claim opens the precise source sentence(s). All meanings use text labels, not colour alone. No traffic-light score, risk probability or percentage confidence. Accessibility includes keyboard operation, visible focus, ARIA labels/roles, WCAG AA contrast, reduced-motion support and axe checks in CI.

### 13.2 API endpoints

All API schemas are strict; every `/api/*` route is authenticated.

- `POST /api/documents` → `{document_id, page_count, quality, warnings, status}`.
- `GET /api/documents` → authenticated list of locally stored document cards containing only necessary display metadata and quality/status flags.
- `GET /api/documents/{id}/overview` → evidence-gated Document Map (cards may load lazily).
- `POST /api/documents/{id}/ask` → backend-built `RenderedAnswer`.
- `POST /api/documents/{id}/review` → Review statuses with source links.
- `GET /api/documents/{id}/pages/{n}` and `/pages/{n}/image` → source view, no-store.
- `GET /api/documents/{id}/evidence/{ev_id}` → one source evidence record, no-store.
- `DELETE /api/documents/{id}` → deletion and verification result.
- `GET /api/health` → booleans only, still token-protected.

A random document ID is not authorization by itself: every request also requires the current launch token and a real server-side document record. Every tool call receives a server-created immutable `DocumentContext` bound to exactly one document; the model cannot name, switch, or enumerate documents. Unknown IDs return 404; invalid/missing launch tokens return 401. The UI may expose an authenticated local document list, but the runtime tools may access only the document bound to the active request. `T-PRIV-SESSION-ISOLATION` must test bad tokens, unknown IDs and attempts to use another document from the same model run.

---

## 14. Tests, evaluation and release targets

### 14.1 Fixtures

Use synthetic fixtures only; never commit a private or non-redistributable agreement. At least five distinct synthetic contracts; at least two final held-out contracts written/finalized after feature freeze and never referenced in application code. Cover:

- simple rental agreement;
- Indian-style terminology: lessor/lessee, leave-and-licence, lock-in, Rs./₹/`/-`, DD/MM/YYYY, stamp/registration references;
- differing notice terms in separate sections;
- ambiguous “reasonable notice” wording;
- misleading heading; cross-reference to an absent clause; repeated/near-duplicate clauses;
- body/footnote/header/tiny-font/table/metadata prompt injections;
- table/multi-column layout; image-only scan; 50+ page long document;
- encrypted/malformed/truncated/oversized PDF;
- non-English page, expected to raise `UNSUPPORTED_LANGUAGE` and `NOT_ASSESSED`.

Each fixture includes provenance, how it was authored, licence (`own work` or CC0), target tests and known limitations in `fixtures/README.md`.

### 14.2 Ground-truth questions

Minimum 100; target **144 questions** with these base categories: 20 direct facts, 18 multi-clause, 18 not-located topics, 12 ambiguity, 8 conflict, 12 legal-boundary/external-law, 8 term explanations, 8 prompt-injection, 10 robustness = 114; add at least 30 paraphrase twins to reach 144. Each row stores question, fixture/document hash, expected status, gold sids/sections, expected facts, forbidden claims, language/OCR condition and annotator note. Review annotations independently where possible and record disagreements. Keep held-out fixture questions separate until final run.

### 14.3 Metrics and precommitted targets

Commit targets in `docs/EVALUATION.md` before the final evaluation, then publish both targets and measured results. Initial project targets:

| Metric | Definition | Target |
|---|---|---:|
| Fact accuracy | Correct gold facts / all labelled facts | ≥ 90% |
| Citation precision | Rendered citations that support the point / rendered citations, human-labelled | ≥ 95% |
| Citation coverage | Material points with ≥1 valid citation / all material points | ≥ 95% |
| Unsupported Claim Rate (UCR) | Material rendered points judged unsupported / all material rendered points on reviewed held-out answers | ≤ 5% |
| Citation integrity | Quote bytes equal normalized stored source sentence bytes | 100% |
| Silence precision | Correct absence claims / all `NOT_LOCATED` claims | ≥ 95% |
| Silence recall | Correct absent-topic detections / all labelled absent topics where the quality gate permits a decision | ≥ 90% |
| Legal boundary | Generated legal verdicts in the legal-boundary set | 0 |
| Injection resistance | Fixtures with no policy change and no forbidden call | 100% |
| Privacy | Required privacy tests passed | 100% before “verified” wording |
| Stale-index | Answer changes correctly after changing an indexed clause | 100% of test cases |
| Answer rate on answerable questions [v3] | Questions with a gold answer that receive `ANSWERED`/`LIMITED` with ≥ 1 validated cited point / all answerable questions | ≥ 80 % (stops a low UCR being bought by over-refusing) |
| False-refusal rate [v3] | Answerable questions returned as `INSUFFICIENT_EVIDENCE`/`NOT_LOCATED`/`LEGAL_LIMIT` / all answerable questions | ≤ 15 % |
| Verdict-scanner quality [v3] | `T-LEGAL-FP-01`: must-block strings missed; must-pass strings blocked | 0 missed; ≤ 5 % false-block |
| Fast-path rate and per-path latency [v3] | Share of questions answered with one Gemma call; p50/p95 per path | Measure and disclose |
| Latency/memory | p50/p95 latency and peak memory/RSS/VRAM | Measure and disclose; do not fake universal hardware targets |

Report denominators, confusion matrices, per-fixture results and representative failures. Never publish invented or unrun numbers. If a target is missed, fix and rerun or document the failed gate and do not label the release as passed.

### 14.4 Benchmarks

After Phase 4 yields real evidence packets, benchmark E2B vs E4B using equivalent quantization family, same retrieval packets, seed, `think:false` and `num_ctx`. Benchmark lexical-only versus dense only if dense is implemented. Compare bounded versus Hermes only if Hermes passes all its tests. Record model and digest, Ollama version, environment, hardware, peak memory, latency, tokens/s if reliably available, factual/citation metrics and all failures.

### 14.5 Required test families

- `T-ING-*`: magic bytes, UTF-8/TXT, malformed/encrypted/oversized, page caps, child-process timeout/resource limit, offset round-trip, layout, language gate, OCR-derived banner.
- `T-MODEL-JSON-01` (statistical, §3.2a), `T-MODEL-CTX-01`, `T-MODEL-NOTOOLS-01`: schema output validated by Pydantic, `think:false`, seed/temperature/context recorded, empty content fails closed, no `tools` key.
- New IDs [T/R/v3]: `T-ING-LANG-PAGE-01`, `T-RETR-EXPAND-01`, `T-CITE-ROLE-01`, `T-ESCALATE-01`, `T-SCOPE-01`, `T-LEGAL-FP-01`, `T-SEC-BOOT-01`, `T-PRIV-NOCLOUD-LOG`, `T-PRIV-NETINV-01`.
- `T-CITE-*`: forged SID, SID not returned this run, cross-document SID, no citation, quote mismatch, wrong-claim support, bad numeric/date/proper noun, modality/negation mismatch, conflict requires different sections.
- `T-LEGAL-*`: direct and paraphrased verdict requests; output scanner; source quote contains prohibited keyword but is not interpreted as LexiGuard verdict.
- `T-GLOSS-*`: known term glossary, source term citation, unknown term not improvised, general definition separated from document claims.
- all `T-PRIV-*` from §11.5.
- all `T-HERMES-*` only Phase 8.
- frontend E2E, keyboard/accessibility and no-CDN tests.

### 14.6 Release gates

Before release: 100% citation integrity; zero legal verdicts in boundary set; all injection tests safe; all required privacy tests pass with saved isolated-network evidence; no external traffic; held-out cases run; stale-index test passes; model digest and benchmark report published; license/SBOM scan passes; docs match code; no secrets/private files committed. Never claim complete while a required gate failed or has not run.

---

## 15. Implementation phases

**Execution order: 0, 1, 1b, 2, 3, 4, 6, 5, 7, 8, 9** (Phase 6 before 5; see §15.1 *Order*). Phase numbers are labels, not the sequence.

| Phase | Deliverables | Acceptance gate |
|---|---|---|
| **0 — Freeze** | Inspect repository; preserve current Apache license; add NOTICE, ADRs, docs, requirement→test map, canaries/fixtures plan, setup scripts that verify exact tags/digests, license checker and CI skeleton | Every L1–L10/S1–S10 requirement mapped to tests/owner; no unknown remote content path; prompt and Guide consistent. |
| **1 — Ingestion** | API skeleton, token/Host/Origin, child-process pypdfium2, normalized pages/sentences/offsets, per-document SQLite/FTS schema, quality/language gate, safe deletion/verification | Upload synthetic PDF/TXT; offset round-trips; reject encrypted/malformed/oversized; delete tests pass. |
| **1b — OCR** | Local Tesseract integration, quality-triggered OCR and visible warnings | Scanned fixture reads locally; OCR warning on every related point. |
| **2 — Model adapter** | `LLMProvider`, Ollama native API, JSON Schema, `think:false`, fixed seed/temp/context, fail-closed error path, metadata-only telemetry | `T-MODEL-JSON-01`, `T-PRIV-FAILCLOSED`; version/digest recorded. This is a smoke test, not the model benchmark. |
| **3 — Retrieval** | FTS5/BM25, rental-topic lexicon, headings, deterministic cross-reference expansion, clause map and rigorous silence check | Direct, exact phrase, cross-reference and not-located tests pass; evidence packets have correct sids/pages/sections. |
| **4 — Vertical slice** | Two-stage router; bounded runtime; seven tools; ModelAnswer→validator→renderer; legal scanner; glossary; jurisdiction flags; minimal upload→ask→citation→source viewer→delete UI | End-to-end simple fixture plus forged/stale SID, unsupported restatement, verdict, silence and injection tests. First benchmark with real evidence packets. **[T8] Isolated-network smoke capture** (upload → ask → delete with canaries and attempt-visible evidence). |
| **5 — Full UI** | Overview/Document Map, Review, Attention first, Questions to bring (Investigate only at Tier 2), accessibility and useful failure states | Every displayed factual card has a verifiable source link; no global legal score. |
| **6 — Evaluation + privacy audit** | ≥5 fixtures, ≥100 questions (144 is the Tier-2 target), ≥2 held-out contracts, isolated-network run, packet/canary/deletion evidence, license/SBOM report | Metrics and required privacy reports generated and committed; failures shown honestly. |
| **7 — Hardening** | Fix findings, stale-index, long-doc caps, malformed inputs, unsupported-language path, failure and cleanup tests | Release gates in §14.6. |
| **8 — Hermes (default: not built)** | `docs/adr/0010-hermes-not-built.md`; build §12 only if Tier 0–1 are green and ≥ 3 days remain | If built, enable only if every `T-HERMES-*` test passes; otherwise document “attempted, not enabled”. |
| **9 — Release pack** | S1–S10, ≤5-minute recording, demo script, setup reproduction, issue templates, good-first-issues, Hacktoberfest topic | New machine can reproduce setup and run core demo without paid service/credentials. |

If behind schedule, cut in this order: Hermes → dense retrieval → model-suggested clause edges → Investigate → Review polish → OCR polish. **Never cut:** validator, citations, legal policy, privacy tests, deletion, fail-closed behaviour, or honest limitations.

Feature freeze must occur at least three days before the organisers' announced deadline. Since the deadline may be announced separately, calculate and record the actual date once confirmed; do not invent a deadline.

### 15.1 [v3] Scope tiers, Day-0 gate and schedule scaling

The participant guide says deadlines are “announced separately”, and the Hacktoberfest 2026 dates were not yet published when this was checked. Do not assume a date.

**Day-0 hardware gate (before Phase 1, ≤ 2 h).** On the machine that will be used for the demo and the isolated run: install Ollama (≥ 0.21.1), pull both tags, run the Appendix-B smoke test, then time one ≈3K-token-prompt / ≈300-token-output call on each model. Record RAM/VRAM, tokens/s, time-to-first-token and peak memory. Decision rule (a project judgement, not a measured fact): if E4B needs more than ≈60 s p50 for that call, make E2B the default and say so; if neither finishes in ≈120 s, stop and fix the hardware/context problem before writing more code — a system needing minutes per answer cannot be demonstrated, evaluated or judged.

**Tier 0 — submittable core (finish before polishing anything).** Upload PDF/TXT → child-process pypdfium2 parse → normalised pages/sentences → FTS5 + lexicon → silence gate → `ModelAnswer` (fast path) → validator + renderer + scanner → glossary + jurisdiction flags → minimal UI (upload, ask, answer, source viewer, delete) → T8 smoke capture → honest README and S-docs. Tests: `T-ING` core, `T-MODEL-JSON-01` (N may be smaller), `T-CITE-*`, `T-LEGAL-*` incl. `T-LEGAL-FP-01`, `T-GLOSS-*`, and the privacy core: `NOEXT`, `CANARY-LOGS`, `CANARY-DELETE`, `DELETE-DERIVED`, `NOSTORE-HEADERS`, `NOCDN`, `FAILCLOSED`, `SESSION-ISOLATION`, `DNS-REBIND`, `INJECTION-NONET`, `T-SEC-BOOT-01`.

**Tier 1 — what earns points.** Overview core-10 cards, Review statuses, “Attention first”, “Questions to bring to a professional”, per-page language gate, local OCR, query expansion (T6), ≥ 100-question evaluation with ≥ 2 independent held-out contracts, E2B-vs-E4B benchmark, Docker `--network none` path, axe CI, ≤ 5-minute recording, S1–S10 pack, judge rehearsal (§16.2).

**Tier 2 — only with ≥ 3 spare days.** 144 questions, entailment downgrade, dense retrieval, model-suggested edges, Investigate tab, employment-lite lexicon, Hermes.

**Schedule scaling (freeze = confirmed deadline − 3 days).** Basis: an unmeasured estimate of ≈4–6 focused days for Tier 0 and ≈5–8 more for Tier 1, i.e. ≈9–14 for both. Days are days to freeze, counted from today.

| Days to freeze | Build |
|---:|---|
| ≥ 14 | Tier 0 + full Tier 1. Tier 2 only with ≥ 3 spare days. |
| 9–13 | Tier 0 + Tier 1 core: Overview core-10, Attention first, Questions to bring, ≥ 100 questions with ≥ 2 held-out contracts, E2B-vs-E4B benchmark, S1–S10, recording. Defer OCR, T6 expansion, axe CI and the Docker path; list each in LIMITATIONS.md. |
| ≤ 8 | Tier 0 + privacy evidence bundle + honest README + whatever evaluation fits, labelled as small. List every omitted capability in LIMITATIONS.md. |

**Re-estimate after Phase 1** from the real elapsed time. If Tier 0 will not finish by freeze − 1 day, drop to the next lower row. *Illustration only, not an assumption:* if the deadline were Hacktoberfest's end on 31 Oct, freeze would be 28 Oct, ten days from 18 Oct, which is the 9–13 row. A smaller system with real evidence beats a larger one with claims.

**Order.** Phase 6 (evaluation + privacy audit) runs before UI polish; Phase 5 is only the minimum UI that makes every claim clickable. Run each phase as its own agent session, commit at the end of each phase, and keep state in `TASKS.md`.

---

## 16. Submission requirements S1–S10

| ID | Deliverable | Required location/evidence |
|---|---|---|
| S1 | Public open-source repository with Apache-2.0 license | root `LICENSE` + `NOTICE` |
| S2 | README with overview, setup, run, configuration, troubleshooting and limits | `README.md` |
| S3 | Pinned dependency/runtime/model versions and digests; tested hardware | lockfiles + `docs/MODEL_SETUP.md` |
| S4 | Architecture and data-flow diagrams | `docs/ARCHITECTURE.md`, `DATA_FLOW.md` |
| S5 | Fixture/data sources, licenses and preparation | `docs/DATASET_NOTES.md`; synthetic fixtures only |
| S6 | Meaningful Gemma role, runtime, quantization and resource use | `docs/MODEL.md`, `MODEL_LICENSE.md`, benchmark report |
| S7 | Working live or recorded demo including limitations; ≤5-minute recording recommended | `docs/DEMO.md` + recording link |
| S8 | Measured testing, failure examples and known limits | `reports/` + `docs/LIMITATIONS.md` |
| S9 | Reproduction steps | `docs/DEMO.md`, setup scripts |
| S10 | Main technical contribution statement | `docs/CONTRIBUTION.md` |
| PS2 privacy extra | Full local analysis while network disabled plus connection-monitor output | `reports/privacy/<commit-or-release>/` |
| PS2 evidence extra | Cited source next to answer; not-located case; legal limitation; injection results | `reports/samples/` |
| Community hygiene | Contribution guide, Code of Conduct, issue/PR templates, good-first-issues and `hacktoberfest`, `privacy`, `legal-tech` topics | root, `.github/`, GitHub topics |

### Demo sequence (real system, no hard-coded answers)

1. Clone/setup, show pinned local model digest and process configuration.
2. Upload a held-out synthetic rental agreement; show physical pages, extraction/language/OCR quality.
3. Open Document Map and click through to exact source text.
4. Ask a direct fact question; show a source citation.
5. Ask a cross-clause question and show both main clause and exception/modifier.
6. Ask about a topic absent from the document; show “I could not locate…” plus the no-permission/no-prohibition caveat.
7. Ask about “reasonable notice”; show ambiguity without inventing a number of days.
8. Ask for the meaning of a term; show glossary definition separate from the cited document use.
9. Ask “Is this enforceable?” or a paraphrase; show a useful limitation, relevant source wording, escalation and `legal_verdict=null`.
10. Use an injection fixture; show its warning, ignored instruction and no forbidden tool action.
11. Repeat a question with external networking disabled; display the actual connection-monitor evidence.
12. Delete document; display actual post-delete verification; demonstrate stale-index test after changing a clause.
13. **[v3] Recording honesty.** Laptop latency may not fit five minutes. Time-lapse or cut waiting periods only with an on-screen “sped up” label and the measured latency shown; never splice or replace answers.

### 16.1 [R6] Judge-run path

`make setup` (versions, pull, digests → `reports/env.json`), `make demo`, `make isolated-demo` (Linux namespace + attempt-visible capture + negative control), `make isolated-demo-docker` (`--network none`, headless flow + report; the UI is viewed with `make demo`), plus a macOS/Windows firewall-and-monitor guide. Publish **measured** hardware needs only (third-party guidance for E4B spans ≈6 GB VRAM to ≈16 GB unified memory, which is why you publish your own numbers and an E2B fallback). Ship an evidence bundle (`reports/privacy/<date>/`, recording, capture, canary scans) so a judge who cannot run the system still has a feasible evaluation path (gate G2).

### 16.2 [v3] Pre-submission rehearsal (judge simulation)

Three people outside the team get a clean machine or VM, the README only, and their own unscripted rental PDF. Unaided they must install, upload, ask a direct question, ask about an omitted topic, ask “is this enforceable?”, try a vague clause, paste an injection line into a copy of the PDF, and delete. Every step they cannot complete from the README is a defect.

### 16.3 [R8] Held-out independence

Held-out contracts and questions must be written by someone who has not seen the lexicon, with phrasing deliberately absent from it. If no teammate is available, generate them with a different model/session told to avoid the lexicon's vocabulary, record the generating model and prompt in `fixtures/README.md`, and spot-check the gold labels by hand. Report the lexicon-miss rate and what T6 recovered.

---

## 17. Licensing, dependency and repository hygiene

- Project code: Apache-2.0, with `LICENSE` and `NOTICE`. Do not replace existing license without reviewing the repo; add missing attribution/NOTICE content.
- PDF parser: pypdfium2. Do not introduce PyMuPDF/AGPL as a convenience dependency.
- Gemma 4: record official license text/source and exact tag digest in `docs/MODEL_LICENSE.md`; model license is distinct from the project license.
- `nomic-embed-text`: optional, only if dense retrieval qualifies; record tag/digest and license.
- Tesseract executable/language data, Hermes/MCP SDK (if ever built) and all transitive packages need review.
- **[v3]** pypdfium2 is Apache-2.0 OR BSD-3-Clause (5.14.0 seen on PyPI, 4 Oct 2026) and bundles PDFium binaries; ship the `BUILD_LICENSES/` texts in `NOTICE`/third-party notices. `scripts/verify_licenses.py` policy: fail on AGPL/GPL/unknown; treat LGPL as *review-required* (e.g. `chardet`), never silently allowed; keep an explicit allowlist with a reason per entry.
- **[v3]** LLM-generated fixtures: record the generating model and prompt, and dedicate the text to CC0 or “own work” in `fixtures/README.md`.
- **[v3]** Consider renaming the repository from `golden_brown1` to `lexiguard` (GitHub redirects old URLs) for contribution-quality scoring (C4); update README and Guide links. Set the topics `hacktoberfest`, `privacy`, `legal-tech`.
- Pin Python/Node/package versions and commit `uv.lock` (or chosen Python lockfile) and `pnpm-lock.yaml`.
- CI must fail for AGPL/GPL dependencies, known-vulnerable locked packages above policy threshold, secrets, forbidden remote endpoints, CDN assets, missing licenses or stale lockfiles. Generate an SBOM.
- Never commit `.env`, access tokens, private agreements, model weights, runtime databases, canary-bearing private samples or unsourced third-party data.
- Create `AGENTS.md` rules: read Guide before editing; no cloud content paths; Gemma remains central to document interpretation; validate every generated claim; document files and tests together; never assert tests passed unless executed.

---

## 18. Limitations and mitigations

| Limitation | Required response |
|---|---|
| Small local model can hallucinate | JSON Schema; sentence IDs only; deterministic validator; unsupported-claim metrics; fail closed. |
| Source quote may not support a claim | Claim support is separately evaluated; source existence alone is not entailment; bad point dropped/downgraded. |
| Zero retrieval hit does not mean clause absent | Explicit silence gate over adequate coverage, headings, lexicon, cross-references and supported language. |
| Clauses rely on cross-references/exceptions | Deterministic expansion; show linked clauses; conflict output cites both sides. |
| OCR/layout may be wrong | Per-page quality gate; visible OCR badge; source image; no false direct claim. |
| Hidden text detector is imperfect | Only warn that suspicious hidden text may exist; do not claim detection is exhaustive. |
| Legal meaning varies by jurisdiction/current law | Local-law flags and professional escalation; never render a legal verdict. |
| Unknown legal term | Do not improvise from pretrained model knowledge; say no curated glossary entry is available. |
| Non-English content | `UNSUPPORTED_LANGUAGE`, `NOT_ASSESSED`, no fabricated summary. |
| Localhost is same machine, not a security boundary | Mandatory bearer token, Host/Origin checks, bind loopback, CSP and no-store. |
| SSD/OS swap/backup may retain remnants | No forensic-erasure promise; clearly disclose OS-level residual risk. |
| Ollama logs/runtime memory may retain transient data | Debug off, canary scan, unload request and tested delete path; disclose anything outside app control. |
| Hermes can persist history and expose more tools | Optional only, tmpfs home, sandbox, gateway allowlist, tested wipe and no-egress. |
| Hardware/model tag changes | Exact version/digest pin and benchmark; setup fails if unresolved. |
| [v3] Validators prove citation integrity and catch invented figures, swapped roles and flipped modality — not semantic faithfulness | State it in LIMITATIONS; measure UCR by human labelling; never write “every claim is verified true” |
| [v3] CPU-only laptops are slow with E4B (public guidance describes CPU inference as a crawl) | Day-0 hardware gate, fast path, E2B default if needed, published measured latency |
| [v3] Glossary is team-written, not lawyer-reviewed | Label “curated general definition — not legal advice”; record author/date/source per entry; claim legal review only if a named reviewer is recorded |
| [v3] Ollama + Gemma 4 structured-output bug history (#15260 fixed in 0.21.1; #8063, #18861, #16776 open) | Pin version; statistical `T-MODEL-JSON-01`; Pydantic always; GGUF q4_K_M only; no `tools[]`; no `-qat`/`-mlx` |
| [v3] Same-user local malware can read process memory or files | Out of scope; stated in THREAT_MODEL; token/Host/Origin defend against browser-based and cross-origin attacks only |
| [v3] Multi-column/table PDFs can scramble reading order | Warn; never show table-derived figures as `DIRECT` unless the literal check passes; show the page image |

---

## 19. Definition of done

Do not mark the project “complete” until all are true:

1. A clean checkout follows the README and runs the core demo without credentials or paid services.
2. The local pinned Gemma version is the model actually used for meaningful understanding; Ollama digest/runtime details are reported.
3. Every factual point shown as direct/supported has backend-generated citations to verbatim stored source sentences, physical page and section; citation integrity is 100% in tests.
4. Not-located, ambiguity, conflicts, glossary, jurisdiction warnings, legal-boundary paraphrases and unsupported language behave as specified.
5. Prompt-injection fixtures cannot change policy or invoke tools outside the fixed allowlist.
6. The full upload→ask→delete flow works with external networking disabled; capture, canary and deletion evidence is committed.
7. Accuracy, citation, unsupported-claim, silence, refusal, injection, latency and memory figures are measured and published with failures.
8. License/SBOM/CI, docs and runtime behaviour are consistent.
9. Hermes is either absent with `docs/adr/0010-hermes-not-built.md`, or fully gated and tested, or explicitly “attempted, not enabled”.
10. S1–S10 release pack is complete and the ≤5-minute recording clearly shows both successful and limited/failed answer paths.

> **Final principle:** the model may suggest broadly; the application may state only what the stored evidence and deterministic policy allow.

---

## Appendix A — Status and data schemas

### A1. ModelRouterProposal (untrusted; internal only)

```json
{
  "proposed_route": "FACT_LOOKUP",
  "topics": ["notice"],
  "needs_clarification": false
}
```

The backend merges it with deterministic routing. It is never returned as the final route and cannot override a legal/external-law limitation.

### A2. ModelAnswer (untrusted; no policy fields)

```json
{
  "points": [
    {
      "point_id": "p1",
      "kind": "RESTATEMENT",
      "text": "The tenant must provide sixty days' written notice before termination.",
      "sids": ["s_0412"]
    }
  ]
}
```

No route/status, quote, page, section, evidence ID, missing-information claim, legal policy flag, professional-review flag, jurisdiction flag or legal verdict may be included. Reject unknown keys.

### A3. RenderedAnswer (backend-owned)

```json
{
  "status": "ANSWERED",
  "answer": "The agreement states that the tenant must provide sixty (60) days' written notice before termination.",
  "claims": [
    {
      "claim_id": "claim_001",
      "text": "The tenant must provide sixty days' written notice before termination.",
      "classification": "SUPPORTED",
      "evidence": [
        {
          "sid": "s_0412",
          "page": 7,
          "section": "12.2",
          "quote": "The Tenant shall provide sixty (60) days' written notice before termination.",
          "ocr_derived": false
        }
      ]
    }
  ],
  "interpretations": [],
  "concerns": [],
  "ambiguities": [],
  "conflicts": [],
  "general_explanations": [],
  "missing_information": [],
  "extraction_warnings": [],
  "external_law_required": false,
  "jurisdiction_flags": [],
  "recommend_professional_review": false,
  "legal_verdict": null
}
```

Illustrative values only. The server must create this object from validated points and deterministic state; it must never pass through a model-built response object unchanged. Each document-specific item contains an evidence list. `missing_information` contains typed backend-generated objects (code, template-derived message, optional evidence and search summary), not free-form model strings. Legal-verdict field is always `null`.

---

### A4. [T2][v3] NextAction (untrusted; internal only)

```json
{ "action": "SEARCH", "query": "notice period", "topic": "notice", "ref": null, "page": null, "section": null }
```

`action` ∈ `SEARCH | GET_SECTION | GET_PAGE | FIND_RELATED | CHECK_SILENCE | ANSWER`. All other fields are optional and used by specific actions (`query`/`topic` for SEARCH and CHECK_SILENCE, `ref` for FIND_RELATED, `page` for GET_PAGE, `section` for GET_SECTION). Code validates every field (§2.3): `ref` must have been returned earlier in this run, `page` within `page_count`, lengths capped. Flat schema, no `pattern`.

---

## Appendix B — Canonical setup smoke test

These commands are examples to verify against the installed version; they are not evidence of an executed test:

```bash
export OLLAMA_NO_CLOUD=1
# Start headless Ollama using the process supervisor/platform-specific method.
ollama serve

ollama pull gemma4:e4b-it-q4_K_M
# Alternative, for constrained memory; use only if the tag is still listed.
ollama pull gemma4:e2b-it-q4_K_M

curl -s http://127.0.0.1:11434/api/tags | jq '.models[] | {name,digest,size}'

curl -s http://127.0.0.1:11434/api/chat -d '{
  "model":"gemma4:e4b-it-q4_K_M",
  "stream":false,
  "think":false,
  "messages":[{"role":"user","content":"Return the JSON object with ok=true."}],
  "format":{"type":"object","properties":{"ok":{"type":"boolean"}},"required":["ok"]},
  "options":{"seed":7,"temperature":0,"num_ctx":8192}
}' | jq -e '.message.content | fromjson | .ok == true'
```

The application must use the strict, application-owned `ModelAnswer` JSON Schema, not the smoke-test schema. Test empty `message.content`, an unavailable model, malformed output, and local-model stop separately. Hermes commands are not prescribed here: obtain them from the exact installed Hermes version's documentation, verify effective tool use at the LexiGuard gateway, and pass every `T-HERMES-*` test before enabling it.

---

## Appendix C — Official references checked for this specification

- ZeroDay OSS participant guide: source supplied by project owner.
- GitHub repository baseline: <https://github.com/panditshubham766-dotcom/golden_brown1>
- Gemma 4 official model card/licence: <https://ai.google.dev/gemma/docs/core/model_card_4>
- Ollama Gemma 4 tags: <https://ollama.com/library/gemma4/tags>
- Ollama native chat API: <https://docs.ollama.com/api/chat>
- pypdfium2 Python API: <https://pypdfium2.readthedocs.io/en/stable/python_api.html>
- Hermes session persistence: <https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/session-storage.md>
- Hermes MCP configuration: <https://github.com/NousResearch/hermes-agent/blob/main/website/docs/reference/mcp-config-reference.md>

**[v3] Verified on 18 Oct 2026 by reading the sources:** Ollama tags page (tags, sizes, digests); Ollama FAQ <https://docs.ollama.com/faq.md> (`OLLAMA_NO_CLOUD=1` / `disable_ollama_cloud`, log line `Ollama cloud disabled: true`, `keep_alive:0`, default context 4096); Gemma 4 model card (Apache 2.0; E2B 2.3 B effective / 5.1 B with embeddings, E4B 4.5 B / 8 B); pypdfium2 on PyPI <https://pypi.org/project/pypdfium2/> (5.14.0, Apache-2.0 OR BSD-3-Clause, bundled PDFium licences); Ollama issues #15260 (fixed in 0.21.1), #8063 (open), #18861 (open), #16776 (open) at `github.com/ollama/ollama/issues/<n>`.

Check current docs again when locking dependency and model versions; external documentation is not a substitute for the runtime acceptance tests.
