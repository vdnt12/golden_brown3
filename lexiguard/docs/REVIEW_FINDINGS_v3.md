# LexiGuard — Independent Review Findings (v3)

**Date:** 18 Oct 2026 · **Reviewed:** `SOLUTION_GUIDE_v2.md` (self-labelled v2.1), `MASTER_IMPLEMENTATION_PROMPT_v2.txt`, `lexiguard_masterprompt_v2_1.txt`, `LexiGuard_Amendments_v2.1.md`, `LexiGuard_Final_Spec_Pack_v2.1.zip`, ZeroDay OSS Participant Guide (all 11 pages).
**Not done:** I ran no code and no model. Everything below is a document review plus checks against public pages read on 18 Oct 2026. Nothing here is a test result.

## 1. Verdict

**The design is strong. The package is not ready to implement from as shipped.** Do not hand the current files to a coding agent. Use the v3 files (this folder), do the Day-0 hardware gate, and accept the tier cut in §4 — then start.

| Question | Answer |
|---|---|
| Is the architecture sound and aligned with the PS2 rubric and gates? | **Yes.** Evidence-first, backend-rendered citations, closed enums, legal policy, privacy evidence all map to criteria 2, 3, 4 (the ones that cap the score at 40). |
| Is everything in the package correct and consistent? | **No.** 6 blockers and 9 serious issues below. Most are fixed in the v3 documents; three need *your* action (hardware gate, deadline, held-out author). |
| Can you proceed directly to implementation? | **Not yet.** After the 6-step checklist in §6 (≈1–2 hours), yes. |
| Biggest risk to winning | **Scope vs. an unannounced deadline**, then **model latency on your laptop**, then a legal-verdict scanner that blocks correct answers. Not the architecture. |

## 2. What I verified (sources read on 18 Oct 2026)

| Claim in the package | Result | Source |
|---|---|---|
| `gemma4:e4b-it-q4_K_M` exists, 6.6 GB, 128K, digest `dc35e8d9c606`; `gemma4:e2b-it-q4_K_M` 4.6 GB, `b37049369adf` | **Confirmed** | Ollama tags page |
| `OLLAMA_NO_CLOUD=1` / `disable_ollama_cloud`; log line `Ollama cloud disabled: true`; `keep_alive:0` unloads; default context 4096 | **Confirmed** | Ollama FAQ |
| FAQ documents Ollama update-check/telemetry behaviour | **Not documented** — so the package must *measure* it, not assert it (done in v3 §11.6) | Ollama FAQ |
| Gemma 4 is Apache 2.0; E4B = 4.5 B effective / 8 B with embeddings | **Confirmed** | Gemma 4 model card |
| pypdfium2 Apache-2.0 OR BSD-3; wheels for Windows/macOS/Linux; bundled PDFium licences must ship | **Confirmed** (5.14.0, 4 Oct 2026) | PyPI |
| Ollama #15260: `think:false` dropped `format` on Gemma 4 | **Confirmed — and it is FIXED in 0.21.1.** Amendments listed it as a live hazard without saying so | GitHub issue page |
| Ollama #8063: schema-invalid output on Gemma 4 | **Confirmed, open — but on `-qat` tags** (e2b/e4b/12b), partly a `\d` pattern grammar error. Amendments *recommend a `-qat` benchmark row*: that is the variant with the open bug | GitHub issue page |
| Ollama #18861: empty reply after tool response with `think:false` | **Confirmed, open (opened 8 Oct 2026) — but reported on `gemma4:26b`**, not E4B. Supports "no `tools[]`" but is not E4B-specific evidence | GitHub issue page |
| Ollama #16776: MLX runner ignores `format` | **Confirmed, open** (reported on `gemma4:26b-mlx`) | GitHub issue page |
| Participant rubric (15/15/15/15/10/12/8/10), cap 40 on criteria 2–4, 0.70/0.30 scoring, gates G1–G5, L1–L4, S1–S10 | **Matches the PDF exactly** | Participant Guide pp.9–11 |
| Gemma 4 E2B/E4B accepted as "Gemma 3n-class" | **Confirmed** | Participant Guide p.7 |
| Submission deadline | **Not found.** PDF says "announced separately"; Hacktoberfest.com says dates not announced | Participant Guide p.11; hacktoberfest.com |
| #15288, #18774 (cited by Amendments) | Not checked by me | — |
| Hermes claims; pypdfium2 highlight behaviour; Tesseract on your OS | Not checked (Hermes is now off the critical path) | — |

