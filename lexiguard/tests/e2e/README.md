# End-to-end tests (planned)

Full-stack tests against a running API and a built frontend. They require Phase 1 (upload) and
Phase 4 (ask), so nothing here can run today.

Planned: Playwright (or equivalent) flows for launch-code bootstrap, upload of each synthetic
fixture, a cited ask, a legal-boundary ask, a silence ask, deletion, and keyboard-only traversal.
Accessibility gating (axe) belongs here too, once the UI shows real answers.

Do not add a test that mocks the backend here; that belongs in `tests/integration/`.
