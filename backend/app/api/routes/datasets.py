from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.routes.workspaces import get_db
from app.models.metadata import Dataset, Workspace
from app.schemas.dataset import DatasetCreate, DatasetRead

router = APIRouter()


@router.get("", response_model=list[DatasetRead])
def list_datasets(db: Session = Depends(get_db)) -> list[Dataset]:
    """List datasets newest-first so the UI can show recent uploads first."""

    return db.query(Dataset).order_by(Dataset.created_at.desc()).all()


@router.post("", response_model=DatasetRead, status_code=201)
def create_dataset(payload: DatasetCreate, db: Session = Depends(get_db)) -> Dataset:
    """Register a dataset record once its source and storage path are known."""

    workspace = db.get(Workspace, payload.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    dataset = Dataset(
        workspace_id=payload.workspace_id,
        name=payload.name,
        source_type=payload.source_type,
        storage_path=payload.storage_path,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset
