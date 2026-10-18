# ADR-0007 — Pattern-based legal-boundary policy; `legal_verdict` always null

- **Status:** Accepted
- **Date:** 2026-10-18

## Context

A local model can drift into advice (“this clause is unenforceable”, “you should refuse to pay”).
The product must explain wording without giving a legal verdict, and the behaviour must be
testable without a lawyer in the loop for every release.

## Decision

- `validation/legal_policy.py` scans assistant-authored text for verdict/advice patterns
  (validity, enforceability, legality, “you should/shouldn’t”, reassurance, outcome prediction).
- A limited source-echo exception applies only to STATED/RESTATEMENT points, i.e. the user’s own
  document wording being reported verbatim.
- On a hit, the system returns `LEGAL_LIMIT` with neutral escalation templates from
  `lexicons/escalation_templates.yaml`; it never softens or rewrites the claim into a verdict.
- `legal_verdict` exists in the schema and is always `null`.
- A corpus (`tests/data/scanner_corpus.jsonl`) asserts both directions: must-block and must-pass.

## Consequences

**Positive**: no legal conclusions; deterministic, fast, auditable; false-block rate measurable.

**Negative**: pattern matching can miss paraphrases and can block legitimate conceptual text;
corpus maintenance is manual; “legal information vs advice” remains a judgement call.

## Alternatives rejected

- Asking the model to avoid verdicts via prompt only: untestable, easily overridden by injection.
- A lawyer-reviewed phrase list: desirable but out of scope for the deadline.

## Follow-ups

- Expand the corpus to the Guide’s full set (≥40 per direction) and track false-block rate.
- Re-run the corpus whenever glossary or prompt text changes.
