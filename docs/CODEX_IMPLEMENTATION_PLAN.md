# Codex Implementation Plan

Review date: 2026-06-05

This plan keeps future Codex work aligned to the DAOS product identity: an AI-Powered Management Information Operating System. Work should strengthen the management information lifecycle only:

1. Information Collection
2. Information Governance
3. Information Analysis
4. Information Intelligence
5. Information Operationalization

Features that do not improve this lifecycle should not be prioritized. Existing implementation tracks remain useful, but they are delivery tracks under the lifecycle rather than the product identity:

- Frontend workflow refactor: Information Analysis and Information Operationalization.
- Ingestion backend consolidation: Information Collection and Information Governance.
- Metadata core: Information Governance and Information Intelligence.
- SQL workspace: Information Analysis.
- AI context layer: Information Intelligence.
- Dashboard operationalization: Information Operationalization.

## Completed In This Stabilization Pass

- Audited repository structure, backend services, frontend modules, tests, and docs.
- Reduced `frontend/src/App.tsx` from a large workflow orchestrator to a 36-line shell.
- Moved workspace state/API orchestration into `frontend/src/features/workspace/hooks/useWorkspaceWorkflow.ts`.
- Split workspace orchestration into dashboard, collaboration, and automation hooks.
- Split the ingestion wizard into an ingestion hook and focused panel components.
- Split the automation studio into focused header, plan summary, signals, recipe, and execution panels.
- Reworked the home view into data-driven sections and cleaned guided-tour UI copy/positioning helpers.
- Added feature components for workspace header, automation studio, collaboration, automation history, dashboard operations, and local AI bridge.
- Removed backend lint blockers in `main.py`, ingestion workflow code, and `tests/conftest.py`.
- Hardened RBAC across workspace-scoped data routes.
- Consolidated ingestion onto `IngestionWorkflowService`, removed the duplicate ingestion service, added queryable ingestion jobs, and streamed upload persistence.
- Added first-class metadata repository boundaries and lifecycle metadata records for schemas, lineage, usage, and AI context.
- Routed ingestion, SQL query execution, dashboard creation, and automation generation through the metadata core.
- Added query execution history, saved queries, execution duration capture, and dataset-to-query lineage metadata.
- Added dashboard dependency records, KPI ownership, dataset-impact lookup, and dashboard lineage metadata.
- Added explanatory docstrings around metadata, analysis, and dashboard workflow boundaries so persistence, orchestration, and route responsibilities are easier to maintain.
- Added a reusable AI context builder that assembles lifecycle-grounded workspace context from metadata, lineage, usage, query history, dashboards, governance, and automation state.
- Added `docs/ARCHITECTURE_REVIEW.md`.
- Added `docs/TECHNICAL_DEBT_REGISTER.md`.
- Validated backend lint, backend tests, frontend build, and local startup endpoints.

## Immediate Next Track

### Track 1: Finish Frontend Workflow Refactor

Goal: make the analyst workflow modular without changing the management information scope.

Tasks:

- Add component tests for the split ingestion wizard.
- Continue simplifying `useIngestionWizard.ts` into data-loading, upload, query, and dashboard-draft hooks once tests protect the flow.
- Keep `WorkspaceControlRoom.tsx` as composition only.
- Add frontend component tests for the ingestion-to-dashboard handoff.
- Add a frontend lint script and quality gate.

Exit criteria:

- No workflow page or component over 250 lines unless it is intentionally table-heavy, schema-heavy, or a stateful hook awaiting test coverage.
- Ingestion upload, SQL preview, dashboard draft approval, dashboard creation, automation generation, and collaboration forms build cleanly and have focused tests.

### Track 2: Consolidate Ingestion Backend

Goal: strengthen Information Collection and Information Governance by making ingestion an observable workflow rather than request-bound upload handling.

Completed:

- Choose one canonical ingestion workflow service.
- Move route orchestration to that service.
- Add durable ingestion job states.
- Record failures, retries, timestamps, and metadata emission in one transactionally clear flow.
- Replace full in-memory upload reads with staged streaming where practical.

Remaining:

- Move profiling and record finalization out of the API request path.
- Add worker handoff, retry counters, resumable failure handling, and operational job metrics.

Exit criteria:

- Upload route remains thin.
- Ingestion job state is queryable.
- Success and failure paths are covered by tests.
- Every ingestion job emits audit and metadata events.

### Track 3: Build Metadata Core

Goal: strengthen Information Governance and Information Intelligence by making metadata the platform nervous system.

Completed:

- Add metadata repository boundaries.
- Add schema registry records.
- Add lineage records.
- Add usage events.
- Add AI context records.
- Route ingestion, SQL, dashboard, and AI workflows through one metadata emitter.

Remaining:

- Add dataset ownership and stewardship metadata.
- Extend SQL lineage beyond source dataset dependencies into saved queries, dashboards, and downstream outputs.
- Add alert readiness, AI dashboard summaries, and operational dashboard health metrics.
- Add operational metrics around metadata emission and record freshness.

Exit criteria:

- Metadata can answer what asset changed, who owns it, what it depends on, how it is used, and which workflows it affected.
- Metadata tests cover consistency across ingestion and SQL workflows.

## Follow-On Tracks

### Information Analysis Track

Completed:

- Add query execution records.
- Add query history.
- Add saved queries.
- Track dataset dependencies from SQL execution.
- Emit usage and lineage metadata from query execution.
- Capture basic query duration metrics.

Remaining:

- Add saved-query-to-dashboard dependencies.
- Add query result persistence where useful for repeatable analysis.
- Add richer SQL parsing for multi-dataset lineage when connector support expands.

### Information Intelligence Track

Completed:

- Add AI context model.
- Build a context builder from metadata, lineage, profiles, query history, dashboards, governance, and workspace state.
- Return grounded context with confidence, sources, and recommended next actions.

Remaining:

- Standardize generated AI outputs with reasoning summary and affected assets.
- Connect automation generation to the reusable AI context builder.
- Add AI-generated dashboard summaries grounded in metadata.

### Information Operationalization Track

Completed:

- Add dashboard dependency records.
- Emit dashboard usage and dependency events.
- Add KPI ownership.
- Add dataset-change impact analysis.
- Emit dataset-to-dashboard and query-to-dashboard lineage metadata.

Remaining:

- Add AI-generated dashboard summaries grounded in metadata.
- Add alert-readiness checks for dashboards.
- Add operational dashboard health metrics.

### Observability And Quality

- Add metrics endpoint.
- Add workflow execution status records.
- Add OpenTelemetry-ready instrumentation.
- Add backend coverage reporting.
- Add frontend tests and E2E smoke tests.

## Working Rules For Future Codex Passes

- Do not add new platform domains before deepening the management information lifecycle through ingestion, metadata, SQL, AI context, and dashboards.
- Keep API routes thin.
- Put business logic in services and persistence in repositories.
- Do not run long jobs inside API requests.
- Every major workflow operation should emit metadata and observability events.
- Every new feature should explicitly map to Information Collection, Information Governance, Information Analysis, Information Intelligence, or Information Operationalization.
- Every major change should update docs to describe implemented behavior only.
- Every pass should end with targeted tests plus the relevant build/startup checks.
