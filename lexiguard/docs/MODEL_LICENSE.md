# Model licence

## Gemma 4

The Gemma 4 model card states **Apache License 2.0**. The exact licence text must be copied from
the official card at `https://ai.google.dev/gemma/docs/core/model_card_4` when the model version
and digest are pinned, and kept verbatim below this heading.

**Status: not yet pasted.** Do not describe the model as “Apache-2.0 verified in this repository”
until the official text is copied here with the date it was retrieved. A link is not a licence
copy; a build-time download is not needed either.

| Field | Value |
|---|---|
| Model family | Gemma 4 |
| Tags used | `gemma4:e4b-it-q4_K_M`, `gemma4:e2b-it-q4_K_M` |
| Effective parameters | E4B 4.5 B effective / 8 B with embeddings; E2B 2.3 B / 5.1 B |
| Licence claimed by model card | Apache-2.0 |
| Retrieved (date) | pending |
| Digest recorded in `reports/env.json` | pending |

## Other components

| Component | Licence | Notes |
|---|---|---|
| pypdfium2 | Apache-2.0 OR BSD-3-Clause | Bundles PDFium; its `BUILD_LICENSES` texts must be included in `NOTICE` when the parser is bundled |
| Tesseract | Apache-2.0 | Local executable; language data has its own licences to record when OCR lands |
| FastAPI / Starlette / Pydantic | MIT / BSD / MIT | Recorded via SBOM |
| React / Vite / TypeScript | MIT | Recorded in `package-lock.json` |

## Rules

- Record model and data licences separately from the project's Apache-2.0.
- CI fails on AGPL/GPL/unknown dependency metadata; LGPL is review-required.
- Do not add model weights to the repository. Do not re-distribute a model except under its own
  terms.
