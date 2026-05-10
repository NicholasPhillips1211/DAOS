from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.auth import Principal, get_current_principal
from app.models.recommendation import Recommendation
from app.schemas.recommendation import RecommendationGenerateResponse, RecommendationRead
from app.services.recommendation_service import RecommendationService
from app.services.recommendation_workflow_service import RecommendationWorkflowService

router = APIRouter()
service = RecommendationService()
workflow_service = RecommendationWorkflowService(service)


@router.post("/generate", response_model=RecommendationGenerateResponse)
def generate_recommendations(
    workspace_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> RecommendationGenerateResponse:
    """Generate action recommendations from the workspace's current maturity signals."""

    created = workflow_service.generate(db, workspace_id, principal)
    return RecommendationGenerateResponse(created_count=len(created), recommendations=created)


@router.get("", response_model=list[RecommendationRead])
def list_recommendations(
    workspace_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> list[Recommendation]:
    """Return previously generated recommendations for the workspace."""

    return workflow_service.list(db, workspace_id, principal)
