from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.auth import Principal, get_current_principal, require_workspace_role
from app.models.automation import AutomationPlan
from app.models.metadata import WorkspaceRole
from app.schemas.automation import AutomationGenerateRequest, AutomationPlanRead
from app.services.automation_service import AutomationService, AutomationExecutor
from app.services.automation_workflow_service import AutomationWorkflowService

router = APIRouter()
automation_service = AutomationService()
automation_executor = AutomationExecutor()
automation_workflow_service = AutomationWorkflowService(automation_service, automation_executor)



@router.get("", response_model=list[AutomationPlanRead])
def list_plans(
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
    workspace_id: int | None = None,
) -> list[AutomationPlan]:
    """List automation plans newest-first, optionally scoped to one workspace."""

    if workspace_id is not None:
        require_workspace_role(db, workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst, WorkspaceRole.viewer})
    return automation_workflow_service.list_plans(db, workspace_id)


@router.post("/generate", response_model=AutomationPlanRead, status_code=201)
def generate_plan(
    payload: AutomationGenerateRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> AutomationPlan:
    """Generate and persist an automation plan for a workspace objective."""

    require_workspace_role(db, payload.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst})
    return automation_workflow_service.generate_plan(db, payload.workspace_id, payload.objective)


@router.get("/{plan_id}", response_model=AutomationPlanRead)
def get_plan(plan_id: int, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)) -> AutomationPlan:
    """Fetch a stored automation plan by id."""

    plan = automation_workflow_service.get_plan_or_404(db, plan_id)
    require_workspace_role(db, plan.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst, WorkspaceRole.viewer})
    return plan


@router.post("/{plan_id}/execute", response_model=AutomationPlanRead)
def execute_plan(plan_id: int, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)) -> AutomationPlan:
    """Execute the automation plan actions and update the plan with results."""

    plan = automation_workflow_service.get_plan_or_404(db, plan_id)
    require_workspace_role(db, plan.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst})

    return automation_workflow_service.execute_plan(db, plan)
