# LexiGuard — Final Product Requirements Document

**PRD version:** 3.2  
**Status:** Final requirements baseline, pending implementation and verification  
**Product:** LexiGuard — private, evidence-backed legal-document triage  
**Target:** ZeroDay OSS Hacktoberfest 2026 — Problem Statement 2 (Private Legal Document Triage Agent)  
**Design authority:** `SOLUTION_GUIDE_v3.md`, specification v3.1  
**Implementation instructions:** `MASTER_IMPLEMENTATION_PROMPT_v3.txt`

> **Status and truthfulness notice:** This document defines what the team intends to build and how acceptance will be evaluated. It is not evidence that the application, any model configuration, privacy controls, metrics, or release gates have already passed. Mark a requirement verified only after its test or evidence artifact exists and has been reviewed.

## 1. Purpose and source authority

LexiGuard helps non-lawyers understand what an English rental or leave-and-licence agreement says, locate supporting passages, notice ambiguity or conflicting wording, and recognise when the document does not provide enough information. It is a preliminary document-understanding aid, not a lawyer, legal research service, or source of legal advice.

If this PRD differs from the implementation guide, the following precedence applies:

1. The official ZeroDay OSS participant guide governs hackathon requirements, compliance gates, and judging.
2. `docs/SOLUTION_GUIDE_v3.md` (specification v3.1) governs LexiGuard's design and implementation contract.
3. `docs/MASTER_IMPLEMENTATION_PROMPT_v3.txt` instructs the coding agent and must not silently override the Solution Guide.
4. This PRD expresses the user-facing and testable product requirements. Any conflict with the Guide must be reconciled in the Guide first, then reflected here, in tests, and in implementation tasks.
5. Runtime commands, model tags, digests, versions, capabilities, and licences must be verified on the actual machine. Do not infer them from this document alone.

## 2. Problem and target users

### 2.1 Problem

Rental agreements can contain dense terminology, cross-references, ambiguous wording, financial obligations, and clauses that appear to conflict. A generic language model can state unsupported conclusions or blur the difference between what a contract says and what it might mean. Uploading personal documents to a hosted service also creates privacy concerns.

### 2.2 Target users

Non-lawyers, especially tenants and landlords, who need a preliminary explanation of the readable contents of an agreement and help identifying questions to raise with a qualified professional.

### 2.3 Primary user story

As a tenant, I want to process a rental agreement on my own computer, ask what it says about deposits or early termination, inspect the exact source passage and page, and see potentially ambiguous or conflicting clauses without the system pretending to determine my legal rights or the agreement's enforceability.

## 3. Product scope

### 3.1 MVP scope

- English-language rental and leave-and-licence agreements.
- Input formats: PDF and plain-text TXT. TXT documents use deterministic virtual pages for source navigation.
- Local parsing, retrieval, inference, storage, and response rendering during normal document processing.
- Source-grounded Q&A, a rental-topic Document Map, a prioritized Review view, a curated legal-terminology glossary, jurisdiction-dependent topic warnings, safe limitation/escalation responses, and application-level deletion verification.
- Reusable implementation that is not hard-coded to a single fixture.

### 3.2 Supported topic coverage

The system should look for relevant evidence about parties and property references; agreement term and renewal; rent and escalation; deposit and advance; utilities; repairs and maintenance; access and inspection; guests, pets, subletting and alterations; notice, lock-in and termination; early exit, penalties, deductions and forfeiture; handover; dispute or venue wording; referenced annexures and schedules; ambiguity, conflicts, and extraction quality.

The Document Map presents the following Core 10 concepts: **Parties, Term, Rent, Deposit, Notice, Lock-in, Penalties, Restrictions, Maintenance, and Disputes**. Each displayed factual item must have verifiable evidence. An empty card must not imply that a provision is legally absent.

### 3.3 Explicit non-goals

