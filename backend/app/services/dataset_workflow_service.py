from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.dependencies import get_or_404
from app.models.metadata import Dataset, Workspace


class DatasetWorkflowService:
    """Own dataset registry workflows so routes only mediate HTTP concerns."""

    def list_datasets(self, db: Session, *, workspace_id: int | None = None, limit: int = 50, offset: int = 0) -> list[Dataset]:
        """Return datasets newest-first, optionally scoped to a single workspace, with pagination."""

        query = db.query(Dataset)
        if workspace_id is not None:
            query = query.filter(Dataset.workspace_id == workspace_id)
        return query.order_by(Dataset.created_at.desc()).limit(limit).offset(offset).all()

    def count_datasets(self, db: Session, *, workspace_id: int | None = None) -> int:
        query = db.query(Dataset)
        if workspace_id is not None:
            query = query.filter(Dataset.workspace_id == workspace_id)
        return query.count()

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