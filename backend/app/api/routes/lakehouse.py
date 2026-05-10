from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.schemas.dataset import DatasetQueryRequest, DatasetQueryResponse
from app.services.audit_service import AuditService
from app.services.lakehouse_service import LakehouseService
from app.services.workspace_workflow_service import WorkspaceWorkflowService

router = APIRouter()
lakehouse_service = LakehouseService()
workspace_workflow_service = WorkspaceWorkflowService(lakehouse_service)
audit_service = AuditService()


@router.post("/{dataset_id}/query", response_model=DatasetQueryResponse)
def query_dataset(
    dataset_id: int,
    payload: DatasetQueryRequest,
    x_user_email: str | None = Header(default=None, alias="X-User-Email"),
    db: Session = Depends(get_db),
) -> DatasetQueryResponse:
    """Execute SQL against a dataset file through the lightweight lakehouse layer."""

    dataset, columns, rows = workspace_workflow_service.query_dataset(db, dataset_id, payload.sql)

    audit_service.log_event(
        dataset.workspace_id,
        "dataset.query_executed",
        actor=x_user_email or "system",
        resource_type="dataset",
        resource_id=dataset.id,
        details=f"Returned {len(rows)} rows",
    )

    return DatasetQueryResponse(columns=columns, rows=rows, row_count=len(rows))