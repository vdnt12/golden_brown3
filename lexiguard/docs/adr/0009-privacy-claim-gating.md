# ADR-0009 — Privacy claims gated on isolated-network evidence and a negative control

- **Status:** Accepted
- **Date:** 2026-10-18

## Context

“100% on-device” is easy to say and hard to prove. A successful `docker run --network none` that
does nothing, or a capture that could not have seen traffic, is not evidence.

## Decision

- The UI and README say **“Designed for local processing”** until an isolated report exists for the
  exact release.
- Evidence requires: an isolated environment with loopback only; attempt-visible capture
  (`strace`-style connect/send trace or dummy-interface capture), filtering that is disclosed; a
  **negative control** that must be detected; a full scripted flow; and a canary scan of
  app-controlled paths.
- Raw loopback payloads are never committed; an empty capture is not reported as proof unless the
  negative control fired.
- Wording rules: deletion is “app-controlled files removed and verified”, never forensic erasure.

## Consequences

**Positive**: claims are falsifiable and reviewable; the team cannot accidentally overclaim.

**Negative**: more work before the claim can be made; the scaffold must repeatedly say “not
verified”.

## Alternatives rejected

- Trusting the architecture: no evidence of the actual binary's behaviour.
- `--network none` without attempt logging: cannot distinguish “no attempt” from “blocked”.

## Follow-ups

- `scripts/run_isolated_demo.sh` currently exits 2 on purpose.
- `tests/privacy/negative_control.py` exists; it has not been run.
