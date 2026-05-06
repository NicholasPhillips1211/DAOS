"""Domain model for persisted trained machine learning artifacts."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TrainedModel(Base):
    """Store the metadata needed to describe a trained model artifact."""

    __tablename__ = "trained_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_column: Mapped[str] = mapped_column(String(255), nullable=False)
    task_type: Mapped[str] = mapped_column(String(32), nullable=False)
    model_type: Mapped[str] = mapped_column(String(64), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(64), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    train_score: Mapped[float] = mapped_column(Float, nullable=False)
    test_score: Mapped[float] = mapped_column(Float, nullable=False)
    overfit_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    artifact_path: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())