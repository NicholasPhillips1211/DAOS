from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.automation import AutomationPlan
from app.models.metadata import Workspace
from app.services.automation_service import AutomationExecutor, AutomationService


class AutomationWorkflowService:
    """Encapsulate automation-plan lifecycle operations.

    The route layer enforces auth/RBAC, while this workflow layer owns existence
    checks and service orchestration for consistent behavior across endpoints.
    """

    def __init__(self, automation_service: AutomationService, automation_executor: AutomationExecutor) -> None:
        self.automation_service = automation_service
        self.automation_executor = automation_executor

    def list_plans(self, db: Session, workspace_id: int | None = None) -> list[AutomationPlan]:
        """Return plans newest-first, optionally scoped to a workspace."""

        query = db.query(AutomationPlan)
        if workspace_id is not None:
            query = query.filter(AutomationPlan.workspace_id == workspace_id)
        return query.order_by(AutomationPlan.created_at.desc()).all()

    def generate_plan(self, db: Session, workspace_id: int, objective: str) -> AutomationPlan:
        """Validate workspace parent then delegate plan generation."""

        if db.get(Workspace, workspace_id) is None:
            raise HTTPException(status_code=404, detail="Workspace not found")
        return self.automation_service.generate_plan(db, workspace_id, objective)

    def get_plan_or_404(self, db: Session, plan_id: int) -> AutomationPlan:
        """Load a plan by id with a consistent 404 contract."""

        plan = db.get(AutomationPlan, plan_id)
        if plan is None:
            raise HTTPException(status_code=404, detail="Automation plan not found")
        return plan

    def execute_plan(self, db: Session, plan: AutomationPlan) -> AutomationPlan:
        """Execute and refresh plan state so callers get updated execution fields."""

        self.automation_executor.execute_plan(db, plan)
        db.refresh(plan)
        return plan
