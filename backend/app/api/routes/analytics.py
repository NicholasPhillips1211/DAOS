from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import (
    Principal,
    WORKSPACE_READ_ROLES,
    WORKSPACE_WRITE_ROLES,
    get_current_principal,
    require_model_workspace_role,
    require_workspace_role,
)
from app.core.dependencies import get_db
from app.models.metadata import Dataset
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

    require_workspace_role(db, payload.workspace_id, principal, WORKSPACE_WRITE_ROLES)
    return analytics_workflow_service.create_insight(
        db,
        workspace_id=payload.workspace_id,
        title=payload.title,
        summary=payload.summary,
        evidence_json=payload.evidence_json,
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
