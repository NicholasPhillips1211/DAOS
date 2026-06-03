# Codex Implementation Plan

Review date: 2026-06-03

This plan keeps future Codex work aligned to the DAOS product identity: an AI-Powered Operational Analytics Workspace. Work should strengthen one of these pillars only:

1. Ingestion Platform
2. Dataset Registry
3. Metadata Engine
4. SQL Workspace
5. AI Context Layer
6. Dashboard Operationalization

## Completed In This Stabilization Pass

- Audited repository structure, backend services, frontend modules, tests, and docs.
- Reduced `frontend/src/App.tsx` from a large workflow orchestrator to a 36-line shell.
- Moved workspace state/API orchestration into `frontend/src/features/workspace/hooks/useWorkspaceWorkflow.ts`.
- Split workspace orchestration into dashboard, collaboration, and automation hooks.
- Split the ingestion wizard into an ingestion hook and focused panel components.
- Split the automation studio into focused header, plan summary, signals, recipe, and execution panels.
- Reworked the home view into data-driven sections and cleaned guided-tour UI copy/positioning helpers.
- Added feature components for workspace header, automation studio, collaboration, automation history, dashboard operations, and local AI bridge.
- Removed backend lint blockers in `main.py`, `ingestion_service.py`, and `tests/conftest.py`.
- Added `docs/ARCHITECTURE_REVIEW.md`.
- Added `docs/TECHNICAL_DEBT_REGISTER.md`.
- Validated backend lint, backend tests, frontend build, and local startup endpoints.

## Immediate Next Track

### Track 1: Finish Frontend Workflow Refactor

Goal: make the analyst workflow modular without changing product scope.

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

Goal: make ingestion an observable workflow rather than request-bound upload handling.

Tasks:

- Choose one canonical ingestion workflow service.
- Move route orchestration to that service.
- Add durable ingestion job states.
- Record failures, retries, timestamps, and metadata emission in one transactionally clear flow.
- Replace full in-memory upload reads with staged streaming where practical.

Exit criteria:

- Upload route remains thin.
- Ingestion job state is queryable.
- Success and failure paths are covered by tests.
- Every ingestion job emits audit and metadata events.

### Track 3: Build Metadata Core

Goal: make metadata the platform nervous system.

Tasks:

- Add metadata repository boundaries.
- Add schema registry records.
- Add lineage records.
- Add usage events.
- Add AI context records.
- Route ingestion, SQL, dashboard, and AI workflows through one metadata emitter.

Exit criteria:

- Metadata can answer what asset changed, who owns it, what it depends on, how it is used, and which workflows it affected.
- Metadata tests cover consistency across ingestion and SQL workflows.

## Follow-On Tracks

### SQL Workspace

- Add query execution records.
- Add query history.
- Add saved queries.
- Track dataset dependencies from SQL.
- Emit usage and lineage metadata from query execution.
- Add query performance metrics.

### AI Context Layer

- Add AI context model.
- Build a context builder from metadata, lineage, profiles, query history, dashboards, governance, and workspace state.
- Standardize AI outputs with confidence, sources, reasoning summary, affected assets, and next action.

### Dashboard Operationalization

- Add dashboard dependency records.
- Emit dashboard usage events.
- Add KPI ownership.
- Add dataset-change impact analysis.
- Add AI-generated dashboard summaries grounded in metadata.

### Observability And Quality

- Add metrics endpoint.
- Add workflow execution status records.
- Add OpenTelemetry-ready instrumentation.
- Add backend coverage reporting.
- Add frontend tests and E2E smoke tests.

## Working Rules For Future Codex Passes

- Do not add new platform domains before deepening ingestion, metadata, SQL, AI context, and dashboards.
- Keep API routes thin.
- Put business logic in services and persistence in repositories.
- Do not run long jobs inside API requests.
- Every major workflow operation should emit metadata and observability events.
- Every major change should update docs to describe implemented behavior only.
- Every pass should end with targeted tests plus the relevant build/startup checks.
