"""Schemas for model training requests, metrics, and artifact metadata."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ModelTrainRequest(BaseModel):
    """Collect the training inputs needed by the baseline ML service."""

    workspace_id: int
    dataset_id: int
    target_column: str
    task_type: str = "classification"
    model_name: str = "decision-tree"


class FeatureImportanceRead(BaseModel):
    """Describe one non-zero feature importance from the trained model."""

    feature: str
    importance: float


class ModelTrainResponse(BaseModel):
    """Expose the training outcome and model metadata to the API caller."""

    id: int
    workspace_id: int
    dataset_id: int
    name: str
    target_column: str
    task_type: str
    model_type: str
    metric_name: str
    metric_value: float
    train_score: float
    test_score: float
    overfit_detected: bool
    artifact_path: str
    feature_importances: list[FeatureImportanceRead]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)