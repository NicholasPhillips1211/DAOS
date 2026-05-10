from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Header, UploadFile
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_or_404
from app.models.metadata import Workspace
from app.schemas.ingestion import IngestionUploadRead
from app.services.audit_service import AuditService
from app.services.ingestion_workflow_service import IngestionWorkflowService
from app.services.quality_service import QualityService

router = APIRouter()
quality_service = QualityService()
ingestion_workflow_service = IngestionWorkflowService(quality_service)
audit_service = AuditService()
RAW_STORAGE_ROOT = Path(__file__).resolve().parents[3] / "data" / "raw"


@router.post("/upload", response_model=IngestionUploadRead, status_code=201)
async def upload_dataset(
    workspace_id: int = Form(...),
    dataset_name: str = Form(...),
    file: UploadFile = File(...),
    x_user_email: str | None = Header(default=None, alias="X-User-Email"),
    db: Session = Depends(get_db),
) -> IngestionUploadRead:
    """Upload, profile, and register a dataset in one modular ingestion workflow."""

    get_or_404(db, Workspace, workspace_id)

    ingestion_workflow_service.validate_dataset_name(dataset_name)
    source_name = ingestion_workflow_service.resolve_source_name(file.filename, dataset_name)

    file_bytes = await file.read()
    storage_path = ingestion_workflow_service.persist_file(RAW_STORAGE_ROOT, workspace_id, source_name, file_bytes)
    dataset, job, report = ingestion_workflow_service.create_ingestion_records(
        db,
        workspace_id,
        dataset_name,
        source_name,
        storage_path,
    )

    audit_service.log_event(
        workspace_id,
        "dataset.uploaded",
        actor=x_user_email or "system",
        resource_type="dataset",
        resource_id=dataset.id,
        details=f"Uploaded {source_name} with quality score {job.quality_score}",
    )

    return IngestionUploadRead(
        dataset_id=dataset.id,
        workspace_id=workspace_id,
        dataset_name=dataset.name,
        state=dataset.state,
        quality_score=job.quality_score,
        row_count=job.row_count,
        rejected_rows=job.rejected_rows,
        storage_path=str(storage_path),
        report_id=report.id,
        created_at=dataset.created_at,
    )
