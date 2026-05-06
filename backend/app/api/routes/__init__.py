from app.api.routes.analytics import router as analytics_router
from app.api.routes.datasets import router as datasets_router
from app.api.routes.ingestion import router as ingestion_router
from app.api.routes.health import router as health_router
from app.api.routes.lakehouse import router as lakehouse_router
from app.api.routes.ml import router as ml_router
from app.api.routes.pipelines import router as pipelines_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.guidance import router as guidance_router
from app.api.routes.visualization import router as visualization_router
from app.api.routes.workspaces import router as workspaces_router

__all__ = ["analytics_router", "datasets_router", "guidance_router", "health_router", "ingestion_router", "lakehouse_router", "ml_router", "pipelines_router", "recommendations_router", "visualization_router", "workspaces_router"]
