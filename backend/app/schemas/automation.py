"""Schemas for generated automation plans and local-LLM assisted workflows."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AutomationGenerateRequest(BaseModel):
    """Request a generated automation plan for one workspace objective."""

    workspace_id: int
    objective: str = "Automate the next best operational step"


class AutomationPlanRead(BaseModel):
    """Expose a generated automation plan and the provider used to create it."""

    id: int
    workspace_id: int
    objective: str
    provider: str
    model_name: str | None = None
    status: str
    execution_status: str
    summary: str
    automation_json: str
    execution_results_json: str | None = None
    created_at: datetime
    executed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)