- No legal verdict about legality, validity, enforceability, fairness, or likely court, eviction, police, or dispute outcome.
- No current-law or jurisdiction-specific legal conclusion from the model's pretrained knowledge; no external-law research in the answering loop.
- No remote LLM, cloud OCR, cloud embeddings, cloud translation, cloud document storage, content-bearing telemetry, or CDN-hosted assets during normal processing.
- No editing, negotiation, signing, automated legal action, or cross-document GraphRAG.
- No broad support claims for employment, corporate, service agreements, or legal notices. If another document type is detected, show a clear scope warning and degrade honestly; do not make rental-specific claims without evidence.
- No non-English analysis in the MVP. Unsupported or uncertain pages are flagged, excluded from retrieval, and treated as unread rather than translated or silently interpreted.
- Hermes is not part of the default build. Any Hermes work is a later, optional decision and must not delay core requirements.

## 4. Product behaviour and user flow

1. **Launch:** The user starts the local application. A one-time launch code is exchanged for a random session bearer token; the token is not embedded in served HTML and is held in browser memory.
2. **Upload:** The user selects a PDF or TXT file. The backend validates size, type, and limits before processing.
3. **Parse and inspect quality:** PDF extraction runs in a limited child process. The system normalizes text, maps it to physical page numbers, checks extraction/language quality, and reports any pages that could not be assessed. Local Tesseract OCR is used only when the quality gate identifies image-only or low-text pages and OCR support is installed.
4. **Overview:** The user sees the evidence-gated Core 10 Document Map. Each populated item opens its source sentence(s); empty or unassessed items are not presented as legal conclusions.
5. **Ask:** The user asks a question. Deterministic routing and local lexical retrieval prepare a bounded evidence packet; local Gemma proposes structured points; deterministic validation and backend rendering decide what can be shown.
6. **Review:** The user sees prioritized attention items, such as candidate conflicts, ambiguous money/time/termination wording, financial obligations, and jurisdiction-dependent topics. The order is a review aid, not a risk score or legal verdict.
7. **Escalation:** When appropriate, LexiGuard presents specific, neutral questions to take to a qualified legal professional, supported by source passages.
8. **Delete:** The user requests deletion and receives a verification report that distinguishes removal of app-controlled data from forensic erasure.

## 5. Functional requirements

### FR-001 — Local document ingestion (PS2 L1)

The application shall accept supported PDF and TXT files and reject files that exceed configured size/page limits or fail type/content validation. PDF parsing shall use `pypdfium2` in a child process with resource limits and a wall-clock timeout. Do not use PyMuPDF. Parser failures must return a controlled error rather than crash the API process.

Acceptance evidence: synthetic PDF/TXT upload tests; malformed, encrypted, truncated, oversized and unsupported-file tests; parser timeout/resource-limit tests; normalized-text offset round-trip tests.

### FR-002 — On-device extraction and interpretation (PS2 L2)

The application shall extract, normalize and store page-bound content locally and use local Gemma inference through Ollama for a meaningful part of document interpretation. Source offsets must refer to the normalized text stored by LexiGuard, not raw PDFium character indices. No private document content may be sent to a remote service during normal processing.

Acceptance evidence: architecture/data-flow review, parser/model tests, and an isolated run with connection-monitoring evidence.

### FR-003 — Plain-language summaries and terminology (PS2 L3)

The application shall explain important clauses and supported legal terms in plain language while preserving the distinction between document text and general explanation. Terminology shall come from a versioned local glossary (`glossary/rental_terms.yaml`). The UI shall separately label **General definition (not from your document)** and **In your document** with its source passage. If the glossary has no curated entry, the system shall say so rather than improvising a legal definition from model memory.

Acceptance evidence: glossary tests for known and unknown terms; source citation tests; legal-boundary scanner tests.

### FR-004 — Obligations, dates, penalties and concerns (PS2 L4)

The application shall identify supported evidence about relevant dates, parties, obligations, rights as stated in the document, deadlines, financial terms, penalties, termination terms, ambiguities, and candidate conflicts. It shall not infer a legal entitlement or outcome merely because a clause appears in the document.

Acceptance evidence: labelled evaluation questions across direct facts, multi-clause questions, ambiguity, conflict, and financial/termination topics.

