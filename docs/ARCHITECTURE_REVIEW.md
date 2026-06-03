# DAOS Architecture Review

Review date: 2026-06-03

DAOS is currently a FastAPI + React operational analytics scaffold with good route/service separation, a working local workflow for CSV ingestion, profiling, SQL querying, dashboard creation, collaboration, automation planning, metadata events, and governance audit events. The product direction in this repository is strongest when it stays centered on:

Ingestion -> Dataset Profiling -> Metadata Generation -> SQL Analysis -> AI Insight Generation -> Dashboard Operationalization.

This review covers the architecture as implemented in the repository after the stabilization and frontend cleanup passes.

## Validation Summary

| Area | Command | Result |
| --- | --- | --- |
| Backend install | `.\.venv\Scripts\python.exe -m pip install -e .\backend[dev]` | Passed after sandbox escalation; installed declared backend runtime and dev dependencies. |
| Backend lint | `.\.venv\Scripts\python.exe -m ruff check backend\app backend\tests` | Passed. |
| Backend tests | `.\.venv\Scripts\python.exe -m pytest backend\tests -q` | Passed: 28 tests. |
| Frontend build | `npm.cmd run build` from `frontend/` | Passed after sandbox escalation. Vite emitted a chunk-size warning for a 503 kB JS asset. |
| Backend startup | `AUTH_ENABLED=false .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000` | Passed; `/api/v1/health` returned `{"status":"ok","service":"daos-backend"}`. |
| Frontend startup | `npm.cmd run dev -- --host 127.0.0.1 --port 5173` | Passed; `http://127.0.0.1:5173` returned HTTP 200. |

Notes:

- Running backend startup without `AUTH_ENABLED=false` failed in this local environment because auth was enabled and no `API_KEYS_CSV` was configured. That is an intended fail-fast behavior, but the local startup docs should make the toggle explicit.
- The in-app browser automation bridge failed to initialize due a local `node_repl` sandbox spawn error, so visual browser automation could not be completed. Endpoint startup checks passed.
- There is no dedicated frontend lint or frontend test script in `frontend/package.json`; the current frontend quality gate is TypeScript plus Vite build.

## Repository Shape

The backend follows a conventional layered structure:

- `backend/app/api/routes/`: HTTP route handlers.
- `backend/app/services/`: domain and workflow services.
- `backend/app/models/`: SQLAlchemy persistence models.
- `backend/app/schemas/`: Pydantic request/response schemas.
- `backend/app/core/`: configuration, database, auth, middleware, errors, observability helpers.
- `backend/tests/`: API and service-oriented pytest coverage.

The frontend is moving toward the requested feature-based structure:

- `frontend/src/app`: app providers.
- `frontend/src/routes`: TanStack Router setup.
- `frontend/src/layouts`: shared route layout.
- `frontend/src/features`: feature modules for workspace, ingestion, dashboards, analytics, datasets, governance, copilot, auth, and related domains.
- `frontend/src/components`: shared UI helpers.
- `frontend/src/hooks`, `frontend/src/services`, `frontend/src/store`: cross-feature utilities.

The root frontend app is now a shell:

- `frontend/src/App.tsx`: 36 lines.
- `frontend/src/features/workspace/pages/WorkspaceControlRoom.tsx`: workspace composition.
- `frontend/src/features/workspace/hooks/useWorkspaceWorkflow.ts`: workspace-level coordination.
- `frontend/src/features/workspace/hooks/useDashboardWorkflow.ts`: dashboard form, template, query-to-dashboard, and chart recommendation orchestration.
- `frontend/src/features/workspace/hooks/useCollaborationWorkflow.ts`: comments and sharing orchestration.
- `frontend/src/features/workspace/hooks/useAutomationWorkflow.ts`: automation generation and execution orchestration.
- `frontend/src/features/ingestion/hooks/useIngestionWizard.ts`: ingestion workflow state and API orchestration.
- `frontend/src/features/ingestion/components/*`: ingestion upload, schema, query, result, and dashboard draft panels.
- `frontend/src/features/dashboards/components/DashboardOperationsPanel.tsx`: dashboard creation workflow panel.
- `frontend/src/features/workspace/components/*`: workspace header, automation shell and subpanels, collaboration, and automation history panels.
- `frontend/src/HomeView.tsx`: data-driven landing/workspace entry screen with stable guided-tour section anchors.
- `frontend/src/GuidedTour.tsx`: guided-tour overlay with extracted highlight positioning helpers.

