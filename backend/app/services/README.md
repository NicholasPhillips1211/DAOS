# Service Layer Guide

This package contains business and workflow services for the DAOS backend.

## Why this layer exists

Routes in `app/api/routes` should primarily handle HTTP concerns:
- Request parsing
- Dependency injection
- Auth and RBAC checks
- Response shaping

Services in this package should handle business logic and orchestration.
This keeps endpoint behavior consistent and makes workflows easier to test and evolve.

## Service categories

1. Domain services (single capability)
- `analytics_service.py`
- `automation_service.py`
- `business_service.py`
- `guidance_service.py`
- `lakehouse_service.py`
- `quality_service.py`
- `visualization_service.py`
- ...

These focus on a specific domain capability (for example, chart recommendation, SQL execution, or text translation).

2. Workflow services (cross-model orchestration)
- `ingestion_workflow_service.py`
- `workspace_workflow_service.py`
- `collaboration_workflow_service.py`
- `automation_workflow_service.py`
- `governance_workflow_service.py`

These coordinate multi-step operations that touch multiple models/tables and enforce a stable business flow used by routes.

3. Cross-cutting support
- `audit_service.py`

These modules support observability, security, or platform-level concerns used by multiple routes/services.

## Conventions

- Keep route handlers thin. Prefer calling one workflow method over duplicating orchestration logic.
- Keep validation closest to the business operation that requires it.
- Raise `HTTPException` in workflow services only when needed to preserve existing API contracts.
- Keep transactions explicit (`add`, `commit`, `refresh`) inside service methods that own persistence.
- Add concise docstrings to explain non-obvious implementation decisions.
- Persist a terminal state for every attempted workflow execution, including malformed input and no-op outcomes.
- Keep plan-level statuses honest: reserve `completed` for workflows that actually executed useful work, and use clearer outcomes such as `failed`, `partial`, `skipped`, or `deferred` when appropriate.
- Prefer idempotent worker steps. Retried jobs should reuse already-created artifacts instead of duplicating datasets, dashboards, or metadata records.
- Emit audit, metadata, or work-item evidence for state changes that operators may need to investigate later.

## Suggested extension pattern

When adding a new endpoint with non-trivial business flow:

1. Add or extend a workflow service method in this package.
2. Keep RBAC checks in the route.
3. Delegate orchestration and persistence to the service.
4. Define the status transitions before writing the handler.
5. Add or update tests for happy path, validation errors, retry/no-op behavior, and persisted failure state.
