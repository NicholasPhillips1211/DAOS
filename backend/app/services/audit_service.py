from __future__ import annotations

from app.models.governance import AuditEvent
from app.core.database import SessionLocal


class AuditService:
    def log_event(self, workspace_id: int, event_type: str, actor: str | None = None, resource_type: str | None = None, resource_id: int | None = None, details: str | None = None) -> AuditEvent:
        """Persist an audit event in the metadata store.

        The service opens its own session so callers can log security and
        collaboration events without coupling those paths to an existing unit of work.
        """

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
            db.commit()
            db.refresh(event)
            return event
        finally:
            db.close()
