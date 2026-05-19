# DAOS

DAOS is a modular Intelligent DataOps platform for analysts and data teams who need one workspace to ingest data, validate quality, explore SQL, produce dashboards, train models, translate technical findings into business language, and coordinate work across the lifecycle.

The repository is structured as a production-oriented scaffold. It already includes a FastAPI backend, a React + TypeScript frontend, Docker and Kubernetes deployment assets, a test suite, and a feature-oriented API layout that can be extended as the product matures.

## What The Platform Does

DAOS is designed around a repeatable flow:

1. Data enters the workspace through upload, sync, or connector-driven ingestion.
2. The backend registers the dataset and prepares metadata on startup.
3. Quality checks, transformations, and profiling make the data usable.
4. SQL analytics, pipelines, ML, and dashboards consume curated datasets.
5. Recommendations, business summaries, and guidance turn outputs into decisions.

The current codebase focuses on the control plane and workspace experience. Many features are intentionally scaffolded so they can be hardened or expanded without changing the overall architecture.

## Repository Layout

- `backend/` contains the FastAPI application, models, schemas, services, and tests.
- `frontend/` contains the Vite-based React UI.
- `data/` holds sample raw datasets and trained artifacts used during local development.
- `docs/` contains architecture notes and product context.
- `docs/prd.md` contains the product requirements document and future improvement roadmap.
- `infra/` contains Kubernetes manifests for deployment.
- `docker-compose.yml` defines the local Postgres + backend stack.

## Architecture

The application is organized as a control plane with a small number of clear responsibilities:

- The frontend is the analyst-facing UI.
- The backend exposes versioned APIs under `/api/v1`.
- The backend creates the database schema on startup.
- The default development database is SQLite, while Docker Compose wires the backend to Postgres.
- Cross-origin requests are allowed only from the local Vite development server by default.
- Security headers can be enforced through backend configuration.

The available API domains include health, workspaces, datasets, ingestion, lakehouse access, pipelines, ML, visualizations, analytics, automation, collaboration, governance, business translation, recommendations, and guidance.

## Prerequisites

- Python 3.11 or newer.
- Node.js 20 or newer.
- npm.
- Docker and Docker Compose if you want the containerized stack.
- Optional: a local OpenAI-compatible LLM server such as LM Studio for automation generation.

## Local Development

### Backend

From the backend directory:

```bash
cd backend
python -m uvicorn app.main:app --reload
```

The backend listens on port `8000`. A lightweight root check is available at `/`, and a health endpoint is available at `/api/v1/health`.

Run the backend test suite with:

```bash
cd backend
pytest tests -q
```

The backend starts by creating database tables through SQLAlchemy metadata. If you are using the default local settings, it stores data in `backend/daos.db`. When started through Docker Compose, it uses Postgres instead.

### Frontend

From the frontend directory:

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server listens on port `5173`.

Create a production build with:

```bash
cd frontend
npm run build
```

Preview the production build locally with:

```bash
cd frontend
npm run preview
```

## Full Local Stack

Use Docker Compose when you want the backend and database together:

```bash
docker compose -f docker-compose.yml up --build
```

This starts:

- Postgres on `5432`.
- The backend on `8000`.

## Configuration

Backend configuration is loaded from environment variables and `.env` files.

Important settings include:

- `APP_NAME` for the service name.
- `API_PREFIX` for the versioned route prefix, defaulting to `/api/v1`.
- `ENVIRONMENT` for deployment labeling.
- `DATABASE_URL` for the database connection string.
- `CORS_ORIGINS` for allowed frontend origins.
- `ENFORCE_SECURITY_HEADERS` to enable or disable security middleware.
- `AUTH_ENABLED` to toggle authentication checks.
- `API_KEYS_CSV` for simple API key configuration when auth is enabled.
- `LLM_BASE_URL` for OpenAI-compatible model endpoints.
- `LLM_MODEL` for the model identifier.
- `LLM_API_KEY` for model authorization.
- `LLM_TIMEOUT_SECONDS` for LLM call timeouts.

Example local LLM settings:

```bash
LLM_BASE_URL=http://localhost:1234/v1
LLM_MODEL=local-model
LLM_API_KEY=
```

If the model server is unavailable, automation falls back to a deterministic plan derived from workspace signals, so the feature still produces useful output offline.

