# docs/LIMITATIONS.md

> **No test has been run yet.** This document describes known design limitations and will be updated with measured results.

## Parser isolation

- **Windows:** No `resource` module available. Parser sandbox enforces only wall-clock timeout, output-size cap and page/size caps. No Job Object memory limit. See `docs/SECURITY.md`.
- **macOS:** `RLIMIT_AS` is not reliably enforced; an RSS watchdog thread is used instead.
- **Linux:** Full limits (`RLIMIT_CPU`, `RLIMIT_AS`, wall timeout, output cap).

In all cases, the network privacy claims do not depend on parser `rlimits`.

## Citation validation

The literal/number/date/role checks in `backend/app/validation/` prove **citation integrity** — that quoted figures, parties and obligations match the stored sentence. They do **not** prove semantic faithfulness (e.g. a wrong relationship between two correct numbers). This is measured by the human-labelled Unsupported Claim Rate (UCR) target ≤ 5% in `docs/EVALUATION.md`.

## Forensic erasure

`DELETE /api/documents/{id}` removes app-controlled files using `PRAGMA secure_delete=ON` and `shutil.rmtree`. This is **NOT** forensic erasure. Data may persist in:
- SSD wear-levelling / over-provisioning areas.
- OS swap or hibernation files.
- External backups (Time Machine, OneDrive, iCloud, etc.).
- Memory pages before OS reclaim.

The deletion response includes this disclaimer.

## Language detection

The language gate uses a non-ML heuristic (non-Latin ratio + English function-word ratio). It may:
- Flag Romanised Hindi as unsupported (safe outcome — excluded from retrieval).
- Pass through unusual English dialects or highly technical text with low function-word ratios.

## Glossary

`glossary/rental_terms.yaml` is curated by the project team. It is **not lawyer-reviewed**. Definitions are general-purpose and may not reflect local law. Every definition is labelled "General definition (not from your document)".

## Model inference

- Gemma 4 E4B/E2B on CPU will be slow (tens of seconds per question on typical consumer hardware).
- `seed` + `temperature:0` gives repeatability on the same machine and build, not bit-identical output across hardware.
- Schema-valid output rate is statistical (target: ≥95% first-try, per T-MODEL-JSON-01). One format-retry is allowed; persistent schema failure returns ERROR_PROCESSING.

## Privacy

- Privacy claims are marked **"Designed for local processing"** until a verified isolated-network run (T-PRIV-NOEXT-01) is completed and committed. No verified run has been done yet.
- The Ollama desktop/tray updater is avoided by starting `ollama serve` headlessly, but update/telemetry behaviour is not yet measured.