## 3. Defects

### Blockers — fix before any code

| # | Finding | Why it matters | Fix (where) |
|---|---|---|---|
| B1 | **The "Final Spec Pack v2.1" zip is the un-amended v2.** Its Guide and prompt are byte-identical to the two uploaded v2 files; it contains neither the Amendments nor the v2.1 prompt. | An agent given the zip implements v2 and never sees T1–T9/R1–R8. | v3 Guide merges everything; delete the zip contents. |
| B2 | **Two prompts with opposite precedence.** v2 prompt: "the Guide wins". v2.1 prompt: "the Amendments win". v2.1 prompt still calls itself v2.0, makes `text` optional where the Guide requires it, says ≥100 questions where the other says 144. Amendments cite a file name (`LexiGuard_Solution_Implementation_v2.md`) that does not exist. | Agent told to "stop and report conflicts" will stall or pick arbitrarily. | One authority (Guide v3) + one prompt (v3). |
| B3 | **The repo baseline in the Guide is stale and the repo's README contradicts the design.** Live `main` has 2 commits and a README claiming a "RAG engine powered by Gemma 4 & FAISS", "100% localhost & on-device execution", "verbatim legal citations". The Guide says 1 commit, no README, lexical-first, dense off. | A public README promising unbuilt/unverified privacy and citations is a "no fabrication"/honesty risk; judges read it first. | Phase 0 replaces the README (Guide §0.2, prompt "Initial repository state"). |
| B4 | **Scope is not survivable for an unannounced deadline.** 9 phases, dozens of named tests, 5 contracts incl. a 50+ page and a scanned one, 144 labelled questions with independent review, two-model benchmark, isolated-network audit, recording, accessibility CI. | My rough estimate (not measured): Tier 0 ≈ 4–6 focused days with AI help, Tier 1 another 5–8. Hacktoberfest ends 31 Oct; the organiser deadline is unknown. Half-built everything scores worse than finished-core. | Tiers + day-0 gate + schedule scaling (Guide §15.1). **You must tell the agent the deadline.** |
| B5 | **No hardware gate; per-question latency is unbounded.** v2.1 allows 5–8 Gemma calls per answer (router, expansion, NextAction ×2, answer, retries, entailment). Public guidance describes CPU-only E4B as "a crawl"; E4B needs ≈6.6 GB for weights alone plus KV cache. | On a CPU laptop one answer can take minutes → can't demo, can't run 100+ evaluation questions ×2 models, recording blows 5 minutes. | Day-0 gate (≤2 h), fast path = 1 call, ceiling 4, E2B default if slow (Guide §8.3a, §15.1). |
| B6 | **The legal-verdict scanner as specified will block correct answers.** Keyword scanning "valid / legal / lawful / void / fair" hits "this agreement is **valid for** 11 months" (ubiquitous in leave-and-licence deeds), "**legal** heirs", "**lawful** purposes", and the glossary's own definitions ("legal right…"). | Correct restatements replaced by limitation templates → accuracy and usability fall; or the team loosens the scanner and a real verdict slips through (cap 40). | Pattern-based scanner with source-echo exception + `T-LEGAL-FP-01` corpus (Guide §9.3a). |

### Serious — fixed in v3 unless marked "you"

