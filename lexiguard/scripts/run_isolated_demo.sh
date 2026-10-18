
#!/usr/bin/env bash
# Privacy evidence run (Guide 11.4). Requires an isolated environment first.
# This scaffold cannot produce evidence: the flow is wired in Phase 4 and the
# audit runner in Phase 6. Refuse loudly rather than emit an empty report.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Checking prerequisites..."
command -v strace >/dev/null 2>&1 || echo "WARN: strace not found (Linux attempt-visible capture unavailable)"
command -v docker >/dev/null 2>&1 || echo "WARN: docker not found (portable --network none path unavailable)"

cat <<'MSG'
This script is a placeholder for the Phase 6 audit runner.

Required evidence (none may be claimed until produced):
  * isolated namespace containing BOTH app and Ollama (loopback up, no egress)
  * strace/dummy-interface attempt capture filtered to non-loopback destinations
  * negative control that IS detected (tests/privacy/negative_control.py)
  * canary scan of app/Ollama/gateway logs and temp state
  * deletion report for the same flow
Saved under reports/privacy/<commit-or-release>/, with no raw loopback payloads.

Exit code 2 = privacy evidence not produced (not a passing result).
MSG
exit 2
