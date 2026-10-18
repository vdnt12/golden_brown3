# Open-source use and licences

| Component | Role | Licence | Notes |
|---|---|---|---|
| Python 3.11+ | Runtime | PSF | — |
| FastAPI / Starlette | HTTP API | MIT / BSD-3-Clause | No cloud services |
| Pydantic / pydantic-settings | Schemas, config | MIT | Strict models are central to the tool contract |
| uvicorn | ASGI server | BSD-3-Clause | Loopback only |
| pypdfium2 | PDF text + page render (Phase 1) | Apache-2.0 OR BSD-3-Clause | Bundles PDFium; ship its licence files in `NOTICE` |
| Tesseract (Phase 1b) | OCR fallback | Apache-2.0 | Local binary; language-data licences recorded when added |
| SQLite / FTS5 | Storage, lexical search | Public domain | `secure_delete=ON`, DELETE journal |
| Ollama | Local model runtime | MIT | ≥0.21.1; native `/api/chat` |
| Gemma 4 | Local model | Apache-2.0 (per model card; text to be copied into `MODEL_LICENSE.md`) | q4_K_M GGUF |
| React / Vite / TypeScript | Frontend | MIT | Bundled, no CDN |
| pytest / ruff / mypy / pip-audit | Dev tooling | MIT/Apache-2.0 | Dev extras only |

Deliberately **not** used in the default install: PyMuPDF (AGPL), `torch`, `sentence-transformers`,
FAISS, any hosted model/API, any analytics or error-reporting SDK.

## Reuse rules

- Preserve `LICENSE` and `NOTICE` from the upstream repository; this project is Apache-2.0.
- `scripts/verify_licenses.py` fails CI on AGPL/GPL/unknown dependency metadata and warns on LGPL.
- `scripts/generate_sbom.sh` writes CycloneDX when the tool is available and otherwise a
  pip-list fallback; attach the report to the release.
- Do not vendor model weights, datasets or fonts without recording their licence and provenance.
- If dense retrieval is ever added, it must use a local embedding model with a recorded licence
  and an ADR; the default build must remain text-only and network-free.
