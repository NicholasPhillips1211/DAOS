from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.routes.workspaces import get_db
from app.core.auth import Principal, get_current_principal, require_workspace_role
from app.models.governance import AuditEvent, DataMask
from app.models.metadata import Workspace
from app.models.metadata import WorkspaceRole
from app.schemas.governance import AuditEventRead, DataMaskCreate, DataMaskRead

router = APIRouter()


@router.get("/audit", response_model=list[AuditEventRead])
def list_audit_events(
    workspace_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> list[AuditEvent]:
    """Expose audit events in reverse chronological order for workspace review."""

    require_workspace_role(db, workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst, WorkspaceRole.viewer})
    return db.query(AuditEvent).filter(AuditEvent.workspace_id == workspace_id).order_by(AuditEvent.created_at.desc()).all()


@router.post("/masks", response_model=DataMaskRead, status_code=201)
def create_data_mask(payload: DataMaskCreate, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)) -> DataMask:
    """Persist a dataset masking rule for a workspace with admin-level access."""

    workspace = db.get(Workspace, payload.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    require_workspace_role(db, payload.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin})
    mask = DataMask(
        workspace_id=payload.workspace_id,
        dataset_id=payload.dataset_id,
        column_name=payload.column_name,
        mask_type=payload.mask_type,
    )
    db.add(mask)
    db.commit()
    db.refresh(mask)
    return mask
