from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import (
    Principal,
    WORKSPACE_READ_ROLES,
    WORKSPACE_WRITE_ROLES,
    get_current_principal,
    require_model_workspace_role,
    require_workspace_role,
)
from app.core.dependencies import get_db
from app.models.analysis import Insight
from app.models.business import BusinessTranslation
from app.schemas.business import BusinessTranslationCreate, BusinessTranslationRead
from app.services.business_service import BusinessTranslationService
from app.services.business_workflow_service import BusinessWorkflowService

router = APIRouter()
service = BusinessTranslationService()
workflow_service = BusinessWorkflowService(service)


@router.post("/translate", response_model=BusinessTranslationRead, status_code=201)
def translate(
    payload: BusinessTranslationCreate,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> BusinessTranslation:
    """Translate a technical insight into a stored business-facing summary."""

    require_workspace_role(db, payload.workspace_id, principal, WORKSPACE_WRITE_ROLES)
    insight = require_model_workspace_role(db, Insight, payload.insight_id, principal, WORKSPACE_READ_ROLES, model_name="Insight")
    if insight.workspace_id != payload.workspace_id:
        raise HTTPException(status_code=400, detail="Insight does not belong to the requested workspace")

    return workflow_service.translate(
        db,
        workspace_id=payload.workspace_id,
        insight_id=payload.insight_id,
        audience=payload.audience,
    )


@router.get("/{translation_id}", response_model=BusinessTranslationRead)
def get_translation(
    translation_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> BusinessTranslation:
    """Fetch one generated business translation by id."""

    return require_model_workspace_role(
        db,
        BusinessTranslation,
        translation_id,
        principal,
        WORKSPACE_READ_ROLES,
        model_name="Translation",
    )
