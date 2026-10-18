# Privacy evidence

The isolated-network report for a release goes in `reports/privacy/<commit-or-release>/`.
It must contain attempt-visible evidence (non-loopback destinations), the negative
control that **was detected**, canary-scan results and the deletion report.

Never commit raw loopback packet payloads: the local API->Ollama request necessarily
contains prompt/evidence text, so loopback traffic may contain canaries without any
external traffic. Until a report exists for the exact release, the UI must say
"Designed for local processing".
