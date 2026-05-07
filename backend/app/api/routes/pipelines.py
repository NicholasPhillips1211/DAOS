from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_or_404
from app.core.auth import Principal, get_current_principal, require_workspace_role
from app.core.config import settings
from app.models.metadata import Workspace
from app.models.metadata import WorkspaceRole
from app.models.pipeline import Pipeline, PipelineRun, PipelineVersion, PipelineStatus
from app.schemas.pipeline import PipelineCreate, PipelineRead, PipelineRunRead, PipelineScheduleUpdate, PipelineVersionCreate
from app.services.pipeline_service import PipelineService

router = APIRouter()
pipeline_service = PipelineService()


@router.get("", response_model=list[PipelineRead])
def list_pipelines(db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal), workspace_id: int | None = None) -> list[Pipeline]:
    """List pipelines, optionally scoped to a workspace when auth is active."""

    if settings.auth_enabled and workspace_id is None:
        raise HTTPException(status_code=400, detail="workspace_id is required when auth is enabled")
    if workspace_id is not None:
        require_workspace_role(db, workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst, WorkspaceRole.viewer})
        return db.query(Pipeline).filter(Pipeline.workspace_id == workspace_id).order_by(Pipeline.created_at.desc()).all()
    return db.query(Pipeline).order_by(Pipeline.created_at.desc()).all()


@router.post("", response_model=PipelineRead, status_code=201)
def create_pipeline(payload: PipelineCreate, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)) -> Pipeline:
    """Create a new pipeline record so the orchestration layer has a home."""

    get_or_404(db, Workspace, payload.workspace_id)
    require_workspace_role(db, payload.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst})
    pipeline = Pipeline(workspace_id=payload.workspace_id, name=payload.name, description=payload.description)
    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)
    return pipeline


@router.post("/{pipeline_id}/schedule", response_model=PipelineRead)
def schedule_pipeline(pipeline_id: int, payload: PipelineScheduleUpdate, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)) -> Pipeline:
    """Persist a schedule expression so the pipeline can run on a cadence."""

    pipeline = get_or_404(db, Pipeline, pipeline_id)
    require_workspace_role(db, pipeline.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst})

    pipeline.schedule_cron = payload.schedule_cron
    pipeline.status = PipelineStatus.scheduled if payload.schedule_cron else PipelineStatus.draft
    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)
    return pipeline


@router.post("/{pipeline_id}/versions", status_code=201)
def create_pipeline_version(pipeline_id: int, payload: PipelineVersionCreate, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)) -> dict[str, int | str]:
    """Store a normalized immutable version of the pipeline definition."""

    pipeline = get_or_404(db, Pipeline, pipeline_id)
    require_workspace_role(db, pipeline.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst})
    try:
        normalized_definition = pipeline_service.validate_definition_json(payload.definition_json)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    version_number = db.query(PipelineVersion).filter(PipelineVersion.pipeline_id == pipeline_id).count() + 1
    version = PipelineVersion(pipeline_id=pipeline_id, version=version_number, definition_json=normalized_definition)
    db.add(version)
    db.commit()
    return {"pipeline_id": pipeline_id, "version": version_number}


@router.post("/{pipeline_id}/run", response_model=PipelineRunRead, status_code=201)
def run_pipeline(pipeline_id: int, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)) -> PipelineRun:
    """Create a run record so execution history is visible in the UI."""

    pipeline = db.get(Pipeline, pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    require_workspace_role(db, pipeline.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst})
    run = PipelineRun(pipeline_id=pipeline_id, status=PipelineStatus.running)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run
