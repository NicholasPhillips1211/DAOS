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


class QueryExecutionRead(BaseModel):
    """Expose query history with operational execution facts."""

    id: int
    workspace_id: int
    dataset_id: int
    sql_text: str
    route: str
    row_count: int
    column_count: int
    duration_ms: int
    actor: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SavedQueryCreate(BaseModel):
    """Capture a named SQL statement for reuse."""

    workspace_id: int
    dataset_id: int
    name: str
    sql_text: str


class SavedQueryRead(BaseModel):
    """Expose a saved query in the analysis workspace."""

    id: int
    workspace_id: int
    dataset_id: int
    name: str
    sql_text: str
    created_by: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
