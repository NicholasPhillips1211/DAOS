from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.work_item import WorkItem


class WorkQueueService:
    """Persist and coordinate background work items without an external broker."""

    def enqueue(
        self,
        db: Session,
        *,
        job_type: str,
        payload: dict[str, Any],
        workspace_id: int | None = None,
        priority: int = 100,
        max_attempts: int = 3,
    ) -> WorkItem:
        """Create a queued work item ready for a worker process to claim."""

        item = WorkItem(
            workspace_id=workspace_id,
            job_type=job_type,
            status="queued",
            priority=priority,
            payload_json=json.dumps(payload, sort_keys=True),
            max_attempts=max(1, max_attempts),
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def list_items(
        self,
        db: Session,
        *,
        workspace_id: int | None = None,
        status: str | None = None,
        job_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[WorkItem]:
        """Return work items newest-first with optional operational filters."""

        query = db.query(WorkItem)
        if workspace_id is not None:
            query = query.filter(WorkItem.workspace_id == workspace_id)
        if status is not None:
            query = query.filter(WorkItem.status == status)
        if job_type is not None:
            query = query.filter(WorkItem.job_type == job_type)
        return query.order_by(WorkItem.created_at.desc()).limit(limit).offset(offset).all()

    def count_items(
        self,
        db: Session,
        *,
        workspace_id: int | None = None,
        status: str | None = None,
        job_type: str | None = None,
    ) -> int:
        """Count work items using the same filters as list endpoints."""

        query = db.query(WorkItem)
        if workspace_id is not None:
            query = query.filter(WorkItem.workspace_id == workspace_id)
        if status is not None:
            query = query.filter(WorkItem.status == status)
        if job_type is not None:
            query = query.filter(WorkItem.job_type == job_type)
        return query.count()

    def get_item(self, db: Session, item_id: int) -> WorkItem | None:
        """Load one work item by id."""

        return db.get(WorkItem, item_id)

    def claim_next(
        self,
        db: Session,
        *,
        worker_id: str,
        job_types: set[str] | None = None,
        stale_after_seconds: float | None = None,
    ) -> WorkItem | None:
        """Claim the next available queued item for a worker.

        Postgres deployments use row locks with ``SKIP LOCKED`` so multiple
        workers can safely compete for work. SQLite development mode cannot
        provide the same concurrency guarantees, but it still follows the same
        state transitions for local single-worker use.
        """

        now = datetime.now(timezone.utc)
        self.requeue_stale_items(
            db,
            job_types=job_types,
            stale_after_seconds=stale_after_seconds,
            now=now,
        )
        query = db.query(WorkItem).filter(
            WorkItem.status == "queued",
            WorkItem.available_at <= now,
        )
        if job_types:
            query = query.filter(WorkItem.job_type.in_(sorted(job_types)))
        if self._supports_skip_locked(db):
            query = query.with_for_update(skip_locked=True)

        item = query.order_by(WorkItem.priority.asc(), WorkItem.created_at.asc()).first()
        if item is None:
            return None

        item.status = "running"
        item.attempts += 1
        item.locked_by = worker_id
        item.locked_at = now
        item.started_at = item.started_at or now
        item.error_message = None
        item.updated_at = now
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def requeue_stale_items(
        self,
        db: Session,
        *,
        job_types: set[str] | None = None,
        stale_after_seconds: float | None = None,
        now: datetime | None = None,
    ) -> int:
        """Recover work items abandoned by workers that stopped heartbeating."""

        current_time = now or datetime.now(timezone.utc)
        stale_after = settings.worker_stale_after_seconds if stale_after_seconds is None else stale_after_seconds
        stale_before = current_time - timedelta(seconds=max(stale_after, 0))
        query = db.query(WorkItem).filter(
            WorkItem.status == "running",
            WorkItem.locked_at.isnot(None),
            WorkItem.locked_at <= stale_before,
        )
        if job_types:
            query = query.filter(WorkItem.job_type.in_(sorted(job_types)))

        recovered = 0
        for item in query.order_by(WorkItem.locked_at.asc()).all():
            item.locked_by = None
            item.locked_at = None
            item.updated_at = current_time
            if item.attempts >= item.max_attempts:
                item.status = "failed"
                item.finished_at = current_time
                item.error_message = "Worker lock expired after max attempts"
            else:
                item.status = "queued"
                item.available_at = current_time
                item.error_message = "Requeued after stale worker lock"
            db.add(item)
            recovered += 1

        if recovered:
            db.commit()
        return recovered

    def mark_succeeded(self, db: Session, item: WorkItem, *, result: dict[str, Any] | None = None) -> WorkItem:
        """Store successful worker output and finish the item."""

        now = datetime.now(timezone.utc)
        return self._finish_locked_item(
            db,
            item,
            values={
                "status": "succeeded",
                "result_json": json.dumps(result or {}, sort_keys=True),
                "error_message": None,
                "locked_by": None,
                "locked_at": None,
                "finished_at": now,
                "updated_at": now,
            },
        )

    def mark_failed(self, db: Session, item: WorkItem, *, error_message: str) -> WorkItem:
        """Fail or requeue an item depending on remaining attempts."""

        now = datetime.now(timezone.utc)
        if item.attempts < item.max_attempts:
            values = {
                "status": "queued",
                "error_message": error_message,
                "locked_by": None,
                "locked_at": None,
                "available_at": now + timedelta(seconds=min(60, 2**max(item.attempts - 1, 0))),
                "updated_at": now,
            }
        else:
            values = {
                "status": "failed",
                "error_message": error_message,
                "locked_by": None,
                "locked_at": None,
                "finished_at": now,
                "updated_at": now,
            }
        return self._finish_locked_item(db, item, values=values)

    @staticmethod
    def payload(item: WorkItem) -> dict[str, Any]:
        """Parse a work item payload safely for handlers."""

        try:
            parsed = json.loads(item.payload_json)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {"value": parsed}

    @staticmethod
    def result(item: WorkItem) -> dict[str, Any] | None:
        """Parse a work item result for API responses."""

        if not item.result_json:
            return None
        try:
            parsed = json.loads(item.result_json)
        except json.JSONDecodeError:
            return {"raw": item.result_json}
        return parsed if isinstance(parsed, dict) else {"value": parsed}

    @staticmethod
    def _supports_skip_locked(db: Session) -> bool:
        bind = db.get_bind()
        return bool(bind and bind.dialect.name == "postgresql")

    @staticmethod
    def _finish_locked_item(db: Session, item: WorkItem, *, values: dict[str, Any]) -> WorkItem:
        locked_by = item.locked_by
        filters = [WorkItem.id == item.id, WorkItem.status == "running"]
        if locked_by is not None:
            filters.append(WorkItem.locked_by == locked_by)

        updated = db.query(WorkItem).filter(*filters).update(values, synchronize_session=False)
        if updated == 0:
            db.rollback()
            current = db.get(WorkItem, item.id)
            return current or item

        db.commit()
        db.refresh(item)
        return item
