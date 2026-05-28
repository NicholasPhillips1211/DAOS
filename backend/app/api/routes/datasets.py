from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_pagination
from app.models.metadata import Dataset
from app.schemas.dataset import DatasetCreate, DatasetRead
from app.services.dataset_workflow_service import DatasetWorkflowService

router = APIRouter()
dataset_workflow_service = DatasetWorkflowService()


@router.get("", response_model=list[DatasetRead])
def list_datasets(
    response: Response,
    workspace_id: int | None = Query(default=None, description="Filter datasets to a single workspace"),
    db: Session = Depends(get_db),
    pagination: dict = Depends(get_pagination),
) -> list[Dataset]:
    """List datasets newest-first, optionally scoped to one workspace."""
    total = dataset_workflow_service.count_datasets(db, workspace_id=workspace_id)
    response.headers["X-Total-Count"] = str(total)
    return dataset_workflow_service.list_datasets(db, workspace_id=workspace_id, limit=pagination["limit"], offset=pagination["offset"])


@router.post("", response_model=DatasetRead, status_code=201)
def create_dataset(payload: DatasetCreate, db: Session = Depends(get_db)) -> Dataset:
    """Register a dataset record once its source and storage path are known."""

    return dataset_workflow_service.create_dataset(
        db,
        workspace_id=payload.workspace_id,
        name=payload.name,
        source_type=payload.source_type,
        storage_path=payload.storage_path,
    )
