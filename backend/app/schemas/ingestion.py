"""Schemas for ingestion job results and upload responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.metadata import DatasetState


class IngestionUploadRead(BaseModel):
    """Return the identifiers and quality summary from an upload."""

    dataset_id: int
    workspace_id: int
    dataset_name: str
    state: DatasetState
    quality_score: int
    row_count: int
    rejected_rows: int
    storage_path: str
    report_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
