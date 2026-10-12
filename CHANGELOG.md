# Changelog

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
