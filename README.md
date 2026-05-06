# Intelligent DataOps Platform

DAOS is a modular Intelligent DataOps Platform that turns raw data into governed, explainable, and business-ready decisions.

It combines ingestion, quality checks, SQL analytics, dashboards, ML, collaboration, business translation, recommendations, and project guidance in one workspace so analysts can move from data to action without stitching together separate tools.

This repository is a greenfield scaffold for a production-oriented DataOps platform.

## Backend

```bash
cd backend
uvicorn app.main:app --reload
```

Run backend tests:

```bash
cd backend
pytest tests -q
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Build frontend:

```bash
cd frontend
npm run build
```

## Local Docker Compose

```bash
docker compose -f docker-compose.yml up --build
```

## CI/CD

- GitHub Actions pipeline: `.github/workflows/ci.yml`
- Jobs:
	- Backend tests (Python 3.11, pytest)
	- Frontend build (Node 20, Vite build)

## Kubernetes Manifests

- Backend deployment/service: `infra/k8s/backend-deployment.yaml`
- Frontend deployment/service: `infra/k8s/frontend-deployment.yaml`

Apply manifests:

```bash
kubectl apply -f infra/k8s/
```
