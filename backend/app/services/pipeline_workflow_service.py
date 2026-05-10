from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_workspace_role
from app.core.config import settings
from app.core.dependencies import get_or_404
from app.models.metadata import Workspace, WorkspaceRole
from app.models.pipeline import Pipeline, PipelineRun, PipelineStatus, PipelineVersion
from app.services.pipeline_service import PipelineService


class PipelineWorkflowService:
    """Coordinate pipeline registry, versioning, and execution-record workflows."""

    def __init__(self, pipeline_service: PipelineService) -> None:
        self.pipeline_service = pipeline_service

    def list_pipelines(self, db: Session, principal: Principal, workspace_id: int | None = None) -> list[Pipeline]:
        """Return pipelines newest-first, optionally scoped to a workspace."""

        if settings.auth_enabled and workspace_id is None:
            raise HTTPException(status_code=400, detail="workspace_id is required when auth is enabled")
        query = db.query(Pipeline)
        if workspace_id is not None:
            require_workspace_role(db, workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst, WorkspaceRole.viewer})
            query = query.filter(Pipeline.workspace_id == workspace_id)
        return query.order_by(Pipeline.created_at.desc()).all()

    def create_pipeline(self, db: Session, principal: Principal, *, workspace_id: int, name: str, description: str | None) -> Pipeline:
        """Create a pipeline after verifying its workspace parent and access policy."""

        get_or_404(db, Workspace, workspace_id)
        require_workspace_role(db, workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst})
        pipeline = Pipeline(workspace_id=workspace_id, name=name, description=description)
        db.add(pipeline)
        db.commit()
        db.refresh(pipeline)
        return pipeline

    def schedule_pipeline(self, db: Session, principal: Principal, pipeline_id: int, schedule_cron: str | None) -> Pipeline:
        """Persist a schedule expression so the pipeline can run on a cadence."""

        pipeline = get_or_404(db, Pipeline, pipeline_id)
        require_workspace_role(db, pipeline.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst})
        pipeline.schedule_cron = schedule_cron
        pipeline.status = PipelineStatus.scheduled if schedule_cron else PipelineStatus.draft
        db.add(pipeline)
        db.commit()
        db.refresh(pipeline)
        return pipeline

    def create_version(self, db: Session, principal: Principal, pipeline_id: int, definition_json: str) -> tuple[int, int]:
        """Store a normalized immutable version of a pipeline definition."""

        pipeline = get_or_404(db, Pipeline, pipeline_id)
        require_workspace_role(db, pipeline.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst})
        try:
            normalized_definition = self.pipeline_service.validate_definition_json(definition_json)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        version_number = db.query(PipelineVersion).filter(PipelineVersion.pipeline_id == pipeline_id).count() + 1
        version = PipelineVersion(pipeline_id=pipeline_id, version=version_number, definition_json=normalized_definition)
        db.add(version)
        db.commit()
        return pipeline_id, version_number

    def run_pipeline(self, db: Session, principal: Principal, pipeline_id: int) -> PipelineRun:
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
