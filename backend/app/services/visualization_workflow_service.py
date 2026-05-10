from __future__ import annotations

from dataclasses import asdict

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.metadata import Dataset
from app.schemas.visualization import ChartRecommendationRead
from app.services.analytics_service import AnalyticsService
from app.services.visualization_service import VisualizationService


class VisualizationWorkflowService:
    """Coordinate chart recommendation flows that depend on dataset statistics."""

    def __init__(self, visualization_service: VisualizationService, analytics_service: AnalyticsService) -> None:
        self.visualization_service = visualization_service
        self.analytics_service = analytics_service

    def recommend_chart(self, db: Session, payload: object) -> ChartRecommendationRead:
        """Load dataset statistics and transform them into a chart recommendation."""

        request = payload
        dataset_id = getattr(request, "dataset_id")
        x_column = getattr(request, "x_column")
        y_column = getattr(request, "y_column")
        goal = getattr(request, "goal")

        dataset = db.get(Dataset, dataset_id)
        if dataset is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
        if not dataset.storage_path:
            raise HTTPException(status_code=400, detail="Dataset has no storage path")

        try:
            stats = self.analytics_service.dataset_statistics(dataset.storage_path)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Dataset file not found") from None

        stats_map = {column["name"]: column for column in stats["columns"]}
        x_kind = stats_map.get(x_column, {}).get("data_type", "string")
        y_kind = stats_map.get(y_column, {}).get("data_type", None) if y_column else None
        recommendation = self.visualization_service.recommend_chart(x_kind, y_kind, goal)
        return ChartRecommendationRead(**asdict(recommendation))
