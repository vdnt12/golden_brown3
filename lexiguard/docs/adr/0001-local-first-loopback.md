# ADR-0001 — Local-first, loopback-only architecture

- **Status:** Accepted
- **Date:** 2026-10-18
- **Deciders:** LexiGuard maintainers
- **Supersedes:** —

## Context

The product handles private rental agreements. The problem statement requires local processing and
the submission requires a privacy story that can be inspected, not asserted. A hosted model or a
bundled cloud SDK would make the central claim untestable and would move document text off-device.

## Decision

- The application binds to `127.0.0.1` only. No `0.0.0.0`, no public interface.
- The model runs locally through Ollama on `127.0.0.1:11434`.
- No cloud model, hosted API, telemetry, analytics or CDN is used at runtime.
- The frontend is built and served same-origin by FastAPI; there is no separate hosted origin.
- Setup-time downloads (packages, model weights, OCR data) are a separate, documented activity and
  never receive user documents.

## Consequences

**Positive**: the privacy claim is testable in an isolated network namespace; there is no
credential to leak; offline operation is possible after setup.

**Negative**: quality is bounded by a 4B-class local model; install size and first-run time are
large; the user must have enough RAM/VRAM.

**Neutral**: an advanced user could point the app at a LAN Ollama, which is out of scope and must
remain undocumented in the default build.

## Alternatives rejected

- Hosted LLM API: violates the core privacy goal.
- Optional cloud fallback: a single misconfiguration would break the claim; rejected.
- Browser-only implementation: no local filesystem or subprocess isolation for PDF parsing.

## Follow-ups

- Isolated-network evidence and canary audit (`docs/PRIVACY.md`).
- Startup warning when the data directory lives in a cloud-synced folder.
