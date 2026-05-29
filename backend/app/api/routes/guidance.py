from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.auth import Principal, get_current_principal
from app.models.guidance import GuidancePlan
from app.schemas.guidance import GuidanceGenerateRequest, GuidancePlanRead
from app.services.guidance_service import GuidanceService
from app.services.guidance_workflow_service import GuidanceWorkflowService

router = APIRouter()
service = GuidanceService()
workflow_service = GuidanceWorkflowService(service)


@router.post("/generate", response_model=GuidancePlanRead, status_code=201)
def generate_guidance(
    payload: GuidanceGenerateRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> GuidancePlan:
    """Create an execution plan that blends current maturity and desired outcomes."""

    return workflow_service.generate_plan(db, workspace_id=payload.workspace_id, objective=payload.objective, principal=principal)


@router.get("/{plan_id}", response_model=GuidancePlanRead)
def get_guidance_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> GuidancePlan:
    """Return a generated guidance plan so the UI can re-display it later."""

    return workflow_service.get_plan(db, plan_id, principal)
