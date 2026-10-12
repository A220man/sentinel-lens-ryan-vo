# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

open-session-runner-host

## Roadmap

### open-session-runner-host — Programmatic runner session embedding via openSession API

Status: done

Acceptance:
- External test runners (Pytest, Vitest, Playwright) can embed an e2e session using open_session() with custom target, working directory, and step progress callback
- Session manages complete fixture graph (agent, app, screen, device, network) with idempotent cleanup on exit
- Secret redaction filter scrubs credentials, API keys, and authorization headers from logs and step artifacts
- REST API exposes full session lifecycle: creation, step execution, telemetry collection, and trace export

Implementation: `backend/app/main.py`, `backend/app/core/runner.py`, `backend/app/services/session_service.py`, `backend/app/api/sessions.py`

Tests: `backend/tests/test_runner_session.py`, `backend/tests/test_api_workflows.py`

### agentic-visual-grounding — Agentic multimodal assertion grounding and semantic locator hierarchy

Status: planned

Acceptance:
- Accessibility tree parser ranks candidate elements using deterministic role and name heuristics offline
- Opt-in multi-provider LLM adapter supports OpenAI, Anthropic, Gemini, and Ollama with error redaction
- Visual difference scoring detects UI regressions and layout shifts across session checkpoints

### replay-evaluation-benchmark — Deterministic replay telemetry and AI/ML locator benchmark suite

Status: planned

Acceptance:
- Deterministic test replay reconstructs session step timelines and artifact bundles
- Reproducible benchmark measures semantic locator accuracy vs baseline fuzzy matching across labeled UI workflows

### enterprise-auth-saml-broker — Keycloak OIDC authentication and upstream SAML IdP broker

Status: planned

Acceptance:
- PKCE authorization code flow with state validation and JWKS token verification
- Role-based access control rejecting unauthenticated and unauthorized requests
- Production startup safety refusing local demo mode in production environments

