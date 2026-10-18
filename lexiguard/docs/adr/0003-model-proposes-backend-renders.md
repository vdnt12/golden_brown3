# ADR-0003 — Model proposes; backend renders citations and status

- **Status:** Accepted
- **Date:** 2026-10-18

## Context

A local 4B model can invent page numbers, misquote text, swap parties or state a legal conclusion.
Users must be able to trust that every quoted passage exists verbatim in their document.

## Decision

- The model returns only `ModelAnswer{points:[{point_id, kind, text, sids}]}`; unknown fields are
  rejected by strict Pydantic models.
- Sentence ids are opaque tokens issued by the backend for this run. Quotes, pages, sections and
  evidence ids are rendered from stored sentence text and metadata.
- A point survives only if provenance, literals, modality/negation, roles, conflict-section and
  legal-boundary checks pass. Otherwise it is dropped or the answer degrades in status.
- `legal_verdict` is a nullable field that is always `null` in outputs.

## Consequences

**Positive**: fabricated quotes become structurally impossible; the UI can show exact spans;
validation failures are attributable.

**Negative**: more backend code; paraphrases that reword numbers can be dropped (fail closed);
citation coverage depends on retrieval.

## Alternatives rejected

- Trusting model-supplied quotes with a string search: off-by-whitespace and hallucinated quotes
  would slip through.
- Post-hoc similarity scoring alone: no hard guarantee.

## Follow-ups

- End-to-end citation-integrity test on every route.
- UCR measurement to quantify semantic gaps (`docs/EVALUATION.md`).
