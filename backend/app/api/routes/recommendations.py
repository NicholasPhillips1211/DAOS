from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.auth import Principal, get_current_principal, require_workspace_role
from app.models.metadata import Workspace
from app.models.metadata import WorkspaceRole
from app.models.recommendation import Recommendation
from app.schemas.recommendation import RecommendationGenerateResponse, RecommendationRead
from app.services.recommendation_service import RecommendationService

router = APIRouter()
service = RecommendationService()


@router.post("/generate", response_model=RecommendationGenerateResponse)
def generate_recommendations(
    workspace_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> RecommendationGenerateResponse:
    """Generate action recommendations from the workspace's current maturity signals."""

    workspace = db.get(Workspace, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    require_workspace_role(db, workspace_id, principal, {WorkspaceRole.owner, WorkspaceRole.admin, WorkspaceRole.analyst})
    created = service.generate_for_workspace(db, workspace_id)
    return RecommendationGenerateResponse(created_count=len(created), recommendations=created)


@router.get("", response_model=list[RecommendationRead])
def list_recommendations(
    workspace_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> list[Recommendation]:
    """Return previously generated recommendations for the workspace."""

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
