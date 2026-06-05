from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile
from sqlalchemy.orm import Session

from app.core.auth import (
    Principal,
    WORKSPACE_READ_ROLES,
    WORKSPACE_WRITE_ROLES,
    get_current_principal,
    require_model_workspace_role,
    require_workspace_role,
    require_workspace_scope,
)
from app.core.dependencies import get_db, get_pagination
from app.models.ingestion import IngestionJob
from app.schemas.ingestion import IngestionJobRead, IngestionUploadRead
from app.services.ingestion_workflow_service import IngestionWorkflowService

router = APIRouter()
ingestion_workflow_service = IngestionWorkflowService()
RAW_STORAGE_ROOT = Path(__file__).resolve().parents[3] / "data" / "raw"


@router.get("/jobs", response_model=list[IngestionJobRead])
def list_ingestion_jobs(
    response: Response,
    workspace_id: int | None = Query(default=None, description="Filter jobs to a single workspace"),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
    pagination: dict = Depends(get_pagination),
) -> list[IngestionJob]:
    """List durable ingestion jobs so workflow state is visible outside uploads."""

    require_workspace_scope(workspace_id)
    if workspace_id is not None:
        require_workspace_role(db, workspace_id, principal, WORKSPACE_READ_ROLES)

    total = ingestion_workflow_service.count_jobs(db, workspace_id=workspace_id)
    response.headers["X-Total-Count"] = str(total)
    return ingestion_workflow_service.list_jobs(
        db,
        workspace_id=workspace_id,
        limit=pagination["limit"],
        offset=pagination["offset"],
    )


@router.get("/jobs/{job_id}", response_model=IngestionJobRead)
def get_ingestion_job(
    job_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> IngestionJob:
    """Fetch one durable ingestion job after enforcing workspace access."""

    return require_model_workspace_role(
        db,
        IngestionJob,
        job_id,
        principal,
        WORKSPACE_READ_ROLES,
        model_name="Ingestion job",
    )


@router.post("/upload", response_model=IngestionUploadRead, status_code=201)
async def upload_dataset(
    workspace_id: int = Form(...),
    dataset_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> IngestionUploadRead:
    """Upload, profile, and register a dataset in one modular ingestion workflow."""

    require_workspace_role(db, workspace_id, principal, WORKSPACE_WRITE_ROLES)

    result = ingestion_workflow_service.process_upload(
        db,
        raw_storage_root=RAW_STORAGE_ROOT,
        workspace_id=workspace_id,
        dataset_name=dataset_name,
        file_name=file.filename,
        file_stream=file.file,
        actor=principal.user_email,
    )
    dataset = result.dataset
    job = result.job
    report = result.report

    return IngestionUploadRead(
        job_id=job.id,
        dataset_id=dataset.id,
        workspace_id=workspace_id,
        dataset_name=dataset.name,
        state=dataset.state,
        status=job.status,
        quality_score=job.quality_score,
        row_count=job.row_count,
        rejected_rows=job.rejected_rows,
        storage_path=str(result.storage_path),
        report_id=report.id,
        error_message=job.error_message,
        created_at=dataset.created_at,
        finished_at=job.finished_at,
    )
