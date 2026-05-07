from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.auth import Principal, get_current_principal, require_workspace_role
from app.models.metadata import Dataset, Workspace
from app.models.metadata import WorkspaceRole
from app.models.ml import TrainedModel
from app.schemas.ml import ModelTrainRequest, ModelTrainResponse, FeatureImportanceRead
from app.services.ml_service import MLService

router = APIRouter()
ml_service = MLService()
MODEL_ARTIFACT_ROOT = Path(__file__).resolve().parents[3] / "data" / "models"


@router.post("/train", response_model=ModelTrainResponse, status_code=201)
def train_model(
    payload: ModelTrainRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> ModelTrainResponse:
    """Train and persist a small baseline model for the selected workspace dataset."""

    workspace = db.get(Workspace, payload.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    require_workspace_role(db, payload.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst})

    dataset = db.get(Dataset, payload.dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not dataset.storage_path:
        raise HTTPException(status_code=400, detail="Dataset has no storage path")

    artifact_path = MODEL_ARTIFACT_ROOT / f"ws{payload.workspace_id}_dataset{payload.dataset_id}_{payload.target_column}.joblib"
    try:
        training_result = ml_service.train_model(dataset.storage_path, payload.target_column, payload.task_type, artifact_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset file not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    trained_model = TrainedModel(
        workspace_id=payload.workspace_id,
        dataset_id=payload.dataset_id,
        name=payload.model_name,
        target_column=payload.target_column,
        task_type=payload.task_type,
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