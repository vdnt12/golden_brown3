# ADR-0011 — Gemma and Hermes model families are both selectable

- **Status:** Accepted (supersedes the "one pinned model family" clauses of ADR-0010)
- **Date:** 2026-10-18

## Context

ADR-0010 rejected a model gateway, automatic routing and silent fallback. It also
froze the build to a single model family. The product requirement now includes
running **both Gemma and Hermes** so a reviewer can compare them on the same
document, and the supplied architecture names both families.

Two different things are called "Hermes":

1. the **Hermes model family** served by Ollama (e.g. `hermes3:8b`);
2. the **Hermes Agent framework**, a tool-calling agent with a 64K context
   requirement.

Only (1) is in scope. (2) would duplicate the bounded runtime, increase memory
pressure and add an unvalidated component, so it stays unbuilt (ADR-0010 still
applies to it).

## Decision

- One provider class (`OllamaNativeProvider`), one loopback endpoint, **two to
  three allowlisted model tags** configured in `Settings`:
  `gemma4:e4b-it-q4_K_M` (default), `gemma4:e2b-it-q4_K_M`, `hermes3:8b`.
- The caller selects a model **explicitly** by alias (`gemma`, `gemma-e2b`,
  `hermes`) or exact allowlisted tag. `GET /api/models` lists only those.
  Unknown names are rejected with HTTP 422; arbitrary registry tags cannot be
  loaded by a client.
- **No automatic fallback and no silent substitution.** If the selected model is
  not installed, the answer is `ERROR_LOCAL_MODEL_UNAVAILABLE`. The UI disables
  unavailable models rather than picking another.
- Every answer records the tag that produced it in `run_meta.model_tag`, so a
  transcript can never be attributed to the wrong model.
- Validation is model-independent: provenance, literals, modality, roles,
  conflict sections and the legal scanner run identically for every model. A
  weaker model can only produce fewer validated claims, never looser checks.
- The system prompt and JSON schema are identical for both families.

## Consequences

**Positive**: side-by-side comparison on the same document; the same contract
tests both models; no hidden network path; the privacy story is unchanged
because both models run in the same local daemon.

**Negative**: two models to benchmark and pin; a model that follows the schema
poorly will produce more `INSUFFICIENT_EVIDENCE` results, which is visible and
honest but may look like a regression.

## Alternatives rejected

- Automatic fallback Gemma → Hermes on failure: makes answer provenance
  ambiguous and hides unavailability.
- Free-form model string from the client: lets a page load an arbitrary model
  and breaks the privacy and resource story.
- Building the Hermes Agent framework: adds a second runtime that would bypass
  the bounded tool loop.

## Verification

- `tests/integration/test_provider_http_roundtrip.py` runs the real adapter over
  HTTP against a stub Ollama for both tags and asserts the recorded model tag,
  model-call count and validator outcome.
- `scripts/verify_models_live.py --real` performs the same flow against a real
  daemon; its output belongs in `reports/model_roundtrip.md` only when run.
