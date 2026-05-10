from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_or_404
from app.models.metadata import Dataset, Workspace


class DatasetWorkflowService:
    """Own dataset registry workflows so routes only mediate HTTP concerns."""

    def list_datasets(self, db: Session) -> list[Dataset]:
        """Return datasets newest-first for UI consumption."""

        return db.query(Dataset).order_by(Dataset.created_at.desc()).all()

    def create_dataset(self, db: Session, *, workspace_id: int, name: str, source_type: str, storage_path: str | None) -> Dataset:
        """Validate workspace membership of the dataset and persist the registry row."""

        get_or_404(db, Workspace, workspace_id)
        dataset = Dataset(
            workspace_id=workspace_id,
            name=name,
            source_type=source_type,
            storage_path=storage_path,
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        return dataset