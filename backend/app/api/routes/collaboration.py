from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.auth import Principal, get_current_principal, require_workspace_role
from app.models.collaboration import Comment, Share
from app.models.metadata import Workspace
from app.models.metadata import WorkspaceRole
from app.schemas.collaboration import CommentCreate, CommentRead, ShareCreate, ShareRead
from app.services.audit_service import AuditService

router = APIRouter()
audit_service = AuditService()


@router.post("/comments", response_model=CommentRead, status_code=201)
def create_comment(payload: CommentCreate, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)) -> Comment:
    """Create a workspace comment and mirror it into audit history."""

    workspace = db.get(Workspace, payload.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    require_workspace_role(db, payload.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst})
    comment = Comment(
        workspace_id=payload.workspace_id,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        user_email=payload.user_email,
        message=payload.message,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    audit_service.log_event(payload.workspace_id, "comment.created", actor=payload.user_email, resource_type=payload.resource_type, resource_id=payload.resource_id, details=payload.message)
    return comment


@router.post("/shares", response_model=ShareRead, status_code=201)
def create_share(payload: ShareCreate, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)) -> Share:
    """Grant a user access to a shared workspace resource."""

    workspace = db.get(Workspace, payload.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    require_workspace_role(db, payload.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin})
    share = Share(
        workspace_id=payload.workspace_id,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        target_email=payload.target_email,
        permission=payload.permission,
    )
    db.add(share)
    db.commit()
    db.refresh(share)
    audit_service.log_event(payload.workspace_id, "share.created", actor=payload.target_email, resource_type=payload.resource_type, resource_id=payload.resource_id, details=payload.permission)
    return share
