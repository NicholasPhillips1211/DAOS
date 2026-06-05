"""Schemas for ingestion job results and upload responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.metadata import DatasetState


class IngestionUploadRead(BaseModel):
    """Return the identifiers and quality summary from an upload."""

    job_id: int
    dataset_id: int
    workspace_id: int
    dataset_name: str
    state: DatasetState
    status: str
    quality_score: int
    row_count: int
    rejected_rows: int
    storage_path: str
    report_id: int
    error_message: str | None = None
    created_at: datetime
    finished_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class IngestionJobRead(BaseModel):
    """Return durable ingestion job state for operators and workflow UIs."""

    id: int
    workspace_id: int
    dataset_id: int | None
    source_name: str
    source_type: str
    status: str
    row_count: int
    rejected_rows: int
    quality_score: int
    error_message: str | None = None
    created_at: datetime
    finished_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
