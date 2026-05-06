"""Schemas for dataset registration and SQL query execution."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.metadata import DatasetState


class DatasetCreate(BaseModel):
    """Register a dataset that points to an existing storage location."""

    workspace_id: int
    name: str
    source_type: str
    storage_path: str | None = None


class DatasetRead(BaseModel):
    """Expose a dataset record along with its workspace and state."""

    id: int
    workspace_id: int
    name: str
    source_type: str
    state: DatasetState
    storage_path: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DatasetQueryRequest(BaseModel):
    """Wrap a SQL statement so the lakehouse endpoint can validate it."""

    sql: str


class DatasetQueryResponse(BaseModel):
    """Return the projected rows produced by a dataset SQL query."""

    columns: list[str]
    rows: list[dict[str, object]]
    row_count: int
