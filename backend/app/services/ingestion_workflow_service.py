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

from app.core.config import settings
from app.core.workflow_jobs import INGESTION_CLEAN_PROFILE_JOB
from app.core.workflow_status import WorkflowStatus
from app.models.ingestion import DataQualityReport, IngestionJob
from app.models.metadata import Dataset, DatasetState
from app.services.audit_service import AuditService
from app.services.metadata_service import MetadataService
from app.services.quality_service import QualityService
from app.services.work_queue_service import WorkQueueService

logger = logging.getLogger("daos.ingestion")


@dataclass(slots=True)
class IngestionWorkflowResult:
    """The committed artifacts produced by a successful ingestion workflow."""

    dataset: Dataset
    job: IngestionJob
    report: DataQualityReport
    storage_path: Path
    raw_storage_path: Path
    rejected_storage_path: Path
    profile: dict[str, Any]


@dataclass(slots=True)
class QueuedIngestionUpload:
    """The durable job and work item created after accepting an upload."""

    job: IngestionJob
    work_item_id: int


class IngestionWorkflowService:
    """Own the full ingestion lifecycle and durable job state transitions."""

    def __init__(
        self,
        quality_service: QualityService | None = None,
        audit_service: AuditService | None = None,
        metadata_service: MetadataService | None = None,
        work_queue_service: WorkQueueService | None = None,
    ) -> None:
        self.quality_service = quality_service or QualityService()
        self.audit_service = audit_service or AuditService()
        self.metadata_service = metadata_service or MetadataService()
        self.work_queue_service = work_queue_service or WorkQueueService()
        self._max_write_attempts = 3
        self._max_db_attempts = 2
        self._chunk_size = 1024 * 1024

    def queue_upload(
        self,
        db: Session,
        *,
        raw_storage_root: Path,
        workspace_id: int,
        dataset_name: str,
        file_name: str | None,
        file_stream: BinaryIO,
        actor: str,
    ) -> QueuedIngestionUpload:
        """Persist an upload and enqueue cleaning, profiling, and registration for a worker."""

        source_name = self._safe_source_name(file_name, dataset_name)
        job: IngestionJob | None = None

        try:
            self.validate_dataset_name(dataset_name)
            source_name = self.resolve_source_name(file_name, dataset_name)
            job = self.start_job(
                db,
                workspace_id=workspace_id,
                dataset_name=dataset_name.strip(),
                source_name=source_name,
                actor=actor,
            )
            storage_path = self.persist_file(raw_storage_root, workspace_id, source_name, file_stream)
            job.storage_path = str(storage_path)
            job.status = WorkflowStatus.queued.value
            job.current_step = "queued_for_cleaning"
            job.progress_percent = 15
            db.add(job)
            db.commit()
            db.refresh(job)

            work_item = self.work_queue_service.enqueue(
                db,
                workspace_id=workspace_id,
                job_type=INGESTION_CLEAN_PROFILE_JOB,
                priority=50,
                payload={"ingestion_job_id": job.id},
            )
            job.work_item_id = work_item.id
            db.add(job)
            db.commit()
            db.refresh(job)

            self.audit_service.log_event(
                workspace_id,
                "dataset.upload_queued",
                actor=actor,
                resource_type="ingestion_job",
                resource_id=job.id,
                details=f"Queued {source_name} for cleaning and profiling",
                db=db,
            )
            return QueuedIngestionUpload(job=job, work_item_id=work_item.id)
        except HTTPException as exc:
            message = self._http_error_message(exc)
            if job is None:
                job = self.record_failed_job(
                    db,
                    workspace_id=workspace_id,
                    source_name=source_name,
                    dataset_name=dataset_name,
                    actor=actor,
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
                    dataset_name=dataset_name,
                    actor=actor,
                    error_message=message,
                )
            else:
                self.mark_job_failed(db, job, message)
            self.emit_failure_events(db, job, actor=actor, dataset_name=dataset_name, error_message=message)
            raise HTTPException(status_code=500, detail=message) from exc

    def process_upload(
        self,
        db: Session,
        *,
        raw_storage_root: Path,
        clean_storage_root: Path | None = None,
        rejected_storage_root: Path | None = None,
        workspace_id: int,
        dataset_name: str,
        file_name: str | None,
        file_stream: BinaryIO,
        actor: str,
    ) -> IngestionWorkflowResult:
        """Synchronously process one upload for legacy callers and focused tests."""

        source_name = self.resolve_source_name(file_name, dataset_name)
        self.validate_dataset_name(dataset_name)
        job = self.start_job(
            db,
            workspace_id=workspace_id,
            dataset_name=dataset_name.strip(),
            source_name=source_name,
            actor=actor,
            status=WorkflowStatus.running.value,
            current_step="persisting_file",
            progress_percent=10,
        )
        storage_path = self.persist_file(raw_storage_root, workspace_id, source_name, file_stream)
        job.storage_path = str(storage_path)
        db.add(job)
        db.commit()
        db.refresh(job)
        result = self.complete_job_with_profile(
            db,
            job=job,
            workspace_id=workspace_id,
            dataset_name=dataset_name.strip(),
            source_name=source_name,
            raw_storage_path=storage_path,
            clean_storage_root=clean_storage_root,
            rejected_storage_root=rejected_storage_root,
        )
        self.emit_success_events_best_effort(db, result, actor=actor)
        return result

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

    def start_job(
        self,
        db: Session,
        *,
        workspace_id: int,
        dataset_name: str,
        source_name: str,
        actor: str | None,
        status: str = WorkflowStatus.staging.value,
        current_step: str = "persisting_file",
        progress_percent: int = 5,
    ) -> IngestionJob:
        """Create a durable job before file persistence or profiling starts."""

        job = IngestionJob(
            workspace_id=workspace_id,
            dataset_name=dataset_name,
            source_name=source_name,
            source_type="file",
            status=status,
            current_step=current_step,
            progress_percent=progress_percent,
            row_count=0,
            rejected_rows=0,
            quality_score=0,
            actor=actor,
            started_at=datetime.now(timezone.utc) if status == WorkflowStatus.running.value else None,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    def process_queued_job(
        self,
        db: Session,
        *,
        job_id: int,
        clean_storage_root: Path | None = None,
        rejected_storage_root: Path | None = None,
    ) -> IngestionWorkflowResult:
        """Run the worker-side cleaning, profiling, and registration path for a queued upload."""

        job = db.get(IngestionJob, job_id)
        if job is None:
            raise ValueError(f"Ingestion job {job_id} was not found")
        existing_result = self._completed_job_result(db, job)
        if existing_result is not None:
            return existing_result
        if not job.storage_path:
            raise ValueError(f"Ingestion job {job_id} has no persisted file path")
        if not job.dataset_name:
            raise ValueError(f"Ingestion job {job_id} has no dataset name")

        try:
            self.mark_job_running(db, job, step="cleaning_dataset", progress_percent=35)
            result = self.complete_job_with_profile(
                db,
                job=job,
                workspace_id=job.workspace_id,
                dataset_name=job.dataset_name,
                source_name=job.source_name,
                raw_storage_path=Path(job.storage_path),
                clean_storage_root=clean_storage_root,
                rejected_storage_root=rejected_storage_root,
            )
        except HTTPException as exc:
            self.mark_job_failed(db, job, self._http_error_message(exc))
            self.emit_failure_events(
                db,
                job,
                actor=job.actor or "worker",
                dataset_name=job.dataset_name or "",
                error_message=self._http_error_message(exc),
            )
            raise
        except Exception as exc:
            message = "Ingestion worker failed"
            logger.exception("ingestion_worker_failed job_id=%s error=%s", job.id, str(exc))
            self.mark_job_failed(db, job, message)
            self.emit_failure_events(
                db,
                job,
                actor=job.actor or "worker",
                dataset_name=job.dataset_name or "",
                error_message=message,
            )
            raise
        self.emit_success_events_best_effort(db, result, actor=job.actor or "worker")
        return result

    def mark_job_running(self, db: Session, job: IngestionJob, *, step: str, progress_percent: int) -> None:
        """Move a queued job into an active worker step."""

        job.status = WorkflowStatus.running.value
        job.current_step = step
        job.progress_percent = progress_percent
        job.started_at = job.started_at or datetime.now(timezone.utc)
        job.error_message = None
        db.add(job)
        db.commit()
        db.refresh(job)

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
        raw_storage_path: Path,
        clean_storage_root: Path | None = None,
        rejected_storage_root: Path | None = None,
    ) -> IngestionWorkflowResult:
        """Clean/profile a persisted file and atomically create the success records."""

        existing_result = self._completed_job_result(db, job)
        if existing_result is not None:
            return existing_result

        cleaned_storage_path = self.cleaned_storage_path(clean_storage_root, workspace_id, source_name)
        rejected_storage_path = self.rejected_storage_path(rejected_storage_root, workspace_id, source_name)

        # The raw artifact is profiled before cleaning so analysts can see what
        # changed, while the registered Dataset always points at the cleaned
        # artifact used by query, dashboard, ML, and automation workflows.
        raw_profile = self.quality_service.profile_csv(raw_storage_path)
        cleaning_summary = self.quality_service.clean_csv(raw_storage_path, cleaned_storage_path, rejected_storage_path)
        profile = self.quality_service.profile_csv(cleaned_storage_path)
        profile["rejected_rows"] = cleaning_summary["rejected_row_count"]
        profile["cleaning"] = cleaning_summary
        profile["raw_profile"] = raw_profile
        profile["quality_delta"] = self.quality_service.compare_profiles(raw_profile, profile, cleaning_summary)
        profile["metadata"] = self._build_profile_metadata(
            profile,
            source_name,
            cleaned_storage_path,
            raw_storage_path,
            rejected_storage_path,
            job.id,
        )

        for attempt in range(1, self._max_db_attempts + 1):
            try:
                dataset = Dataset(
                    workspace_id=workspace_id,
                    name=dataset_name,
                    source_type="file",
                    state=DatasetState.cleansed,
                    storage_path=str(cleaned_storage_path),
                )
                db.add(dataset)
                db.flush()

                report = DataQualityReport(
                    dataset_id=dataset.id,
                    summary_json=self.quality_service.render_summary_json(profile),
                )
                job.dataset_id = dataset.id
                job.status = WorkflowStatus.completed.value
                job.current_step = "cleaned_and_profiled"
                job.progress_percent = 100
                job.row_count = profile["row_count"]
                job.rejected_rows = cleaning_summary["rejected_row_count"]
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
                    storage_path=cleaned_storage_path,
                    raw_storage_path=raw_storage_path,
                    rejected_storage_path=rejected_storage_path,
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
        dataset_name: str,
        actor: str | None,
        error_message: str,
    ) -> IngestionJob:
        """Create a failed job for validation failures that occur before processing."""

        job = IngestionJob(
            workspace_id=workspace_id,
            dataset_name=dataset_name.strip() or None,
            source_name=source_name,
            source_type="file",
            status=WorkflowStatus.failed.value,
            current_step="validation_failed",
            progress_percent=100,
            row_count=0,
            rejected_rows=0,
            quality_score=0,
            error_message=error_message,
            actor=actor,
            finished_at=datetime.now(timezone.utc),
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    def mark_job_failed(self, db: Session, job: IngestionJob, error_message: str) -> None:
        """Persist a failed terminal state for a started ingestion job."""

        job.status = WorkflowStatus.failed.value
        job.current_step = WorkflowStatus.failed.value
        job.progress_percent = 100
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

    def emit_success_events_best_effort(self, db: Session, result: IngestionWorkflowResult, *, actor: str) -> None:
        """Emit success events without corrupting the committed ingestion result."""

        try:
            self.emit_success_events(db, result, actor=actor)
        except Exception as exc:
            logger.warning(
                "ingestion_success_event_emit_failed job_id=%s dataset_id=%s error=%s",
                result.job.id,
                result.dataset.id,
                str(exc),
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
        cleaned_storage_path: Path,
        raw_storage_path: Path,
        rejected_storage_path: Path,
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
            "quality_delta": profile.get("quality_delta", {}),
            "cleaning": profile.get("cleaning", {}),
        }
        fingerprint = hashlib.sha256(
            json.dumps(fingerprint_source, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        return {
            "profile_version": "1.4",
            "ingestion_job_id": job_id,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "source_name": source_name,
            "storage_path": str(cleaned_storage_path),
            "raw_storage_path": str(raw_storage_path),
            "cleaned_storage_path": str(cleaned_storage_path),
            "rejected_storage_path": str(rejected_storage_path),
            "cleaning": profile.get("cleaning", {}),
            "quality_delta": profile.get("quality_delta", {}),
            "raw_profile": profile.get("raw_profile", {}),
            "column_count": len(schema),
            "issue_count": len(profile.get("issues", [])),
            "schema": schema,
            "profile_fingerprint": fingerprint,
        }

    @staticmethod
    def cleaned_storage_path(clean_storage_root: Path | None, workspace_id: int, source_name: str) -> Path:
        root = clean_storage_root or Path(settings.clean_storage_root)
        return root / f"ws{workspace_id}_{Path(source_name).stem}_cleaned.csv"

    @staticmethod
    def rejected_storage_path(rejected_storage_root: Path | None, workspace_id: int, source_name: str) -> Path:
        root = rejected_storage_root or Path(settings.rejected_storage_root)
        return root / f"ws{workspace_id}_{Path(source_name).stem}_rejected.csv"

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

    def _completed_job_result(self, db: Session, job: IngestionJob) -> IngestionWorkflowResult | None:
        if job.dataset_id is None:
            return None

        dataset = db.get(Dataset, job.dataset_id)
        if dataset is None:
            raise ValueError(f"Ingestion job {job.id} references missing dataset {job.dataset_id}")

        report = (
            db.query(DataQualityReport)
            .filter(DataQualityReport.dataset_id == dataset.id)
            .order_by(DataQualityReport.created_at.desc(), DataQualityReport.id.desc())
            .first()
        )
        if report is None:
            raise ValueError(f"Ingestion job {job.id} references dataset {dataset.id} without a quality report")

        storage_path = dataset.storage_path or job.storage_path
        if not storage_path:
            raise ValueError(f"Ingestion job {job.id} completed without a storage path")
        profile = self._profile_from_report(report)
        metadata = profile.get("metadata", {}) if isinstance(profile.get("metadata", {}), dict) else {}

        return IngestionWorkflowResult(
            dataset=dataset,
            job=job,
            report=report,
            storage_path=Path(storage_path),
            raw_storage_path=Path(metadata.get("raw_storage_path") or job.storage_path or storage_path),
            rejected_storage_path=Path(metadata.get("rejected_storage_path") or storage_path),
            profile=profile,
        )

    @staticmethod
    def _profile_from_report(report: DataQualityReport) -> dict[str, Any]:
        try:
            parsed = json.loads(report.summary_json)
        except json.JSONDecodeError:
            return {"raw": report.summary_json}
        return parsed if isinstance(parsed, dict) else {"value": parsed}
