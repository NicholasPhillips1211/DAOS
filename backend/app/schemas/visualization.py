"""Schemas for dashboards and chart recommendation responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DashboardCreate(BaseModel):
    """Capture the fields needed to create a dashboard container."""

    workspace_id: int
    name: str
    description: str | None = None


class DashboardRead(BaseModel):
    """Expose a dashboard with its persisted creation timestamp."""

    id: int
    workspace_id: int
    name: str
    description: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChartRecommendationRequest(BaseModel):
    """Describe the dataset columns and goal for chart selection."""

    dataset_id: int
    x_column: str
    y_column: str | None = None
    goal: str = "compare"


class ChartRecommendationRead(BaseModel):
    """Return the recommended chart type and supporting advice."""

    chart_type: str
    reason: str
    best_practices: list[str]