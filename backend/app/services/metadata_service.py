from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.governance import AuditEvent

logger = logging.getLogger("daos.metadata")


class MetadataService:
    """Emit and query metadata events that power lineage and AI grounding."""

    def emit_event(
        self,
        db: Session,
        *,
        workspace_id: int,
        event_type: str,
        resource_type: str,
        resource_id: int,
        details: dict[str, Any],
        actor: str | None = None,
    ) -> AuditEvent:
        """Persist one metadata event into the shared audit store."""

        event = AuditEvent(
            workspace_id=workspace_id,
            event_type=event_type,
            actor=actor,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details, sort_keys=True),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    def list_events(
        self,
        db: Session,
        *,
        workspace_id: int,
        event_type: str | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Return metadata events newest-first with optional filters."""

        query = db.query(AuditEvent).filter(AuditEvent.workspace_id == workspace_id)
        query = query.filter(AuditEvent.event_type.like("metadata.%"))

        if event_type:
            query = query.filter(AuditEvent.event_type == event_type)
        if resource_type:
            query = query.filter(AuditEvent.resource_type == resource_type)
        if resource_id is not None:
            query = query.filter(AuditEvent.resource_id == resource_id)

        capped_limit = max(1, min(limit, 500))
        return query.order_by(AuditEvent.created_at.desc()).limit(capped_limit).all()

    def parse_details(self, event: AuditEvent) -> dict[str, Any]:
        """Parse JSON details safely for API response rendering."""

        if not event.details:
            return {}
        try:
            parsed = json.loads(event.details)
            return parsed if isinstance(parsed, dict) else {"value": parsed}
        except json.JSONDecodeError:
            logger.warning("metadata_event_unparseable id=%s", event.id)
            return {"raw": event.details}
