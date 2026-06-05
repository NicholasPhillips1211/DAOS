# Implementation Tracks — Sequence, Dependencies, and Actionable Checklist

This page is a direct transcription of the roadmap diagram (seven implementation tracks), converted into actionable tasks, sprint sequencing, and a prioritized checklist for Phase 1 work.

## At-a-glance
- Seven implementation tracks: Auth, DB layer, Ingest, ML, Analytics, Frontend, Infra.
- Start immediately: Alembic migration completion (schema foundation).
- Sprint 1: Foundation (Auth, Async DB, lint/type checks, K8s hardening prep).
- Sprint 2: Domain services (Ingest, ML Registry, Analytics features, Frontend decomposition).
- Sprint 3: Pipeline engine + UI completion (ARQ, promotion tooling, OTel, real-time status).
- Cross-track integrations run alongside sprints: audit trail, lineage graph, real-time pipeline status.

---

## Tracks (T1–T7)
- T1 — Auth
  - Goals: JWT auth + user registration/login, refresh tokens, default `auth_enabled = true`, add auth enforcement on all routes.
  - Outputs: `users` table and repo, login/register routes, token refresh, middleware, docs & OpenAPI security schemes.

- T2 — DB layer
  - Goals: Complete Alembic initial migration, migrate to `AsyncSession` / `async_sessionmaker`, repository base class, pagination utilities.
  - Outputs: `alembic/versions` completed & tested, `get_db` async dependency, useful repository helpers.

- T3 — Ingest
  - Goals: Multi-format ingestion (CSV/JSON/Parquet), robust upload pipeline, quality v2, connectors, ingestion state machine, write artifacts to storage.
  - Outputs: `IngestionWorkflowService.process_upload()`, durable ingestion jobs, artifact paths, quality profiler integration.

- T4 — ML
  - Goals: Model selection (tree/forest), model registry (versions), SHAP explainability, predict API, drift monitoring.
  - Outputs: `MLService` model selection, `ModelVersion` entities, explain endpoint, drift job scaffolding.

- T5 — Analytics
  - Goals: DuckDB-backed SQL console for CSV artifacts, LLM abstraction for auto-insights, dashboard metric endpoints.
  - Outputs: SQL execution service (DuckDB), auto-insight generator, metrics endpoints.

- T6 — Frontend
  - Goals: Decompose `App.tsx` into `features/*`, use TanStack Query for server state, Zustand for UI slices, error boundaries, simpler `App.tsx` (<100 KB).
  - Outputs: Feature modules (`ingestion`, `automation`, `analytics`, `ml`, `workspace`), global toasts, error boundaries.

- T7 — Infra
  - Goals: K8s hardening (probes, resources, init containers), run Alembic as init step, add OpenTelemetry scaffolding, HPA, PodDisruptionBudget.
  - Outputs: production-ready K8s manifests, init container manifests for migrations, OTel config.

---

## Sprint Plan
### Start (immediate)
- Complete initial Alembic migration. This is blocking for everything else that touches DB schema.

### Sprint 1 — Foundation (recommended 2–3 weeks)
- T1: JWT + users (register/login, refresh tokens). Auth default on.
- T2: Async engine (AsyncSession), repository base, pagination utilities.
- Add `ruff` + `mypy` to CI and `pre-commit` locally.
- Infra: Begin K8s hardening work (render manifests for readiness/liveness, secrets ref pattern).

### Sprint 2 — Domain services (3–4 weeks)
- T3: Implement ingestion `process_upload()` → quality profile → artifact store.
- T4: Model registry + model selection logic (decision tree + random forest fallback option).
- T5: DuckDB SQL console + auto-insights prototype.
- T6: Decompose frontend: move ingestion and automation into `features/`.

### Sprint 3 — Pipeline engine & UI completion (3–4 weeks)
- T3/T4: ARQ worker implementation for pipeline execution, cron scheduling.
- Promotion flow: champion model promotion tooling.
- Business LLM integration + narrative generation.
- Frontend: Error boundaries, full feature slices, WebSocket status updates.
- Infra: OTel integration and release.

---

## Cross-track Integrations (run alongside sprints)
- Audit trail completeness
  - Implement `AuditService.emit(workspace_id, event_type, actor, resource, detail)`.
  - Hook calls into ingestion, pipeline runs, model train/promotion, share/create, comments.

- Data lineage graph
  - `DataLineageEdge` table to record source -> target transformations.
  - Write lineage during ingest/transform/train/predict flows.

- Real-time pipeline status
  - ARQ workers publish progress to Redis; backend forwards via WebSocket or SSE to frontend.

---

## Core Journeys (end-to-end)
- Analyst journey: Upload → Quality → SQL console (DuckDB) → Auto-insights → Business narrative → Dashboard.
- ML journey: Train (Tree/Forest) → Explain (SHAP) → Promote (Champion model) → Predict (serve + logging) → Drift check → Alert/retrain.
- Pipeline journey: Define DAG → Version JSON → Schedule (CRON via ARQ) → Execute typed steps → Live status → Audit & lineage.

---

## Definition of “Fully Realised”
- User capability: Register → upload → query → insight → translate → train → dashboard without leaving the app.
- Operator capability: Full audit trail, RBAC, masks, lineage DAG, OTel metrics, structured logs, K8s HPA.
- Engineering quality: JWT on every route, Alembic for every schema change, mypy + ruff, >=75% service test coverage, CI E2E run.

---

## Prioritized Phase 1 Checklist (short-term, actionable)
These are the items I recommend tackling immediately and in Sprint 1 order.

1. Alembic: ensure `alembic upgrade head` completes locally and in CI; add test task that runs migrations against test DB.
2. Auth: set `auth_enabled = True` default, implement JWT user flows, add `AUTH_*` env var checks in startup.
3. Async DB: move `get_db` to `AsyncSession` and provide compatibility wrappers for blocking calls.
4. Frontend secret removal: remove hard-coded `DEV_API_KEY` and use `VITE_API_KEY` build env; add dev guidelines for local run.
5. Ingestion: keep deepening `IngestionWorkflowService.process_upload()` with worker handoff after streamed artifact persistence and `QualityService.profile_csv`.
6. SQL console: add DuckDB-backed simple executor for CSV artifacts with row-limit and timeout.
7. Pagination: add `limit`/`offset` to list endpoints and `X-Total-Count` header.
8. CI linting: add `ruff` + `mypy` job; add `pre-commit` config.

Each checklist item should become a small PR with tests and CI green.

---

## Next Actions I can take for you
- Create GitHub issues for each Phase 1 checklist item, with labels and estimated story points.
- Open a PR that implements one Phase 1 item (pick which).
- Create a Project board (GitHub Projects) with the sprints, backlog and dependencies.

Which would you like me to do next? If you want a PR, tell me which checklist item to implement first and I'll start coding.
