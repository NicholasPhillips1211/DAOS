from time import perf_counter

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.auth import (
    Principal,
    WORKSPACE_READ_ROLES,
    WORKSPACE_WRITE_ROLES,
    get_current_principal,
    require_model_workspace_role,
    require_workspace_role,
    require_workspace_scope,
)
from app.core.dependencies import get_db, get_pagination
from app.models.metadata import Dataset
from app.schemas.dataset import DatasetCreate, DatasetQueryRequest, DatasetQueryResponse, DatasetRead
from app.schemas.work_item import WorkItemSubmitRead
from app.services.analytics_service import AnalyticsService
from app.services.analytics_workflow_service import AnalyticsWorkflowService
from app.services.audit_service import AuditService
from app.services.dataset_workflow_service import DatasetWorkflowService
from app.services.lakehouse_service import LakehouseService
from app.services.workspace_workflow_service import WorkspaceWorkflowService
from app.services.work_queue_service import WorkQueueService

router = APIRouter()
dataset_workflow_service = DatasetWorkflowService()
lakehouse_service = LakehouseService()
workspace_workflow_service = WorkspaceWorkflowService(lakehouse_service)
audit_service = AuditService()
analytics_workflow_service = AnalyticsWorkflowService(AnalyticsService())
work_queue_service = WorkQueueService()


@router.get("", response_model=list[DatasetRead])
def list_datasets(
    response: Response,
    workspace_id: int | None = Query(default=None, description="Filter datasets to a single workspace"),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
    pagination: dict = Depends(get_pagination),
) -> list[Dataset]:
    """List datasets newest-first, optionally scoped to one workspace."""

    require_workspace_scope(workspace_id)
    if workspace_id is not None:
        require_workspace_role(db, workspace_id, principal, WORKSPACE_READ_ROLES)

    total = dataset_workflow_service.count_datasets(db, workspace_id=workspace_id)
    response.headers["X-Total-Count"] = str(total)
    return dataset_workflow_service.list_datasets(db, workspace_id=workspace_id, limit=pagination["limit"], offset=pagination["offset"])


@router.post("", response_model=DatasetRead, status_code=201)
def create_dataset(
    payload: DatasetCreate,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> Dataset:
    """Register a dataset record once its source and storage path are known."""

    require_workspace_role(db, payload.workspace_id, principal, WORKSPACE_WRITE_ROLES)
    return dataset_workflow_service.create_dataset(
        db,
        workspace_id=payload.workspace_id,
        name=payload.name,
        source_type=payload.source_type,
        storage_path=payload.storage_path,
    )


@router.post("/{dataset_id}/query", response_model=DatasetQueryResponse)
def query_dataset(
    dataset_id: int,
    payload: DatasetQueryRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> DatasetQueryResponse:
    """Execute SQL against a dataset file through the app-facing dataset route."""

    require_model_workspace_role(db, Dataset, dataset_id, principal, WORKSPACE_READ_ROLES, model_name="Dataset")
    started_at = perf_counter()
    dataset, columns, rows = workspace_workflow_service.query_dataset(db, dataset_id, payload.sql)
    duration_ms = int((perf_counter() - started_at) * 1000)

    audit_service.log_event(
        dataset.workspace_id,
        "dataset.query_executed",
        actor=principal.user_email,
        resource_type="dataset",
        resource_id=dataset.id,
        details=f"Returned {len(rows)} rows",
        db=db,
    )
    analytics_workflow_service.record_query_execution(
        db,
        dataset=dataset,
        sql_text=payload.sql,
        route="datasets",
        row_count=len(rows),
        column_count=len(columns),
        duration_ms=duration_ms,
        actor=principal.user_email,
    )

    return DatasetQueryResponse(columns=columns, rows=rows, row_count=len(rows))


@router.post("/{dataset_id}/query-jobs", response_model=WorkItemSubmitRead, status_code=status.HTTP_202_ACCEPTED)
def queue_dataset_query(
    dataset_id: int,
    payload: DatasetQueryRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> WorkItemSubmitRead:
    """Queue SQL execution when a query may be too expensive for the request path."""

    dataset = require_model_workspace_role(db, Dataset, dataset_id, principal, WORKSPACE_READ_ROLES, model_name="Dataset")
    item = work_queue_service.enqueue(
        db,
        workspace_id=dataset.workspace_id,
        job_type="lakehouse.query",
        payload={"dataset_id": dataset.id, "sql": payload.sql, "actor": principal.user_email},
    )
    return WorkItemSubmitRead(
        work_item_id=item.id,
        workspace_id=item.workspace_id,
        job_type=item.job_type,
        status=item.status,
        created_at=item.created_at,
    )
