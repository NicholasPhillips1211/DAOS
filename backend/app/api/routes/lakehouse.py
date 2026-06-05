from time import perf_counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import (
    Principal,
    WORKSPACE_READ_ROLES,
    get_current_principal,
    require_model_workspace_role,
)
from app.core.dependencies import get_db
from app.models.metadata import Dataset
from app.schemas.dataset import DatasetQueryRequest, DatasetQueryResponse
from app.services.analytics_service import AnalyticsService
from app.services.analytics_workflow_service import AnalyticsWorkflowService
from app.services.audit_service import AuditService
from app.services.lakehouse_service import LakehouseService
from app.services.workspace_workflow_service import WorkspaceWorkflowService

router = APIRouter()
lakehouse_service = LakehouseService()
workspace_workflow_service = WorkspaceWorkflowService(lakehouse_service)
audit_service = AuditService()
analytics_workflow_service = AnalyticsWorkflowService(AnalyticsService())


@router.post("/{dataset_id}/query", response_model=DatasetQueryResponse)
def query_dataset(
    dataset_id: int,
    payload: DatasetQueryRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> DatasetQueryResponse:
    """Execute SQL against a dataset file through the lightweight lakehouse layer."""

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
        route="lakehouse",
        row_count=len(rows),
        column_count=len(columns),
        duration_ms=duration_ms,
        actor=principal.user_email,
    )

    return DatasetQueryResponse(columns=columns, rows=rows, row_count=len(rows))
