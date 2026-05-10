from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.analysis import Insight
from app.models.metadata import Dataset, Workspace
from app.services.analytics_service import AnalyticsService


class AnalyticsWorkflowService:
    """Bundle analytics persistence and file-statistic reads behind a single API."""

    def __init__(self, analytics_service: AnalyticsService) -> None:
        self.analytics_service = analytics_service

    def create_insight(self, db: Session, *, workspace_id: int, title: str, summary: str, evidence_json: str | None) -> Insight:
        """Persist an insight after verifying its parent workspace exists."""

        if db.get(Workspace, workspace_id) is None:
            raise HTTPException(status_code=404, detail="Workspace not found")
        insight = Insight(
            workspace_id=workspace_id,
            title=title,
            summary=summary,
            evidence_json=evidence_json,
        )
        db.add(insight)
        db.commit()
        db.refresh(insight)
        return insight

    def dataset_statistics(self, db: Session, dataset_id: int) -> tuple[Dataset, dict[str, object]]:
        """Load a dataset and compute statistics from its stored CSV path."""

        dataset = db.get(Dataset, dataset_id)
        if dataset is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
        if not dataset.storage_path:
            raise HTTPException(status_code=400, detail="Dataset has no storage path")
        try:
            payload = self.analytics_service.dataset_statistics(dataset.storage_path)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Dataset file not found") from None
        return dataset, payload