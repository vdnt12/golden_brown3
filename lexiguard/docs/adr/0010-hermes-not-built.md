# ADR-0010 — Hermes model gateway not built

- **Status:** Superseded in part by ADR-0011 (Hermes Agent framework still not built; the Hermes model family is now selectable)
- **Date:** 2026-10-18

## Context

An earlier design considered a Hermes-style gateway for routing between local models/providers for
resilience and a “second opinion”. It is not required by the problem statement, adds an unverified
component, and complicates the privacy story and the model-version pinning.

## Decision

- No gateway, no multi-provider routing, no model fallback. `model/gateway.py` refuses construction
  with a clear error and points to this ADR.
- Exactly one provider class (`OllamaNativeProvider`). ADR-0011 later allowed several
  allowlisted model tags (Gemma E4B/E2B and a Hermes tag) to be selected explicitly; there is
  still no automatic fallback or silent substitution.
- Failure to reach the model returns `ERROR_LOCAL_MODEL_UNAVAILABLE` and stops.

## Consequences

**Positive**: one model, one failure mode, one thing to benchmark and pin; no hidden network paths;
smaller codebase.

**Negative**: no automatic resilience if the model misbehaves; switching models requires a config
change and a re-run of acceptance tests.

## Alternatives rejected

- Gateway with silent fallback: violates fail-closed and muddies evaluation.
- Multi-model “second opinion”: doubles cost/latency with no measured benefit.

## Follow-ups

- Remove any future dead hooks rather than leaving them half-built.
- If a gateway is ever proposed, it needs a new ADR with a threat model and a privacy plan.
