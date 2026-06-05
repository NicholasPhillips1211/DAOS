from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.auth import Principal, WORKSPACE_READ_ROLES, get_current_principal, require_workspace_role
from app.core.dependencies import get_db
from app.core.dependencies import get_pagination
from app.schemas.metadata import MetadataEventRead
from app.services.metadata_service import MetadataService

router = APIRouter()
metadata_service = MetadataService()


@router.get("/events", response_model=list[MetadataEventRead])
def list_metadata_events(
    response: Response,
    workspace_id: int = Query(..., description="Workspace scope for metadata retrieval"),
    event_type: str | None = Query(default=None, description="Exact event type filter"),
    resource_type: str | None = Query(default=None, description="Resource type filter"),
    resource_id: int | None = Query(default=None, description="Resource id filter"),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
    pagination: dict = Depends(get_pagination),
) -> list[MetadataEventRead]:
    """Expose queryable metadata events for lineage and workflow intelligence."""

    require_workspace_role(db, workspace_id, principal, WORKSPACE_READ_ROLES)
    total = metadata_service.count_events(db, workspace_id=workspace_id, event_type=event_type, resource_type=resource_type, resource_id=resource_id)
    response.headers["X-Total-Count"] = str(total)

    events = metadata_service.list_events(
        db,
        workspace_id=workspace_id,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        limit=pagination["limit"],
    )

    return [
        MetadataEventRead(
            id=event.id,
            workspace_id=event.workspace_id,
            event_type=event.event_type,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            actor=event.actor,
            details=metadata_service.parse_details(event),
            created_at=event.created_at,
        )
        for event in events
    ]
