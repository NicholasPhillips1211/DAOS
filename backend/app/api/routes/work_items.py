import json

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.auth import (
    Principal,
    WORKSPACE_READ_ROLES,
    get_current_principal,
    require_workspace_role,
    require_workspace_scope,
)
from app.core.dependencies import get_db, get_pagination
from app.models.work_item import WorkItem
from app.schemas.work_item import WorkItemRead
from app.services.work_queue_service import WorkQueueService

router = APIRouter()
work_queue_service = WorkQueueService()


@router.get("", response_model=list[WorkItemRead])
def list_work_items(
    response: Response,
    workspace_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    job_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
    pagination: dict = Depends(get_pagination),
) -> list[WorkItemRead]:
    """List background work items for operational visibility."""

    require_workspace_scope(workspace_id)
    if workspace_id is not None:
        require_workspace_role(db, workspace_id, principal, WORKSPACE_READ_ROLES)
    total = work_queue_service.count_items(db, workspace_id=workspace_id, status=status, job_type=job_type)
    response.headers["X-Total-Count"] = str(total)
    items = work_queue_service.list_items(
        db,
        workspace_id=workspace_id,
        status=status,
        job_type=job_type,
        limit=pagination["limit"],
        offset=pagination["offset"],
    )
    return [_read_from_item(item) for item in items]


@router.get("/{work_item_id}", response_model=WorkItemRead)
def get_work_item(
    work_item_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> WorkItemRead:
    """Fetch one background work item."""

    item = work_queue_service.get_item(db, work_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Work item not found")
    if item.workspace_id is not None:
        require_workspace_role(db, item.workspace_id, principal, WORKSPACE_READ_ROLES)
    return _read_from_item(item)


def _read_from_item(item: WorkItem) -> WorkItemRead:
    return WorkItemRead(
        id=item.id,
        workspace_id=item.workspace_id,
        job_type=item.job_type,
        status=item.status,
        priority=item.priority,
        payload=_parse_json(item.payload_json),
        result=_parse_json(item.result_json) if item.result_json else None,
        error_message=item.error_message,
        attempts=item.attempts,
        max_attempts=item.max_attempts,
        available_at=item.available_at,
        locked_by=item.locked_by,
        locked_at=item.locked_at,
        started_at=item.started_at,
        finished_at=item.finished_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _parse_json(value: str) -> dict[str, object]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {"raw": value}
    return parsed if isinstance(parsed, dict) else {"value": parsed}
