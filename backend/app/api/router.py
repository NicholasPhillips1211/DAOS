from fastapi import APIRouter

from app.api.routes import analytics, datasets, health, ingestion, lakehouse, ml, pipelines, visualization, workspaces, collaboration, governance, business, recommendations, guidance

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["ingestion"])
api_router.include_router(lakehouse.router, prefix="/datasets", tags=["lakehouse"])
api_router.include_router(pipelines.router, prefix="/pipelines", tags=["pipelines"])
api_router.include_router(ml.router, prefix="/ml", tags=["ml"])
api_router.include_router(visualization.router, prefix="/visualizations", tags=["visualizations"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(collaboration.router, prefix="/collaboration", tags=["collaboration"])
api_router.include_router(governance.router, prefix="/governance", tags=["governance"])
api_router.include_router(business.router, prefix="/business", tags=["business"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
api_router.include_router(guidance.router, prefix="/guidance", tags=["guidance"])
