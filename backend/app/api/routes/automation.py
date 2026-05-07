from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.routes.workspaces import get_db
from app.core.auth import Principal, get_current_principal, require_workspace_role
from app.models.automation import AutomationPlan
from app.models.metadata import Workspace, WorkspaceRole
from app.schemas.automation import AutomationGenerateRequest, AutomationPlanRead
from app.services.automation_service import AutomationService, AutomationExecutor

router = APIRouter()
automation_service = AutomationService()
automation_executor = AutomationExecutor()



@router.get("", response_model=list[AutomationPlanRead])
def list_plans(
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
    workspace_id: int | None = None,
) -> list[AutomationPlan]:
    """List automation plans newest-first, optionally scoped to one workspace."""

    if workspace_id is not None:
        require_workspace_role(db, workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst, WorkspaceRole.viewer})
        return db.query(AutomationPlan).filter(AutomationPlan.workspace_id == workspace_id).order_by(AutomationPlan.created_at.desc()).all()
    return db.query(AutomationPlan).order_by(AutomationPlan.created_at.desc()).all()


@router.post("/generate", response_model=AutomationPlanRead, status_code=201)
def generate_plan(
    payload: AutomationGenerateRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> AutomationPlan:
    """Generate and persist an automation plan for a workspace objective."""

    workspace = db.get(Workspace, payload.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    require_workspace_role(db, payload.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst})
    return automation_service.generate_plan(db, payload.workspace_id, payload.objective)


@router.get("/{plan_id}", response_model=AutomationPlanRead)
def get_plan(plan_id: int, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)) -> AutomationPlan:
    """Fetch a stored automation plan by id."""

    plan = db.get(AutomationPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Automation plan not found")
    require_workspace_role(db, plan.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst, WorkspaceRole.viewer})
    return plan


@router.post("/{plan_id}/execute", response_model=AutomationPlanRead)
def execute_plan(plan_id: int, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)) -> AutomationPlan:
    """Execute the automation plan actions and update the plan with results."""

    plan = db.get(AutomationPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Automation plan not found")
    require_workspace_role(db, plan.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst})

    automation_executor.execute_plan(db, plan)
    db.refresh(plan)
    return plan
