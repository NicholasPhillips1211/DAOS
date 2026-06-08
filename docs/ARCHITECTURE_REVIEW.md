# DAOS Architecture Review

Review date: 2026-06-05

DAOS is currently a FastAPI + React scaffold for an AI-Powered Management Information Operating System with good route/service separation, a working local workflow for CSV ingestion, cleaning, profiling, SQL querying, dashboard creation, collaboration, automation planning, metadata events, and governance audit events. The product direction in this repository is strongest when it stays centered on the management information lifecycle:

Information Collection -> Information Governance -> Information Analysis -> Information Intelligence -> Information Operationalization.

This review covers the architecture as implemented in the repository after the stabilization, RBAC, frontend cleanup, Track 2 ingestion consolidation, and first metadata-core implementation passes.

## Validation Summary

| Area | Command | Result |
| --- | --- | --- |
| Backend install | `.\.venv\Scripts\python.exe -m pip install -e .\backend[dev]` | Passed after sandbox escalation; installed declared backend runtime and dev dependencies. |
| Backend lint | `.\.venv\Scripts\python.exe -m ruff check backend\app backend\tests` | Passed. |
| Backend tests | `.\.venv\Scripts\python.exe -m pytest backend\tests -q` | Passed: 34 tests. |
| Frontend build | `npm.cmd run build` from `frontend/` | Passed after sandbox escalation. Vite emitted a chunk-size warning for a 503.42 kB JS asset. |
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

### Ingestion, Cleaning, And Profiling

Implemented flow:

- `POST /api/v1/ingestion/upload` validates workspace access through RBAC, persists the raw file, and queues cleaning/profiling work through `WorkItem`.
- `IngestionWorkflowService` creates a durable `IngestionJob`, streams the uploaded CSV to workspace-scoped raw storage, creates cleaned and rejected-row CSV artifacts through DuckDB-backed `QualityService`, profiles raw versus cleaned quality, creates `Dataset` and `DataQualityReport` records, and transitions the job to `completed` or `failed`.
- The `Dataset` record points to the cleaned artifact, while the ingestion job and quality metadata preserve the raw, cleaned, and rejected artifact paths for auditability.
- `GET /api/v1/ingestion/jobs` and `GET /api/v1/ingestion/jobs/{job_id}` expose job state after enforcing workspace access.
- Successful ingestion emits audit and metadata events, including the ingestion job id, cleaning summary, raw-vs-clean quality delta, artifact fingerprints, schema snapshot, usage records, and raw-to-clean lineage.
- Tests cover successful upload, missing workspace, non-CSV rejection, blank dataset name rejection, quality report retrieval, queryability, job state retrieval, failure state recording, and RBAC on job access.

Gaps:

- Only CSV is supported.
- Cleaning policy is fixed; analyst preview, rule configuration, rejected-row review/download UX, and promotion approval are not implemented yet.
- Retry handling exists for file and DB writes, while production-scale resumable checkpoints still need to be added.

### Information Governance Metadata

Implemented flow:

- `Dataset` records are created during ingestion.
- Cleaning and quality profile metadata are stored in the quality report JSON.
- `MetadataService` emits metadata-prefixed events into the shared audit-event table.
- `GET /api/v1/metadata/events` can query metadata events.
- `MetadataRepository` provides first-class persistence boundaries for schema, lineage, usage, and AI context records.
- `GET /api/v1/metadata/schemas`, `/lineage`, `/usage`, and `/ai-context` expose lifecycle metadata with workspace RBAC.
- `POST /api/v1/metadata/ai-context/build` creates reusable workspace context from the full management information lifecycle.
- Successful ingestion records a dataset schema snapshot, ingestion-job-to-dataset lineage, raw-to-clean lineage, collection and cleaning usage, and dataset-profile AI context.

Gaps:

- Metadata ownership, stewardship, classification, and freshness records are not implemented yet.
- SQL, dashboard, alert, and workflow metadata are only partially modeled.
- Dashboard dependency records are not yet implemented as explicit metadata assets.

### Information Analysis

Implemented flow:

- Dataset query endpoints can run SQL against uploaded datasets.
- Tests cover querying cleaned uploaded CSV data through lakehouse and dataset query routes.
- Dataset statistics can be generated for uploaded CSV files.
- Dataset and lakehouse query execution now records query execution history, row/column counts, duration, metadata usage, and dataset-to-query lineage.
- `GET /api/v1/analytics/query-executions` exposes workspace-scoped query history.
- `GET /api/v1/analytics/saved-queries` and `POST /api/v1/analytics/saved-queries` support reusable SQL statements.

Gaps:

- Analytics statistics currently load CSV rows into memory.
- SQL lineage records source datasets and can feed dashboard dependency lineage; multi-dataset lineage is still future work.

### Information Intelligence And Automation

Implemented flow:

- Automation generation can call a local OpenAI-compatible endpoint or deterministic fallback.
- Automation records can be generated and executed.
- Automation generation records an AI context snapshot grounded in the generated plan payload.
- Dataset ingestion records dataset-profile AI context for downstream AI grounding.
- The AI context builder assembles workspace-level context with lifecycle sections, sources, confidence, and recommended next actions.
- Tests cover automation behavior.

Gaps:

- Generated AI outputs do not yet consistently include reasoning summary and affected assets.
- Automation generation still builds its own signal snapshot instead of consuming the reusable AI context builder.

### Information Operationalization

Implemented flow:

