# Architecture decision records

Short, dated decisions with consequences. A decision that changes an invariant in
`docs/ARCHITECTURE.md` requires a new ADR (or a superseding one), not a silent code change.

| ADR | Title | Status |
|---|---|---|
| [0001](0001-local-first-loopback.md) | Local-first, loopback-only architecture | Accepted |
| [0002](0002-ollama-native-json-schema.md) | Gemma 4 via native Ollama `/api/chat` with a JSON Schema, no tools | Accepted |
| [0003](0003-model-proposes-backend-renders.md) | Model proposes; backend renders citations and status | Accepted |
| [0004](0004-lexical-first-retrieval.md) | Lexical-first retrieval with SQLite FTS5, no vector database | Accepted |
| [0005](0005-per-document-sqlite.md) | Per-document SQLite with `secure_delete=ON`, DELETE journal | Accepted |
| [0006](0006-no-entailment-dense-default.md) | No entailment or dense retrieval in the default build (Tier 2 deferred) | Accepted |
| [0007](0007-legal-boundary-policy.md) | Pattern-based legal-boundary policy; `legal_verdict` always null | Accepted |
| [0008](0008-fail-closed-status-precedence.md) | Fail-closed degradation and fixed status precedence | Accepted |
| [0009](0009-privacy-claim-gating.md) | Privacy claims gated on isolated-network evidence and a negative control | Accepted |
| [0010](0010-hermes-not-built.md) | Hermes Agent framework not built | Superseded in part by 0011 |
| [0011](0011-gemma-and-hermes-model-selection.md) | Gemma and Hermes model families both selectable | Accepted |

Conventions: status is one of Proposed / Accepted / Superseded / Rejected. Dates are ISO. An
accepted ADR is not edited to change its decision; write a new one that supersedes it.
