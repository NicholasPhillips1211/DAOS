from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.collaboration import Comment, Share
from app.models.metadata import Workspace


class CollaborationWorkflowService:
    """Coordinate collaboration writes so route handlers stay transport-focused.

    Comments and shares share the same workspace existence guard and persistence
    shape, so centralizing this avoids drift across endpoints.
    """

    def _require_workspace(self, db: Session, workspace_id: int) -> None:
        if db.get(Workspace, workspace_id) is None:
            raise HTTPException(status_code=404, detail="Workspace not found")

    def create_comment(self, db: Session, *, workspace_id: int, resource_type: str, resource_id: int, user_email: str, message: str) -> Comment:
        """Persist a workspace comment after validating workspace existence."""

        self._require_workspace(db, workspace_id)
        comment = Comment(
            workspace_id=workspace_id,
            resource_type=resource_type,
            resource_id=resource_id,
            user_email=user_email,
            message=message,
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return comment

    def create_share(self, db: Session, *, workspace_id: int, resource_type: str, resource_id: int, target_email: str, permission: str) -> Share:
        """Persist a share grant for a workspace resource after parent validation."""

        self._require_workspace(db, workspace_id)
        share = Share(
            workspace_id=workspace_id,
            resource_type=resource_type,
            resource_id=resource_id,
            target_email=target_email,
            permission=permission,
        )
        db.add(share)
        db.commit()
        db.refresh(share)
        return share
