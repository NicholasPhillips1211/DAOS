from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.metadata import Dataset
from app.schemas.dataset import DatasetQueryRequest, DatasetQueryResponse
from app.services.audit_service import AuditService
from app.services.lakehouse_service import LakehouseService

router = APIRouter()
lakehouse_service = LakehouseService()
audit_service = AuditService()


@router.post("/{dataset_id}/query", response_model=DatasetQueryResponse)
def query_dataset(
    dataset_id: int,
    payload: DatasetQueryRequest,
    x_user_email: str | None = Header(default=None, alias="X-User-Email"),
    db: Session = Depends(get_db),
) -> DatasetQueryResponse:
    """Execute SQL against a dataset file through the lightweight lakehouse layer."""

    if not payload.sql.strip():
        raise HTTPException(status_code=400, detail="SQL query is required")

    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not dataset.storage_path:
        raise HTTPException(status_code=400, detail="Dataset has no storage path")

    try:
        columns, rows = lakehouse_service.query_csv(dataset.storage_path, payload.sql)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset file not found") from None
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Query failed: {exc}") from exc

    audit_service.log_event(
        dataset.workspace_id,
        "dataset.query_executed",
        actor=x_user_email or "system",
        resource_type="dataset",
        resource_id=dataset.id,
        details=f"Returned {len(rows)} rows",
    )

    return DatasetQueryResponse(columns=columns, rows=rows, row_count=len(rows))