### FR-005 — Evidence-backed answers and source navigation (PS2 L5)

Every material document-specific point displayed as a fact, restatement, interpretation, concern, ambiguity, or conflict must be tied to valid source sentence IDs (`sids`) returned by an approved tool for the same document and current run. The model may propose sentence IDs but shall not author citation quotes, physical page numbers, section names, evidence IDs, or final statuses. The backend shall obtain verbatim quotations, page labels, section labels, source references, and navigation targets from immutable local storage.

The backend shall reject forged, stale, cross-document, or not-returned sentence IDs. It shall check citation provenance, numbers, dates, roles, modality and negation using conservative normalization. A conflict must cite at least two sentences from different sections and display both passages. A citation-integrity check proves that the quote matches stored source text; it does not, by itself, prove that the interpretation is semantically correct.

Acceptance evidence: `T-CITE-*` tests including forged/stale/cross-document IDs, quote mismatch, unsupported numbers/dates/roles, modality flips, wrong-claim support, and cross-section conflict rendering.

### FR-006 — Explicit statements versus interpretation (PS2 L6)

The response model shall use typed points, including `STATED`, `RESTATEMENT`, `INTERPRETATION`, `CONCERN`, `AMBIGUITY`, `CONFLICT`, and `GENERAL_EXPLANATION`. The UI shall clearly label and visually separate stated text from interpretive or attention-oriented content. No colour or score alone may communicate meaning. Generated concern text shall describe what wording merits attention and shall not call a clause fair, unfair, normal, enforceable, or illegal.

Acceptance evidence: schema, validator, and UI tests that inspect the displayed type and label for each point kind.

### FR-007 — Ambiguity, silence and jurisdiction dependence (PS2 L7)

The application shall identify ambiguity and candidate conflicts, flag topics that may depend on local law, and distinguish `NOT_LOCATED` from `INSUFFICIENT_EVIDENCE`.

The backend may assign `NOT_LOCATED` only when all required checks are satisfied: document/page coverage is adequate; no unread pages could contain the topic; language is supported; topic lexicon, lexical full-text and heading searches have run; relevant cross-references and incorporated annexures/schedules have been considered; and dense retrieval has also run if it has been enabled. Zero search hits alone are insufficient. Otherwise return `INSUFFICIENT_EVIDENCE`.

A `NOT_LOCATED` response shall describe the readable scope checked and state that not locating a provision does not mean it is allowed or prohibited. Unsupported or inconclusive language pages shall be flagged `UNREAD_LANGUAGE`; affected review categories shall be `NOT_ASSESSED`; such pages disable definitive silence claims. The document shall show an `UNSUPPORTED_LANGUAGE` warning when applicable.

Jurisdiction flags are cautions only, such as “May depend on local law — confirm locally.” They shall not state what local law requires.

Acceptance evidence: direct, paraphrased, cross-reference, absent-topic, low-coverage, unread-page and unsupported-language test cases.

### FR-008 — Refusal, limitation and professional escalation (PS2 L8)

A deterministic pre-router and stricter-route merge shall intercept direct and paraphrased requests for legal verdicts, outcome predictions, current-law answers, or advice such as whether to sign. The system shall explain what the document says, what cannot be established from the document alone, and when a qualified legal professional is appropriate. When appropriate, it shall provide specific, neutral, source-cited questions to raise with that professional.

The output scanner shall scan assistant-authored text, dynamic headlines, summaries, labels, glossary output and escalation text. It shall not rewrite immutable source quotations; source quotations must be labelled as quoted source text, not LexiGuard's legal assessment. The verdict scanner shall use contextual verdict/outcome/advice patterns and a source-echo exception for direct stated/restated wording such as “valid for 11 months.”

Acceptance evidence: a versioned `T-LEGAL-FP-01` corpus with at least 40 must-block and 40 must-pass examples; zero missed must-block cases and no more than 5% false blocks on that defined corpus; direct/paraphrased refusal and source-quotation exception tests. These are suite-specific targets, not a universal guarantee.

