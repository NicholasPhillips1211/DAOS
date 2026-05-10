from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.ingestion import DataQualityReport, IngestionJob
from app.models.metadata import Dataset, DatasetState
from app.services.quality_service import QualityService


class IngestionWorkflowService:
    """Own ingestion orchestration so API routes stay focused on HTTP concerns.

    This service encapsulates the full write path (persist file, profile, and create
    metadata records) because those steps must stay consistent wherever ingestion is used.
    """

    def __init__(self, quality_service: QualityService) -> None:
        self.quality_service = quality_service

    def validate_dataset_name(self, dataset_name: str) -> None:
        """Reject blank dataset names early to avoid creating unlabeled records."""

        if not dataset_name.strip():
            raise HTTPException(status_code=400, detail="Dataset name is required")

    def resolve_source_name(self, file_name: str | None, dataset_name: str) -> str:
        """Pick the most useful source name while preserving strict CSV-only support."""

        source_name = file_name or dataset_name
        if not source_name.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail="Only CSV uploads are supported in the MVP")
        return source_name

    def persist_file(self, raw_storage_root: Path, workspace_id: int, source_name: str, file_bytes: bytes) -> Path:
        """Store uploaded bytes in workspace-scoped raw storage for reproducible profiling."""

        raw_storage_root.mkdir(parents=True, exist_ok=True)
        storage_path = raw_storage_root / f"ws{workspace_id}_{source_name}"
        storage_path.write_bytes(file_bytes)
        return storage_path

    def create_ingestion_records(
        self,
        db: Session,
        workspace_id: int,
        dataset_name: str,
        source_name: str,
        storage_path: Path,
    ) -> tuple[Dataset, IngestionJob, DataQualityReport]:
        """Create dataset, quality report, and ingestion job in one transaction boundary."""

        dataset = Dataset(
            workspace_id=workspace_id,
            name=dataset_name,
            source_type="file",
            state=DatasetState.raw,
            storage_path=str(storage_path),
        )
        db.add(dataset)
        db.flush()

        profile = self.quality_service.profile_csv(storage_path)
        report = DataQualityReport(dataset_id=dataset.id, summary_json=self.quality_service.render_summary_json(profile))
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
        return dataset, job, report
