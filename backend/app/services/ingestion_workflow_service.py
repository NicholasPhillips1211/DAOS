from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.ingestion import DataQualityReport, IngestionJob
from app.models.metadata import Dataset, DatasetState
from app.services.quality_service import QualityService

logger = logging.getLogger("daos.ingestion")


class IngestionWorkflowService:
    """Own ingestion orchestration so API routes stay focused on HTTP concerns.

    This service encapsulates the full write path (persist file, profile, and create
    metadata records) because those steps must stay consistent wherever ingestion is used.
    """

    def __init__(self, quality_service: QualityService) -> None:
        self.quality_service = quality_service
        self._max_write_attempts = 3
        self._max_db_attempts = 2

    def validate_dataset_name(self, dataset_name: str) -> None:
        """Reject blank dataset names early to avoid creating unlabeled records."""

        if not dataset_name.strip():
            raise HTTPException(status_code=400, detail="Dataset name is required")

    def resolve_source_name(self, file_name: str | None, dataset_name: str) -> str:
        """Pick the most useful source name while preserving strict CSV-only support."""

        source_name = Path(file_name or dataset_name).name
        if not source_name.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail="Only CSV uploads are supported in the MVP")
        return source_name

    def persist_file(self, raw_storage_root: Path, workspace_id: int, source_name: str, file_bytes: bytes) -> Path:
        """Store uploaded bytes in workspace-scoped raw storage for reproducible profiling."""

        raw_storage_root.mkdir(parents=True, exist_ok=True)
        storage_path = raw_storage_root / f"ws{workspace_id}_{source_name}"

        # Atomic replace avoids partially-written files if process interruption occurs.
        for attempt in range(1, self._max_write_attempts + 1):
            temp_path = storage_path.with_suffix(f"{storage_path.suffix}.tmp")
            try:
                temp_path.write_bytes(file_bytes)
                temp_path.replace(storage_path)
                return storage_path
            except OSError as exc:
                logger.warning(
                    "ingestion_file_persist_retry workspace_id=%s source_name=%s attempt=%s error=%s",
                    workspace_id,
                    source_name,
                    attempt,
                    str(exc),
                )
                if attempt >= self._max_write_attempts:
                    raise HTTPException(status_code=500, detail="Failed to persist uploaded dataset") from exc
                time.sleep(0.05 * attempt)

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

        profile = self.quality_service.profile_csv(storage_path)
        profile["metadata"] = self._build_profile_metadata(profile, source_name, storage_path)

        for attempt in range(1, self._max_db_attempts + 1):
            try:
                dataset = Dataset(
                    workspace_id=workspace_id,
                    name=dataset_name,
                    source_type="file",
                    state=DatasetState.raw,
                    storage_path=str(storage_path),
                )
                db.add(dataset)
                db.flush()

                report = DataQualityReport(
                    dataset_id=dataset.id,
                    summary_json=self.quality_service.render_summary_json(profile),
                )
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
            except SQLAlchemyError as exc:
                db.rollback()
                logger.warning(
                    "ingestion_record_commit_retry workspace_id=%s source_name=%s attempt=%s error=%s",
                    workspace_id,
                    source_name,
                    attempt,
                    str(exc),
                )
                if attempt >= self._max_db_attempts:
                    raise HTTPException(status_code=500, detail="Failed to finalize ingestion records") from exc

        raise HTTPException(status_code=500, detail="Failed to finalize ingestion records")

    def _build_profile_metadata(self, profile: dict[str, Any], source_name: str, storage_path: Path) -> dict[str, Any]:
        """Attach operational metadata used by downstream lineage and AI workflows."""

        schema = [
            {"name": column.get("name", ""), "inferred_type": column.get("inferred_type", "unknown")}
            for column in profile.get("columns", [])
        ]
        fingerprint_source = {
            "row_count": profile.get("row_count", 0),
            "rejected_rows": profile.get("rejected_rows", 0),
            "quality_score": profile.get("quality_score", 0),
            "schema": schema,
            "issues": profile.get("issues", []),
        }
        fingerprint = hashlib.sha256(
            json.dumps(fingerprint_source, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        return {
            "profile_version": "1.1",
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "source_name": source_name,
            "storage_path": str(storage_path),
            "column_count": len(schema),
            "issue_count": len(profile.get("issues", [])),
            "schema": schema,
            "profile_fingerprint": fingerprint,
        }
