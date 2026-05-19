"""Schemas for workspace creation and membership management."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.metadata import WorkspaceRole


class WorkspaceCreate(BaseModel):
    """Create the root workspace container for a team or project."""

    name: str
    description: str | None = None


class WorkspaceRead(BaseModel):
    """Expose a workspace record to API consumers."""

    id: int
    name: str
    description: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MembershipCreate(BaseModel):
    """Assign a user email and role to a workspace."""

    user_email: EmailStr
    role: WorkspaceRole = WorkspaceRole.viewer


class MembershipRead(BaseModel):
    """Return the persisted workspace membership record."""

    id: int
    user_email: EmailStr
    role: WorkspaceRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkspaceDatasetSummary(BaseModel):
    """Expose the most relevant dataset metadata for workspace overviews."""

    id: int
    name: str
    source_type: str
    state: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkspaceSummaryRead(BaseModel):
    """Return the current workspace health and onboarding signals."""

    workspace_id: int
    workspace_name: str
    workspace_description: str | None = None
    dataset_count: int
    membership_count: int
    has_datasets: bool
    recommended_next_action: str
    recent_datasets: list[WorkspaceDatasetSummary]
    latest_dataset: WorkspaceDatasetSummary | None = None

    model_config = ConfigDict(from_attributes=True)
