from __future__ import annotations

import argparse
import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.workflow_jobs import INGESTION_CLEAN_PROFILE_JOB_TYPES, expand_work_job_types
from app.models.automation import AutomationPlan
from app.models.metadata import Dataset
from app.models.visualization import Dashboard
from app.models.work_item import WorkItem
from app.services.analytics_service import AnalyticsService
from app.services.analytics_workflow_service import AnalyticsWorkflowService
from app.services.automation_service import AutomationExecutor, AutomationService
from app.services.automation_workflow_service import AutomationWorkflowService
from app.services.ingestion_workflow_service import IngestionWorkflowService
from app.services.lakehouse_service import LakehouseService
from app.services.metadata_service import MetadataService
from app.services.ml_service import MLService
from app.services.ml_workflow_service import MLWorkflowService
from app.services.work_queue_service import WorkQueueService

logger = logging.getLogger("daos.worker")
ASYNC_QUERY_PREVIEW_LIMIT = 100


class WorkerRunner:
    """Claim and execute persisted work items."""

    def __init__(self, *, worker_id: str | None = None, work_queue_service: WorkQueueService | None = None) -> None:
        self.worker_id = worker_id or f"worker-{uuid4()}"
        self.work_queue_service = work_queue_service or WorkQueueService()
        self.ingestion_service = IngestionWorkflowService(work_queue_service=self.work_queue_service)
        self.lakehouse_service = LakehouseService()
        self.analytics_workflow_service = AnalyticsWorkflowService(AnalyticsService())
        self.ml_workflow_service = MLWorkflowService(MLService())
        self.automation_workflow_service = AutomationWorkflowService(AutomationService(), AutomationExecutor())
        self.metadata_service = MetadataService()

    def run_once(self, *, job_types: set[str] | None = None) -> WorkItem | None:
        """Claim and execute at most one work item."""

        with SessionLocal() as db:
            item = self.work_queue_service.claim_next(
                db,
                worker_id=self.worker_id,
                job_types=expand_work_job_types(job_types),
            )
            if item is None:
                return None

            try:
                result = self._dispatch(db, item)
            except Exception as exc:  # noqa: BLE001
                logger.exception("work_item_failed id=%s job_type=%s", item.id, item.job_type)
                self.work_queue_service.mark_failed(db, item, error_message=str(exc) or exc.__class__.__name__)
            else:
                self.work_queue_service.mark_succeeded(db, item, result=result)
            db.refresh(item)
            return item

    def run_loop(self, *, poll_seconds: float, job_types: set[str] | None = None) -> None:
        """Continuously process available work items."""

        logger.info("worker_started worker_id=%s", self.worker_id)
        while True:
            item = self.run_once(job_types=job_types)
            if item is None:
                time.sleep(poll_seconds)

    def _dispatch(self, db: Session, item: WorkItem) -> dict[str, object]:
        payload = self.work_queue_service.payload(item)
        if item.job_type in INGESTION_CLEAN_PROFILE_JOB_TYPES:
            return self._run_ingestion_clean_profile(db, payload)
        if item.job_type == "lakehouse.query":
            return self._run_lakehouse_query(db, payload)
        if item.job_type == "ml.train":
            return self._run_ml_train(db, payload)
        if item.job_type == "automation.generate":
            return self._run_automation_generate(db, payload)
        if item.job_type == "automation.execute":
            return self._run_automation_execute(db, payload)
        if item.job_type == "dashboard.refresh":
            return self._run_dashboard_refresh(db, payload)
        raise ValueError(f"Unsupported work item type: {item.job_type}")

    def _run_ingestion_clean_profile(self, db: Session, payload: dict[str, object]) -> dict[str, object]:
        job_id = int(payload["ingestion_job_id"])
        result = self.ingestion_service.process_queued_job(
            db,
            job_id=job_id,
            clean_storage_root=Path(settings.clean_storage_root),
            rejected_storage_root=Path(settings.rejected_storage_root),
        )
        return {
            "ingestion_job_id": result.job.id,
            "dataset_id": result.dataset.id,
            "report_id": result.report.id,
            "row_count": result.job.row_count,
            "quality_score": result.job.quality_score,
            "storage_path": str(result.storage_path),
            "raw_storage_path": str(result.raw_storage_path),
            "rejected_storage_path": str(result.rejected_storage_path),
        }

    def _run_lakehouse_query(self, db: Session, payload: dict[str, object]) -> dict[str, object]:
        dataset_id = int(payload["dataset_id"])
        sql = str(payload["sql"])
        actor = str(payload.get("actor") or "worker")
        dataset = db.get(Dataset, dataset_id)
        if dataset is None:
            raise ValueError("Dataset not found")
        if not dataset.storage_path:
            raise ValueError("Dataset has no storage path")

        started = time.perf_counter()
        columns, rows = self.lakehouse_service.query_csv(dataset.storage_path, sql)
        duration_ms = int((time.perf_counter() - started) * 1000)
        preview_rows = rows[:ASYNC_QUERY_PREVIEW_LIMIT]
        execution = self.analytics_workflow_service.record_query_execution(
            db,
            dataset=dataset,
            sql_text=sql,
            route="lakehouse.async",
            row_count=len(rows),
            column_count=len(columns),
            duration_ms=duration_ms,
            actor=actor,
        )
        return {
            "query_execution_id": execution.id,
            "dataset_id": dataset.id,
            "columns": columns,
            "row_count": len(rows),
            "preview_rows": preview_rows,
            "preview_row_count": len(preview_rows),
            "truncated": len(rows) > len(preview_rows),
            "duration_ms": duration_ms,
        }

    def _run_ml_train(self, db: Session, payload: dict[str, object]) -> dict[str, object]:
        trained_model, training_result = self.ml_workflow_service.train_model(
            db,
            workspace_id=int(payload["workspace_id"]),
            dataset_id=int(payload["dataset_id"]),
            model_name=str(payload.get("model_name") or "decision-tree"),
            target_column=str(payload["target_column"]),
            task_type=str(payload.get("task_type") or "classification"),
            artifact_root=Path(settings.model_artifact_root),
        )
        return {
            "trained_model_id": trained_model.id,
            "dataset_id": trained_model.dataset_id,
            "metric_name": trained_model.metric_name,
            "metric_value": trained_model.metric_value,
            "feature_importances": training_result["feature_importances"],
        }

    def _run_automation_generate(self, db: Session, payload: dict[str, object]) -> dict[str, object]:
        workspace_id = int(payload["workspace_id"])
        objective = str(payload.get("objective") or "Automate the next best operational step")
        actor = str(payload.get("actor") or "worker")
        plan = asyncio.run(self.automation_workflow_service.generate_plan(db, workspace_id, objective))
        self.metadata_service.record_ai_context(
            db,
            workspace_id=plan.workspace_id,
            context_type="automation_plan",
            resource_type="automation_plan",
            resource_id=plan.id,
            actor=actor,
            context={
                "objective": plan.objective,
                "provider": plan.provider,
                "model_name": plan.model_name,
                "summary": plan.summary,
                "plan": self._parse_json(plan.automation_json),
            },
        )
        return {"automation_plan_id": plan.id, "provider": plan.provider, "summary": plan.summary}

    def _run_automation_execute(self, db: Session, payload: dict[str, object]) -> dict[str, object]:
        plan_id = int(payload["plan_id"])
        plan = db.get(AutomationPlan, plan_id)
        if plan is None:
            raise ValueError("Automation plan not found")
        updated = self.automation_workflow_service.execute_plan(db, plan)
        return {
            "automation_plan_id": updated.id,
            "execution_status": updated.execution_status,
            "execution_results": self._parse_json(updated.execution_results_json or "{}"),
        }

    def _run_dashboard_refresh(self, db: Session, payload: dict[str, object]) -> dict[str, object]:
        dashboard_id = int(payload["dashboard_id"])
        actor = str(payload.get("actor") or "worker")
        dashboard = db.get(Dashboard, dashboard_id)
        if dashboard is None:
            raise ValueError("Dashboard not found")

        refreshed_at = datetime.now(timezone.utc).isoformat()
        self.metadata_service.record_usage_event(
            db,
            workspace_id=dashboard.workspace_id,
            asset_type="dashboard",
            asset_id=dashboard.id,
            action="dashboard.refresh_completed",
            actor=actor,
            details={"refreshed_at": refreshed_at},
        )
        return {"dashboard_id": dashboard.id, "refreshed_at": refreshed_at}

    @staticmethod
    def _parse_json(value: str) -> dict[str, object]:
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {"raw": value}
        return parsed if isinstance(parsed, dict) else {"value": parsed}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the DAOS background worker")
    parser.add_argument("--loop", action="store_true", help="Continuously poll for work")
    parser.add_argument("--poll-seconds", type=float, default=settings.worker_poll_seconds)
    parser.add_argument("--job-type", action="append", dest="job_types", help="Restrict the worker to a job type")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    runner = WorkerRunner(worker_id=settings.worker_id)
    job_types = set(args.job_types) if args.job_types else None
    if args.loop:
        runner.run_loop(poll_seconds=args.poll_seconds, job_types=job_types)
        return 0

    item = runner.run_once(job_types=job_types)
    return 0 if item is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