## Workflow Review

### Ingestion And Profiling

Implemented flow:

- `POST /api/v1/ingestion/upload` validates workspace existence.
- The route reads the upload bytes, delegates persistence/profiling/record creation to `IngestionService`, then emits audit and metadata events.
- `IngestionService` stores a workspace-scoped raw CSV file, profiles it through `QualityService`, creates `Dataset`, `IngestionJob`, and `DataQualityReport` records, and adds profile metadata including schema summary and profile fingerprint.
- Tests cover successful upload, missing workspace, non-CSV rejection, blank dataset name rejection, quality report retrieval, and queryability.

Gaps:

- Uploads are read fully into memory in the API request.
- Only CSV is supported.
- Ingestion is synchronous and request-bound.
- `ingestion_workflow_service.py` duplicates much of `ingestion_service.py` and is not wired into the upload route.
- Retry handling exists for file and DB writes, but there is no durable async retry state.

### Dataset Registry And Metadata

Implemented flow:

- `Dataset` records are created during ingestion.
- Quality profile metadata is stored in the quality report JSON.
- `MetadataService` emits metadata-prefixed events into the shared audit-event table.
- `GET /api/v1/metadata/events` can query metadata events.

Gaps:

- Metadata is not yet a first-class registry layer with dedicated repository boundaries.
- Schema registry, lineage registry, usage events, AI context records, and dashboard dependency records are not yet implemented as explicit metadata assets.
- Metadata emission is present for ingestion profile creation, but it is not consistent across SQL queries, dashboards, AI interactions, alerts, and workflow execution.

### SQL Analytics

Implemented flow:

- Dataset query endpoints can run SQL against uploaded datasets.
- Tests cover querying uploaded CSV data through lakehouse and dataset query routes.
- Dataset statistics can be generated for uploaded CSV files.

Gaps:

- Query history, saved queries, query execution metrics, and query-to-dataset dependency records are not first-class models yet.
- Analytics statistics currently load CSV rows into memory.
- SQL execution emits audit events, but metadata lineage/usage generation is still shallow.

### AI And Automation

Implemented flow:

- Automation generation can call a local OpenAI-compatible endpoint or deterministic fallback.
- Automation records can be generated and executed.
- Tests cover automation behavior.

Gaps:

- AI is not yet grounded through a dedicated AI Context Layer.
- Outputs do not consistently include source assets, affected assets, confidence, reasoning summary, and next action in a platform-wide format.
- Automation is useful, but it risks being generic unless it is bound to metadata, lineage, dataset profiles, query history, dashboard dependencies, and governance state.

### Dashboard Operationalization

Implemented flow:

- Dashboards can be created.
- Dashboard creation from query output is supported in the frontend workflow.
- Collaboration comments and shares can be recorded.
- Audit tests cover dashboard creation events.

Gaps:

- Dashboard dependency tracking is not yet modeled.
- Dashboard usage events, KPI ownership, alert-readiness, AI dashboard summaries, and dataset-change impact analysis are not implemented yet.
- Dashboard metadata is not yet integrated into a broader metadata registry.

### Observability

Implemented flow:

- Request logging middleware records method, path, status, duration, and request ID.
- Error handlers provide structured error responses.
- Health endpoints exist.
- Audit events are available for governance workflows.

Gaps:

- Metrics endpoint, OpenTelemetry tracing, worker/job observability, and alert-ready error tracking are not yet implemented.
- Workflow status is not consistently modeled across ingestion, query, dashboard, and AI operations.

## Service Classification

