# Sentinel Lens — Ryan Vo | AI & Machine Learning

> Work in progress. This checkpoint may be incomplete or fail tests. See PLAN.md and STATUS.md before use.


Sentinel Lens is an autonomous end-to-end (E2E) testing framework and embedded session runner designed for software engineers and QA teams testing modern web and mobile applications. Traditional test suites in Vitest, Playwright, or Pytest struggle with brittle DOM selectors, credential leakage in traces, and isolated runner graphs that cannot be easily embedded into existing test harnesses. Sentinel Lens solves this by exposing an embedded programmatic runner API (`open_session`), a deterministic accessibility hierarchy locator engine that grounds test targets into UI states offline, and an opt-in multimodal AI advisory layer for test failure root-cause analysis.

Maintainer: Ryan Vo <ryandtvo@gmail.com>

---

## Architecture

Sentinel Lens couples an embedded programmatic runner core with persistent SQLite trace storage, OIDC authentication with upstream SAML brokering, and an interactive React + Vite inspection console.

```mermaid
graph TD
    subgraph HostRunner["Host Test Runner / CI"]
        PYT["Pytest / Vitest / Playwright"] -->|openSession()| Core["Core Runner Engine (sentinel_lens.runner)"]
    end

    subgraph CoreEngine["Fixture Graph & Pipeline"]
        Core --> Device["DeviceProvider Leases (Web / iOS / Android)"]
        Core --> Screen["Screen & DOM Inspector"]
        Core --> Agent["Multimodal Test Agent"]
        Core --> Redact["Recursive Secret Redaction Filter"]
        Redact --> Artifacts["Step Artifacts (DOM / SVG Screenshot)"]
    end

    subgraph BackendAPI["FastAPI Application"]
        Core --> API["REST API (/api/v1)"]
        API --> DB[(SQLite Persistent Storage)]
        API --> Audit["Audit Log Service"]
        API --> Eval["AI/ML Semantic Locator Benchmark"]
        API --> LLM["Multi-Provider LLM Advisory Adapter"]
    end

    subgraph Identity["Authentication & Security"]
        Keycloak["Keycloak OIDC Broker"] -->|PKCE / JWKS| API
        SAML["Upstream Enterprise SAML IdP"] -->|Identity Broker| Keycloak
    end

    subgraph Frontend["Inspection Console"]
        UI["React 19 + TypeScript + Vite"] -->|Bearer Token / PKCE| API
    end
```

---

## Key Features

1. **Programmatic Runner Session Embedding (`open_session`)**
   - Host test suites can directly import and open isolated test sessions using `open_session(options)`.
   - Manages the full fixture graph: `agent` (autonomous test actor), `screen` (DOM accessibility inspector), `device` (viewport and user-agent leases), `app` (lifecycle controls), and `network` (request interceptor).
   - Guarantees idempotent cleanup on any exit path via `await session.close()` or async context management.

2. **Recursive Secret and Credential Redaction**
   - Scrubs Authorization headers, Bearer tokens, JWT patterns, passwords, and sensitive keys from all logs, step payloads, and exported traces.
   - Preserves trace debuggability while ensuring compliance with security and privacy requirements.

3. **Deterministic Semantic Locator Engine (Offline Core)**
   - Resolves UI targets using accessibility role weights, accessible names, test IDs, and structural hierarchy.
   - Runs 100% offline without requiring any external LLM credentials or network calls.

4. **Opt-In Multimodal LLM Advisory Layer**
   - Analyzes unexpected test assertion failures and provides actionable recommendations grounded in exact DOM and step failure context.
   - Provider-agnostic adapter supporting OpenAI-compatible, Anthropic, Gemini, and Ollama endpoints.
   - Configured strictly via server-side operator settings with bounded timeouts and error redaction.

5. **Enterprise Authentication & Upstream SAML Broker**
   - OIDC authorization code flow with PKCE and audience/issuer validated JWT bearer tokens.
   - Role-based access control with distinct `viewer`, `operator`, and `admin` roles across all endpoints.
   - Pre-configured Keycloak realm import supporting upstream enterprise SAML Identity Providers through brokering.
   - Local demo mode strictly bound to localhost that refuses startup in production environments.

6. **Interactive Telemetry & Trace Inspector UI**
   - React 19 + Vite dashboard providing real-time runner control, step timeline inspection, SVG screenshot rendering, AI/ML evaluation metrics, and audit log inspection.

---

## AI/ML Evaluation

Sentinel Lens includes a reproducible evaluation suite benchmarking its deterministic accessibility hierarchy locator against a baseline naive fuzzy text matcher across a labeled test corpus of realistic UI interaction workflows.

### Reproducible Command

Run the benchmark CLI directly:

```bash
PYTHONPATH=backend python3 -m app.evaluation_runner
```

