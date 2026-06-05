# DAOS Technical Debt Register

Review date: 2026-06-05

This register tracks debt that directly affects DAOS as an AI-Powered Management Information Operating System. Items are prioritized by their impact on the management information lifecycle: Information Collection, Information Governance, Information Analysis, Information Intelligence, and Information Operationalization.

Features, refactors, and debt work that do not improve this lifecycle should not be prioritized.

## Register

| ID | Lifecycle Stage | Area | Evidence | Impact | Priority | Next Action | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TD-001 | Information Collection | Frontend ingestion workflow size | `frontend/src/features/ingestion/hooks/useIngestionWizard.ts` is now the largest ingestion file at 357 lines after the component split. | The UI is easier to reason about, but the hook still owns upload, query, dashboard draft, and workspace summary state. | P1 | Add tests, then split the hook into data-loading, upload, query, and dashboard-draft hooks. | In progress |
| TD-002 | Information Operationalization | Root dashboard/workspace orchestration | `App.tsx`, `useWorkspaceWorkflow.ts`, and `AutomationStudio.tsx` now delegate to feature modules and focused panels. | The root bottleneck is removed; dashboard workflow still needs tests before deeper operationalization. | P1 | Add dashboard workflow tests and then extend dependency/usage metadata. | In progress |
| TD-003 | Information Collection | Duplicate ingestion services | `backend/app/services/ingestion_service.py` has been removed and upload routes now use `IngestionWorkflowService`. | The duplicate orchestration path is resolved; the remaining risk is the size of the canonical workflow service. | P0 | Split worker-facing steps out of `IngestionWorkflowService` when async execution is introduced. | Addressed |
| TD-004 | Information Governance | Metadata core is early | `MetadataRepository` and first-class schema, lineage, usage, and AI context records now exist. | Metadata has a real backbone, but ownership, stewardship, classification, freshness, and migration depth are still missing. | P0 | Add ownership, stewardship, classification, freshness records, and migration coverage. | In progress |
| TD-005 | Information Collection | Upload processing remains request-bound | `IngestionWorkflowService` streams upload persistence, but profiling still runs synchronously in the API request. | Large files no longer require one full route-level read, but long profiling work can still block requests. | P0 | Enqueue profiling after staged persistence and return job state immediately. | In progress |
| TD-006 | Information Collection | CSV-only ingestion | `resolve_source_name` rejects non-CSV files. | Required CSV, Parquet, JSON, and Excel ingestion depth is not present. | P1 | Add file-type-specific readers with DuckDB, Polars, PyArrow, and Parquet-native flows. | Open |
| TD-007 | Information Collection | Worker handoff missing | Ingestion jobs now record `running`, `completed`, and `failed` states with failure reasons, but execution is still in-process. | Workflow state is queryable, but retries and long-running ingestion are not yet durable worker operations. | P0 | Add worker handoff, retry counters, and resumable execution records. | In progress |
| TD-008 | Information Analysis | Query history is basic | Query executions, saved queries, row/column counts, and duration are now persisted. | SQL analysis has history, but not saved-query-to-dashboard dependencies, result persistence, or multi-dataset lineage. | P0 | Add saved-query-to-dashboard dependencies and richer SQL lineage when connector support expands. | In progress |
| TD-009 | Information Governance | SQL metadata lineage is source-only | SQL execution now emits usage metadata and dataset-to-query lineage records. | Metadata can see which dataset powered a query execution, but cannot yet connect saved queries to dashboards and downstream outputs. | P0 | Add saved-query, dashboard, and downstream-output lineage metadata. | In progress |
| TD-010 | Information Operationalization | Dashboard operational metadata is basic | Dashboard dependencies, KPI owners, dataset-impact lookup, and dashboard lineage now exist. | Dashboards are traceable operational assets, but still lack health scoring, alert readiness, and AI-generated summaries. | P0 | Add dashboard health, alert readiness, and AI-generated dashboard summaries. | In progress |
| TD-011 | Information Intelligence | AI output contract is incomplete | A reusable AI context builder now creates lifecycle-grounded workspace context with confidence, sources, and next actions. | AI has shared grounding, but automation and dashboard summaries do not yet consume it consistently or expose reasoning summaries and affected assets. | P0 | Connect AI workflows to the context builder and standardize reasoning summaries plus affected assets. | In progress |
| TD-012 | Information Governance | Metrics and tracing not yet implemented | Request logging and health exist; metrics endpoint and traces are not present. | Operators cannot fully answer what failed, why, who is affected, and what next. | P1 | Add metrics endpoint, workflow status records, and OpenTelemetry-ready instrumentation. | Open |
| TD-013 | Information Operationalization | Frontend tests and lint missing | `frontend/package.json` has `dev`, `build`, and `preview`, but no `test` or `lint`. | Frontend workflow refactors rely mainly on TypeScript build. | P1 | Add component tests for ingestion, dashboard draft, and workspace panels; add lint script. | Open |
| TD-014 | Information Operationalization | Frontend bundle warning | Vite build reports a JS chunk above 500 kB. | The app may become slow as workflow modules deepen. | P2 | Add route-level or feature-level code splitting and review manual chunks. | Open |
| TD-015 | Information Governance | Auth configuration friction | Backend startup fails when auth is enabled without `API_KEYS_CSV`. | Local smoke checks fail unless the local auth toggle is explicit. | P2 | Document local `AUTH_ENABLED=false` or provide API keys in `.env.example` guidance. | Open |
| TD-016 | Information Governance | Thin workflow services | Several workflow services are under 50 lines and may be wrappers instead of durable orchestration. | Service layer looks mature but may not yet own business invariants. | P1 | Audit each workflow service and deepen only lifecycle-critical DAOS capabilities first. | Open |

