from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.metadata import Workspace, WorkspaceMembership
from app.schemas.workspace import (
    MembershipCreate,
    MembershipRead,
    WorkspaceCreate,
    WorkspaceRead,
    WorkspaceSummaryRead,
)
from app.services.workspace_management_service import WorkspaceManagementService

router = APIRouter()
workspace_management_service = WorkspaceManagementService()


@router.get("", response_model=list[WorkspaceRead])
def list_workspaces(db: Session = Depends(get_db)) -> list[Workspace]:
    """List workspaces newest-first so the freshest project is easiest to find."""

    return workspace_management_service.list_workspaces(db)


@router.post("", response_model=WorkspaceRead, status_code=201)
def create_workspace(payload: WorkspaceCreate, db: Session = Depends(get_db)) -> Workspace:
    """Create a workspace because every other artifact hangs off this root record."""

    return workspace_management_service.create_workspace(db, name=payload.name, description=payload.description)


@router.post("/{workspace_id}/members", response_model=MembershipRead, status_code=201)
def add_member(workspace_id: int, payload: MembershipCreate, db: Session = Depends(get_db)) -> WorkspaceMembership:
    """Attach a user to a workspace with a role used by downstream RBAC checks."""

    return workspace_management_service.add_member(db, workspace_id=workspace_id, user_email=payload.user_email, role=payload.role)


@router.get("/{workspace_id}/summary", response_model=WorkspaceSummaryRead)
def get_workspace_summary(workspace_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    """Return onboarding signals for the active workspace."""

    return workspace_management_service.get_workspace_summary(db, workspace_id=workspace_id)
