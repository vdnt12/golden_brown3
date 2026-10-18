# Contributing

Thanks for considering a contribution. LexiGuard is a privacy-first legal-document triage tool;
correctness and honesty matter more than feature count.

## Before you start

1. Read `README.md`, `STRUCTURE.md`, `docs/ARCHITECTURE.md` and `AGENTS.md`.
2. Check `TASKS.md` for the current phase. Do not implement features from a later phase while an
   earlier gate is open.
3. For anything that changes a contract, privacy wording, a hard limit or the deletion behaviour,
   open an issue or draft ADR first.

## Development setup

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
npm install
PYTHONPATH=backend python3 -m pytest
python3 -m ruff check backend tests scripts
npm run build
```

## Rules

- **No unverified claims.** Do not describe the project as private, accurate or running locally
  without a committed report. The UI currently says “Local by default” and the docs say exactly
  which part is unverified.
- **No network additions.** No telemetry, analytics, CDNs, cloud models, hosted APIs or browser
  storage for document data. CI and review enforce this; exceptions require an ADR.
- **Model never authors facts.** Quotes, pages, sections and statuses are backend-owned from stored
  text. Model output is a proposal that must pass validation.
- **Tests first** for validator, scanner, parser and deletion changes. A behaviour change without a
  test is not mergeable.
- **Docs in the same PR.** Update `ARCHITECTURE.md`, `DATA_FLOW.md`, `LIMITATIONS.md` and
  `TEST_PLAN.md` where applicable.
- **Fixtures stay synthetic.** Never commit real agreements, personal data or model weights.
- **Apache-2.0.** By contributing you agree your work is licensed under the repository licence and
  that you have the right to submit it.

## Pull requests

Use the PR template. Include:

- what changed and why;
- the exact commands you ran and their output summaries;
- privacy impact (does any data move?);
- legal-boundary impact (can the model now say something it could not before?);
- docs updated;
- tests added.

## Hacktoberfest

This project is part of the ZeroDay OSS Hacktoberfest 2026 submission. Quality contributions are
welcome in: tests, parser robustness, accessibility, lexicon coverage, documentation of limits,
and evaluation tooling. Spam PRs (formatting-only, generated noise) will be closed.

## Code of conduct

Be respectful and constructive. Harassment or discrimination is not tolerated. See
`CODE_OF_CONDUCT.md`.
