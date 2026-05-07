from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.business import BusinessTranslation
from app.models.analysis import Insight
from app.models.metadata import Workspace
from app.schemas.business import BusinessTranslationCreate, BusinessTranslationRead
from app.services.business_service import BusinessTranslationService

router = APIRouter()
service = BusinessTranslationService()


@router.post("/translate", response_model=BusinessTranslationRead, status_code=201)
def translate(payload: BusinessTranslationCreate, db: Session = Depends(get_db)) -> BusinessTranslation:
    """Translate a technical insight into a stored business-facing summary."""

    workspace = db.get(Workspace, payload.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    insight = db.get(Insight, payload.insight_id)
    if insight is None:
        raise HTTPException(status_code=404, detail="Insight not found")

    summary, recommendations = service.generate(insight, payload.audience)
    bt = BusinessTranslation(
        workspace_id=payload.workspace_id,
        insight_id=payload.insight_id,
        audience=payload.audience,
        summary=summary,
        recommendations_json=recommendations,
    )
    db.add(bt)
    db.commit()
    db.refresh(bt)
    return bt


@router.get("/{translation_id}", response_model=BusinessTranslationRead)
def get_translation(translation_id: int, db: Session = Depends(get_db)) -> BusinessTranslation:
    """Fetch one generated business translation by id."""

    bt = db.get(BusinessTranslation, translation_id)
    if bt is None:
        raise HTTPException(status_code=404, detail="Translation not found")
    return bt
