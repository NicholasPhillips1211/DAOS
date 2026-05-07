from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.auth import Principal, get_current_principal, require_workspace_role
from app.models.analysis import Insight
from app.models.metadata import Dataset, Workspace
from app.models.metadata import WorkspaceRole
from app.schemas.analysis import DatasetStatisticsRead, InsightCreate, InsightRead
from app.services.analytics_service import AnalyticsService

router = APIRouter()
analytics_service = AnalyticsService()


@router.post("/insights", response_model=InsightRead, status_code=201)
def create_insight(
    payload: InsightCreate,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> Insight:
    workspace = db.get(Workspace, payload.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    require_workspace_role(db, payload.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst})
    insight = Insight(
        workspace_id=payload.workspace_id,
        title=payload.title,
        summary=payload.summary,
        evidence_json=payload.evidence_json,
    )
    db.add(insight)
    db.commit()
    db.refresh(insight)
    return insight


@router.get("/datasets/{dataset_id}/statistics", response_model=DatasetStatisticsRead)
def dataset_statistics(dataset_id: int, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)) -> DatasetStatisticsRead:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not dataset.storage_path:
        raise HTTPException(status_code=400, detail="Dataset has no storage path")
    require_workspace_role(db, dataset.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst, WorkspaceRole.viewer})

    try:
        payload = analytics_service.dataset_statistics(dataset.storage_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset file not found") from None

    return DatasetStatisticsRead(dataset_id=dataset_id, **payload)