### FR-009 — Demonstrable on-device privacy (PS2 L9)

During normal document processing, private content—including the original file, extracted text, chunks, embeddings if enabled, summaries, answers, names, metadata, user questions and derived evidence—shall remain on the device. The default runtime shall not use remote models, cloud OCR/embedding/translation/storage, telemetry, analytics, crash reporting or CDN-hosted assets. Any remaining network calls must be inventoried, carry no private content, and be optional or disabled for the privacy demonstration. Setup-time downloads of models and dependencies are a separate workflow and must never receive private documents.

Required controls:

- FastAPI binds only to `127.0.0.1`.
- Every `/api/*` request requires a random bearer token. Use a one-time launch code in the URL fragment, exchange it at `/api/session`, and keep the resulting token in browser memory; never embed it in served HTML.
- Validate `Host` and `Origin` on state-changing requests; no wildcard CORS.
- Serve the production UI and API from the same origin, bundle assets locally, apply a Content Security Policy with `default-src 'self'`, and use `Cache-Control: no-store` on document endpoints.
- Store document data under per-document directories; use SQLite/FTS5, `PRAGMA secure_delete=ON`, rollback journal mode (`journal_mode=DELETE`, not WAL), and disable answer history by default.
- Use `OLLAMA_NO_CLOUD=1`, run a headless `ollama serve` for the privacy demo, do not set `OLLAMA_DEBUG`, and do not rely on the desktop tray application's defaults as proof of privacy.
- Default to lexical-first SQLite FTS5/BM25, a versioned rental-topic lexicon, and deterministic cross-reference expansion. Dense retrieval is off unless evaluation proves a worthwhile recall improvement; if enabled, it must use local Ollama `/api/embed` with a pinned model digest and must remain inside the document's local storage boundary.
- Do not include filenames or file metadata in model prompts. Treat extracted text, OCR text, document content and model outputs as untrusted input; document injection detection raises a warning only and cannot change policy or permissions.

Verification shall include a full upload → ask/analyse → delete run with networking disabled or blocked, attempt-visible connection monitoring, a negative control that proves the monitor detects a known attempt, canary checks in app-controlled files/logs, and an explicit inventory of remaining network calls. An empty capture without a working negative control is not sufficient evidence. Environment flags alone are not proof. No privacy claim may be marked verified until the evidence bundle is reviewed. Never place real private contracts in the coding-agent workspace or synthetic test corpus; use synthetic fixtures for implementation and demos.

Acceptance evidence: all required `T-PRIV-*` tests and the isolated network report for the exact tested commit/build.

### FR-010 — Application-level deletion and verification

On deletion, the backend shall close database connections and parser/page handles; issue a version-verified local model-unload request where supported; remove the document directory, database, FTS shadow/derived data, temporary page images and app-controlled history; clear frontend state; revoke the document session binding; and scan app-controlled data/temp/logs for test canaries. The report shall distinguish what was verified removed from data outside the application's control.

The system shall **not** claim secure forensic erasure. SSD wear levelling, operating-system swap/hibernation, backups, or external runtime logs may retain remnants beyond application control. Any such known limitation must be disclosed.

Acceptance evidence: delete, delete-derived-data, database/FTS cleanup, canary scan, session-revocation and post-delete retrieval tests.

### FR-011 — Meaningful Gemma use and reproducible open-source implementation (PS2 L10)

Gemma shall perform a meaningful document-understanding task, not merely be named in the repository. The project shall provide model acquisition instructions, exact model tag and observed digest, quantization, runtime/version, tested OS/hardware, measured memory and latency, a license record, setup instructions, architecture/data-flow explanation, and reproducible demonstration steps.

The default model decision is:

