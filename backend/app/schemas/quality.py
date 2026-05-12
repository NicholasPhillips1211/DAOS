"""Response schemas for data quality reports and dataset profiling."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ColumnSummary(BaseModel):
    """Per-column quality metrics extracted during CSV profiling."""

    name: str
    missing: int
    sample_size: int
    inferred_type: str


class QualityReportRead(BaseModel):
    """Stored quality report as created during ingestion."""

    id: int
    dataset_id: int
    row_count: int
    rejected_rows: int
    quality_score: int
    columns: list[ColumnSummary]
    issues: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DataProfileRead(BaseModel):
    """Live re-profile output with full column statistics."""

    dataset_id: int
    row_count: int
    rejected_rows: int
    quality_score: int
    columns: list[ColumnSummary]
    issues: list[str]
