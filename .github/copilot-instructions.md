# DAOS Copilot Instructions

Treat DAOS as an enterprise-grade AI-powered analytics operating system, not a prototype.

## Core principles
- Build for scale: assume concurrency, large datasets, long-running jobs, and multi-tenant deployments.
- Prefer modular design: thin API routes, service layers, repositories, dependency injection, and isolated domains.
- Keep AI-native behavior in mind: source-grounded, explainable, metadata-aware, and extensible for RAG and semantic workflows.
- Make everything metadata-aware: lineage, ownership, tags, schema tracking, auditability, versioning, and governance.
- Use production-quality implementation only: no TODO scaffolding, placeholder logic, or tutorial-style shortcuts.

## Backend expectations
- Use Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, asyncpg, and PostgreSQL.
- Keep routes thin and move business logic into services.
- Keep database access in repositories.
- Use async endpoints and background workers for ingestion, profiling, AI processing, indexing, and other long-running work.
- Favor DuckDB, Polars, and PyArrow for analytics workloads; avoid Pandas unless there is a strong reason.

## Frontend expectations
- Use React, TypeScript, Vite, Tailwind CSS, shadcn/ui, TanStack Query, TanStack Router, Zustand, and Framer Motion.
- Organize by feature area and keep components reusable and focused.
- Optimize for analyst and enterprise UX: minimal clutter, responsive layouts, performant dashboards, and workflow-centric interactions.

## Security, observability, and quality
- Support JWT auth, refresh rotation, RBAC, tenant isolation, OAuth2/SSO/MFA-ready architecture, and API key management.
- Never hardcode secrets and always validate permissions and sensitive operations.
- Include structured logging, metrics, tracing, health checks, error handling, and observability hooks.
- Prefer tests with every meaningful change: unit, integration, API, worker, frontend, and E2E where applicable.

## Implementation discipline
- Prioritize scalability, maintainability, observability, AI extensibility, and developer experience.
- Use migrations for schema changes.
- Keep long-running operations asynchronous.
- Avoid simplistic, naive, or in-memory-only implementations when data volume or concurrency matters.
