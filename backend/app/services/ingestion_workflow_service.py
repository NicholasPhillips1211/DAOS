from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.ingestion import DataQualityReport, IngestionJob
from app.models.metadata import Dataset, DatasetState
from app.services.audit_service import AuditService
from app.services.metadata_service import MetadataService
from app.services.quality_service import QualityService

logger = logging.getLogger("daos.ingestion")


@dataclass(slots=True)
class IngestionWorkflowResult:
    """The committed artifacts produced by a successful ingestion workflow."""

    dataset: Dataset
    job: IngestionJob
    report: DataQualityReport
    storage_path: Path
    profile: dict[str, Any]


class IngestionWorkflowService:
    """Own the full ingestion lifecycle and durable job state transitions."""

    def __init__(
        self,
        quality_service: QualityService | None = None,
        audit_service: AuditService | None = None,
        metadata_service: MetadataService | None = None,
    ) -> None:
        self.quality_service = quality_service or QualityService()
        self.audit_service = audit_service or AuditService()
        self.metadata_service = metadata_service or MetadataService()
        self._max_write_attempts = 3
        self._max_db_attempts = 2
        self._chunk_size = 1024 * 1024

    def process_upload(
        self,
        db: Session,
        *,
        raw_storage_root: Path,
        workspace_id: int,
        dataset_name: str,
        file_name: str | None,
        file_stream: BinaryIO,
        actor: str,
    ) -> IngestionWorkflowResult:
        """Persist, profile, register, audit, and emit metadata for one upload."""

        source_name = self._safe_source_name(file_name, dataset_name)
        job: IngestionJob | None = None

        try:
            self.validate_dataset_name(dataset_name)
            source_name = self.resolve_source_name(file_name, dataset_name)
            job = self.start_job(db, workspace_id=workspace_id, source_name=source_name)
            storage_path = self.persist_file(raw_storage_root, workspace_id, source_name, file_stream)
            result = self.complete_job_with_profile(
                db,
                job=job,
                workspace_id=workspace_id,
                dataset_name=dataset_name.strip(),
                source_name=source_name,
                storage_path=storage_path,
            )
            self.emit_success_events(db, result, actor=actor)
            return result
        except HTTPException as exc:
            message = self._http_error_message(exc)
            if job is None:
                job = self.record_failed_job(
                    db,
                    workspace_id=workspace_id,
                    source_name=source_name,
                    error_message=message,
                )
            else:
                self.mark_job_failed(db, job, message)
            self.emit_failure_events(db, job, actor=actor, dataset_name=dataset_name, error_message=message)
            raise
        except Exception as exc:
            message = "Ingestion workflow failed"
            logger.exception(
                "ingestion_workflow_failed workspace_id=%s source_name=%s error=%s",
                workspace_id,
                source_name,
                str(exc),
            )
            if job is None:
                job = self.record_failed_job(
                    db,
                    workspace_id=workspace_id,
                    source_name=source_name,
                    error_message=message,
                )
            else:
                self.mark_job_failed(db, job, message)
            self.emit_failure_events(db, job, actor=actor, dataset_name=dataset_name, error_message=message)
            raise HTTPException(status_code=500, detail=message) from exc

    def validate_dataset_name(self, dataset_name: str) -> None:
        """Reject blank dataset names before creating dataset records."""

        if not dataset_name.strip():
            raise HTTPException(status_code=400, detail="Dataset name is required")

    def resolve_source_name(self, file_name: str | None, dataset_name: str) -> str:
        """Pick a safe source filename while preserving strict CSV-only support."""

        source_name = self._safe_source_name(file_name, dataset_name)
        if not source_name.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail="Only CSV uploads are supported in the MVP")
        return source_name

    def start_job(self, db: Session, *, workspace_id: int, source_name: str) -> IngestionJob:
        """Create a durable running job before file persistence or profiling starts."""

        job = IngestionJob(
            workspace_id=workspace_id,
            source_name=source_name,
            source_type="file",
            status="running",
            row_count=0,
            rejected_rows=0,
            quality_score=0,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    def persist_file(
        self,
        raw_storage_root: Path,
        workspace_id: int,
        source_name: str,
        file_stream: BinaryIO,
    ) -> Path:
        """Stream uploaded bytes to workspace-scoped raw storage using atomic replace."""

        raw_storage_root.mkdir(parents=True, exist_ok=True)
        storage_path = raw_storage_root / f"ws{workspace_id}_{source_name}"
        temp_path = storage_path.with_suffix(f"{storage_path.suffix}.tmp")

        for attempt in range(1, self._max_write_attempts + 1):
            try:
                file_stream.seek(0)
                with temp_path.open("wb") as target:
                    while chunk := file_stream.read(self._chunk_size):
                        target.write(chunk)
                temp_path.replace(storage_path)
                return storage_path
            except OSError as exc:
                self._remove_temp_file(temp_path)
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

    def complete_job_with_profile(
        self,
        db: Session,
        *,
        job: IngestionJob,
        workspace_id: int,
        dataset_name: str,
        source_name: str,
        storage_path: Path,
    ) -> IngestionWorkflowResult:
        """Profile a persisted file and atomically create the success records."""

        profile = self.quality_service.profile_csv(storage_path)
        profile["metadata"] = self._build_profile_metadata(profile, source_name, storage_path, job.id)

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
                job.dataset_id = dataset.id
                job.status = "completed"
                job.row_count = profile["row_count"]
                job.rejected_rows = profile["rejected_rows"]
                job.quality_score = profile["quality_score"]
                job.error_message = None
                job.finished_at = datetime.now(timezone.utc)

                db.add(report)
                db.add(job)
                db.commit()
                db.refresh(dataset)
                db.refresh(report)
                db.refresh(job)
                return IngestionWorkflowResult(
                    dataset=dataset,
                    job=job,
                    report=report,
                    storage_path=storage_path,
                    profile=profile,
                )
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

    def record_failed_job(
        self,
        db: Session,
        *,
        workspace_id: int,
        source_name: str,
        error_message: str,
    ) -> IngestionJob:
        """Create a failed job for validation failures that occur before processing."""

        job = IngestionJob(
            workspace_id=workspace_id,
            source_name=source_name,
            source_type="file",
            status="failed",
            row_count=0,
            rejected_rows=0,
            quality_score=0,
            error_message=error_message,
            finished_at=datetime.now(timezone.utc),
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    def mark_job_failed(self, db: Session, job: IngestionJob, error_message: str) -> None:
        """Persist a failed terminal state for a started ingestion job."""

        job.status = "failed"
        job.error_message = error_message
        job.finished_at = datetime.now(timezone.utc)
        db.add(job)
        db.commit()
        db.refresh(job)

    def list_jobs(
        self,
        db: Session,
        *,
        workspace_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[IngestionJob]:
        """Return ingestion jobs newest-first, optionally scoped to a workspace."""

        query = db.query(IngestionJob)
        if workspace_id is not None:
            query = query.filter(IngestionJob.workspace_id == workspace_id)
        return query.order_by(IngestionJob.created_at.desc()).limit(limit).offset(offset).all()

    def count_jobs(self, db: Session, *, workspace_id: int | None = None) -> int:
        """Return the total number of ingestion jobs matching a workspace scope."""

        query = db.query(IngestionJob)
        if workspace_id is not None:
            query = query.filter(IngestionJob.workspace_id == workspace_id)
        return query.count()

    def emit_success_events(self, db: Session, result: IngestionWorkflowResult, *, actor: str) -> None:
        """Emit audit and metadata events after the successful job transaction commits."""

        dataset = result.dataset
        job = result.job
        report = result.report
        self.audit_service.log_event(
            dataset.workspace_id,
            "dataset.uploaded",
            actor=actor,
            resource_type="dataset",
            resource_id=dataset.id,
            details=f"Uploaded {job.source_name} with quality score {job.quality_score}",
            db=db,
        )
        self.metadata_service.record_ingestion_profile(
            db,
            workspace_id=dataset.workspace_id,
            dataset_id=dataset.id,
            dataset_name=dataset.name,
            job_id=job.id,
            report_id=report.id,
            source_name=job.source_name,
            storage_path=str(result.storage_path),
            actor=actor,
            profile=result.profile,
        )

    def emit_failure_events(
        self,
        db: Session,
        job: IngestionJob,
        *,
        actor: str,
        dataset_name: str,
        error_message: str,
    ) -> None:
        """Best-effort audit and metadata emission for failed ingestion jobs."""

        try:
            self.audit_service.log_event(
                job.workspace_id,
                "dataset.upload_failed",
                actor=actor,
                resource_type="ingestion_job",
                resource_id=job.id,
                details=error_message,
                db=db,
            )
            self.metadata_service.emit_event(
                db,
                workspace_id=job.workspace_id,
                event_type="metadata.ingestion.failed",
                resource_type="ingestion_job",
                resource_id=job.id,
                actor=actor,
                details={
                    "job_id": job.id,
                    "dataset_name": dataset_name.strip() or None,
                    "source_name": job.source_name,
                    "status": job.status,
                    "error_message": error_message,
                },
            )
        except Exception as exc:
            logger.warning(
                "ingestion_failure_event_emit_failed job_id=%s error=%s",
                job.id,
                str(exc),
            )

    def _build_profile_metadata(
        self,
        profile: dict[str, Any],
        source_name: str,
        storage_path: Path,
        job_id: int,
    ) -> dict[str, Any]:
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
            "profile_version": "1.2",
            "ingestion_job_id": job_id,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "source_name": source_name,
            "storage_path": str(storage_path),
            "column_count": len(schema),
            "issue_count": len(profile.get("issues", [])),
            "schema": schema,
            "profile_fingerprint": fingerprint,
        }

    @staticmethod
    def _safe_source_name(file_name: str | None, dataset_name: str) -> str:
        source_name = Path(file_name or dataset_name.strip() or "upload").name
        return source_name or "upload"

    @staticmethod
    def _http_error_message(exc: HTTPException) -> str:
        return str(exc.detail or "Ingestion request failed")

    @staticmethod
    def _remove_temp_file(temp_path: Path) -> None:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            logger.warning("ingestion_temp_cleanup_failed path=%s", temp_path)