## Feature Guide

### Health And Runtime Checks

Use the root route and health route to confirm the service is up:

- `GET /` returns the application name and environment.
- `GET /api/v1/health` returns a simple `ok` payload for probes and smoke tests.

### Workspaces And Datasets

These modules provide the foundation for organizing work around named projects, registered datasets, and workspace state. They are the right place to extend when adding dataset metadata, workspace scoping, or new catalog behaviors.

The workspace API also exposes a summary endpoint at `/api/v1/workspaces/{workspace_id}/summary` so the UI can surface onboarding guidance, recent datasets, and next-step prompts.

### Ingestion And Lakehouse

These routes are intended for moving raw data into the platform and making it queryable in analytical form. Use them when implementing file upload, sync, staging, validation, or SQL-facing dataset workflows.

### Pipelines And Automation

Pipelines capture repeatable processing logic. Automation is used to generate actionable plans from workspace context. The automation endpoint lives under `/api/v1/automation` and is designed to work with a local model server, but does not depend on one being available.

### ML, Visualizations, Analytics, And Recommendations

These services support exploration, insight generation, model training, explainability, and presentation of results. Extend them when adding charts, prediction flows, comparison reports, or recommendation logic.

### Collaboration, Governance, And Business Translation

These modules support auditability, traceability, and communication between technical and non-technical users. They are the right place to add approvals, narrative summaries, governed sharing, and role-aware workflows.

### Guidance

The guidance layer is intended to help users move through the product and understand next steps. Use it for onboarding, workflow hints, and contextual help.

## Maintenance Guide

### What To Check Regularly

- Keep backend dependencies aligned with Python 3.11 and the current FastAPI stack.
- Verify the frontend builds cleanly before merging UI changes.
- Run the test suite after changes to API contracts, service logic, or routing.
- Check Docker Compose and Kubernetes manifests when ports, environment variables, or service names change.
- Update documentation whenever a new route, environment variable, or deployment step is added.

### Safe Change Process

1. Make the smallest change that addresses the requirement.
2. Run targeted backend or frontend tests first.
3. Run the build or full test suite when the change affects shared behavior.
4. Review the generated API surface and update the README if users need to know about it.

### Data And Artifact Hygiene

- Keep generated database files, build outputs, and dependency folders out of version control.
- Treat sample data under `data/` as local development input unless a file is explicitly meant to be committed.
- Update `.gitignore` if new build artifacts or temporary files are introduced.

## Testing

Backend tests live under `backend/tests/` and can be run with pytest.

Recommended checks before merging:

```bash
cd backend
pytest tests -q
```

```bash
cd frontend
npm run build
```

If you change deployment wiring or environment variables, also validate the compose stack:

```bash
docker compose -f docker-compose.yml up --build
```

## Deployment

### Docker And Compose

The compose file is the quickest way to stand up a local production-like backend with Postgres.

### Kubernetes

Kubernetes manifests are provided for the backend and frontend:

- `infra/k8s/backend-deployment.yaml`
- `infra/k8s/frontend-deployment.yaml`

Apply them with:

```bash
kubectl apply -f infra/k8s/
```

## CI And Quality Gates

The repository is expected to validate two core paths in CI:

- Backend tests on Python 3.11.
- Frontend production build on Node 20.

If you add new major behavior, include regression coverage in the appropriate test layer so the CI pipeline protects it.

## Troubleshooting

- If the backend cannot connect to the database, confirm `DATABASE_URL` matches the environment you are running.
- If the frontend cannot reach the backend, check the allowed CORS origins and the API prefix.
- If automation does not call a model server, verify `LLM_BASE_URL`, `LLM_MODEL`, and `LLM_API_KEY`.
- If Docker Compose fails, confirm that ports `5432` and `8000` are free.
- If database state looks stale during development, remove the local SQLite file or reset the Postgres volume depending on your setup.

## Extending The Application

When adding new functionality, follow the existing structure:

- Add route handlers in `backend/app/api/routes/`.
- Put request and response contracts in `backend/app/schemas/`.
- Keep domain logic in `backend/app/services/`.
- Add persistence models in `backend/app/models/`.
- Add tests in `backend/tests/`.
- Update the frontend when the user workflow changes.

This keeps the platform maintainable as it grows from scaffolded features into a fully integrated product.
