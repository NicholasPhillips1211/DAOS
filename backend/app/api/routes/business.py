from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.business import BusinessTranslation
from app.schemas.business import BusinessTranslationCreate, BusinessTranslationRead
from app.services.business_service import BusinessTranslationService
from app.services.business_workflow_service import BusinessWorkflowService

router = APIRouter()
service = BusinessTranslationService()
workflow_service = BusinessWorkflowService(service)


@router.post("/translate", response_model=BusinessTranslationRead, status_code=201)
def translate(payload: BusinessTranslationCreate, db: Session = Depends(get_db)) -> BusinessTranslation:
    """Translate a technical insight into a stored business-facing summary."""

    return workflow_service.translate(
        db,
        workspace_id=payload.workspace_id,
        insight_id=payload.insight_id,
        audience=payload.audience,
    )


@router.get("/{translation_id}", response_model=BusinessTranslationRead)
def get_translation(translation_id: int, db: Session = Depends(get_db)) -> BusinessTranslation:
    """Fetch one generated business translation by id."""

    return workflow_service.get_translation(db, translation_id)
