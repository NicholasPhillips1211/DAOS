from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_workspace_role
from app.models.metadata import Workspace, WorkspaceRole
from app.models.recommendation import Recommendation
from app.services.recommendation_service import RecommendationService


class RecommendationWorkflowService:
    """Wrap workspace recommendation generation and retrieval behind a stable API."""

    def __init__(self, recommendation_service: RecommendationService) -> None:
        self.recommendation_service = recommendation_service

    def generate(self, db: Session, workspace_id: int, principal: Principal) -> list[Recommendation]:
        """Validate access and generate recommendations from workspace maturity signals."""

        workspace = db.get(Workspace, workspace_id)
        if workspace is None:
            raise HTTPException(status_code=404, detail="Workspace not found")
        require_workspace_role(db, workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst})
        return self.recommendation_service.generate_for_workspace(db, workspace_id)

    def list(self, db: Session, workspace_id: int, principal: Principal) -> list[Recommendation]:
        """List recommendations newest-first for the requested workspace."""

        workspace = db.get(Workspace, workspace_id)
        if workspace is None:
            raise HTTPException(status_code=404, detail="Workspace not found")
        require_workspace_role(db, workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst, WorkspaceRole.viewer})
        return (
            db.query(Recommendation)
            .filter(Recommendation.workspace_id == workspace_id)
            .order_by(Recommendation.created_at.desc())
            .all()
        )
