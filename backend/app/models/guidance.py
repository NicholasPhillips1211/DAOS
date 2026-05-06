"""Domain model for generated project guidance plans."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class GuidancePlan(Base):
    """Persist KPI, milestone, and risk guidance for a workspace."""

    __tablename__ = "guidance_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    objective: Mapped[str] = mapped_column(String(255), nullable=False)
    kpis_json: Mapped[str] = mapped_column(Text, nullable=False)
    milestones_json: Mapped[str] = mapped_column(Text, nullable=False)
    risks_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
