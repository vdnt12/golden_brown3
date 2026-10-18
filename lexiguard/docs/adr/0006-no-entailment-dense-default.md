# ADR-0006 — No entailment or dense retrieval in the default build (Tier 2 deferred)

- **Status:** Accepted
- **Date:** 2026-10-18

## Context

The design lists an optional entailment pass and optional dense retrieval. Both add a second model
(or a large dependency), new failure modes, extra latency and evaluation obligations. The core
guarantees — verbatim quotes, correct statuses, legal-boundary behaviour — do not depend on them.

## Decision

- Entailment checking is **off by default** and is not part of the default install.
- Dense retrieval is not implemented; retrieval is lexical (ADR-0004).
- These are Tier 2 features. They may be added only with a new ADR, an evaluation that shows the
  lexical/deterministic baseline is insufficient, and a local-only model with a recorded licence.

## Consequences

**Positive**: smaller install, fewer models, simpler privacy story, faster iteration on the parts
that matter for correctness.

**Negative**: semantic faithfulness is not directly checked; vocabulary mismatch can reduce recall;
a claim with the right numbers in the wrong relationship can pass validation (measured by UCR).

## Alternatives rejected

- Ship entailment by default: doubles model calls and latency for an unmeasured gain.
- Ship dense retrieval because “RAG needs vectors”: not supported by this corpus size.

## Follow-ups

- Report UCR honestly in `EVALUATION.md`; describe the residual gap in `LIMITATIONS.md`.
