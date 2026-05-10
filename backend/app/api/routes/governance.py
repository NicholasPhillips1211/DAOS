from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.auth import Principal, get_current_principal, require_workspace_role
from app.models.governance import AuditEvent, DataMask
from app.models.metadata import WorkspaceRole
from app.schemas.governance import AuditEventRead, DataMaskCreate, DataMaskRead
from app.services.governance_workflow_service import GovernanceWorkflowService

router = APIRouter()
governance_workflow_service = GovernanceWorkflowService()


@router.get("/audit", response_model=list[AuditEventRead])
def list_audit_events(
    workspace_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> list[AuditEvent]:
    """Expose audit events in reverse chronological order for workspace review."""

    require_workspace_role(db, workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst, WorkspaceRole.viewer})
    return governance_workflow_service.list_audit_events(db, workspace_id)


@router.post("/masks", response_model=DataMaskRead, status_code=201)
def create_data_mask(payload: DataMaskCreate, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)) -> DataMask:
    """Persist a dataset masking rule for a workspace with admin-level access."""

    require_workspace_role(db, payload.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin})
    return governance_workflow_service.create_data_mask(
        db,
        workspace_id=payload.workspace_id,
        dataset_id=payload.dataset_id,
        column_name=payload.column_name,
        mask_type=payload.mask_type,
    )
