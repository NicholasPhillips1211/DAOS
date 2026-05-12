from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.governance import AuditEvent
from app.core.database import SessionLocal


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
            event = AuditEvent(
                workspace_id=workspace_id,
                event_type=event_type,
                actor=actor,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
            )
            db.add(event)
            if owns_session:
                db.commit()
                db.refresh(event)
            return event
        finally:
            if owns_session:
                db.close()