- Primary candidate: `gemma4:e4b-it-q4_K_M`.
- Hardware fallback: `gemma4:e2b-it-q4_K_M` using the corresponding quantization family for a fair comparison.
- Minimum intended Ollama version: 0.21.1.
- Use native Ollama `POST /api/chat` on loopback, not `/v1`; simple JSON Schema with Pydantic validation; `think:false`; fixed seed; temperature 0; `num_ctx=8192` by default; `stream:false`; and never send a `tools` key.
- Record the actual installed version, `/api/tags` digest, model capabilities and test output. Model digests can change; never silently substitute an alias or use cloud tags, `-qat`, `-mlx`, `-nvfp4`, or `-mxfp8` variants.
- Empty `message.content` is a failure even if thinking text exists. Model/runtime failures must fail closed.

Day-0 hardware gate: before substantial implementation work, benchmark each candidate with approximately a 3,000-token prompt and a short, approximately 300-token response. Record machine, model/digest, RAM/VRAM, latency, time-to-first-token and peak memory. As a project decision rule, if E4B exceeds approximately 60 seconds p50 for that benchmark, use E2B as the default; if neither completes within approximately 120 seconds, stop and resolve the hardware/context issue before expanding the build. These are gating thresholds, not previously measured results.

Acceptance evidence: `T-MODEL-*` tests, setup report, model-license record, and benchmark report.

### FR-012 — UI, accessibility and failure states

The frontend shall support keyboard navigation, visible focus, screen-reader labels/roles, WCAG AA contrast, reduced-motion preferences, clear errors, and an axe CI check. Factual cards must link to precise source evidence. The UI shall not display a global legal-risk score, risk probability, or percentage confidence. Long-running actions and OCR-derived evidence must have useful status/warning messages. Review items shall follow the defined attention-first order: candidate clause conflicts; ambiguity about money, time or termination; payment/forfeiture/deduction/penalty/lock-in obligations; jurisdiction-flagged clauses; then remaining items. Each item must explain its order neutrally, not through a score or legal verdict.

Implementation baseline: React + Vite + TypeScript, built and served by FastAPI from the same origin; Python + FastAPI on `127.0.0.1`; all fonts, icons and scripts bundled locally; no CDN; Content Security Policy with `default-src 'self'`. The browser shall not store document content in `localStorage` or other persistent browser storage.

Acceptance evidence: frontend end-to-end tests, keyboard checks, axe CI output, no-CDN test and failure-state coverage.

## 6. AI and deterministic-code boundary

### 6.1 Gemma may propose

- A structured internal route proposal when deterministic routing is uncertain.
- Bounded retrieval expansion terms or a schema-constrained next action when the permitted refinement path needs them.
- The `text` field of a restatement, interpretation, ambiguity, concern or conflict explanation using only the supplied evidence packet.
- Paraphrasing of an existing curated glossary definition without changing its meaning.
- Candidate sentence IDs from the current evidence packet.

Model output is untrusted proposal data. The model may not author the final route/status, `NOT_LOCATED` decision, citation metadata, verbatim quote, page/section label, legal-review flag, jurisdiction flag, policy, or legal verdict. It may not call arbitrary tools or select arbitrary URLs/models.

### 6.2 Deterministic backend owns

File validation and parsing; normalized page/sentence IDs and metadata; storage and retrieval; tool allowlists and execution; evidence packet construction; all schema/provenance validation; status decisions; numeric/date/role/modality checks; legal policy and verdict scanning; jurisdiction flags; citation rendering; source navigation; deletion; network policy; and final response schema.

### 6.3 Bounded runtime and call budget

The default runtime is a bounded Python state machine, not an unconstrained general agent. Deterministic pre-routing, retrieval and silence checks run first. A confident retrieval fast path uses exactly one Gemma answer call. A refinement path may add one refinement call (query expansion **or** a `NextAction` round, not both) before the answer call. The absolute ceiling is four Gemma calls per question, including retries. The runtime shall allow no more than eight tool calls total per user request, no more than two retrieval/refinement loops, and no more than twelve evidence chunks per tool call. Question length, request timeout, model timeout, response size/token count and tool argument size must be capped; the user question limit is 500 characters. Retries may include only validation violation codes and minimal schema errors, not the entire source document. A question must never enter an unbounded retry loop. The default entailment pass is off.

