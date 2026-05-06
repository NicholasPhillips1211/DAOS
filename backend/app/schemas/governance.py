"""Schemas for audit history and data masking operations."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditEventRead(BaseModel):
    """Expose an audit event as a read-only record."""

    id: int
    workspace_id: int
    event_type: str
    actor: str | None
    resource_type: str | None
    resource_id: int | None
    details: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DataMaskCreate(BaseModel):
    """Request a new column mask for a dataset in a workspace."""

    workspace_id: int
    dataset_id: int
    column_name: str
    mask_type: str


class DataMaskRead(BaseModel):
    """Return the persisted mask rule and its timestamp."""

    id: int
    workspace_id: int
    dataset_id: int
    column_name: str
    mask_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
