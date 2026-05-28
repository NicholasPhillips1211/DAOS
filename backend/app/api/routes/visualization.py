from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_pagination
from app.models.visualization import Dashboard
from app.schemas.visualization import (
    ChartRecommendationRead,
    ChartRecommendationRequest,
    DashboardCreate,
    DashboardRead,
)
from app.services.analytics_service import AnalyticsService
from app.services.audit_service import AuditService
from app.services.visualization_service import VisualizationService
from app.services.workspace_workflow_service import WorkspaceWorkflowService
from app.services.visualization_workflow_service import VisualizationWorkflowService

router = APIRouter()
visualization_service = VisualizationService()
analytics_service = AnalyticsService()
workspace_workflow_service = WorkspaceWorkflowService()
visualization_workflow_service = VisualizationWorkflowService(visualization_service, analytics_service)
audit_service = AuditService()


@router.get("/dashboards", response_model=list[DashboardRead])
def list_dashboards(response: Response, db: Session = Depends(get_db), pagination: dict = Depends(get_pagination)) -> list[Dashboard]:
    """List dashboards newest-first for the workspace overview page."""
    total = db.query(Dashboard).count()
    response.headers["X-Total-Count"] = str(total)
    return db.query(Dashboard).order_by(Dashboard.created_at.desc()).limit(pagination["limit"]).offset(pagination["offset"]).all()


@router.post("/dashboards", response_model=DashboardRead, status_code=201)
def create_dashboard(
    payload: DashboardCreate,
    x_user_email: str | None = Header(default=None, alias="X-User-Email"),
    db: Session = Depends(get_db),
) -> Dashboard:
    """Create a dashboard record as a container for charts and summaries."""

    dashboard = workspace_workflow_service.create_dashboard(
        db,
        payload.workspace_id,
        payload.name,
        payload.description,
    )

    audit_service.log_event(
        payload.workspace_id,
        "dashboard.created",
        actor=x_user_email or "system",
        resource_type="dashboard",
        resource_id=dashboard.id,
        details=payload.description or payload.name,
    )

    return dashboard


@router.post("/recommend-chart", response_model=ChartRecommendationRead)
def recommend_chart(payload: ChartRecommendationRequest, db: Session = Depends(get_db)) -> ChartRecommendationRead:
    """Recommend a chart type from the dataset's column shapes and goal."""

    return visualization_workflow_service.recommend_chart(db, payload)