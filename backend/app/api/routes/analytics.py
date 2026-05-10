from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.auth import Principal, get_current_principal, require_workspace_role
from app.models.metadata import WorkspaceRole
from app.schemas.analysis import DatasetStatisticsRead, InsightCreate, InsightRead
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

    require_workspace_role(db, payload.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst})
    return analytics_workflow_service.create_insight(
        db,
        workspace_id=payload.workspace_id,
        title=payload.title,
        summary=payload.summary,
        evidence_json=payload.evidence_json,
    )


@router.get("/datasets/{dataset_id}/statistics", response_model=DatasetStatisticsRead)
def dataset_statistics(dataset_id: int, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)) -> DatasetStatisticsRead:
    """Return computed CSV statistics through the analytics workflow boundary."""

    dataset, payload = analytics_workflow_service.dataset_statistics(db, dataset_id)
    require_workspace_role(db, dataset.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst, WorkspaceRole.viewer})
    return DatasetStatisticsRead(dataset_id=dataset_id, **payload)
