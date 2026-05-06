from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.metadata import Workspace, WorkspaceMembership
from app.schemas.workspace import MembershipCreate, MembershipRead, WorkspaceCreate, WorkspaceRead

router = APIRouter()


def get_db() -> Session:
    """Yield a short-lived database session for request-scoped operations."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[WorkspaceRead])
def list_workspaces(db: Session = Depends(get_db)) -> list[Workspace]:
    """List workspaces newest-first so the freshest project is easiest to find."""

    return db.query(Workspace).order_by(Workspace.created_at.desc()).all()


@router.post("", response_model=WorkspaceRead, status_code=201)
def create_workspace(payload: WorkspaceCreate, db: Session = Depends(get_db)) -> Workspace:
    """Create a workspace because every other artifact hangs off this root record."""

    workspace = Workspace(name=payload.name, description=payload.description)
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace


@router.post("/{workspace_id}/members", response_model=MembershipRead, status_code=201)
def add_member(workspace_id: int, payload: MembershipCreate, db: Session = Depends(get_db)) -> WorkspaceMembership:
    """Attach a user to a workspace with a role used by downstream RBAC checks."""

    workspace = db.get(Workspace, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    membership = WorkspaceMembership(workspace_id=workspace_id, user_email=payload.user_email, role=payload.role)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership
