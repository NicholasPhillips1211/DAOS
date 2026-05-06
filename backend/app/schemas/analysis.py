"""Schemas for insight creation and analytics responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InsightCreate(BaseModel):
    """Capture the minimum fields needed to persist an insight."""

    workspace_id: int
    title: str
    summary: str
    evidence_json: str


class InsightRead(BaseModel):
    """Expose a stored insight with its persisted timestamp."""

    id: int
    workspace_id: int
    title: str
    summary: str
    evidence_json: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ColumnStatistic(BaseModel):
    """Describe one profiled column in a dataset statistics response."""

    name: str
    data_type: str
    non_null_count: int
    null_count: int
    distinct_count: int
    min_value: float | str | None = None
    max_value: float | str | None = None
    mean_value: float | None = None


class DatasetStatisticsRead(BaseModel):
    """Return row, column, and per-column statistics for a dataset."""

    dataset_id: int
    row_count: int
    column_count: int
    columns: list[ColumnStatistic]
