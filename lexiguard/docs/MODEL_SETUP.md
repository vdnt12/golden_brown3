# Model setup and recorded environment

**Status: template. Nothing on this page has been measured yet.**
The adapter (`model/ollama_native.py`), the provider factory and the availability probe are
implemented and wired into `/api/health` and the ask route; only the *numbers* below are missing.
Fill each field on the actual demo machine and paste the command output that produced it. Never
copy values from the Ollama tags page into a report as if you had measured them.

If `/api/health` reports `model_available: false`, the ask route returns
`ERROR_LOCAL_MODEL_UNAVAILABLE` — by design, not a bug.

---

## 1. Day-0 hardware gate (before Phase 1, ≤2 h)

On the machine used for the demo and the isolated run:

1. Install Ollama ≥ 0.21.1 and confirm `ollama --version`.
2. Start headless with cloud disabled:
   ```bash
   OLLAMA_NO_CLOUD=1 ollama serve
   ```
   Confirm the log contains `Ollama cloud disabled: true` (record the exact line).
3. Pull both tags:
   ```bash
   ollama pull gemma4:e4b-it-q4_K_M
   ollama pull gemma4:e2b-it-q4_K_M
   ```
4. Record `/api/tags` names, digests and sizes:
   ```bash
   python3 scripts/verify_model_tags.py     # writes reports/env.json
   ```
5. Run the smoke test in Guide Appendix B, then time one ~3K-token-prompt / ~300-token-output
   call on each model:
   ```bash
   python3 scripts/benchmark_model.py --models gemma4:e4b-it-q4_K_M gemma4:e2b-it-q4_K_M
   ```
6. Apply the decision rule (project judgement, not measured fact):
   - E4B p50 > ~60 s for that call → make E2B the default and say so.
   - Neither finishes in ~120 s → stop; fix hardware/context before writing more code.

---

## 2. Environment record (fill in)

| Field | Value |
|---|---|
| Date/time | |
| Repo commit | |
| OS / kernel | |
| CPU | |
| RAM | |
| GPU / VRAM (if any) | |
| Ollama version | |
| `OLLAMA_NO_CLOUD=1` log line | |
| E4B tag / digest / size | |
| E2B tag / digest / size | |
| Effective `num_ctx` per request | 8192 (set explicitly) |
| `T-MODEL-JSON-01` run (≥50 calls/schema) | not run |
| First-try schema-valid rate | |
| Valid after single retry | |
| Empty content rate | |
| `T-MODEL-CTX-01` (incl. repeated-identical prompt) | not run |
| `T-MODEL-NOTOOLS-01` (live request audit) | not run |
| E4B p50 / p95 for 3K-in/300-out | |
| E2B p50 / p95 for 3K-in/300-out | |
| Peak memory/RSS | |
| `keep_alive:0` unload verified? | |
| Chosen default model + reason | |

---

## 3. Pinning

- Record **digests**, not just tags; tags are mutable.
- The version you pin is the one on which every `T-MODEL-*` test passes.
- Re-run `T-MODEL-*` after any Ollama or model upgrade; digests move.
- Seeds give same-machine repeatability, not cross-hardware determinism. Never claim otherwise.
- Do not benchmark `-qat` (open schema bug) or `-mlx` (runner ignores `format`).

---

## 4. Privacy-relevant setup flags

```bash
export OLLAMA_NO_CLOUD=1
export DO_NOT_TRACK=1
export HF_HUB_OFFLINE=1      # dense models are not installed by default
# Do NOT set OLLAMA_DEBUG
```

Flags are defence in depth, not proof. Measure attempts in the isolated run (see `PRIVACY.md`).
Setup-time downloads are a separate, documented activity and must never receive user documents.
