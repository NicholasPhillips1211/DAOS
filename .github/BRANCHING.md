# DAOS Branch Strategy for Blueprint Execution

## Branch to Workstream Mapping

- `feature/core-ingestion-depth`
  - Scope: ingestion reliability, profiling depth, SQL handoff continuity, dashboard readiness handoff.
- `feature/metadata-core`
  - Scope: metadata event stream, lineage-ready metadata payloads, metadata query APIs.
- `feature/backend-observability`
  - Scope: request/error metrics, telemetry capture, observability endpoint, operational signals.
- `feature/frontend-refactor`
  - Scope: feature-driven frontend structure, routed app shell, modular state and services scaffolding.
- `feature/ai-workflow-intelligence`
  - Scope: grounded AI payloads, confidence scoring, traceability metadata for generated plans.
- `feature/testing-suite`
  - Scope: reliability-path tests, ingestion/quality validation tests, standardized pytest config.
- `feature/operational-hardening`
  - Scope: retry primitives, hardened write paths, structured failure handling.
- `docs/blueprint`
  - Scope: execution plan, branch governance, rollout tracking artifacts.

## Branch Governance

- Keep one coherent capability per branch.
- Require passing tests on branch-specific changes before merge.
- Prefer squash merge after review to maintain concise history.
- Merge sequence should follow the workstream dependency chain from foundation to hardening.

## Suggested Merge Sequence

1. `feature/core-ingestion-depth`
2. `feature/metadata-core`
3. `feature/backend-observability`
4. `feature/frontend-refactor`
5. `feature/ai-workflow-intelligence`
6. `feature/testing-suite`
7. `feature/operational-hardening`
8. `docs/blueprint`
