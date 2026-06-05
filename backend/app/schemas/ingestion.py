"""Schemas for ingestion job results and upload responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.metadata import DatasetState


class IngestionUploadRead(BaseModel):
    """Return the identifiers and quality summary from an upload."""

    job_id: int
    work_item_id: int | None = None
    dataset_id: int | None = None
    workspace_id: int
    dataset_name: str
    state: DatasetState | None = None
    status: str
    current_step: str | None = None
    progress_percent: int = 0
    quality_score: int
    row_count: int
    rejected_rows: int
    storage_path: str | None = None
    report_id: int | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class IngestionJobRead(BaseModel):
    """Return durable ingestion job state for operators and workflow UIs."""

    id: int
    workspace_id: int
    dataset_id: int | None
    work_item_id: int | None = None
    dataset_name: str | None = None
    source_name: str
    source_type: str
    storage_path: str | None = None
    status: str
    current_step: str | None = None
    progress_percent: int = 0
    row_count: int
    rejected_rows: int
    quality_score: int
    error_message: str | None = None
    actor: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