| Classification | Services |
| --- | --- |
| Domain services | `analytics_service.py`, `automation_service.py`, `business_service.py`, `guidance_service.py`, `lakehouse_service.py`, `metadata_service.py`, `ml_service.py`, `pipeline_service.py`, `quality_service.py`, `recommendation_service.py`, `visualization_service.py`, `workspace_management_service.py` |
| Workflow services | `automation_workflow_service.py`, `business_workflow_service.py`, `collaboration_workflow_service.py`, `dataset_workflow_service.py`, `governance_workflow_service.py`, `guidance_workflow_service.py`, `ingestion_workflow_service.py`, `ml_workflow_service.py`, `pipeline_workflow_service.py`, `recommendation_workflow_service.py`, `visualization_workflow_service.py`, `workspace_workflow_service.py` |
| Cross-cutting / infrastructure | `audit_service.py`, `backend/app/core/*` middleware, config, auth, database, retry, error handling, and observability utilities |

The classification is useful, but several workflow services are thin and some are not wired as the canonical orchestration path. The next backend maturity step should consolidate duplicate services and make workflow services own durable multi-step operations.

## Oversized Files

| File | Lines | Review |
| --- | ---: | --- |
| `frontend/src/features/ingestion/hooks/useIngestionWizard.ts` | 357 | Owns the full ingestion workflow state; easier to read than the prior monolith, but still the next frontend simplification target. |
| `backend/app/services/automation_service.py` | 389 | Largest backend service; likely mixes provider calling, fallback generation, execution, and persistence formatting. |
| `frontend/src/HomeView.tsx` | 199 | Data-driven presentational component; lower risk than workflow-heavy files. |
| `backend/app/services/ingestion_service.py` | 164 | Improved by removing a shadowed legacy upload helper; still overlaps with `ingestion_workflow_service.py`. |
| `frontend/src/features/workspace/hooks/useDashboardWorkflow.ts` | 163 | Focused dashboard orchestration; acceptable size but should gain tests before deeper dashboard operationalization. |
| `frontend/src/GuidedTour.tsx` | 138 | Extracted helper logic and cleaned UI copy; needs visual smoke coverage rather than more splitting. |

## Architecture Strengths

- API routes are mostly thin and delegate to services.
- Backend tests cover many current routes and critical MVP workflows.
- Metadata events exist and can be queried.
- Request logging and structured errors are already in place.
- The frontend now has a small root `App.tsx`, feature-oriented control-room modules, an ingestion workflow split into hook plus panel components, and an automation studio split into focused subpanels.
- Home and guided-tour UI copy has been normalized to clean ASCII text after removing corrupted display characters.
- The codebase has enough structure to deepen core DAOS workflows without introducing new platform domains.

## Architecture Risks

- Metadata is still event-like, not yet the platform nervous system.
- Ingestion is synchronous, CSV-only, and memory-bound at upload time.
- SQL analytics lacks query-history and lineage models.
- AI features are not yet systematically grounded in DAOS metadata.
- Dashboards are records and UI workflows, not operational assets with dependencies, ownership, usage, and impact analysis.
- Frontend tests are absent, and frontend lint is not configured.
- Several services are thin or duplicative.

## Next Implementation Priorities

1. Consolidate ingestion into one canonical workflow service, add an ingestion job state model, and move long-running work out of the request path.
2. Add focused frontend tests for the split ingestion wizard and then continue simplifying `useIngestionWizard.ts` into smaller data-loading, upload, query, and dashboard-draft hooks.
3. Implement first-class metadata architecture: metadata repository, event emitter, schema registry, lineage records, usage events, and audit event integration.
4. Add query history, saved queries, execution metrics, dataset dependency tracking, and metadata emission for SQL workflows.
5. Add dashboard dependency metadata, dashboard usage events, KPI ownership, and dataset-change impact checks.
6. Build the AI Context Layer before adding new AI UI: context builder, source-grounded response format, confidence, affected assets, and recommended next action.
7. Add metrics-ready observability for ingestion jobs, query execution, metadata events, AI requests, and dashboard loads.
8. Add frontend component tests and a frontend lint script so frontend changes have a comparable quality gate to backend changes.
