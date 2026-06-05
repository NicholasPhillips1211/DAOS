import json
from typing import Any

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.auth import (
    Principal,
    WORKSPACE_READ_ROLES,
    WORKSPACE_WRITE_ROLES,
    get_current_principal,
    require_workspace_role,
    require_workspace_scope,
)
from app.core.dependencies import get_db, get_pagination
from app.models.automation import AutomationPlan
from app.schemas.automation import AutomationGenerateRequest, AutomationPlanRead
from app.schemas.work_item import WorkItemSubmitRead
from app.services.automation_service import AutomationService, AutomationExecutor
from app.services.automation_workflow_service import AutomationWorkflowService
from app.services.metadata_service import MetadataService
from app.services.work_queue_service import WorkQueueService

router = APIRouter()
automation_service = AutomationService()
automation_executor = AutomationExecutor()
automation_workflow_service = AutomationWorkflowService(automation_service, automation_executor)
metadata_service = MetadataService()
work_queue_service = WorkQueueService()



@router.get("", response_model=list[AutomationPlanRead])
def list_plans(
    response: Response,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
    workspace_id: int | None = None,
    pagination: dict = Depends(get_pagination),
) -> list[AutomationPlan]:
    """List automation plans newest-first, optionally scoped to one workspace."""

    require_workspace_scope(workspace_id)
    if workspace_id is not None:
        require_workspace_role(db, workspace_id, principal, WORKSPACE_READ_ROLES)
    total = automation_workflow_service.count_plans(db, workspace_id)
    response.headers["X-Total-Count"] = str(total)
    return automation_workflow_service.list_plans(db, workspace_id, limit=pagination["limit"], offset=pagination["offset"])


@router.post("/generate", response_model=AutomationPlanRead, status_code=201)
async def generate_plan(
    payload: AutomationGenerateRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> AutomationPlan:
    """Generate and persist an automation plan for a workspace objective."""

    require_workspace_role(db, payload.workspace_id, principal, WORKSPACE_WRITE_ROLES)
    plan = await automation_workflow_service.generate_plan(db, payload.workspace_id, payload.objective)
    metadata_service.record_ai_context(
        db,
        workspace_id=plan.workspace_id,
        context_type="automation_plan",
        resource_type="automation_plan",
        resource_id=plan.id,
        actor=principal.user_email,
        context={
            "objective": plan.objective,
            "provider": plan.provider,
            "model_name": plan.model_name,
            "summary": plan.summary,
            "plan": _parse_automation_json(plan.automation_json),
        },
    )
    return plan


@router.post("/generate-jobs", response_model=WorkItemSubmitRead, status_code=status.HTTP_202_ACCEPTED)
def queue_generate_plan(
    payload: AutomationGenerateRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> WorkItemSubmitRead:
    """Queue automation-plan generation for a background worker."""

    require_workspace_role(db, payload.workspace_id, principal, WORKSPACE_WRITE_ROLES)
    item = work_queue_service.enqueue(
        db,
        workspace_id=payload.workspace_id,
        job_type="automation.generate",
        payload={"workspace_id": payload.workspace_id, "objective": payload.objective, "actor": principal.user_email},
    )
    return WorkItemSubmitRead(
        work_item_id=item.id,
        workspace_id=item.workspace_id,
        job_type=item.job_type,
        status=item.status,
        created_at=item.created_at,
    )


@router.get("/{plan_id}", response_model=AutomationPlanRead)
def get_plan(plan_id: int, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)) -> AutomationPlan:
    """Fetch a stored automation plan by id."""

    plan = automation_workflow_service.get_plan_or_404(db, plan_id)
    require_workspace_role(db, plan.workspace_id, principal, WORKSPACE_READ_ROLES)
    return plan


@router.post("/{plan_id}/execute", response_model=AutomationPlanRead)
def execute_plan(plan_id: int, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)) -> AutomationPlan:
    """Execute the automation plan actions and update the plan with results."""

    plan = automation_workflow_service.get_plan_or_404(db, plan_id)
    require_workspace_role(db, plan.workspace_id, principal, WORKSPACE_WRITE_ROLES)

    return automation_workflow_service.execute_plan(db, plan)


@router.post("/{plan_id}/execute-jobs", response_model=WorkItemSubmitRead, status_code=status.HTTP_202_ACCEPTED)
def queue_execute_plan(plan_id: int, db: Session = Depends(get_db), principal: Principal = Depends(get_current_principal)) -> WorkItemSubmitRead:
    """Queue automation-plan execution for a background worker."""

    plan = automation_workflow_service.get_plan_or_404(db, plan_id)
    require_workspace_role(db, plan.workspace_id, principal, WORKSPACE_WRITE_ROLES)
    item = work_queue_service.enqueue(
        db,
        workspace_id=plan.workspace_id,
        job_type="automation.execute",
        payload={"plan_id": plan.id, "actor": principal.user_email},
    )
    return WorkItemSubmitRead(
        work_item_id=item.id,
        workspace_id=item.workspace_id,
        job_type=item.job_type,
        status=item.status,
        created_at=item.created_at,
    )


def _parse_automation_json(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {"value": parsed}
    except json.JSONDecodeError:
        return {"raw": value}
