from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.auth import Principal, get_current_principal, require_workspace_role
from app.models.collaboration import Comment, Share
from app.models.metadata import WorkspaceRole
from app.schemas.collaboration import CommentCreate, CommentRead, ShareCreate, ShareRead
from app.services.audit_service import AuditService
from app.services.collaboration_workflow_service import CollaborationWorkflowService

router = APIRouter()
audit_service = AuditService()
collaboration_workflow_service = CollaborationWorkflowService()


@router.post("/comments", response_model=CommentRead, status_code=201)
def create_comment(payload: CommentCreate, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)) -> Comment:
    """Create a workspace comment and mirror it into audit history."""

    require_workspace_role(db, payload.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst})
    comment = collaboration_workflow_service.create_comment(
        db,
        workspace_id=payload.workspace_id,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        user_email=payload.user_email,
        message=payload.message,
    )
    audit_service.log_event(payload.workspace_id, "comment.created", actor=payload.user_email, resource_type=payload.resource_type, resource_id=payload.resource_id, details=payload.message)
    return comment


@router.post("/shares", response_model=ShareRead, status_code=201)
def create_share(payload: ShareCreate, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)) -> Share:
    """Grant a user access to a shared workspace resource."""

    require_workspace_role(db, payload.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin})
    share = collaboration_workflow_service.create_share(
        db,
        workspace_id=payload.workspace_id,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        target_email=payload.target_email,
        permission=payload.permission,
    )
    audit_service.log_event(payload.workspace_id, "share.created", actor=payload.target_email, resource_type=payload.resource_type, resource_id=payload.resource_id, details=payload.permission)
    return share
