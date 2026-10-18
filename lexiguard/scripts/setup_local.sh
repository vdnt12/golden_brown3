
#!/usr/bin/env bash
# Local setup for LexiGuard (Tier 0 / Phase 0).
# Downloads models and packages ONLY here; document processing never downloads.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "== LexiGuard setup =="
python3 --version
node --version || echo "node not found (frontend build optional for Tier 0)"

REQUIRED_OLLAMA="0.21.1"
if ! command -v ollama >/dev/null 2>&1; then
  echo "ERROR: Ollama is not installed. Install Ollama >= ${REQUIRED_OLLAMA} and re-run." >&2
  exit 1
fi

OLLAMA_VERSION="$(ollama --version 2>/dev/null | awk '{print $NF}')"
echo "Ollama version: ${OLLAMA_VERSION}"
python3 - "$REQUIRED_OLLAMA" "$OLLAMA_VERSION" <<'PY'
import re
import sys

def parts(value: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", value)[:3])

required, installed = sys.argv[1], sys.argv[2]
if parts(installed) < parts(required):
    raise SystemExit(f"ERROR: Ollama {installed} < required {required}")
PY

echo "Pulling pinned model tags (setup-time network use only)..."
ollama pull gemma4:e4b-it-q4_K_M
ollama pull gemma4:e2b-it-q4_K_M

echo "Recording actual tags/digests into reports/env.json ..."
python3 scripts/verify_model_tags.py

echo "Installing Python dependencies (scaffold) ..."
python3 -m pip install -e ".[dev]"

echo "Building frontend ..."
if command -v npm >/dev/null 2>&1; then
  npm install --no-audit --no-fund
  npm run build
else
  echo "npm not available: frontend not built. API will return a placeholder at /."
fi

echo "Setup finished. Run: make demo"
