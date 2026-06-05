from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.auth import (
    Principal,
    WORKSPACE_READ_ROLES,
    WORKSPACE_WRITE_ROLES,
    get_current_principal,
    require_model_workspace_role,
    require_workspace_role,
    require_workspace_scope,
)
from app.core.dependencies import get_db, get_pagination
from app.models.metadata import Dataset
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
def list_dashboards(
    response: Response,
    workspace_id: int | None = Query(default=None, description="Filter dashboards to a single workspace"),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
    pagination: dict = Depends(get_pagination),
) -> list[Dashboard]:
    """List dashboards newest-first for the workspace overview page."""

    require_workspace_scope(workspace_id)
    query = db.query(Dashboard)
    if workspace_id is not None:
        require_workspace_role(db, workspace_id, principal, WORKSPACE_READ_ROLES)
        query = query.filter(Dashboard.workspace_id == workspace_id)

    total = query.count()
    response.headers["X-Total-Count"] = str(total)
    return query.order_by(Dashboard.created_at.desc()).limit(pagination["limit"]).offset(pagination["offset"]).all()


@router.post("/dashboards", response_model=DashboardRead, status_code=201)
def create_dashboard(
    payload: DashboardCreate,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> Dashboard:
    """Create a dashboard record as a container for charts and summaries."""

    require_workspace_role(db, payload.workspace_id, principal, WORKSPACE_WRITE_ROLES)
    dashboard = workspace_workflow_service.create_dashboard(
        db,
        payload.workspace_id,
        payload.name,
        payload.description,
    )

    audit_service.log_event(
        payload.workspace_id,
        "dashboard.created",
        actor=principal.user_email,
        resource_type="dashboard",
        resource_id=dashboard.id,
        details=payload.description or payload.name,
    )

    return dashboard


@router.post("/recommend-chart", response_model=ChartRecommendationRead)
def recommend_chart(
    payload: ChartRecommendationRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> ChartRecommendationRead:
    """Recommend a chart type from the dataset's column shapes and goal."""

    require_model_workspace_role(db, Dataset, payload.dataset_id, principal, WORKSPACE_READ_ROLES, model_name="Dataset")
    return visualization_workflow_service.recommend_chart(db, payload)
