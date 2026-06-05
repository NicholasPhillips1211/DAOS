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
    DashboardDependencyCreate,
    DashboardDependencyRead,
    DashboardImpactRead,
    DashboardKpiOwnerCreate,
    DashboardKpiOwnerRead,
    DashboardRead,
)
from app.services.analytics_service import AnalyticsService
from app.services.audit_service import AuditService
from app.services.metadata_service import MetadataService
from app.services.visualization_service import VisualizationService
from app.services.workspace_workflow_service import WorkspaceWorkflowService
from app.services.visualization_workflow_service import VisualizationWorkflowService

router = APIRouter()
visualization_service = VisualizationService()
analytics_service = AnalyticsService()
workspace_workflow_service = WorkspaceWorkflowService()
visualization_workflow_service = VisualizationWorkflowService(visualization_service, analytics_service)
audit_service = AuditService()
metadata_service = MetadataService()


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
    metadata_service.record_usage_event(
        db,
        workspace_id=payload.workspace_id,
        asset_type="dashboard",
        asset_id=dashboard.id,
        action="dashboard.created",
        actor=principal.user_email,
        details={"name": dashboard.name, "description": dashboard.description},
    )

    return dashboard


@router.get("/dashboards/impact", response_model=DashboardImpactRead)
def dataset_dashboard_impact(
    workspace_id: int = Query(..., description="Workspace scope for impact analysis"),
    dataset_id: int = Query(..., description="Dataset whose downstream dashboards should be listed"),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> DashboardImpactRead:
    """Return dashboards affected by a dataset change."""

    require_workspace_role(db, workspace_id, principal, WORKSPACE_READ_ROLES)
    return visualization_workflow_service.dataset_impact(db, workspace_id=workspace_id, dataset_id=dataset_id)


@router.get("/dashboards/{dashboard_id}/dependencies", response_model=list[DashboardDependencyRead])
def list_dashboard_dependencies(
    dashboard_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> list[DashboardDependencyRead]:
    """List governed information dependencies for a dashboard."""

    require_model_workspace_role(db, Dashboard, dashboard_id, principal, WORKSPACE_READ_ROLES, model_name="Dashboard")
    dependencies = visualization_workflow_service.list_dashboard_dependencies(db, dashboard_id=dashboard_id)
    return [
        DashboardDependencyRead(
            id=dependency.id,
            workspace_id=dependency.workspace_id,
            dashboard_id=dependency.dashboard_id,
            dataset_id=dependency.dataset_id,
            query_execution_id=dependency.query_execution_id,
            dependency_type=dependency.dependency_type,
            details=visualization_workflow_service.parse_details(dependency.details_json),
            created_at=dependency.created_at,
        )
        for dependency in dependencies
    ]


@router.post("/dashboards/{dashboard_id}/dependencies", response_model=DashboardDependencyRead, status_code=201)
def create_dashboard_dependency(
    dashboard_id: int,
    payload: DashboardDependencyCreate,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> DashboardDependencyRead:
    """Register a dataset or query execution as powering a dashboard."""

    require_model_workspace_role(db, Dashboard, dashboard_id, principal, WORKSPACE_WRITE_ROLES, model_name="Dashboard")
    dependency = visualization_workflow_service.create_dashboard_dependency(
        db,
        dashboard_id=dashboard_id,
        dataset_id=payload.dataset_id,
        query_execution_id=payload.query_execution_id,
        dependency_type=payload.dependency_type,
        details=payload.details,
        actor=principal.user_email,
    )
    return DashboardDependencyRead(
        id=dependency.id,
        workspace_id=dependency.workspace_id,
        dashboard_id=dependency.dashboard_id,
        dataset_id=dependency.dataset_id,
        query_execution_id=dependency.query_execution_id,
        dependency_type=dependency.dependency_type,
        details=visualization_workflow_service.parse_details(dependency.details_json),
        created_at=dependency.created_at,
    )


@router.get("/dashboards/{dashboard_id}/kpi-owners", response_model=list[DashboardKpiOwnerRead])
def list_dashboard_kpi_owners(
    dashboard_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> list[DashboardKpiOwnerRead]:
    """List KPI owners assigned to a dashboard."""

    require_model_workspace_role(db, Dashboard, dashboard_id, principal, WORKSPACE_READ_ROLES, model_name="Dashboard")
    return visualization_workflow_service.list_kpi_owners(db, dashboard_id=dashboard_id)


@router.post("/dashboards/{dashboard_id}/kpi-owners", response_model=DashboardKpiOwnerRead, status_code=201)
def create_dashboard_kpi_owner(
    dashboard_id: int,
    payload: DashboardKpiOwnerCreate,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> DashboardKpiOwnerRead:
    """Assign ownership for a dashboard KPI."""

    require_model_workspace_role(db, Dashboard, dashboard_id, principal, WORKSPACE_WRITE_ROLES, model_name="Dashboard")
    return visualization_workflow_service.create_kpi_owner(
        db,
        dashboard_id=dashboard_id,
        kpi_name=payload.kpi_name,
        owner_email=payload.owner_email,
        description=payload.description,
        actor=principal.user_email,
    )


@router.post("/recommend-chart", response_model=ChartRecommendationRead)
def recommend_chart(
    payload: ChartRecommendationRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> ChartRecommendationRead:
    """Recommend a chart type from the dataset's column shapes and goal."""

    require_model_workspace_role(db, Dataset, payload.dataset_id, principal, WORKSPACE_READ_ROLES, model_name="Dataset")
    return visualization_workflow_service.recommend_chart(db, payload)
