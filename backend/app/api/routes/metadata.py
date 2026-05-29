from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from app.core.dependencies_async import get_db_async
from app.schemas.metadata import MetadataEventRead
from app.services.metadata_service import MetadataService
from app.core.dependencies import get_pagination

router = APIRouter()
metadata_service = MetadataService()


@router.get("/events", response_model=list[MetadataEventRead])
async def list_metadata_events(
    workspace_id: int = Query(..., description="Workspace scope for metadata retrieval"),
    event_type: str | None = Query(default=None, description="Exact event type filter"),
    resource_type: str | None = Query(default=None, description="Resource type filter"),
    resource_id: int | None = Query(default=None, description="Resource id filter"),
    db = Depends(get_db_async),
    pagination: dict = Depends(get_pagination),
    response: Response = None,
) -> list[MetadataEventRead]:
    """Expose queryable metadata events for lineage and workflow intelligence."""

    # Support both async and sync DB sessions.
    from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession

    if isinstance(db, _AsyncSession):
        total = await metadata_service.count_events_async(
            db, workspace_id=workspace_id, event_type=event_type, resource_type=resource_type, resource_id=resource_id
        )
        if response is not None:
            response.headers["X-Total-Count"] = str(total)

        events = await metadata_service.list_events_async(
            db,
            workspace_id=workspace_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            limit=pagination["limit"],
        )
    else:
        total = metadata_service.count_events(db, workspace_id=workspace_id, event_type=event_type, resource_type=resource_type, resource_id=resource_id)
        if response is not None:
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