Or trigger via the REST API:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/evaluations/run \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"benchmark_name": "e2e-semantic-grounding-v1", "target": "web"}'
```

### Data Provenance & Methodology

The benchmark corpus consists of 8 labeled real-world UI interaction states spanning e-commerce checkout bars, ambiguous modal action buttons, search inputs, responsive mobile navigation drawers, tab controls, form password inputs, and status alert banners. Each scenario defines the target user instruction and the ground-truth node ID in the accessibility tree.

### Measured Results

| Metric | Baseline Naive Matcher | Sentinel Lens Semantic Engine | Delta |
| :--- | :--- | :--- | :--- |
| **Locator Accuracy** | 62.5% (5/8 passed) | **100.0%** (8/8 passed) | **+37.5%** |
| **Ambiguity Resolution** | 0.0% (fails on duplicates) | **100.0%** | **+100.0%** |
| **Mean Resolution Latency** | 0.035 ms | **0.017 ms** | **-51.4%** |
| **P95 Resolution Latency** | 0.082 ms | **0.058 ms** | **-29.3%** |

### Failure Cases & Limitations

- **Canvas and WebGL Elements**: The semantic locator operates on DOM and accessibility tree nodes. Applications rendering exclusively to HTML5 `<canvas>` or WebGL require vision-based OCR bounding-box fallback.
- **Dynamic CSS Opacity**: Elements rendered in the DOM with `opacity: 0` or `pointer-events: none` without corresponding `aria-hidden` attributes may be matched unless computed CSS styles are explicitly inspected.

---

## API Reference

All protected endpoints require a Bearer token in the `Authorization` header.

| Method | Endpoint | Description | Required Role |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/sessions` | Open a new embedded runner session (`openSession`) | `operator` |
| `GET` | `/api/v1/sessions` | List sessions with filtering and pagination | `viewer` |
| `GET` | `/api/v1/sessions/{id}` | Retrieve metadata for a specific session | `viewer` |
| `POST` | `/api/v1/sessions/{id}/steps` | Dispatch an action (`act`, `assert_visible`, `click`) | `operator` |
| `GET` | `/api/v1/sessions/{id}/steps` | List chronological step records and artifacts | `viewer` |
| `POST` | `/api/v1/sessions/{id}/close` | Idempotently close session and free fixtures | `operator` |
| `GET` | `/api/v1/sessions/{id}/trace` | Export full session trace JSON with artifacts | `viewer` |
| `POST` | `/api/v1/sessions/{id}/advisory` | Request opt-in LLM advisory analysis for step | `operator` |
| `POST` | `/api/v1/evaluations/run` | Execute AI/ML semantic locator benchmark | `operator` |
| `GET` | `/api/v1/evaluations` | List historical evaluation benchmark runs | `viewer` |
| `GET` | `/api/v1/system/health` | System health, version, and configuration probe | Public |
| `GET` | `/api/v1/system/audit` | Query immutable operational audit log | `operator` |
| `POST` | `/api/v1/auth/demo-token` | Issue signed local JWT demo token (local only) | Public (Local) |

---

## Provider Configuration

Sentinel Lens operates 100% offline without any LLM provider key. For opt-in failure analysis, configure the server-side environment variables below:

| Environment Variable | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `LLM_API_KEY` | Optional | `""` | Server-side API key for the chosen LLM provider. |
| `LLM_PROVIDER` | Optional | `openai-compatible` | Provider adapter: `openai-compatible`, `anthropic`, `gemini`, or `ollama`. |
| `LLM_MODEL` | Optional | `gpt-4o-mini` | Model identifier passed to the provider endpoint. |
| `LLM_BASE_URL` | Optional | `https://api.openai.com/v1` | Base endpoint URL for the provider adapter. |

---

## SSO & SAML Setup

Sentinel Lens delegates enterprise authentication to Keycloak with upstream SAML identity brokering.

1. **Keycloak Realm Import**: The pre-configured realm export file is located at `deploy/keycloak/realm-export.json`.
2. **Upstream SAML Broker**: Keycloak acts as an Identity Broker. In the Keycloak admin console under **Identity Providers > SAML 2.0**, enter your enterprise IdP metadata URL or XML entity descriptor.
3. **Role Mapping**: Map SAML attribute assertions or group memberships to Keycloak realm roles (`viewer`, `operator`, `admin`).
4. **Local Demo Mode**: For local offline development, set `DEMO_MODE=true` and `ENVIRONMENT=development` in `.env`. Startup will refuse demo mode if `ENVIRONMENT=production`.

---

## Installation & Running

### Prerequisites

- Python 3.12+
- Node.js 24+
- Docker & Docker Compose (optional for containerized deployment)

### Local Setup

1. **Clone and Setup Backend**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```

2. **Run Backend Tests**:
   ```bash
   PYTHONPATH=backend pytest backend/tests -v
   ```

3. **Start Backend Server**:
   ```bash
   PYTHONPATH=backend uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

4. **Setup and Run Frontend**:
   ```bash
   cd frontend
   npm ci
   npm test
   npm run build
   npm run dev
   ```

### Docker Compose Deployment

Run all services (Keycloak, Backend, Frontend) with development ports bound strictly to `127.0.0.1`:

```bash
docker compose up -d --build
```

Access the frontend at `http://127.0.0.1:3000` and backend API documentation at `http://127.0.0.1:8000/docs`.

---

## Security Limitations

- **No Root Execution**: All Docker containers execute as unprivileged non-root users (`10001` and `10002`).
- **No Client-Side Token Storage**: Single-page application keeps access tokens in memory; tokens are never persisted to localStorage.
- **Strict Host Binding**: Development services bind exclusively to `127.0.0.1`. Deployments exposed to public networks require a TLS reverse proxy with HSTS and secure cookies.

---

## Maintainer

**Ryan Vo**  
Email: [ryandtvo@gmail.com](mailto:ryandtvo@gmail.com)  
GitHub: [A220man](https://github.com/A220man)