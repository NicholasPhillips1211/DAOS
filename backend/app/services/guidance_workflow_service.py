from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_workspace_role
from app.models.guidance import GuidancePlan
from app.models.metadata import Workspace, WorkspaceRole
from app.services.guidance_service import GuidanceService


class GuidanceWorkflowService:
    """Handle guidance-plan orchestration and storage through one interface."""

    def __init__(self, guidance_service: GuidanceService) -> None:
        self.guidance_service = guidance_service

    def generate_plan(self, db: Session, *, workspace_id: int, objective: str, principal: Principal) -> GuidancePlan:
        """Validate access, confirm the workspace exists, and persist a generated plan."""

        if db.get(Workspace, workspace_id) is None:
            raise HTTPException(status_code=404, detail="Workspace not found")
        require_workspace_role(db, workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst})
        return self.guidance_service.generate_plan(db, workspace_id, objective)

    def get_plan(self, db: Session, plan_id: int, principal: Principal) -> GuidancePlan:
        """Load a guidance plan and enforce the same workspace role gate used elsewhere."""

        plan = db.get(GuidancePlan, plan_id)
        if plan is None:
            raise HTTPException(status_code=404, detail="Guidance plan not found")
        require_workspace_role(db, plan.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst, WorkspaceRole.viewer})
        return plan