The context packet target is approximately 2,500 estimated tokens. Per-question wall-clock budget is four times the measured Day-0 p50 of the selected model, capped by the configured request timeout; skip optional refinement when more than half the budget is spent. Record measured per-path latency and the fast-path rate.

## 7. Storage, parsing and retrieval requirements

- Use one document directory per uploaded document: `data/docs/<doc_id>/`.
- Use SQLite plus FTS5; verify FTS5 at startup and fail with a clear message if unavailable.
- Use `unicode61` tokenization with diacritic removal; optional Porter indexing is allowed. Add normalized-number search so common formats such as `Rs. 25,000/-`, `25000` and `₹25,000` can be found consistently.
- Retrieval is lexical-first: FTS5/BM25 plus versioned topic lexicon and deterministic cross-reference expansion. Retrieval lexicons aid search; they are not evidence and must never appear as proof in an answer.
- Dense retrieval stays disabled unless a measured evaluation shows a meaningful recall improvement. If enabled, run it locally through Ollama embeddings with a pinned digest and required query/document prefixes; test lexical-only against hybrid using the same question set.
- PDF parser workers must be time/resource limited. On Windows use a Job Object plus wall-clock watchdog; on POSIX use `rlimit` plus watchdog as specified in the Solution Guide.
- OCR uses local Tesseract only for pages flagged by the quality gate. OCR-derived claims must display an `OCR-derived — check the page image` warning. Do not claim scan support until the scanned-PDF fixture and OCR tests pass.
- Per-page language gate: English only. Pages with unsupported or inconclusive language are excluded and labelled; no network translation or unsupported-language summary is permitted.
- The suspicious-hidden-text detector is heuristic only. It may warn that hidden text could exist but must not claim that hidden text is absent.

## 8. Non-functional requirements

### 8.1 Local-only processing and network behaviour

Normal document processing must run without external network access. Setup-time downloading of the selected model, dependencies, or permitted public fixture resources is a separate documented process. Every remaining network call must be inventoried and shown not to transmit private content; calls should be optional or off. Localhost is not treated as a sufficient security boundary on its own.

### 8.2 Performance

- No more than four Gemma calls per question, retries included.
- Confident fast path uses exactly one Gemma answer call before any necessary format/validation retry.
- Evidence packet target approximately 2,500 estimated tokens; default `num_ctx=8192`, subject to the actual runtime configuration.
- Per-question wall-clock budget is four times Day-0 p50, subject to a hard configured request timeout.
- Report p50/p95 latency, peak memory, selected model/digest, hardware, and measured throughput if reliably available. Do not state benchmark values before measurement.

### 8.3 Reliability and failure behaviour

Malformed inputs, unsupported language, insufficient evidence, missing local model, timeout, invalid model output, failed validation, and deletion failures shall result in a controlled message/status. The system shall never bypass validation or fall back to a remote service. Examples of controlled statuses include `NOT_LOCATED`, `INSUFFICIENT_EVIDENCE`, `UNSUPPORTED_LANGUAGE`, `NOT_ASSESSED`, `ERROR_LOCAL_MODEL_UNAVAILABLE`, and `ERROR_PROCESSING`, as applicable to the condition.

### 8.4 Licensing and supply chain

The repository shall use Apache-2.0 with root `LICENSE` and `NOTICE`, preserving and inspecting any existing license rather than overwriting it blindly. CI shall fail if an AGPL/GPL dependency is introduced. Model and data licenses shall be recorded separately. Pin dependencies and model digests; include a dependency/SBOM and license report. Record bundled PDFium licensing. Use synthetic fixtures or clearly licensed material; never commit private or non-redistributable agreements.

## 9. Evaluation plan and precommitted targets

Targets shall be committed before final evaluation, then published alongside measured results, denominators, confusion matrices, per-fixture outcomes and representative failures. Targets below are not current achievements.

### 9.1 Evaluation corpus

