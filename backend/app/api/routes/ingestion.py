from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
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
from app.core.config import settings
from app.core.dependencies import get_db, get_pagination
from app.models.ingestion import DataQualityReport, IngestionJob
from app.models.metadata import Dataset
from app.schemas.ingestion import IngestionJobRead, IngestionUploadRead
from app.services.ingestion_workflow_service import IngestionWorkflowService

router = APIRouter()
ingestion_workflow_service = IngestionWorkflowService()
RAW_STORAGE_ROOT = Path(settings.raw_storage_root)


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


@router.post("/upload", response_model=IngestionUploadRead, status_code=status.HTTP_202_ACCEPTED)
async def upload_dataset(
    workspace_id: int = Form(...),
    dataset_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> IngestionUploadRead:
    """Upload a dataset and queue cleaning, profiling, and registration for a worker."""

    require_workspace_role(db, workspace_id, principal, WORKSPACE_WRITE_ROLES)

    result = ingestion_workflow_service.queue_upload(
        db,
        raw_storage_root=RAW_STORAGE_ROOT,
        workspace_id=workspace_id,
        dataset_name=dataset_name,
        file_name=file.filename,
        file_stream=file.file,
        actor=principal.user_email,
    )
    return _upload_read_from_job(db, result.job)


def _upload_read_from_job(db: Session, job: IngestionJob) -> IngestionUploadRead:
    dataset = db.get(Dataset, job.dataset_id) if job.dataset_id is not None else None
    report = (
        db.query(DataQualityReport)
        .filter(DataQualityReport.dataset_id == job.dataset_id)
        .order_by(DataQualityReport.created_at.desc())
        .first()
        if job.dataset_id is not None
        else None
    )
    return IngestionUploadRead(
        job_id=job.id,
        work_item_id=job.work_item_id,
        dataset_id=job.dataset_id,
        workspace_id=job.workspace_id,
        dataset_name=dataset.name if dataset is not None else (job.dataset_name or job.source_name),
        state=dataset.state if dataset is not None else None,
        status=job.status,
        current_step=job.current_step,
        progress_percent=job.progress_percent,
        quality_score=job.quality_score,
        row_count=job.row_count,
        rejected_rows=job.rejected_rows,
        storage_path=dataset.storage_path if dataset is not None else job.storage_path,
        report_id=report.id if report is not None else None,
        error_message=job.error_message,
        created_at=dataset.created_at if dataset is not None else job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )
