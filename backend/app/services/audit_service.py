from __future__ import annotations

import logging

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.retry import RetryPolicy, with_retry
from app.models.governance import AuditEvent
from app.core.database import SessionLocal

logger = logging.getLogger("daos.audit")


class AuditService:
    def log_event(
        self,
        workspace_id: int,
        event_type: str,
        actor: str | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
        details: str | None = None,
        db: Session | None = None,
    ) -> AuditEvent:
        """Persist an audit event in the metadata store.

        When *db* is supplied the event participates in the caller's transaction
        so it rolls back together with the main operation on failure.  When no
        session is provided the service falls back to an independent session for
        backward compatibility with call sites that fire-and-forget.
        """

        owns_session = db is None
        if owns_session:
            db = SessionLocal()

        try:
            def persist() -> AuditEvent:
                event = AuditEvent(
                    workspace_id=workspace_id,
                    event_type=event_type,
                    actor=actor,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    details=details,
                )
                db.add(event)
                db.commit()
                db.refresh(event)
                return event

            def on_retry(attempt: int, exc: Exception) -> None:
                db.rollback()
                logger.warning(
                    "audit_persist_retry workspace_id=%s event_type=%s attempt=%s error=%s",
                    workspace_id,
                    event_type,
                    attempt,
                    str(exc),
                )

            return with_retry(
                persist,
                on_retry=on_retry,
                policy=RetryPolicy(attempts=2, base_delay_seconds=0.02),
            )
        except SQLAlchemyError as exc:
            db.rollback()
            logger.exception("audit_persist_failed workspace_id=%s event_type=%s", workspace_id, event_type)
            raise HTTPException(status_code=500, detail="Failed to persist audit event") from exc
        finally:
            if owns_session:
                db.close()
