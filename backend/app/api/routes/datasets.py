from fastapi import APIRouter, Depends, Query, Response
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
from app.services.audit_service import AuditService
from app.services.dataset_workflow_service import DatasetWorkflowService
from app.services.lakehouse_service import LakehouseService
from app.services.metadata_service import MetadataService
from app.services.workspace_workflow_service import WorkspaceWorkflowService

router = APIRouter()
dataset_workflow_service = DatasetWorkflowService()
lakehouse_service = LakehouseService()
workspace_workflow_service = WorkspaceWorkflowService(lakehouse_service)
audit_service = AuditService()
metadata_service = MetadataService()


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
    dataset, columns, rows = workspace_workflow_service.query_dataset(db, dataset_id, payload.sql)

    audit_service.log_event(
        dataset.workspace_id,
        "dataset.query_executed",
        actor=principal.user_email,
        resource_type="dataset",
        resource_id=dataset.id,
        details=f"Returned {len(rows)} rows",
        db=db,
    )
    metadata_service.record_usage_event(
        db,
        workspace_id=dataset.workspace_id,
        asset_type="dataset",
        asset_id=dataset.id,
        action="dataset.query_executed",
        actor=principal.user_email,
        details={"route": "datasets", "row_count": len(rows), "columns": columns},
    )

    return DatasetQueryResponse(columns=columns, rows=rows, row_count=len(rows))
