"""Schemas for comments and sharing operations inside a workspace."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class CommentCreate(BaseModel):
    """Accept a new comment attached to a workspace resource."""

    workspace_id: int
    resource_type: str
    resource_id: int
    user_email: EmailStr
    message: str


class CommentRead(BaseModel):
    """Return a persisted comment with its creation timestamp."""

    id: int
    workspace_id: int
    resource_type: str
    resource_id: int
    user_email: EmailStr
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShareCreate(BaseModel):
    """Capture the target and permission for a resource share action."""

    workspace_id: int
    resource_type: str
    resource_id: int
    target_email: EmailStr
    permission: str


class ShareRead(BaseModel):
    """Return a persisted share grant with its timestamp."""

    id: int
    workspace_id: int
    resource_type: str
    resource_id: int
    target_email: EmailStr
    permission: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
