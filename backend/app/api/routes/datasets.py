from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.metadata import Dataset
from app.schemas.dataset import DatasetCreate, DatasetRead
from app.services.dataset_workflow_service import DatasetWorkflowService

router = APIRouter()
dataset_workflow_service = DatasetWorkflowService()


@router.get("", response_model=list[DatasetRead])
def list_datasets(db: Session = Depends(get_db)) -> list[Dataset]:
    """List datasets newest-first so the UI can show recent uploads first."""

    return dataset_workflow_service.list_datasets(db)


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
