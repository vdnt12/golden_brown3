
#!/usr/bin/env bash
# SBOM + licence report (Guide 17). Requires setup-time network to install tools.
set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p reports/sbom
if python3 -m pip show cyclonedx-bom >/dev/null 2>&1; then
  python3 -m cyclonedx_py environment --output-file reports/sbom/backend.cdx.json
else
  echo "cyclonedx-bom not installed: pip install cyclonedx-bom" >&2
  python3 -m pip list --format=json > reports/sbom/pip-list.json
  echo "Wrote raw pip list as a fallback; generate a real CycloneDX SBOM before release." >&2
fi

python3 scripts/verify_licenses.py | tee reports/sbom/licence-report.txt
echo "SBOM artifacts in reports/sbom/ (commit only if free of local paths/secrets)."
