# ADR-0008 — Fail-closed degradation and fixed status precedence

- **Status:** Accepted
- **Date:** 2026-10-18

## Context

Multiple conditions can be true at once (ambiguous text, conflicting clauses, unsupported claims,
absent topic, legal limit). Without a fixed order, the UI can show a reassuring status while a
harder condition is true.

## Decision

- Statuses come from a closed enum and resolve by fixed precedence:
  `ERROR_PROCESSING > ERROR_LOCAL_MODEL_UNAVAILABLE > LEGAL_LIMIT > CONFLICTING > AMBIGUOUS >
  INSUFFICIENT_EVIDENCE > NOT_LOCATED > LIMITED > OUT_OF_SCOPE > ANSWERED`.
- A point that fails validation is dropped; if nothing survives, the answer degrades to
  `INSUFFICIENT_EVIDENCE`.
- `NOT_LOCATED` is allowed only when the silence gate proves readable coverage; otherwise the
  result is `INSUFFICIENT_EVIDENCE`.
- Errors never fall back to another model or a cached answer.
- Missing-information codes are a closed enum: `UNREADABLE_CONTENT`,
  `REFERENCED_MATERIAL_NOT_PROVIDED`, `TOPIC_NOT_LOCATED`, `CONTEXT_REQUIRED`.

## Consequences

**Positive**: the worst relevant condition wins; no optimistic status; deterministic UI.

**Negative**: users may see a limitation when a partial answer exists; answer rate is lower.

## Alternatives rejected

- “Best effort” aggregation: hides conflicts and legal limits.
- Model-chosen status: untestable and unsafe.

## Follow-ups

- Property tests over all condition combinations (`core/enums.py`).
- UI must display the winning status with its missing-information reason.
