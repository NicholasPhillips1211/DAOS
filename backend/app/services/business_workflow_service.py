from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.analysis import Insight
from app.models.business import BusinessTranslation
from app.models.metadata import Workspace
from app.services.business_service import BusinessTranslationService


class BusinessWorkflowService:
    """Coordinate insight-to-business-language translation workflows."""

    def __init__(self, business_translation_service: BusinessTranslationService) -> None:
        self.business_translation_service = business_translation_service

    def translate(self, db: Session, *, workspace_id: int, insight_id: int, audience: str) -> BusinessTranslation:
        """Validate parent records, generate text, and persist the business summary."""

        if db.get(Workspace, workspace_id) is None:
            raise HTTPException(status_code=404, detail="Workspace not found")
        insight = db.get(Insight, insight_id)
        if insight is None:
            raise HTTPException(status_code=404, detail="Insight not found")
        if insight.workspace_id != workspace_id:
            raise HTTPException(status_code=400, detail="Insight does not belong to the requested workspace")

        summary, recommendations = self.business_translation_service.generate(insight, audience)
        translation = BusinessTranslation(
            workspace_id=workspace_id,
            insight_id=insight_id,
            audience=audience,
            summary=summary,
            recommendations_json=recommendations,
        )
        db.add(translation)
        db.commit()
        db.refresh(translation)
        return translation

    def get_translation(self, db: Session, translation_id: int) -> BusinessTranslation:
        """Return a stored translation or raise a standard not-found error."""

        translation = db.get(BusinessTranslation, translation_id)
        if translation is None:
            raise HTTPException(status_code=404, detail="Translation not found")
        return translation
