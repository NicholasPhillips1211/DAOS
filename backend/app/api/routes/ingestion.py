from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Header, UploadFile
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_or_404
from app.models.metadata import Workspace
from app.schemas.ingestion import IngestionUploadRead
from app.services.audit_service import AuditService
from app.services.ingestion_service import IngestionService
from app.services.metadata_service import MetadataService

router = APIRouter()
ingestion_service = IngestionService()
audit_service = AuditService()
metadata_service = MetadataService()
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

    file_bytes = await file.read()
    dataset, job, report, storage_path = ingestion_service.process_upload(
        db,
        raw_storage_root=RAW_STORAGE_ROOT,
        workspace_id=workspace_id,
        dataset_name=dataset_name,
        file_name=file.filename,
        file_bytes=file_bytes,
    )

    audit_service.log_event(
        workspace_id,
        "dataset.uploaded",
        actor=x_user_email or "system",
        resource_type="dataset",
        resource_id=dataset.id,
        details=f"Uploaded {file.filename or dataset.name} with quality score {job.quality_score}",
        db=db,
    )

    metadata_service.emit_event(
        db,
        workspace_id=workspace_id,
        event_type="metadata.ingestion.profile_created",
        resource_type="dataset",
        resource_id=dataset.id,
        actor=x_user_email or "system",
        details={
            "dataset_name": dataset.name,
            "report_id": report.id,
            "row_count": job.row_count,
            "rejected_rows": job.rejected_rows,
            "quality_score": job.quality_score,
        },
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
