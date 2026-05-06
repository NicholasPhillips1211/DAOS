"""Schemas for business-friendly translations of technical insights."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BusinessTranslationCreate(BaseModel):
    """Request the fields required to generate a business translation."""

    workspace_id: int
    insight_id: int
    audience: str


class BusinessTranslationRead(BaseModel):
    """Expose a generated translation and the derived recommendation payload."""

    id: int
    workspace_id: int
    insight_id: int | None
    audience: str
    summary: str
    recommendations_json: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
