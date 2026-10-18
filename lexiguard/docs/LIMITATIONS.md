# Known limitations

This file is deliberately blunt. If a behaviour is not implemented, or was not
exercised on this machine, it is listed here rather than implied by a green test.

## 1. What is proven, and what is not

| Claim | Status | Evidence |
|---|---|---|
| Ingests 510/510 CUAD contracts without failure | **proven** | `reports/cuad_evaluation.json` |
| Every rendered quotation is an exact substring of stored text | **proven** (9,731 CUAD + 24 PRS + fixture quotations, 0 failures) | same |
| A model that invents a figure is rejected | **proven** with a scripted stand-in provider | `reports/fixture_evaluation.json`, `tests/integration` |
| A cited sentence that was never shown to the model is rejected | **proven** | `SID_NOT_EXPOSED_IN_RUN` rows |
| Gemma/Hermes answer quality on real contracts | **not proven** — no GPU, no Ollama in the build sandbox | `reports/model_roundtrip.md` is a stub-runtime transcript |
| OCR on scanned PDFs | **implemented, not exercised** — Tesseract absent; synthetic PDFs are digital | `ocr_available: false` in `/api/health` |
| Indian statute text (IndiaCode) | **not obtained** — edge filter blocks the PDF | `datasets/manifest.json → inaccessible_sources` |
| open-india-law dataset | **not obtained** — HF gate requires a token | same |

## 2. Retrieval and mapping

- Concept matching is regex-based over sentences. On CUAD the **parties** card
  recalls 95.7% of contracts but only **2.4%** of lawyer-labelled party spans:
  it finds the contract, not every party sentence. Treat the map as an index into
  the document, not a checklist.
- A card that says `NOT_LOCATED` means "no matching sentence was found in the
  readable text". It never means the clause is absent, void or unenforceable.
- `INSUFFICIENT_EVIDENCE` means the question/claim could not be settled from the
  text that was read; it is the honest answer for partial documents.
- Conflict detection compares numeric values across sections. It produces
  **candidates**; on discursive documents (a policy brief comparing states) it
  will flag comparisons, not contradictions. See `reports/india_law_evaluation.md`.
- Retrieval is lexical (SQLite FTS5) with a bounded refinement round. There is no
  embedding model, so a paraphrase that shares no words with the document may
  miss. `_relevant()` deliberately drops low-overlap hits, which makes honest
  `NOT_LOCATED` possible at the cost of some recall.
- The 32-hex document id is not a capability: all access requires the session
  bearer token, which is bound to the process lifetime.

## 3. Model layer

- Two families are wired: Gemma (`gemma4:e4b-it-q4_K_M` primary,
  `gemma4:e2b-it-q4_K_M` low-memory) and Hermes (`hermes3:8b`). Both go through
  the same adapter, prompt, schema and validator (ADR-0011).
- **No live inference was run in this environment.** The sandbox has no Ollama
  daemon and no GPU. `reports/model_roundtrip.md` is produced against a stub that
  speaks Ollama's HTTP contract; it proves transport, schema enforcement,
  provenance checks and rendering for both tags, and proves nothing about answer
  quality. Run `python3 scripts/verify_models_live.py --real` on a machine with
  the models pulled to replace it.
- The model is untrusted: its output is parsed, validated and mostly discarded
  when it does not match quoted text. A weak model therefore degrades to
  `INSUFFICIENT_EVIDENCE`, which is safe but unhelpful.
- Temperature 0 and `seed: 42` reduce, but do not eliminate, run-to-run variation
  across quantisation/kernels.
- `num_ctx: 8192` bounds the context. The packet builder refuses oversized
  packets instead of truncating them silently.

## 4. Ingestion and formats

- PDF only, `.txt` only (UTF-8), 20 MB and 300 pages by default.
- Scanned PDFs without a text layer need local Tesseract. Without it the pages are
  marked unread and absence claims are disabled — not silently skipped.
- `.docx`, `.rtf`, images and password-protected PDFs are rejected.
- PDF parsing runs in a forked child process with a timeout. On Python 3.13 this
  emits a `DeprecationWarning` about fork in a multi-threaded process; a future
  Python release will change the default start method. This is a known risk, not
  a failure.
- Hidden-text detection is a **heuristic**: a run of ≥5 zero-width characters, or
  an uncompressed `/Tr 3` invisible-text marker. A negative does not prove the
  absence of white-on-white text in a compressed stream.
- `language_detected` is script-based, not a language classifier: it detects
  non-Latin scripts and very low English function-word density.

## 5. Security and privacy

- Loopback binding, Host allowlist, Origin check on state-changing requests,
  single-use launch code (60 s), in-memory bearer token, no `localStorage`.
- Rate limiting on `/api/session` is **not implemented**; codes are 256-bit and
  single-use, but this is still a gap against the supplied guide.
- Deletion removes app-controlled files and the SQLite index and verifies their
  absence. It is **not forensic erasure**: SSD wear-levelling, swap, hibernation,
  filesystem journals and backups are outside the application.
- The model daemon (`ollama serve`) is a separate process outside LexiGuard's
  sandbox. LexiGuard cannot prove what that daemon logs or whether it phones
  home. The claims in `docs/PRIVACY.md` are scoped to code in this repository.
- No independent security review, no penetration test, no fuzzing campaign.

## 6. UI

- React + TypeScript, built with Vite; the build is checked in `frontend/dist`.
- No browser-based end-to-end test and no accessibility audit (axe/Lighthouse)
  has been run here. Keyboard focus order and contrast were written to WCAG AA
  intent but are unverified.
- The UI never renders a claim the backend did not send, and has no code path to
  construct a verdict. `legal_verdict` is `null` by type.

## 7. Datasets

- CUAD is **commercial** contracts; a high score there says nothing about tenancy
  accuracy. The PRS brief is a policy document, not an agreement. Neither was used
  to train or tune a model.
- No real tenancy agreement was used anywhere. All fixtures are synthetic.
