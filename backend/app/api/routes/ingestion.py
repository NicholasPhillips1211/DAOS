from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Header, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from app.core.dependencies_async import get_db_async
from app.models.metadata import Workspace, Dataset, DatasetState
from app.models.ingestion import IngestionJob
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
    enqueue_profile: bool = Form(False),
    file: UploadFile = File(...),
    x_user_email: str | None = Header(default=None, alias="X-User-Email"),
    db: AsyncSession = Depends(get_db_async),
) -> IngestionUploadRead:
    """Upload, profile, and register a dataset in one modular ingestion workflow."""

    # Support both async and sync DB sessions during phased migration.
    from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession
    if isinstance(db, _AsyncSession):
        workspace = await db.get(Workspace, workspace_id)
        if not workspace:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Workspace not found")

        file_bytes = await file.read()
        dataset, job, report, storage_path = await ingestion_service.process_upload_async(
            db,
            raw_storage_root=RAW_STORAGE_ROOT,
            workspace_id=workspace_id,
            dataset_name=dataset_name,
            file_name=file.filename,
            file_bytes=file_bytes,
        )
    else:
        # Sync DB session path (tests and legacy callers).
        workspace = db.get(Workspace, workspace_id)
        if not workspace:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Workspace not found")

        file_bytes = await file.read()
        if enqueue_profile:
            # Persist file and create dataset + pending job, then enqueue background profiling.
            # Use sync path when tests run with sync sessions.
            from app.core.database import SessionLocal

            storage_path = ingestion_service.persist_file(RAW_STORAGE_ROOT, workspace_id, ingestion_service.resolve_source_name(file.filename, dataset_name), file_bytes)
            db_sync = None
            if isinstance(db, AsyncSession):
                # open a sync session to create dataset and pending job
                db_sync = SessionLocal()
            else:
                db_sync = db

            try:
                dataset = Dataset(
                    workspace_id=workspace_id,
                    name=dataset_name,
                    source_type="file",
                    state=DatasetState.raw,
                    storage_path=str(storage_path),
                )
                db_sync.add(dataset)
                db_sync.flush()

                job = IngestionJob(
                    workspace_id=workspace_id,
                    dataset_id=dataset.id,
                    source_name=ingestion_service.resolve_source_name(file.filename, dataset_name),
                    source_type="file",
                    status="pending",
                    row_count=0,
                    rejected_rows=0,
                    quality_score=0.0,
                )
                db_sync.add(job)
                db_sync.commit()
                db_sync.refresh(dataset)
            finally:
                if isinstance(db, AsyncSession):
                    db_sync.close()

            # enqueue background profiling task
            from app.tasks.queue import default_queue

            await default_queue.enqueue(
                "profile_dataset",
                dataset.id,
                workspace_id,
                str(storage_path),
                dataset.name,
            )

            # create placeholder report reference values
            report = None
        else:
            dataset, job, report, storage_path = ingestion_service.process_upload(
                db,
                raw_storage_root=RAW_STORAGE_ROOT,
                workspace_id=workspace_id,
                dataset_name=dataset_name,
                file_name=file.filename,
                file_bytes=file_bytes,
            )

    # Audit and metadata services are sync; call them in a thread to avoid blocking.
    await asyncio.to_thread(
        audit_service.log_event,
        workspace_id,
        "dataset.uploaded",
        x_user_email or "system",
        "dataset",
        dataset.id,
        f"Uploaded {file.filename or dataset.name} with quality score {job.quality_score}",
        None,
    )

    def _emit_sync():
        from app.core.database import SessionLocal

        db_sync = SessionLocal()
        try:
            return metadata_service.emit_event(
                db_sync,
                workspace_id=workspace_id,
                event_type="metadata.ingestion.profile_created",
                resource_type="dataset",
                resource_id=dataset.id,
                details={
                    "dataset_name": dataset.name,
                    "report_id": report.id,
                    "row_count": job.row_count,
                    "rejected_rows": job.rejected_rows,
                    "quality_score": job.quality_score,
                },
                actor=x_user_email or "system",
            )
        finally:
            db_sync.close()

    await asyncio.to_thread(_emit_sync)

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
