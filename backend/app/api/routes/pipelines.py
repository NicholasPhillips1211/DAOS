from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.auth import Principal, get_current_principal
from app.models.metadata import WorkspaceRole
from app.models.pipeline import Pipeline, PipelineRun
from app.schemas.pipeline import PipelineCreate, PipelineRead, PipelineRunRead, PipelineScheduleUpdate, PipelineVersionCreate
from app.services.pipeline_service import PipelineService
from app.services.pipeline_workflow_service import PipelineWorkflowService

router = APIRouter()
pipeline_service = PipelineService()
pipeline_workflow_service = PipelineWorkflowService(pipeline_service)


@router.get("", response_model=list[PipelineRead])
def list_pipelines(db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal), workspace_id: int | None = None) -> list[Pipeline]:
    """List pipelines, optionally scoped to a workspace when auth is active."""

    return pipeline_workflow_service.list_pipelines(db, principal, workspace_id)


@router.post("", response_model=PipelineRead, status_code=201)
def create_pipeline(payload: PipelineCreate, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)) -> Pipeline:
    """Create a new pipeline record so the orchestration layer has a home."""

    return pipeline_workflow_service.create_pipeline(db, principal, workspace_id=payload.workspace_id, name=payload.name, description=payload.description)


@router.post("/{pipeline_id}/schedule", response_model=PipelineRead)
def schedule_pipeline(pipeline_id: int, payload: PipelineScheduleUpdate, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)) -> Pipeline:
    """Persist a schedule expression so the pipeline can run on a cadence."""

    return pipeline_workflow_service.schedule_pipeline(db, principal, pipeline_id, payload.schedule_cron)


@router.post("/{pipeline_id}/versions", status_code=201)
def create_pipeline_version(pipeline_id: int, payload: PipelineVersionCreate, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)) -> dict[str, int | str]:
    """Store a normalized immutable version of the pipeline definition."""

    pipeline_id, version_number = pipeline_workflow_service.create_version(db, principal, pipeline_id, payload.definition_json)
    return {"pipeline_id": pipeline_id, "version": version_number}


@router.post("/{pipeline_id}/run", response_model=PipelineRunRead, status_code=201)
def run_pipeline(pipeline_id: int, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)) -> PipelineRun:
    """Create a run record so execution history is visible in the UI."""

    return pipeline_workflow_service.run_pipeline(db, principal, pipeline_id)
