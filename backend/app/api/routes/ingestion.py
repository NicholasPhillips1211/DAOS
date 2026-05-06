from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.routes.workspaces import get_db
from app.models.ingestion import DataQualityReport, IngestionJob
from app.models.metadata import Dataset, DatasetState, Workspace
from app.schemas.ingestion import IngestionUploadRead
from app.services.quality_service import QualityService

router = APIRouter()
quality_service = QualityService()
RAW_STORAGE_ROOT = Path(__file__).resolve().parents[3] / "data" / "raw"


@router.post("/upload", response_model=IngestionUploadRead, status_code=201)
async def upload_dataset(
    workspace_id: int = Form(...),
    dataset_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> IngestionUploadRead:
    workspace = db.get(Workspace, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")

    source_name = file.filename or dataset_name
    if not source_name.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV uploads are supported in the MVP")

    RAW_STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    storage_path = RAW_STORAGE_ROOT / f"ws{workspace_id}_{source_name}"

    file_bytes = await file.read()
    storage_path.write_bytes(file_bytes)

    dataset = Dataset(
        workspace_id=workspace_id,
        name=dataset_name,
        source_type="file",
        state=DatasetState.raw,
        storage_path=str(storage_path),
    )
    db.add(dataset)
    db.flush()

    profile = quality_service.profile_csv(storage_path)
    report = DataQualityReport(dataset_id=dataset.id, summary_json=quality_service.render_summary_json(profile))
    job = IngestionJob(
        workspace_id=workspace_id,
        dataset_id=dataset.id,
        source_name=source_name,
        source_type="file",
        status="completed",
        row_count=profile["row_count"],
        rejected_rows=profile["rejected_rows"],
        quality_score=profile["quality_score"],
    )
    db.add(report)
    db.add(job)
    db.commit()
    db.refresh(dataset)
    db.refresh(report)

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