## Recently Addressed

| ID | Change | Evidence |
| --- | --- | --- |
| TD-002 | Reduced root frontend orchestration and split automation UI panels. | `frontend/src/App.tsx` is now 36 lines; `frontend/src/features/workspace/components/AutomationStudio.tsx` is now a 24-line shell with focused subpanels. |
| TD-003 | Consolidated ingestion onto one canonical workflow service. | `backend/app/services/ingestion_service.py` was removed; `backend/app/api/routes/ingestion.py` uses `IngestionWorkflowService`. |
| TD-005 | Replaced route-level full upload reads with streamed file persistence. | `IngestionWorkflowService.persist_file` streams chunks from the upload file object into raw storage. |
| TD-007 | Added queryable ingestion job state and failure recording. | `GET /api/v1/ingestion/jobs` and `GET /api/v1/ingestion/jobs/{job_id}` expose job state with RBAC. |
| TD-001 | Split the ingestion wizard monolith and removed the stale root wrapper. | `frontend/src/features/ingestion/IngestionWizard.tsx` now composes focused panel components. |
| TD-004 | Added first-class metadata records and repository boundary. | `MetadataRepository` persists schema, lineage, usage, and AI context records exposed through `/api/v1/metadata/*`. |
| TD-009 | Added query usage metadata. | Dataset and lakehouse query routes emit `dataset.query_executed` usage records. |
| TD-010 | Added dashboard usage metadata. | Dashboard creation emits `dashboard.created` usage records. |
| TD-011 | Added AI grounding records. | Dataset ingestion emits `dataset_profile` AI context and automation generation emits `automation_plan` AI context. |
| TD-008 | Added query history and saved queries. | `QueryExecution` and `SavedQuery` persist SQL history, reusable statements, row/column counts, and duration. |
| TD-009 | Added dataset-to-query lineage. | Query execution emits `dataset.query_executed` usage and `dataset -> query_execution` lineage records. |
| TD-010 | Added dashboard dependencies and KPI ownership. | Dashboard dependency and KPI owner endpoints persist operational metadata and dataset-impact lookup surfaces affected dashboards. |
| TD-011 | Added reusable AI context builder. | `POST /api/v1/metadata/ai-context/build` persists workspace context grounded in collection, governance, analysis, intelligence, and operationalization evidence. |
| Maintainability | Clarified service boundaries with descriptive docstrings. | Metadata, analysis, and dashboard workflow/repository methods now explain why persistence, orchestration, and HTTP responsibilities are separated. |
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
