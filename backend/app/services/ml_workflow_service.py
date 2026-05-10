from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.metadata import Dataset, Workspace
from app.models.ml import TrainedModel
from app.services.ml_service import MLService


class MLWorkflowService:
    """Keep model-training orchestration separate from the HTTP route surface."""

    def __init__(self, ml_service: MLService) -> None:
        self.ml_service = ml_service

    def train_model(
        self,
        db: Session,
        *,
        workspace_id: int,
        dataset_id: int,
        model_name: str,
        target_column: str,
        task_type: str,
        artifact_root: Path,
    ) -> tuple[TrainedModel, dict[str, object]]:
        """Validate inputs, train a baseline model, and persist the metadata row."""

        if db.get(Workspace, workspace_id) is None:
            raise HTTPException(status_code=404, detail="Workspace not found")

        dataset = db.get(Dataset, dataset_id)
        if dataset is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
        if not dataset.storage_path:
            raise HTTPException(status_code=400, detail="Dataset has no storage path")

        artifact_path = artifact_root / f"ws{workspace_id}_dataset{dataset_id}_{target_column}.joblib"
        try:
            training_result = self.ml_service.train_model(dataset.storage_path, target_column, task_type, artifact_path)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Dataset file not found") from None
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        trained_model = TrainedModel(
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            name=model_name,
            target_column=target_column,
            task_type=task_type,
            model_type=training_result["model_type"],
            metric_name=training_result["metric_name"],
            metric_value=training_result["metric_value"],
            train_score=training_result["train_score"],
            test_score=training_result["test_score"],
            overfit_detected=training_result["overfit_detected"],
            artifact_path=training_result["artifact_path"],
        )
        db.add(trained_model)
        db.commit()
        db.refresh(trained_model)
        return trained_model, training_result
