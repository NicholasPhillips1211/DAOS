# Architecture Overview

## Product Description

DAOS is a modular Intelligent DataOps Platform for analysts and data teams who need a single workspace for ingesting data, validating quality, analyzing with SQL, producing dashboards, training models, and translating technical findings into business language.

The platform is designed to be production-oriented from the start: it uses a FastAPI control plane, React-based analyst UI, persistent metadata storage, auditable collaboration flows, and deployable infrastructure artifacts for Docker and Kubernetes.

## System Shape

- React + TypeScript frontend for analyst workflows
- FastAPI backend for control-plane APIs and orchestration
- PostgreSQL for metadata and workflow state
- Object storage for raw and curated data assets
- Lakehouse table format for SQL access over analytical datasets
- Kubernetes for deployment and horizontal scaling

## Core Data Flow

1. Source data enters via file upload, API, database sync, or streaming connector.
2. Raw data lands in immutable storage and is registered in metadata tables.
3. Cleaning and normalization jobs generate quality reports and curated outputs.
4. SQL analytics, pipelines, dashboards, and ML jobs consume curated data.
5. Insights and business summaries are published back into the workspace.

## MVP Boundaries

- Batch-first ingestion
- Dataset profiling and quality reporting
- Workspace metadata and dataset registry
- Pipeline definitions and run history
- SQL analytics and dashboard shell
- Lightweight ML explainability
- RBAC and audit logging hooks
