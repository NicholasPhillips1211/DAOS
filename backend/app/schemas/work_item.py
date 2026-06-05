"""Schemas for background work queue visibility."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class WorkItemRead(BaseModel):
    """Expose one background work item and its operational state."""

    id: int
    workspace_id: int | None
    job_type: str
    status: str
    priority: int
    payload: dict[str, Any]
    result: dict[str, Any] | None = None
    error_message: str | None = None
    attempts: int
    max_attempts: int
    available_at: datetime
    locked_by: str | None = None
    locked_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkItemSubmitRead(BaseModel):
    """Return the accepted job identifier for async endpoints."""

    work_item_id: int
    workspace_id: int | None
    job_type: str
    status: str
    created_at: datetime

