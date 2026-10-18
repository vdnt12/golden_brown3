# Privacy

**Current claim level: “Designed for local processing.”**
No isolated-network report exists for this build, so no stronger wording may appear in the UI,
README, slides or demo narration. The switch to “Verified local processing — see report.” requires
the Phase 6 evidence below, for the exact release being shown.

---

## 1. Network-call inventory (to be verified by capture, not asserted)

| Component | Destination | When | Carries document content? | Default | Evidence status |
|---|---|---|---|---|---|
| Browser ↔ API | `127.0.0.1:<port>` | normal use | yes (local only) | on | loopback by code; not captured |
| API ↔ Ollama | `127.0.0.1:11434` | normal use | yes (local only) | on | loopback enforced in provider constructor |
| Ollama → ollama.com | model pull / update checks | setup only, updater unknown | no | must not occur during use | **unmeasured** |
| pip / npm / Tesseract data | package registries | setup only | no | never during document processing | documented in setup script |
| Anything else | — | — | — | none | no other client exists in code |

Notes:
- The Ollama FAQ does not document update/telemetry behaviour. The isolated run must **measure**
  attempts rather than assume zero.
- Raw loopback payloads are never saved. They necessarily contain prompt/evidence text, so saving
  them would itself create a document-content leak in the repo.
- Environment flags (`OLLAMA_NO_CLOUD=1`, `DO_NOT_TRACK=1`, `HF_HUB_OFFLINE=1`,
  `OLLAMA_DEBUG` unset) are defence in depth, **not proof**.

---

## 2. Localhost hardening in this build (implemented and tested)

| Control | Implementation | Test |
|---|---|---|
| Loopback bind | `Settings.host = 127.0.0.1`; runner uses settings | server smoke (§TEST_PLAN 1) |
| One-time launch code | 256-bit, single-use, 60 s TTL, URL fragment | `test_security_units`, `test_api_boot` |
| No secret in HTML | `/` contains no code; fragment stripped client-side | `test_placeholder_index_contains_no_secret` |
| Bearer on every `/api/*` | middleware, constant-time compare | `test_api_boot` |
| Exact Host allowlist | `127.0.0.1:<port>`, `localhost:<port>` only | `test_bad_host_is_rejected` |
| Origin check on writes | exact allowlist; no wildcard CORS | `test_bad_origin_is_rejected_on_post` |
| CSP / headers | `default-src 'self'`, no inline, frame-deny, nosniff | header check on live server |
| `no-store` for API | middleware on `/api/*` | code + header check |
| No browser persistence | token in module memory; no storage APIs used | code review |
| Socket guard in tests | non-loopback `connect` raises | `tests/conftest.py` |

Still to add (Phase 1/4): per-IP rate limits, request-time caps, document-work cancellation on
delete, model unload verification, log redaction tests.

---

## 3. Data handling

| Data | Storage | Retention |
|---|---|---|
| Source PDF/TXT | `data/docs/<doc_id>/` | until Delete |
| Pages/sentences/chunks/FTS | per-document SQLite in the same directory | until Delete |
| Questions/answers | memory only | request lifetime |
| Run ledger | per-document SQLite (ids, counts, codes; no text) | until Delete |
| Browser token | JS memory | tab lifetime / launch URL reload |
| Embeddings/history | never created in the default build | — |
| Logs | content-free by policy (no question, filename, names, evidence) | to be tested in Phase 1 |

`doc_id` is a random 128-bit server value; the client never chooses a path. Display filenames are
sanitised and used only for UI display.

### Deletion wording

Correct: “App-controlled files for this document were removed and their absence was verified.”
Incorrect: “Data was securely erased from your device.” SSD wear-levelling, OS swap/hibernation,
filesystem journals and external backups are outside the application's control.

Deletion steps: reject new work → close handles → unload model (`keep_alive:0`, verify version) →
remove directory → clear session binding → canary scan of app-controlled paths → report. Today
only directory removal + scan + report exist (`store/delete.py`, `services/lifecycle.py`).

---

## 4. Canaries and fixtures

Every synthetic fixture embeds `CANARY-LG-<NAME>-NNN`. After an upload→ask→delete run, the audit
searches app/Ollama/gateway logs, temp dirs and the isolated workspace for those strings.

- Canary **present** in app-controlled files after delete → failure.
- Canary present in loopback traffic → expected (local content); do not capture it.
- Canary present in a **non-loopback** capture → critical privacy failure.

Current fixtures: simple, Indian-style, conflict, ambiguous, injection (see `fixtures/README.md`).

---

## 5. Evidence procedure (Phase 6, not yet run)

1. Put **app and Ollama in the same isolated environment** (network namespace with loopback only,
   or equivalent) so loopback works while egress does not.
2. Capture **connection attempts**, not just successes:
   `strace -f -e trace=connect,sendto,sendmsg` filtered to non-loopback/non-AF_UNIX destinations,
   or a dummy interface + `tcpdump` with a DROP rule. Save the filtered log and an unfiltered
   destination summary.
3. Run the **negative control** (`tests/privacy/negative_control.py`, target `192.0.2.1`). The
   report must show the control **was detected**; otherwise the instrument is untrustworthy and
   an empty capture means nothing.
4. Run the complete scripted flow: launch-code exchange → upload synthetic fixture → ask → delete
   → canary scan → deletion report.
5. Save under `reports/privacy/<commit-or-release>/`:
   `environment.txt`, `ollama --version`, the log line `Ollama cloud disabled: true`, filtered
   attempts, negative-control result, canary results, deletion report, `docker inspect` network
   mode if the Docker path was used.
6. Portable path: `docker run --network none` headless flow writing its report to a separate
   writable volume. A `--network none` container publishes **no ports**, so this is privacy
   evidence, not an interactive UI. Judges use `make demo` for the UI and the report for privacy.

No step above has been performed for this build.

---

## 6. Wording rules

| Situation | Allowed wording |
|---|---|
| No isolated report for this release | “Designed for local processing.” |
| Successful report committed for this exact release | “Verified local processing — see report <link>.” |
| Deletion | “App-controlled files removed and verified.” |
| Ollama unload verified | “The local model was asked to unload (keep_alive: 0); see report.” |
| Everything else | Describe the design goal, never a guarantee |

If a claim cannot be backed by a committed artifact produced by a recorded command, it does not go
in the README, UI, slides or demo script.
