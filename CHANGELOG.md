# Changelog

## 1.3.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

### Added
- Evaluation runner CLI now supports `--json` flag for CI/CD machine-readable output
- Evaluation runner CLI supports `--output` flag to write JSON results to file
- Evaluation runner CLI supports `--target` flag for web/mobile_android/mobile_ios environments
- New `run_benchmark_json()` function for programmatic access to benchmark results
- Default human-readable output preserved for interactive use

### Changed
- Updated PLAN.md with evaluation-ci-integration feature completion

### Fixed
- All 27 backend tests pass with enhanced evaluation runner

Partial code published for continued development. Known issues: STATUS.md.

## 1.1.0 — 2026-10-23

### Added
- Evaluation Dashboard: Export evaluation benchmark results as JSON from the UI.

### Changed
- Updated portfolio.json summary and status to reflect completed checkpoint.

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to Sentinel Lens are documented here.

## 1.0.0 — Initial Release (2026-10-12)

### Added
- Embedded programmatic runner engine exposing `open_session()` on `sentinel_lens.runner` for host test suites (Pytest, Vitest, Playwright, Jest).
- Complete fixture graph lifecycle manager covering `agent`, `app`, `screen`, `device`, and `network` with idempotent async cleanup.
- Recursive secret and credential redaction pipeline filtering authorization headers, tokens, and sensitive values across step traces and artifacts.
- Deterministic semantic accessibility hierarchy locator engine achieving 100% accuracy on labeled test benchmark (+37.5% over naive baseline).
- Multi-provider opt-in LLM advisory adapter supporting OpenAI-compatible, Anthropic, Gemini, and Ollama endpoints with bounded timeouts and error redaction.
- Full-stack persistent storage with parameterized SQLAlchemy SQLite models, pagination, filtering, and transactional audit logging.
- Keycloak OIDC authentication architecture with PKCE, audience/issuer validation, RBAC (`viewer`, `operator`, `admin`), and production startup safety verification.
- React 19 + TypeScript + Vite frontend with Runner Console, Trace Inspector, SVG artifact renderer, AI/ML Evaluation Dashboard, and Audit Log.
- Complete Docker Compose setup with Keycloak, backend, frontend, non-root users, healthchecks, and localhost port bindings.
- Fully automated test suites with 27 backend pytest tests and 4 frontend Vitest tests.
