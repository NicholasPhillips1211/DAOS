"""Routes for retrieving stored quality reports and live dataset re-profiling."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_or_404
from app.models.ingestion import DataQualityReport
from app.models.metadata import Dataset
from app.schemas.quality import DataProfileRead, QualityReportRead
from app.services.quality_service import QualityService

router = APIRouter()
quality_service = QualityService()


@router.get("/{dataset_id}/quality", response_model=QualityReportRead)
def get_quality_report(dataset_id: int, db: Session = Depends(get_db)) -> QualityReportRead:
    """Return the stored quality report created during ingestion."""

    get_or_404(db, Dataset, dataset_id)

    report = (
        db.query(DataQualityReport)
        .filter(DataQualityReport.dataset_id == dataset_id)
        .order_by(DataQualityReport.created_at.desc())
        .first()
    )

    if not report:
        raise HTTPException(status_code=404, detail="No quality report found for this dataset")

    summary = json.loads(report.summary_json)

    return QualityReportRead(
        id=report.id,
        dataset_id=dataset_id,
        row_count=summary.get("row_count", 0),
        rejected_rows=summary.get("rejected_rows", 0),
        quality_score=summary.get("quality_score", 0),
        columns=summary.get("columns", []),
        issues=summary.get("issues", []),
        created_at=report.created_at,
    )


@router.get("/{dataset_id}/profile", response_model=DataProfileRead)
def profile_dataset(dataset_id: int, db: Session = Depends(get_db)) -> DataProfileRead:
    """Run a live re-profile of the dataset file and return fresh quality metrics."""

    dataset = get_or_404(db, Dataset, dataset_id)

    if not dataset.storage_path:
        raise HTTPException(status_code=400, detail="Dataset has no storage path for profiling")

    file_path = Path(dataset.storage_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset file not found on disk")

    profile = quality_service.profile_csv(file_path)

    return DataProfileRead(
        dataset_id=dataset_id,
        row_count=profile["row_count"],
        rejected_rows=profile["rejected_rows"],
        quality_score=profile["quality_score"],
        columns=profile["columns"],
        issues=profile["issues"],
    )
