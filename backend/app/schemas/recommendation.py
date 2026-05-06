"""Schemas for recommendation output and generated recommendation batches."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RecommendationRead(BaseModel):
    """Expose one generated recommendation for the workspace."""

    id: int
    workspace_id: int
    title: str
    recommendation_type: str
    priority: str
    rationale: str
    action_text: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecommendationGenerateResponse(BaseModel):
    """Return the newly generated recommendation set and its count."""

    created_count: int
    recommendations: list[RecommendationRead]
