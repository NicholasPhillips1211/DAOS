# DAOS Branching Map — Remediation Blueprint

This document maps the remediation blueprint sections to dedicated local branches. Create branches locally using `scripts/create_branches.ps1`.

- feature/core-ingestion-depth: Deepen ingestion, profiling, dataset pipelines, and E2E ingestion tests.
- feature/metadata-core: Implement metadata engine, lineage, profiling metadata, and metadata APIs.
- feature/backend-observability: Add OpenTelemetry, metrics, structured logging, and health checks.
- feature/frontend-refactor: Reorganize frontend into feature-driven architecture and modular state.
- feature/ai-workflow-intelligence: Implement metadata-grounded RAG pipelines and AI workflow services.
- feature/testing-suite: Add unit, integration, worker, and E2E test harnesses targeting 70%+ coverage.
- feature/operational-hardening: Retry logic, structured errors, audit events, and worker resilience.
- docs/blueprint: Documentation, migration guides, PR templates, and roadmap artifacts.

Guidance:
- Work should prioritize depth-first changes and be limited to the core workflow: ingestion → profiling → SQL exploration → AI insight → dashboards.
- Keep PRs focused; open one pull request per branch that implements a coherent set of changes.
- Avoid adding new top-level domains until the core workflow is stabilized.
