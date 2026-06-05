# Architecture Overview

## Product Description

DAOS is an AI-Powered Management Information Operating System for teams that need a single workspace for collecting information, governing quality and access, analyzing with SQL and visual tools, generating intelligence, and operationalizing decisions.

The platform is designed to be production-oriented from the start: it uses a FastAPI control plane, React-based analyst UI, persistent metadata storage, auditable collaboration flows, and deployable infrastructure artifacts for Docker and Kubernetes.

## System Shape

- React + TypeScript frontend for analyst workflows
- FastAPI backend for control-plane APIs and orchestration
- PostgreSQL for metadata and workflow state
- Object storage for raw and curated data assets
- Lakehouse table format for SQL access over analytical datasets
- Kubernetes for deployment and horizontal scaling

## Management Information Lifecycle Flow

1. Information Collection begins through file upload, API, database sync, streaming connector, or user input.
2. Information Governance registers raw assets, captures metadata, validates quality, enforces access, and records audit events.
3. Information Analysis uses curated information through SQL analytics, profiling, transformations, dashboards, and ML workflows.
4. Information Intelligence grounds recommendations, summaries, explanations, and AI assistance in governed metadata and analysis.
5. Information Operationalization publishes intelligence into dashboards, collaboration, approvals, automations, exports, and monitored actions.

## MVP Boundaries

- Batch-first ingestion
- Dataset profiling and quality reporting
- Workspace metadata and dataset registry
- Pipeline definitions and run history
- SQL analytics and dashboard shell
- Lightweight ML explainability
- RBAC and audit logging hooks