| # | Finding | Fix |
|---|---|---|
| S1 | **Amendment T3 recommends a `-qat` benchmark row; the open schema bug #8063 is on `-qat`.** Also #15260 is fixed (≥0.21.1) but the package never states a minimum version. | Exclude `-qat/-mlx`; minimum Ollama 0.21.1; no `pattern`/`\d` in schemas (§3.2a). |
| S2 | **Metrics can be gamed by refusing.** Targets (UCR ≤5 %, silence precision ≥95 %…) are all satisfiable by answering almost nothing. | Add answer-rate ≥80 %, false-refusal ≤15 %, scanner false-block ≤5 % (§14.3). |
| S3 | **The isolated-network test proves little as written.** A loopback-only namespace makes an empty capture true by construction. | Record connection *attempts* (strace/dummy interface), add a **negative control** that must be detected, plus a `docker --network none` path that also works for Windows/macOS judges (§11.4). |
| S4 | **Token bootstrap leaks the token to any local process.** The token is embedded in the HTML served to anyone who can `GET /`; the Guide's own limitation row says "localhost is not a security boundary" and relies on the token. | One-time fragment code → in-memory token; HTML holds no secret; `T-SEC-BOOT-01`; meta fallback with honest threat model (§11.3). |
| S5 | **Language gate depends on an unnamed detector; TXT has no pages; parser limits are Linux-only.** | Deterministic script/stop-word gate; TXT virtual pages; platform matrix with startup notices (§6.1, §6.2, §6.4). |
| S6 | **"Reviewed" glossary overclaims.** A team-written glossary is not lawyer-reviewed. | Renamed "curated"; UI label "not legal advice"; reviewer recorded per entry or no review claim (§9.4, §18). |
| S7 | **Overstated guarantee wording** ("every factual output is validator-approved"). The checks prove quote integrity and catch invented numbers, swapped roles, flipped modality — not that the paraphrase is semantically faithful. | Documented limit; UCR measured by human labelling (§9.1, §18). |
| S8 | **Context-truncation guard can be fooled.** `prompt_eval_count` may under-report when a prompt prefix is cached (to verify on your build). | Pre-budget by token estimate *and* post-check; repeated-prompt test (§3.2a). |
| S9 | **Held-out independence needs a second person.** If you wrote the lexicon and the test contracts, the held-out set is not held-out. | Teammate, or a different model with provenance logged and hand-checked gold labels (§16.3). **(you)** |

### Minor / housekeeping

- Guide Appendix B smoke test used `additionalProperties:false`, contradicting T1 → removed.
- `T-MODEL-JSON-01` had no thresholds → ≥95 % first-try, ≥99 % after one retry, set before the run.
- Phase order text said "do not reorder" while Amendments moved Phase 6 before 5 → stated in §15.1.
- Seeds give same-machine repeatability, not cross-hardware determinism → stated.
- LGPL handling undefined in the licence gate; PDFium `BUILD_LICENSES` must ship → §17.
- Recording ≤5 min vs minutes-per-answer latency → time-lapse allowed only when labelled (§16).
- Repo name `golden_brown1` is weak for the contribution-quality score → optional rename to `lexiguard`; topics not set yet.
- Hermes: the rubric awards it nothing; now ADR-0010 by default (Amendments R7, kept).

## 4. Scope decision (recommended)

| Tier | Contents | Do it when |
|---|---|---|
| **0 – submittable core** | Upload PDF/TXT → parse → FTS5 + lexicon → silence gate → 1-call Gemma answer → validator/renderer/scanner → glossary + jurisdiction flags → minimal UI → T8 isolated smoke capture → honest README | Always, first |
| **1 – points** | Overview core-10, Review, Attention first, Questions to bring, per-page language, OCR, query expansion, ≥100 questions + ≥2 independent held-out, E2B-vs-E4B benchmark, Docker path, axe CI, recording, S1–S10, 3-person rehearsal | Full Tier 1: ≥14 days to freeze. Tier 1 core only: 9–13 days (Guide §15.1 table) |
| **2 – nice** | 144 questions, entailment, dense, suggested edges, Investigate, employment-lite, Hermes | ≥3 spare days only |

## 5. What is genuinely good — keep

