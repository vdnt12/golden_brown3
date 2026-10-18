# ADR-0002 — Gemma 4 via native Ollama `/api/chat` with a JSON Schema, no tools

- **Status:** Accepted
- **Date:** 2026-10-18

## Context

Open issues report that Ollama's OpenAI-compatible `/v1` path handles Gemma structured output less
reliably than the native path, and that `think:false` was needed for `format` to work on Gemma 4
(fixed in Ollama 0.21.1). Tool calling is nondeterministic and hard to bound; the agent loop must be
deterministic and capped.

## Decision

- Use native `POST /api/chat`, `stream:false`, `think:false`, `format` = a simple app-owned JSON
  Schema, `options.seed` fixed, `temperature: 0`, `num_ctx: 8192`.
- Never send a `tools` key; tool choice is a schema-constrained `NextAction` executed by code.
- Pin `gemma4:e4b-it-q4_K_M` (GGUF q4_K_M), fallback `gemma4:e2b-it-q4_K_M`; never `:cloud`,
  `-mlx`, `-qat`, `-nvfp4`, `-mxfp8` or larger variants.
- Require Ollama ≥ 0.21.1; validate output with Pydantic; allow one format retry; fail closed.
- Pre-budget the prompt and assert `prompt_eval_count + eval_count < num_ctx`.

## Consequences

**Positive**: bounded, reproducible-ish output; no model-initiated side effects; deterministic
tool allowlists.

**Negative**: tied to Ollama's native API and version behaviour; tags/digests move; seeds are
same-machine only.

## Alternatives rejected

- `/v1` chat completions: known structured-output issues with Gemma.
- Free-form JSON parsing: fragile.
- Model-driven tool calling: unbounded loops, injection surface, hard to audit.

## Follow-ups

- `T-MODEL-JSON-01`, `T-MODEL-CTX-01`, `T-MODEL-NOTOOLS-01` acceptance on the pinned version.
- Record `/api/tags` digests in `reports/env.json`.
