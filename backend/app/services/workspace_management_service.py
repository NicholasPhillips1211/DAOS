from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.metadata import Workspace, WorkspaceMembership


class WorkspaceManagementService:
    """Own workspace registry and membership persistence."""

    def list_workspaces(self, db: Session) -> list[Workspace]:
        """Return workspaces newest-first for workspace pickers."""

        return db.query(Workspace).order_by(Workspace.created_at.desc()).all()

    def create_workspace(self, db: Session, *, name: str, description: str | None) -> Workspace:
        """Create a workspace because it is the root record for all downstream artifacts."""

        workspace = Workspace(name=name, description=description)
        db.add(workspace)
        db.commit()
        db.refresh(workspace)
        return workspace

    def add_member(self, db: Session, *, workspace_id: int, user_email: str, role: str) -> WorkspaceMembership:
        """Attach a user to an existing workspace using the caller-provided role."""

        workspace = db.get(Workspace, workspace_id)
        if workspace is None:
            raise HTTPException(status_code=404, detail="Workspace not found")

        membership = WorkspaceMembership(workspace_id=workspace_id, user_email=user_email, role=role)
        db.add(membership)
        db.commit()
        db.refresh(membership)
        return membership
