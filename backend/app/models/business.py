"""Domain models for business-facing translations of technical insights."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BusinessTranslation(Base):
    """Store a business summary, audience, and recommendation payload."""

    __tablename__ = "business_translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    insight_id: Mapped[int] = mapped_column(ForeignKey("insights.id", ondelete="SET NULL"), nullable=True, index=True)
    audience: Mapped[str] = mapped_column(String(100), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    recommendations_json: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
