from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import (
    Principal,
    WORKSPACE_WRITE_ROLES,
    get_current_principal,
    require_model_workspace_role,
    require_workspace_role,
)
from app.core.config import settings
from app.core.dependencies import get_db
from app.models.metadata import Dataset
from app.schemas.ml import FeatureImportanceRead, ModelTrainRequest, ModelTrainResponse
from app.schemas.work_item import WorkItemSubmitRead
from app.services.ml_service import MLService
from app.services.ml_workflow_service import MLWorkflowService
from app.services.work_queue_service import WorkQueueService

router = APIRouter()
ml_service = MLService()
ml_workflow_service = MLWorkflowService(ml_service)
work_queue_service = WorkQueueService()
MODEL_ARTIFACT_ROOT = Path(settings.model_artifact_root)


@router.post("/train", response_model=ModelTrainResponse, status_code=201)
def train_model(
    payload: ModelTrainRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> ModelTrainResponse:
    """Train and persist a small baseline model for the selected workspace dataset."""

    require_workspace_role(db, payload.workspace_id, principal, WORKSPACE_WRITE_ROLES)
    dataset = require_model_workspace_role(db, Dataset, payload.dataset_id, principal, WORKSPACE_WRITE_ROLES, model_name="Dataset")
    if dataset.workspace_id != payload.workspace_id:
        raise HTTPException(status_code=400, detail="Dataset does not belong to the requested workspace")

    trained_model, training_result = ml_workflow_service.train_model(
        db,
        workspace_id=payload.workspace_id,
        dataset_id=payload.dataset_id,
        model_name=payload.model_name,
        target_column=payload.target_column,
        task_type=payload.task_type,
        artifact_root=MODEL_ARTIFACT_ROOT,
    )

    return ModelTrainResponse(
        id=trained_model.id,
        workspace_id=trained_model.workspace_id,
        dataset_id=trained_model.dataset_id,
        name=trained_model.name,
        target_column=trained_model.target_column,
        task_type=trained_model.task_type,
        model_type=trained_model.model_type,
        metric_name=trained_model.metric_name,
        metric_value=trained_model.metric_value,
        train_score=trained_model.train_score,
        test_score=trained_model.test_score,
        overfit_detected=trained_model.overfit_detected,
        artifact_path=trained_model.artifact_path,
        feature_importances=[FeatureImportanceRead(**item) for item in training_result["feature_importances"]],
        created_at=trained_model.created_at,
    )


@router.post("/train-jobs", response_model=WorkItemSubmitRead, status_code=status.HTTP_202_ACCEPTED)
def queue_model_training(
    payload: ModelTrainRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> WorkItemSubmitRead:
    """Queue model training for worker execution."""

    require_workspace_role(db, payload.workspace_id, principal, WORKSPACE_WRITE_ROLES)
    dataset = require_model_workspace_role(db, Dataset, payload.dataset_id, principal, WORKSPACE_WRITE_ROLES, model_name="Dataset")
    if dataset.workspace_id != payload.workspace_id:
        raise HTTPException(status_code=400, detail="Dataset does not belong to the requested workspace")

    item = work_queue_service.enqueue(
        db,
        workspace_id=payload.workspace_id,
        job_type="ml.train",
        payload={
            "workspace_id": payload.workspace_id,
            "dataset_id": payload.dataset_id,
            "target_column": payload.target_column,
            "task_type": payload.task_type,
            "model_name": payload.model_name,
        },
    )
    return WorkItemSubmitRead(
        work_item_id=item.id,
        workspace_id=item.workspace_id,
        job_type=item.job_type,
        status=item.status,
        created_at=item.created_at,
    )
