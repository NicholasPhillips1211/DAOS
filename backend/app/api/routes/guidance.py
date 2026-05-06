from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.routes.workspaces import get_db
from app.core.auth import Principal, get_current_principal, require_workspace_role
from app.models.guidance import GuidancePlan
from app.models.metadata import Workspace
from app.models.metadata import WorkspaceRole
from app.schemas.guidance import GuidanceGenerateRequest, GuidancePlanRead
from app.services.guidance_service import GuidanceService

router = APIRouter()
service = GuidanceService()


@router.post("/generate", response_model=GuidancePlanRead, status_code=201)
def generate_guidance(
    payload: GuidanceGenerateRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> GuidancePlan:
    """Create an execution plan that blends current maturity and desired outcomes."""

    workspace = db.get(Workspace, payload.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    require_workspace_role(db, payload.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst})
    return service.generate_plan(db, payload.workspace_id, payload.objective)


@router.get("/{plan_id}", response_model=GuidancePlanRead)
def get_guidance_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> GuidancePlan:
    """Return a generated guidance plan so the UI can re-display it later."""

    plan = db.get(GuidancePlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Guidance plan not found")
    require_workspace_role(db, plan.workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst, WorkspaceRole.viewer})
    return plan
