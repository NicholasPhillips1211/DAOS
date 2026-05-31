from fastapi import APIRouter, Depends, Header
import asyncio

from app.core.dependencies_async import get_db_async
from app.core.auth import Principal, get_current_principal
from app.schemas.dataset import DatasetQueryRequest, DatasetQueryResponse
from app.services.audit_service import AuditService
from app.services.lakehouse_service import LakehouseService
from app.services.workspace_workflow_service import WorkspaceWorkflowService

router = APIRouter()
lakehouse_service = LakehouseService()
workspace_workflow_service = WorkspaceWorkflowService(lakehouse_service)
audit_service = AuditService()


@router.post("/{dataset_id}/query", response_model=DatasetQueryResponse)
async def query_dataset(
    dataset_id: int,
    payload: DatasetQueryRequest,
    x_user_email: str | None = Header(default=None, alias="X-User-Email"),
    db = Depends(get_db_async),
    principal: Principal = Depends(get_current_principal),
) -> DatasetQueryResponse:
    """Execute SQL against a dataset file through the lightweight lakehouse layer.

    This endpoint supports both sync and async DB sessions during our phased
    migration. When provided an `AsyncSession` it will call the async workflow
    and lakehouse query; otherwise it falls back to the existing sync behavior.
    """

    from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession

    if isinstance(db, _AsyncSession):
        dataset, columns, rows = await workspace_workflow_service.query_dataset_async(db, dataset_id, payload.sql, principal)

        # Emit audit event in a thread using a sync DB session so the audit
        # persists independently of the async transaction handling.
        await asyncio.to_thread(
            audit_service.log_event,
            dataset.workspace_id,
            "dataset.query_executed",
            x_user_email or "system",
            "dataset",
            dataset.id,
            f"Returned {len(rows)} rows",
            None,
        )
    else:
        dataset, columns, rows = workspace_workflow_service.query_dataset(db, dataset_id, payload.sql, principal)
        audit_service.log_event(
            dataset.workspace_id,
            "dataset.query_executed",
            actor=x_user_email or "system",
            resource_type="dataset",
            resource_id=dataset.id,
            details=f"Returned {len(rows)} rows",
            db=db,
        )

    return DatasetQueryResponse(columns=columns, rows=rows, row_count=len(rows))