- At least five distinct synthetic contracts.
- At least 100 labelled questions for the baseline release; target 144 when time permits.
- At least two held-out contracts authored/finalized by someone who has not seen the retrieval lexicon, kept out of the implementation workspace until the freeze/evaluation step.
- Include direct facts, multi-clause questions, absent topics, ambiguity, conflict, legal-boundary/current-law requests, glossary questions, prompt injection, layout/OCR issues, long documents, malformed files, unsupported-language pages and paraphrases.
- Each fixture shall record provenance, authoring method, license, expected statuses, source sentence IDs/sections, expected facts, forbidden claims and known limitations. Use synthetic/own-work fixtures unless redistribution rights for any other material are clearly established.

### 9.2 Metrics and acceptance targets

| Metric | Definition | Target on the defined evaluation suite |
|---|---|---:|
| Fact accuracy | Correct labelled facts / all labelled facts | ≥ 90% |
| Citation precision | Human-labelled citations that support the point / all rendered citations | ≥ 95% |
| Citation coverage | Material points with at least one valid citation / all material points | ≥ 95% |
| Citation integrity | Rendered quote equals the stored source text under the specified normalization | 100% |
| Unsupported Claim Rate (UCR) | Human-labelled unsupported material points / reviewed material points on held-out answers | ≤ 5% |
| Silence precision | Correct `NOT_LOCATED` claims / all `NOT_LOCATED` claims | ≥ 95% |
| Silence recall | Correct absent-topic detections / labelled absent topics where the quality gate permits a decision | ≥ 90% |
| Answer rate on answerable questions | Answerable questions receiving `ANSWERED`/`LIMITED` with at least one validated cited point / all answerable questions | ≥ 80% |
| False-refusal rate | Answerable questions incorrectly returned as `INSUFFICIENT_EVIDENCE`, `NOT_LOCATED`, or `LEGAL_LIMIT` / all answerable questions | ≤ 15% |
| Legal-boundary suite | Assistant-authored legal verdicts in defined boundary tests | 0 |
| Verdict scanner | Missed must-block / false blocks on `T-LEGAL-FP-01` | 0 missed / ≤ 5% false blocks |
| Injection resistance | Defined injection fixtures with no policy change or forbidden call | 100% |
| Privacy test pass rate | Required privacy tests passing with saved evidence | 100% before verified wording |
| Stale-index behaviour | Correct answers after an indexed clause is changed | 100% of test cases |
| Latency and memory | p50/p95 per path; peak RSS/VRAM | Measure and publish; no fabricated fixed universal target |
| Fast-path rate | Share of questions using one Gemma answer call | Measure and publish |

Passing an evaluation suite does not prove that all possible inputs are safe or correct. If a target is missed, fix and rerun or document the failed gate; do not label the release as passed.

## 10. Hackathon deliverables and compliance requirements

| ID | Requirement | Expected evidence |
|---|---|---|
| S1 | Public source repository with open-source license | Root `LICENSE` and `NOTICE`; public repository |
| S2 | README covering overview, setup, run, configuration, troubleshooting and limitations | `README.md` |
| S3 | Pinned dependencies and versions; runtime/model version, model digest, OS and tested hardware | Lockfiles and `docs/MODEL_SETUP.md` |
| S4 | Architecture and data-flow explanation/diagrams | `docs/ARCHITECTURE.md`, `docs/DATA_FLOW.md` |
| S5 | Dataset/fixture sources, licensing, preparation and attribution | `docs/DATASET_NOTES.md`, fixture README |
| S6 | Meaningful Gemma role and model acquisition/runtime details | `docs/MODEL.md`, model license and benchmark report |
| S7 | Working real-system demo with limits described | Demo instructions/recording; up to about five minutes is recommended, not assumed mandatory |
| S8 | Measured test results and known limitations stated honestly | `reports/` and `docs/LIMITATIONS.md` |
| S9 | Reproduction instructions without paid services or undisclosed credentials | Setup scripts and `docs/DEMO.md` |
| S10 | Main technical contribution statement | `docs/CONTRIBUTION.md` |

PS2-specific evidence must include a full local analysis with networking disabled or blocked and connection-monitor output; an explanation of how private-content transmission is prevented and any remaining network calls; model acquisition instructions covering variant, quantization, license and runtime; sample outputs with citations beside source; a `NOT_LOCATED` example; and, where implemented, refusal/escalation and adversarial/prompt-injection examples.

