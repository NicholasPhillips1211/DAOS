# DAOS Remediation Execution Plan

## Objective
Transform DAOS from architectural scaffold into a production-grade operational analytics workspace by executing depth-first remediation in isolated branches.

## Phase Alignment

### Phase 1: Core Operational Foundation
- Branch: `feature/core-ingestion-depth`
- Deliverables:
  - reliable ingestion execution path
  - profile generation and persisted quality metadata
  - query and dashboard handoff continuity

### Phase 2: Metadata and Observability Backbone
- Branches:
  - `feature/metadata-core`
  - `feature/backend-observability`
- Deliverables:
  - queryable metadata event stream
  - telemetry visibility (requests, errors, latency)

### Phase 3: Frontend Architectural Maturity
- Branch: `feature/frontend-refactor`
- Deliverables:
  - routed app shell
  - feature-domain module structure
  - modular state/service boundaries

### Phase 4: AI Workflow Intelligence
- Branch: `feature/ai-workflow-intelligence`
- Deliverables:
  - confidence-scored generated outputs
  - trace IDs and grounding evidence in AI payloads

### Phase 5: Reliability and Hardening
- Branches:
  - `feature/testing-suite`
  - `feature/operational-hardening`
- Deliverables:
  - failure-path coverage for ingestion and quality
  - retry utility and hardened persistence paths

## Exit Criteria
- Branch-specific tests pass before merge.
- No branch introduces unrelated platform domains.
- Core analyst workflow remains the primary optimization target:
  1. ingestion
  2. profiling
  3. SQL exploration
  4. AI insight generation
  5. dashboard operationalization
# DAOS — Weakness Remediation & Engineering Correction Blueprint (Condensed)

## Purpose
Operationalize the DAOS core: ingestion, dataset profiling, SQL exploration, AI insight generation, and dashboard operationalization.

## Phases & Branch Mapping

Phase 1 — Core Operational Foundation (branch: feature/core-ingestion-depth)
- Harden ingestion reliability, schema validation, profiling metadata capture, and ingestion tests.
- Implement dataset explorer APIs and SQL workspace foundations.

Phase 2 — Metadata & Observability (branches: feature/metadata-core, feature/backend-observability)
- Metadata engine with lineage, ownership, schema evolution, profiling metadata, and searchable metadata store.
- OpenTelemetry instrumentation, metrics export, health endpoints, and structured logging.

Phase 3 — Frontend Refactor & Testing (branches: feature/frontend-refactor, feature/testing-suite)
- Feature-driven frontend architecture and modular state management.
- Unit, integration, and E2E tests for core workflows. CI updates.

Phase 4 — AI Workflow Intelligence & Hardening (branches: feature/ai-workflow-intelligence, feature/operational-hardening)
- Metadata-grounded RAG pipelines, explainability, confidence scores, and operational orchestration suggestions.
- Retries, audit events, structured errors, worker resilience, and observability validation.

## Rules
- Prioritize depth before breadth; every change must improve the core analyst workflow.
- Every backend service must emit logs, metrics, traces, and produce metadata for operations.
- Avoid adding new domain surfaces; consolidate and deepen current modules.

## Next Steps
1. Run `scripts/create_branches.ps1` to create local branches.
2. Pick one branch and open a focused PR implementing a single coherent capability.
3. Run tests and CI checks; iterate.

