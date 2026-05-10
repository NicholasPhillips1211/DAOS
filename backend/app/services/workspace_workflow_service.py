from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.metadata import Dataset, Workspace
from app.models.visualization import Dashboard
from app.services.lakehouse_service import LakehouseService


class WorkspaceWorkflowService:
    """Bundle workspace-level workflows used across routes.

    Grouping these cross-model operations here keeps route modules thin and lets us
    evolve business rules in one place without touching HTTP transport logic.
    """

    def __init__(self, lakehouse_service: LakehouseService | None = None) -> None:
        self.lakehouse_service = lakehouse_service

    def create_dashboard(self, db: Session, workspace_id: int, name: str, description: str | None) -> Dashboard:
        """Create and return a dashboard after validating parent workspace and title."""

        workspace = db.get(Workspace, workspace_id)
        if workspace is None:
            raise HTTPException(status_code=404, detail="Workspace not found")
        if not name.strip():
            raise HTTPException(status_code=400, detail="Dashboard name is required")

        dashboard = Dashboard(workspace_id=workspace_id, name=name, description=description)
        db.add(dashboard)
        db.commit()
        db.refresh(dashboard)
        return dashboard

    def query_dataset(self, db: Session, dataset_id: int, sql: str) -> tuple[Dataset, list[str], list[dict[str, object]]]:
        """Resolve dataset metadata and execute SQL against its persisted CSV path."""

        if not sql.strip():
            raise HTTPException(status_code=400, detail="SQL query is required")

        dataset = db.get(Dataset, dataset_id)
        if dataset is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
        if not dataset.storage_path:
            raise HTTPException(status_code=400, detail="Dataset has no storage path")
        if self.lakehouse_service is None:
            raise HTTPException(status_code=500, detail="Lakehouse service is not configured")

        try:
            columns, rows = self.lakehouse_service.query_csv(dataset.storage_path, sql)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Dataset file not found") from None
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Query failed: {exc}") from exc

        return dataset, columns, rows