The required compliance gates include a public licensed repository, reproducible demo, real rather than mocked system, disclosed data/licensing, no secrets in the repository, locally run Gemma, no private content leaving the device, no systematic fabrication of clauses/citations, and no presentation of the system as legal advice.

## 11. Release acceptance gates

A release must not be declared complete until the required gates for that release are passed with checked-in evidence. At minimum:

- Citation integrity passes; no forged/stale/cross-document source references are rendered.
- Zero assistant-authored legal verdicts occur in the defined boundary suite.
- All defined prompt-injection tests remain within policy with no unauthorized tool calls.
- Required privacy tests pass and an isolated-network evidence bundle is saved for the exact tested commit/build. Connection monitoring includes a successful negative control.
- Held-out questions/contracts are evaluated; answer rate and false-refusal rate are reported.
- Stale-index and deletion/derived-data tests pass.
- Actual model tags/digests, Ollama version, setup output and hardware benchmark are recorded.
- License/SBOM checks pass; no secrets or private/non-redistributable data are committed.
- README and documentation match the actual code. Claims such as “100% local,” “verified offline,” “citations always correct,” or “securely erased” may not be used without appropriate evidence and must still be narrowly scoped to what the tests establish.

Every phase gate must preserve its raw output, exit code and Git SHA under `reports/phase-<id>/`; update `docs/PHASE_LOG.md` and commit only after review. The actual repository and branch must be inspected before edits. Do not push to `main` without explicit approval.

## 12. Deferred features (Tier 2 / not required for MVP)

Only consider these once the core release gates are green and there is meaningful schedule buffer:

- Optional Hermes integration with a separately isolated sandbox, ephemeral `HERMES_HOME`, no egress, a restricted model gateway/tool allowlist and complete persistence/deletion tests. Default decision: considered, not built.
- Dense local retrieval using Ollama embeddings and a pinned `nomic-embed-text` digest, only if evaluation shows a measured recall improvement.
- Model-suggested clause-graph edges, labelled as possible links requiring verification.
- An Investigate tab for deeper search/source navigation.
- Broader employment/service agreement support.

These features must not weaken or delay citation validation, legal policy, local privacy, deletion, fail-closed behaviour, reproducibility or honest limitations.

## 13. Requirements-to-evidence summary

| Requirement | Primary verification artifact |
|---|---|
| FR-001 ingestion | `T-ING-*` test output |
| FR-002 local extraction/inference | `T-ING-*`, `T-MODEL-*`, architecture review |
| FR-003 glossary | `T-GLOSS-*` |
| FR-004 obligation/concern identification | labelled evaluation set and per-fixture results |
| FR-005 citations | `T-CITE-*`, citation metrics, source-rendering tests |
| FR-006 output types | schema, validator and UI tests |
| FR-007 ambiguity/silence/language | retrieval/silence/language tests and evaluation metrics |
| FR-008 legal safety/escalation | `T-LEGAL-*`, `T-ESCALATE-01`, scanner corpus report |
| FR-009 privacy | `T-PRIV-*`, isolated capture, negative control, canary reports and network inventory |
| FR-010 deletion | deletion/derived-data/canary/session revocation tests |
| FR-011 Gemma/reproducibility | `T-MODEL-*`, environment/digest report, model license, benchmark, reproducible demo |
| FR-012 UI/accessibility | frontend E2E, keyboard checks, axe output and no-CDN test |
| S1–S10 | release checklist and corresponding documents/evidence |

---

## 14. Change control

Any change to a locked architecture decision, model family, network boundary, source-of-truth ownership, evidence/citation contract, legal policy, or deletion policy must be supported by measured evidence or a documented requirement, and must identify the affected requirements, implementation files, tests, and risks. Record fixed decisions in an Architecture Decision Record (ADR); update the Solution Guide before altering this PRD or implementation prompt. Do not silently add a competing prompt or revive superseded v1/v2/v2.1 documents.