- Model never types quotes, pages or sections; backend renders them from stored sentences (this is what makes criterion 2 winnable).
- Closed missing-information enum and `NOT_LOCATED` only after a full silence procedure.
- Deterministic pre-router for legal-verdict paraphrases; "stricter route wins".
- Source quotes immutable and visually separated from LexiGuard's own prose.
- "Designed for local processing" until a saved isolated-run report exists.
- Privacy evidence that avoids saving raw loopback payloads; honest deletion wording (no forensic-erasure claim).
- No `tools[]` to Ollama, GGUF q4_K_M only, Pydantic always.
- Specific escalation panel and deterministic "Attention first" (answers the rubric's "specific escalation" and "useful prioritisation").

## 6. Do these six things before the first coding session

0. **Today, before anything else:** replace the root `README.md` on `main` with `docs/README_REPLACEMENT.md` (the live README is public and makes claims that are false: FAISS RAG, 100% on-device, verbatim citations). This does not need an agent session.
1. Put `SOLUTION_GUIDE_v3.md`, `MASTER_IMPLEMENTATION_PROMPT_v3.txt` and this file in `docs/` on a branch; do **not** commit the v2/v2.1 prompts, the Amendments or the zip.
2. Give the agent write access to that branch (or it will only show diffs), and say explicitly "do not push to `main`".
3. Run the **Day-0 hardware gate** and tell the agent the result (RAM, GPU/CPU, E4B vs E2B timing).
4. Tell the agent the **organiser deadline** as soon as it is announced; until then it builds Tier 0.
5. Decide **who writes the held-out contracts** (§16.3).
6. Run phases as **separate sessions**; commit after each; paste back real test output before approving the next phase.

## 7a. Post-delivery consistency audit (v3.1 patch, 18 Oct 2026)

Re-reading v3.0 against itself found five defects that the original review did not list. All are patched in the v3.1 files; none was tested by running code.

| # | Defect in v3.0 | Fix |
|---|---|---|
| C1 | §15 heading said "do not reorder" while §15.1 runs Phase 6 before 5 (the same contradiction as the old B2, in miniature). Phase 5 also listed Investigate, which is Tier 2. | Heading states the execution order; Investigate moved to Tier 2. |
| C2 | The call ceiling did not add up: "expansion and/or NextAction" + answer + 2 retries = up to 5 calls against a ceiling of 4. No wall-clock cap, so 4 calls could still mean minutes. | "Or", not "and/or"; worst cases listed (3 fast, 4 refined); wall-clock cap = 4 × Day-0 p50 (judgement, untested). |
| C3 | `docker --network none` publishes no ports, so a judge's browser cannot reach a UI inside it. The portable privacy path as written could not be demoed. | Docker target is a headless scripted flow that writes a report; UI stays on `make demo`; no claim of an interactive isolated UI. |
| C4 | Schedule scaling promised Tier 1 (minus OCR/axe) in 7–11 days, but the estimates sum to ≈9–14 days; the table in §4 here said ≥7. | Three-row table (≥14 / 9–13 / ≤8), re-estimate after Phase 1. |
| C5 | The honest README was left to the agent's Phase 0, but the false README is public now. | Checklist step 0: replace it today with `README_REPLACEMENT.md`. |

Also re-confirmed on 18 Oct 2026: Ollama #15260 was fixed by a change shipped in v0.21.1 and scoped to gemma4 (a commenter confirms it worked). I did not re-open #8063, #18861 or #16776, or the tags page.

## 7. Residual risks I cannot remove from here

- Gemma 4 E4B quality on real, messy Indian rental PDFs is unknown until measured; fail-closed behaviour will turn model weakness into *abstentions*, which the answer-rate metric will expose — expect to tune retrieval and prompts.
- Table/multi-column extraction order with pypdfium2 can be wrong; the design warns and never fabricates highlights, but accuracy on such pages will be lower.
- Ollama and Gemma 4 are moving targets (three structured-output/empty-reply bugs open on 18 Oct). Pin versions and re-run `T-MODEL-*` after any upgrade.
- Scanner patterns, thresholds (BM25 confidence, 60 s rule) and token estimates in v3 are my design judgements, untested.
