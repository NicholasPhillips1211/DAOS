"""Schemas for generating and reading project guidance plans."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GuidanceGenerateRequest(BaseModel):
    """Request a guidance plan for one workspace and business objective."""

    workspace_id: int
    objective: str = "Improve decision velocity with trustworthy data"


class GuidancePlanRead(BaseModel):
    """Expose a generated plan with KPI, milestone, and risk payloads."""

    id: int
    workspace_id: int
    objective: str
    kpis_json: str
    milestones_json: str
    risks_json: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
