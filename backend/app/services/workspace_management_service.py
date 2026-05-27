from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.metadata import Dataset, Workspace, WorkspaceMembership, WorkspaceRole
from app.services.audit_service import AuditService


class WorkspaceManagementService:
    """Own workspace registry and membership persistence."""

    def __init__(self):
        self.audit_service = AuditService()

    def list_workspaces(self, db: Session, *, user_email: str | None = None) -> list[Workspace]:
        """Return workspaces newest-first for workspace pickers."""

        query = db.query(Workspace)
        if settings.auth_enabled and user_email is not None:
            query = query.join(WorkspaceMembership).filter(WorkspaceMembership.user_email == user_email).distinct()
        return query.order_by(Workspace.created_at.desc()).all()

    def create_workspace(self, db: Session, *, name: str, description: str | None, owner_email: str | None = None) -> Workspace:
        """Create a workspace because it is the root record for all downstream artifacts."""

        workspace = Workspace(name=name, description=description)
        db.add(workspace)
        db.flush()

        if owner_email:
            membership = WorkspaceMembership(workspace_id=workspace.id, user_email=owner_email, role=WorkspaceRole.owner)
            db.add(membership)

        db.commit()
        db.refresh(workspace)

        self.audit_service.log_event(
            workspace_id=workspace.id,
            event_type="workspace.created",
            actor=owner_email,
            resource_type="workspace",
            resource_id=workspace.id,
            details=f"Workspace '{name}' created.",
            db=db,
        )

        return workspace

    def add_member(
        self,
        db: Session,
        *,
        workspace_id: int,
        user_email: str,
        role: str,
        actor_email: str | None = None,
    ) -> WorkspaceMembership:
        """Attach a user to an existing workspace using the caller-provided role."""

        workspace = db.get(Workspace, workspace_id)
        if workspace is None:
            raise HTTPException(status_code=404, detail="Workspace not found")

        membership = WorkspaceMembership(workspace_id=workspace_id, user_email=user_email, role=role)
        db.add(membership)
        db.commit()
        db.refresh(membership)

        self.audit_service.log_event(
            workspace_id=workspace_id,
            event_type="workspace.member_added",
            actor=actor_email,
            resource_type="workspace",
            resource_id=workspace_id,
            details=f"User {user_email} added with role {role}.",
            db=db,
        )

        return membership

    def get_workspace_summary(self, db: Session, *, workspace_id: int) -> dict[str, object]:
        """Return onboarding signals that help the UI guide the next workflow step."""

        workspace = db.get(Workspace, workspace_id)
        if workspace is None:
            raise HTTPException(status_code=404, detail="Workspace not found")

        dataset_query = db.query(Dataset).filter(Dataset.workspace_id == workspace_id).order_by(Dataset.created_at.desc())
        recent_datasets = dataset_query.limit(3).all()
        dataset_count = db.query(func.count(Dataset.id)).filter(Dataset.workspace_id == workspace_id).scalar() or 0
        membership_count = db.query(func.count(WorkspaceMembership.id)).filter(WorkspaceMembership.workspace_id == workspace_id).scalar() or 0

        latest_dataset = recent_datasets[0] if recent_datasets else None
        recommended_next_action = (
            "Upload a CSV to create the first dataset and unlock query analysis."
            if dataset_count == 0
            else f"Open {latest_dataset.name if latest_dataset else 'the latest dataset'} and run SQL to refine the workspace."
        )

        return {
            "workspace_id": workspace.id,
            "workspace_name": workspace.name,
            "workspace_description": workspace.description,
            "dataset_count": dataset_count,
            "membership_count": membership_count,
            "has_datasets": dataset_count > 0,
            "recommended_next_action": recommended_next_action,
            "recent_datasets": recent_datasets,
            "latest_dataset": latest_dataset,
        }
