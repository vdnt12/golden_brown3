# Security tests (planned)

Dedicated security suite for Phase 4/6. Today, boot/auth/Host/Origin tests live in
`tests/integration/test_api_boot.py`; do not duplicate them here without moving the originals.

Planned cases (see `docs/TEST_PLAN.md`):

- `T-SESSION-ISOLATION`: two browser sessions cannot see each other's documents or tokens.
- `T-DNS-REBIND`: a rebound host cannot reach the API even with a valid token.
- `T-INJECTION-NONET`: injection fixtures cannot trigger a network call or a tool outside the allowlist.
- `T-NOSTORE-HEADERS`: every `/api/*` response carries `no-store` (checked live, not by unit mock).
- `T-FAILCLOSED`: parser crash, model timeout and malformed model output degrade to an error status.
- `T-URL-TOKEN`: launch codes are single-use, expire and never appear in served HTML or logs.

Nothing in this directory should be described as passing until the command was actually run.
