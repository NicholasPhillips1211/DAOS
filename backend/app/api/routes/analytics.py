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
from app.schemas.analysis import (
    DatasetStatisticsRead,
    InsightCreate,
    InsightRead,
    QueryExecutionRead,
    SavedQueryCreate,
    SavedQueryRead,
)
from app.services.analytics_service import AnalyticsService
from app.services.analytics_workflow_service import AnalyticsWorkflowService

router = APIRouter()
analytics_service = AnalyticsService()
analytics_workflow_service = AnalyticsWorkflowService(analytics_service)


@router.post("/insights", response_model=InsightRead, status_code=201)
def create_insight(
    payload: InsightCreate,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    """Persist an insight after workspace access has been validated."""

    require_workspace_role(db, payload.workspace_id, principal, WORKSPACE_WRITE_ROLES)
    return analytics_workflow_service.create_insight(
        db,
        workspace_id=payload.workspace_id,
        title=payload.title,
        summary=payload.summary,
        evidence_json=payload.evidence_json,
    )


@router.get("/query-executions", response_model=list[QueryExecutionRead])
def list_query_executions(
    response: Response,
    workspace_id: int | None = Query(default=None, description="Workspace scope for query history"),
    dataset_id: int | None = Query(default=None, description="Filter query history to one dataset"),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
    pagination: dict = Depends(get_pagination),
):
    """List persisted SQL executions for analysis history and governance."""

    require_workspace_scope(workspace_id)
    require_workspace_role(db, workspace_id, principal, WORKSPACE_READ_ROLES)
    total = analytics_workflow_service.count_query_executions(db, workspace_id=workspace_id, dataset_id=dataset_id)
    response.headers["X-Total-Count"] = str(total)
    return analytics_workflow_service.list_query_executions(
        db,
        workspace_id=workspace_id,
        dataset_id=dataset_id,
        limit=pagination["limit"],
        offset=pagination["offset"],
    )


@router.get("/saved-queries", response_model=list[SavedQueryRead])
def list_saved_queries(
    response: Response,
    workspace_id: int | None = Query(default=None, description="Workspace scope for saved queries"),
    dataset_id: int | None = Query(default=None, description="Filter saved queries to one dataset"),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
    pagination: dict = Depends(get_pagination),
):
    """List reusable SQL statements for the analysis workflow."""

    require_workspace_scope(workspace_id)
    require_workspace_role(db, workspace_id, principal, WORKSPACE_READ_ROLES)
    total = analytics_workflow_service.count_saved_queries(db, workspace_id=workspace_id, dataset_id=dataset_id)
    response.headers["X-Total-Count"] = str(total)
    return analytics_workflow_service.list_saved_queries(
        db,
        workspace_id=workspace_id,
        dataset_id=dataset_id,
        limit=pagination["limit"],
        offset=pagination["offset"],
    )


@router.post("/saved-queries", response_model=SavedQueryRead, status_code=201)
def create_saved_query(
    payload: SavedQueryCreate,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    """Persist a named SQL query after validating workspace write access."""

    require_workspace_role(db, payload.workspace_id, principal, WORKSPACE_WRITE_ROLES)
    return analytics_workflow_service.create_saved_query(
        db,
        workspace_id=payload.workspace_id,
        dataset_id=payload.dataset_id,
        name=payload.name,
        sql_text=payload.sql_text,
        created_by=principal.user_email,
    )


@router.get("/datasets/{dataset_id}/statistics", response_model=DatasetStatisticsRead)
def dataset_statistics(
    dataset_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> DatasetStatisticsRead:
    """Return computed CSV statistics through the analytics workflow boundary."""

    require_model_workspace_role(db, Dataset, dataset_id, principal, WORKSPACE_READ_ROLES, model_name="Dataset")
    _, payload = analytics_workflow_service.dataset_statistics(db, dataset_id)
    return DatasetStatisticsRead(dataset_id=dataset_id, **payload)
