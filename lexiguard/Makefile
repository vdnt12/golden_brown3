
.PHONY: setup install demo isolated-demo isolated-demo-docker test lint typecheck frontend clean verify-tags eval ask models smoke

PY ?= python3

setup:
	bash scripts/setup_local.sh

install:
	$(PY) -m pip install -e ".[dev]"

demo:
	PYTHONPATH=backend $(PY) -m app

isolated-demo:
	bash scripts/run_isolated_demo.sh

# Headless scripted privacy flow inside `docker run --network none`.
# Still intentionally fails until a real capture exists; do not report a pass.
isolated-demo-docker:
	@echo "Phase 6: the headless scripted privacy flow is not implemented."
	@echo "See scripts/run_isolated_demo.sh and docs/PRIVACY.md."
	@exit 2

test:
	$(PY) -m pytest -q

lint:
	$(PY) -m ruff check backend tests scripts

typecheck:
	$(PY) -m mypy

frontend:
	npm install --no-audit --no-fund
	npm run build

smoke:
	$(PY) scripts/live_api_smoke.py

verify-tags:
	$(PY) scripts/verify_model_tags.py

eval:
	$(PY) scripts/evaluate_fixtures.py --json reports/fixture_evaluation.json --md reports/fixture_evaluation.md

# make ask FILE=fixtures/x.pdf Q="What is the rent?"
ask:
	PYTHONPATH=backend $(PY) -m app.cli ask "$(FILE)" "$(Q)" $(if $(MODEL),--model $(MODEL),)

models:
	PYTHONPATH=backend $(PY) -m app.cli models

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache reports/sbom frontend/dist
