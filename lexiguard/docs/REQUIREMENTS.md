# Requirements traceability

Requirement text is summarised from the ZeroDay OSS participant guide (PS2) and the
`SOLUTION_GUIDE_v3.md` requirements map. Status uses the same honest scale as `TEST_PLAN.md`:
**done (fixtures)** means implemented and exercised on the committed synthetic fixtures;
**partial** means some pieces exist or a live-model/privacy step is missing; **not started** means
no claim may be made.

---

## 1. Functional requirements (L1–L10)

| ID | Requirement | Design location | Evidence / tests | Status |
|---|---|---|---|---|
| L1 | Accept PDF and TXT; private ingestion | `ingest/pipeline.py`, `parser.py`, `worker.py`, `api/documents.py` | E2E TXT + PDF upload, page image, delete | **done (fixtures)** |
| L2 | Local extraction + local model interpretation | `ingest/*`, `agent/runtime.py`, `model/ollama_native.py` | runtime with scripted provider; adapter payload tests | **partial**: no live model run |
| L3 | Plain-language glossary, clearly not legal advice | `glossary/rental_terms.yaml`, `services/glossary_service.py`, TERM route | term question → glossary explanation + disclaimer | **done (fixtures)** |
| L4 | Rights/obligations/dates/penalties/termination coverage | `retrieval/concepts.py`, `services/{overview,review}.py` | 5 fixtures: 7–10 of 11 concepts found; 3–8 review items | **done (fixtures)** |
| L5 | Verifiable passages with sids and backend quotes | `validation/*`, `schemas/response.py` | provenance/citation/renderer tests; invented literal rejected 5/5 | **done (fixtures)** |
| L6 | Explicit vs interpretive separation | `PointKind`, `Classification`, UI sections | schema tests; separate UI sections and answer buckets | **done (fixtures)** |
| L7 | Ambiguity, silence and jurisdiction dependence surfaced | `services/silence_context.py`, `retrieval/vagueness.py`, statuses | absent topic → NOT_LOCATED; ambiguity fixture → AMBIGUITY item | **done (fixtures)** |
| L8 | Limit/refuse/escalate legal conclusions | `agent/router.py`, `validation/legal_policy.py` | LEGAL_LIMIT on every fixture; block/pass corpus tests | **done (fixtures)** |
| L9 | Privacy demonstrated, not asserted | `security/*`, deletion, privacy docs | Host/auth/boot tests; canary helper | **partial**: no isolated evidence exists |
| L10 | Meaningful Gemma use + reusable open source | `model/`, `agent/`, docs, CI | adapter + runtime tests | **partial**: genuinely used in the design, but no live-model evidence exists |

Hard rule: L1–L10 are not “done” because modules exist. They are done when the Phase 6 evaluation
and privacy reports exist for the release being submitted.

---

## 2. Submission requirements (S1–S10)

| ID | Deliverable | Where | Status |
|---|---|---|---|
| S1 | Public Apache-2.0 repository | `LICENSE`, `NOTICE` | present (root license text downloaded from apache.org; preserve repo’s original copy on merge) |
| S2 | README with overview, setup, run, config, troubleshooting, limits | `README.md` | **present, honest** about unmeasured model and privacy results |
| S3 | Pinned dependency/runtime/model versions and digests | `pyproject.toml`, `package-lock.json`, `docs/MODEL_SETUP.md` | **partial**: Python ranges not locked; digests to be recorded on the demo machine |
| S4 | Architecture and data-flow diagrams | `docs/ARCHITECTURE.md`, `docs/DATA_FLOW.md`, `docs/architecture-overview.html` | **present** |
| S5 | Fixture/data sources, licenses, preparation | `docs/DATASET_NOTES.md`, `fixtures/README.md` | **present**: 5 synthetic TXT + 3 derived PDF fixtures |
| S6 | Privacy statement + verified network inventory | `docs/PRIVACY.md` | **unverified** (no isolated run) |
| S7 | Test + evaluation evidence | `docs/TEST_PLAN.md`, `docs/EVALUATION.md`, `reports/fixture_evaluation.md` | **partial**: 117 tests pass, fixture evaluation committed; no live-model accuracy numbers |
| S8 | Demo (≤5 min) reproducible | `docs/DEMO.md` | **not ready**: requires Phase 4 |
| S9 | Honest limitations | `docs/LIMITATIONS.md` | **present** |
| S10 | Contribution/rehearsal evidence | `docs/CONTRIBUTION.md` | **planned**; no rehearsal yet |

---

## 3. Non-functional invariants (must never regress)

| Invariant | Enforced by | Test evidence |
|---|---|---|
| Model cannot set route/status/quote/page/section/verdict | strict schemas + renderer | `test_schemas`, `test_renderer` |
| No `tools` key to Ollama; native `/api/chat` only | payload builder | `test_model_payload` |
| Loopback bind; exact Host; Origin on writes; bearer on every `/api/*` | middleware | `test_api_boot` |
| No CDN or inline script/style | CSP + no-CDN CI job + bundled UI | build passes; CI grep |
| Hard caps (8 tools / 4 model calls / 2 loops / 12 chunks / 2.5K tokens / 500 chars) | code constants | budget/packet tests |
| Absence claims gated | silence gate | `test_silence_packets` |
| Deletion verified, no forensic-erasure claim | lifecycle/delete | `test_delete_lifecycle` |
| No answer history; no browser storage of document data | design + UI code | code review; no storage APIs used |
| No legal verdict text rendered | scanner + renderer | `test_legal_scanner`, `test_renderer` |
| Honest docs only | review + AGENTS.md | this repo’s docs |

---

## 4. Acceptance gates by phase (short form)

| Phase | Gate before continuing |
|---|---|
| 0 | Docs/ADRs/CI/setup scripts present; no false “passing” claims |
| 1 | Upload TXT → offsets round-trip via API → delete verified; malformed rejected |
| 1b | Scanned fixture reads locally; OCR banner on derived points |
| 2 | T-MODEL-JSON-01 / CTX-01 / NOTOOLS-01 pass on the pinned version; digest recorded |
| 3 | Direct, phrase, cross-reference and silence tests pass |
| 4 | End-to-end ask with validated citations; forged sid/role/literal/verdict/injection tests |
| 6 | Evaluation + isolated privacy report committed (targets in `EVALUATION.md`) |
| 5 | Every displayed fact clickable; axe CI; no colour-only status |
| 7 | Hardening findings closed or documented |
| 8 | ADR-0010 (“Hermes not built”) committed |
| 9 | S1–S10 pack, demo, rehearsal |

Freeze = organiser deadline − 3 days. The deadline is not known yet; do not invent one.
