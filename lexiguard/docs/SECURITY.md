# Security

## Reporting

Do not open a public issue for a vulnerability that could expose documents or bypass the legal
privacy gates. Send a private report to the maintainers listed in `CONTRIBUTING.md` with the
commit, reproduction, and impact. Never attach a real agreement; use a synthetic fixture.

## Security posture of this build

The application is designed as a loopback-only tool. The security boundary is **the process and
its request handling**, not the localhost network. Same-user malware is out of scope and is stated
to users.

Implemented and tested:

- Loopback bind (`127.0.0.1`) and exact Host allowlist (DNS-rebinding resistance).
- One-time launch code in the URL fragment, single-use, 60 s TTL; in-memory bearer token;
  constant-time comparison; no secret in served HTML.
- Bearer required on every `/api/*` route including health; Origin allowlist on state-changing
  requests; no wildcard CORS.
- CSP baseline with no inline script/style; `nosniff`, `no-referrer`, frame deny, `no-store` on
  API responses.
- Upload validation by magic bytes, size and UTF-8 validity; display-name sanitisation; no
  user-derived filesystem paths.
- SQLite `secure_delete=ON`, rollback journal (no WAL), foreign keys on; per-document directories.
- Deletion validates 32-hex ids and resolves only under `data/docs/`; directory removal verified;
  canary scan reports hits.
- Test socket guard blocks non-loopback connections.

Not implemented yet / not proven:

- PDF child-process isolation (limits matrix exists; supervisor is Phase 1).
- Rate limits, request-time caps and delete-time cancellation (Phase 1/4).
- Model-unload verification on the installed Ollama version (Phase 2).
- Log-redaction tests; content-free logging is policy, not yet asserted by tests.
- Isolated-network privacy proof (Phase 6).
- SBOM and pinned Python lockfile (CI scaffold only; `package-lock.json` exists).

## Parser isolation matrix (Guide 6.2)

| OS | CPU limit | Address-space / RSS | Wall clock | Output cap | Startup notice |
|---|---|---|---|---|---|
| Linux | `RLIMIT_CPU` (Phase 1) | `RLIMIT_AS` (Phase 1) | yes (Phase 1) | yes | none |
| macOS | CPU time where supported | RSS watchdog needed | yes | yes | “reduced parser isolation” |
| Windows | not available | Job Object (optional) | yes | yes | “reduced parser isolation” |

`backend/app/ingest/worker.py` reports the matrix and the notices. A missing limit is never
silently skipped: it is reported at startup.

## CSP baseline

```text
default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self';
img-src 'self' blob: data:; font-src 'self'; object-src 'none';
base-uri 'self'; frame-ancestors 'none'
```

No CDN, no inline scripts or styles, all fonts/icons bundled. `frontend/index.html` has no inline
script; production headers are applied by FastAPI middleware.

## Secrets

- No secret is stored in the repository. The launch code is generated per process and printed only
  to the local console.
- Tokens live in process memory (server) and JS module memory (client). No cookies, query params,
  localStorage, sessionStorage, IndexedDB or logs.
- Do not add `.env` files, keys or model weights to the repository; `.gitignore` excludes them.

## Dependencies

- Apache-2.0 project licence; `scripts/verify_licenses.py` fails on AGPL/GPL/unknown metadata and
  warns on LGPL.
- Never introduce `torch`, `sentence-transformers`, Hugging Face Hub access, PyMuPDF, FAISS or a
  cloud model in the default install. Dense retrieval, if ever enabled, must use local Ollama
  embeddings behind an ADR.
- Pin the Ollama version whose `T-MODEL-*` tests pass; record `/api/tags` digests in
  `docs/MODEL_SETUP.md`.

## Wire-level behaviour

| Route | Auth | Cache | Notes |
|---|---|---|---|
| `GET /` and bundled assets | none | normal static caching | Contains no secret |
| `POST /api/session` | launch code in body | `no-store` | Origin checked; code single-use |
| All other `/api/*` | bearer | `no-store` | Host checked; errors contain no internals |

Health responses are booleans only: no versions, paths, environment values, prompts or DB content.
