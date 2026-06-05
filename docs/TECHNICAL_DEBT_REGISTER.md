# DAOS Technical Debt Register

Review date: 2026-06-03

This register tracks debt that directly affects DAOS as an AI-Powered Operational Analytics Workspace. Items are prioritized by their impact on the six core pillars: Ingestion Platform, Dataset Registry, Metadata Engine, SQL Workspace, AI Context Layer, and Dashboard Operationalization.

## Register

| ID | Pillar | Area | Evidence | Impact | Priority | Next Action | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TD-001 | Ingestion Platform | Frontend ingestion workflow size | `frontend/src/features/ingestion/hooks/useIngestionWizard.ts` is now the largest ingestion file at 357 lines after the component split. | The UI is easier to reason about, but the hook still owns upload, query, dashboard draft, and workspace summary state. | P1 | Add tests, then split the hook into data-loading, upload, query, and dashboard-draft hooks. | In progress |
| TD-002 | Dashboard Operationalization | Root dashboard/workspace orchestration | `App.tsx`, `useWorkspaceWorkflow.ts`, and `AutomationStudio.tsx` now delegate to feature modules and focused panels. | The root bottleneck is removed; dashboard workflow still needs tests before deeper operationalization. | P1 | Add dashboard workflow tests and then extend dependency/usage metadata. | In progress |
| TD-003 | Ingestion Platform | Duplicate ingestion services | `backend/app/services/ingestion_service.py` has been removed and upload routes now use `IngestionWorkflowService`. | The duplicate orchestration path is resolved; the remaining risk is the size of the canonical workflow service. | P0 | Split worker-facing steps out of `IngestionWorkflowService` when async execution is introduced. | Addressed |
| TD-004 | Metadata Engine | Metadata is audit-event backed only | `MetadataService` persists `metadata.*` events into `AuditEvent`. | Metadata cannot yet serve as registry, lineage, AI context, and operational dependency backbone. | P0 | Add dedicated metadata repository and models for schema, lineage, usage, and AI context records. | Open |
| TD-005 | Ingestion Platform | Upload processing remains request-bound | `IngestionWorkflowService` streams upload persistence, but profiling still runs synchronously in the API request. | Large files no longer require one full route-level read, but long profiling work can still block requests. | P0 | Enqueue profiling after staged persistence and return job state immediately. | In progress |
| TD-006 | Ingestion Platform | CSV-only ingestion | `resolve_source_name` rejects non-CSV files. | Required CSV, Parquet, JSON, and Excel ingestion depth is not present. | P1 | Add file-type-specific readers with DuckDB, Polars, PyArrow, and Parquet-native flows. | Open |
| TD-007 | Ingestion Platform | Worker handoff missing | Ingestion jobs now record `running`, `completed`, and `failed` states with failure reasons, but execution is still in-process. | Workflow state is queryable, but retries and long-running ingestion are not yet durable worker operations. | P0 | Add worker handoff, retry counters, and resumable execution records. | In progress |
| TD-008 | SQL Workspace | Query history and saved queries missing | Query tests verify execution but not persisted query records. | SQL analysis cannot yet provide usage, lineage, performance history, or saved analyst workflows. | P0 | Add query execution, query history, saved query, dependency, and performance models. | Open |
| TD-009 | Metadata Engine | SQL metadata emission is shallow | SQL execution has audit coverage, but not first-class metadata lineage/usage. | Metadata cannot answer which datasets power which queries and dashboards. | P0 | Emit usage and lineage metadata from query execution. | Open |
| TD-010 | Dashboard Operationalization | Dashboard dependencies missing | Dashboard records exist, but dependency and usage tracking are not first-class. | Dashboards remain static assets instead of operational assets. | P0 | Add dashboard dependency records, usage events, KPI ownership, and impact analysis. | Open |
| TD-011 | AI Context Layer | AI is not yet metadata-grounded | Automation generation can use LLM/fallback but lacks a shared AI context model. | AI can become generic rather than workflow-aware and explainable. | P0 | Build AI context model and context builder from metadata, profiles, lineage, query history, dashboards, governance, and workspace state. | Open |
| TD-012 | Observability | Metrics and tracing not yet implemented | Request logging and health exist; metrics endpoint and traces are not present. | Operators cannot fully answer what failed, why, who is affected, and what next. | P1 | Add metrics endpoint, workflow status records, and OpenTelemetry-ready instrumentation. | Open |
| TD-013 | Testing | Frontend tests and lint missing | `frontend/package.json` has `dev`, `build`, and `preview`, but no `test` or `lint`. | Frontend workflow refactors rely mainly on TypeScript build. | P1 | Add component tests for ingestion, dashboard draft, and workspace panels; add lint script. | Open |
| TD-014 | Build Quality | Frontend bundle warning | Vite build reports a JS chunk above 500 kB. | The app may become slow as workflow modules deepen. | P2 | Add route-level or feature-level code splitting and review manual chunks. | Open |
| TD-015 | Local Startup | Auth configuration friction | Backend startup fails when auth is enabled without `API_KEYS_CSV`. | Local smoke checks fail unless the local auth toggle is explicit. | P2 | Document local `AUTH_ENABLED=false` or provide API keys in `.env.example` guidance. | Open |
| TD-016 | Backend Service Depth | Thin workflow services | Several workflow services are under 50 lines and may be wrappers instead of durable orchestration. | Service layer looks mature but may not yet own business invariants. | P1 | Audit each workflow service and deepen only core DAOS pillars first. | Open |

## Recently Addressed

| ID | Change | Evidence |
| --- | --- | --- |
| TD-002 | Reduced root frontend orchestration and split automation UI panels. | `frontend/src/App.tsx` is now 36 lines; `frontend/src/features/workspace/components/AutomationStudio.tsx` is now a 24-line shell with focused subpanels. |
| TD-003 | Consolidated ingestion onto one canonical workflow service. | `backend/app/services/ingestion_service.py` was removed; `backend/app/api/routes/ingestion.py` uses `IngestionWorkflowService`. |
| TD-005 | Replaced route-level full upload reads with streamed file persistence. | `IngestionWorkflowService.persist_file` streams chunks from the upload file object into raw storage. |
| TD-007 | Added queryable ingestion job state and failure recording. | `GET /api/v1/ingestion/jobs` and `GET /api/v1/ingestion/jobs/{job_id}` expose job state with RBAC. |
| TD-001 | Split the ingestion wizard monolith and removed the stale root wrapper. | `frontend/src/features/ingestion/IngestionWizard.tsx` now composes focused panel components. |
| UI cleanup | Normalized corrupted frontend display text. | `frontend/src/HomeView.tsx` and `frontend/src/GuidedTour.tsx` now use clean ASCII copy and the source scan found no corrupted display markers. |

## Quality Gate Snapshot

Passing:

- `.\.venv\Scripts\python.exe -m ruff check backend\app backend\tests`
- `.\.venv\Scripts\python.exe -m pytest backend\tests -q`
- `npm.cmd run build`
- Backend health startup with `AUTH_ENABLED=false`
- Frontend dev server startup on `http://127.0.0.1:5173`

Known gaps:

- No frontend lint script.
- No frontend test script.
- Browser automation smoke check could not run because the in-app browser bridge failed to initialize in this local sandbox.
