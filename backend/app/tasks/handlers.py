from __future__ import annotations

from app.tasks.queue import default_queue
from app.services.ingestion_service import IngestionService
from app.core.database import SessionLocal
from pathlib import Path
import logging

logger = logging.getLogger("daos.tasks")


@default_queue.register("profile_dataset")
async def profile_dataset(dataset_id: int, workspace_id: int, storage_path: str, dataset_name: str) -> None:
    """Background task to profile an existing dataset and persist report + job.

    This runs in the queue worker and uses a fresh sync DB session to avoid
    mixing request-scoped transactions with background processing.
    """
    svc = IngestionService()
    # Run profiler in thread to avoid blocking the worker event loop.
    profile = svc.quality_service.profile_csv(Path(storage_path))

    db = SessionLocal()
    try:
        # Load dataset row
        dataset = db.get(svc.models.Dataset if hasattr(svc, "models") else None, dataset_id)
        # Fallback: query by id
        from app.models.metadata import Dataset as _Dataset

        dataset = db.get(_Dataset, dataset_id)

        if not dataset:
            logger.warning("profile_dataset_missing_dataset id=%s", dataset_id)
            return

        svc.create_job_and_report_for_dataset(db, dataset, profile)
    except Exception:
        logger.exception("profile_dataset_failed dataset_id=%s", dataset_id)
    finally:
        db.close()