- Dashboards can be created.
- Dashboard creation from query output is supported in the frontend workflow.
- Dashboard creation records metadata usage events.
- Dashboards can register dataset and query execution dependencies.
- KPI owners can be assigned to dashboards.
- Dataset-impact lookup returns dashboards and KPI owners affected by a dataset change.
- Dashboard dependencies emit dataset-to-dashboard and query-to-dashboard lineage metadata.
- Collaboration comments and shares can be recorded.
- Audit tests cover dashboard creation events.

Gaps:

- Alert-readiness and AI dashboard summaries are not implemented yet.
- Dashboard metadata has dependency and ownership records, but does not yet include health/freshness scoring.

### Observability

Implemented flow:

- Request logging middleware records method, path, status, duration, and request ID.
- Error handlers provide structured error responses.
- Health endpoints exist.
- Audit events are available for governance workflows.

Gaps:

- Metrics endpoint exists, but OpenTelemetry tracing, worker observability, and alert-ready error tracking are not yet implemented.
- Ingestion workflow status is now modeled through queryable jobs, but query, dashboard, and AI operations still need consistent workflow-status models.

## Service Classification

| Classification | Services |
| --- | --- |
| Domain services | `ai_context_builder_service.py`, `analytics_service.py`, `automation_service.py`, `business_service.py`, `guidance_service.py`, `lakehouse_service.py`, `metadata_service.py`, `ml_service.py`, `pipeline_service.py`, `quality_service.py`, `recommendation_service.py`, `visualization_service.py`, `workspace_management_service.py` |
| Workflow services | `automation_workflow_service.py`, `business_workflow_service.py`, `collaboration_workflow_service.py`, `dataset_workflow_service.py`, `governance_workflow_service.py`, `guidance_workflow_service.py`, `ingestion_workflow_service.py`, `ml_workflow_service.py`, `pipeline_workflow_service.py`, `recommendation_workflow_service.py`, `visualization_workflow_service.py`, `workspace_workflow_service.py` |
| Cross-cutting / infrastructure | `audit_service.py`, `backend/app/core/*` middleware, config, auth, database, retry, error handling, and observability utilities |

The classification is useful, but several workflow services are still thin. The next backend maturity step should make workflow services own durable multi-step operations with worker handoff and status records.

## Oversized Files

| File | Lines | Review |
| --- | ---: | --- |
| `frontend/src/features/ingestion/hooks/useIngestionWizard.ts` | 357 | Owns the full ingestion workflow state; easier to read than the prior monolith, but still the next frontend simplification target. |
| `backend/app/services/automation_service.py` | 454 | Largest backend service; mixes provider calling, fallback generation, execution, and persistence formatting. |
| `backend/app/services/ingestion_workflow_service.py` | 427+ | Canonical ingestion workflow; owns job state, streaming file persistence, cleaning, profiling, audit, and metadata emission. Should be split as cleaning policy and artifact lifecycle rules deepen. |
| `frontend/src/HomeView.tsx` | 199 | Data-driven presentational component; lower risk than workflow-heavy files. |
| `frontend/src/features/workspace/hooks/useDashboardWorkflow.ts` | 163 | Focused dashboard orchestration; acceptable size but should gain tests before deeper dashboard operationalization. |
| `frontend/src/GuidedTour.tsx` | 138 | Extracted helper logic and cleaned UI copy; needs visual smoke coverage rather than more splitting. |

## Architecture Strengths

- API routes are mostly thin and delegate to services.
- Recent metadata, analysis, and dashboard services now include explanatory docstrings that describe why responsibilities sit at route, service, and repository layers.
- Backend tests cover many current routes and critical MVP workflows.
- Metadata events, schema records, lineage records, usage events, and AI context records exist and can be queried.
- Request logging and structured errors are already in place.
- The frontend now has a small root `App.tsx`, feature-oriented control-room modules, an ingestion workflow split into hook plus panel components, and an automation studio split into focused subpanels.
- Home and guided-tour UI copy has been normalized to clean ASCII text after removing corrupted display characters.
- The codebase has enough structure to deepen core DAOS workflows without introducing new platform domains.

## Architecture Risks

- Metadata is now a first-class core, but it is still early and does not yet cover dataset ownership, dashboard health, or freshness.
- Ingestion is async and CSV-only; DuckDB now owns worker-side CSV cleaning/profiling, but resumable checkpoints and policy controls still need production depth.
- SQL analytics has query history and source-dataset lineage; multi-dataset lineage remains future work.
- AI has a reusable metadata-grounded context builder, but automation and summaries still need to consume it directly.
- Dashboards now have dependency and KPI ownership metadata, but still need health, alert readiness, and AI summaries.
- Frontend tests are absent, and frontend lint is not configured.
- Several services are thin or duplicative.

## Next Implementation Priorities

1. Deepen ingestion cleaning with configurable policies, rejected-row review/download UX, and analyst preview/approval before promotion.
2. Add focused frontend tests for the split ingestion wizard and then continue simplifying `useIngestionWizard.ts` into smaller data-loading, upload, query, and dashboard-draft hooks.
3. Complete Information Governance metadata with ownership, stewardship, classification, freshness, and migration coverage.
4. Strengthen Information Analysis with saved-query-to-dashboard dependencies, repeatable result persistence, and richer SQL lineage as connector support expands.
5. Strengthen Information Operationalization with dashboard health, alert-readiness checks, and AI dashboard summaries.
6. Connect automation and dashboard summaries to the reusable AI context builder, then standardize reasoning summaries and affected assets.
7. Add metrics-ready observability for ingestion jobs, query execution, metadata events, AI requests, and dashboard loads.
8. Add frontend component tests and a frontend lint script so frontend changes have a comparable quality gate to backend changes.
