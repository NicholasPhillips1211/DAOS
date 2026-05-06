"""Schemas for pipeline definitions, schedules, and execution history."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.pipeline import PipelineStatus


class PipelineCreate(BaseModel):
    """Capture the fields required to create a new pipeline record."""

    workspace_id: int
    name: str
    description: str | None = None


class PipelineRead(BaseModel):
    """Expose the persisted pipeline with its current schedule and state."""

    id: int
    workspace_id: int
    name: str
    description: str | None = None
    schedule_cron: str | None = None
    status: PipelineStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PipelineVersionCreate(BaseModel):
    """Wrap the raw JSON definition for validation and versioning."""

    definition_json: str


class PipelineScheduleUpdate(BaseModel):
    """Accept the cron string used to enable or disable scheduling."""

    schedule_cron: str | None = None


class PipelineRunRead(BaseModel):
    """Return the persisted pipeline execution record."""

    id: int
    pipeline_id: int
    status: PipelineStatus
    started_at: datetime
    finished_at: datetime | None = None
    log_message: str | None = None

    model_config = ConfigDict(from_attributes=True)
