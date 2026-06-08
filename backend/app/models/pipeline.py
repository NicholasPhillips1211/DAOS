"""Domain models for pipeline definitions, versions, and execution history."""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.workflow_status import WorkflowStatus
from app.core.database import Base


class PipelineStatus(str, Enum):
    """Lifecycle states used to track pipeline execution and scheduling."""

    draft = WorkflowStatus.draft.value
    scheduled = WorkflowStatus.scheduled.value
    running = WorkflowStatus.running.value
    succeeded = WorkflowStatus.succeeded.value
    failed = WorkflowStatus.failed.value


class Pipeline(Base):
    """Store the top-level pipeline record used by the orchestration layer."""

    __tablename__ = "pipelines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    schedule_cron: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[PipelineStatus] = mapped_column(SAEnum(PipelineStatus), nullable=False, default=PipelineStatus.draft)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    versions: Mapped[list["PipelineVersion"]] = relationship(back_populates="pipeline", cascade="all, delete-orphan")


class PipelineVersion(Base):
    """Persist an immutable version of a pipeline definition."""

    __tablename__ = "pipeline_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pipeline_id: Mapped[int] = mapped_column(ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    definition_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    pipeline: Mapped[Pipeline] = relationship(back_populates="versions")


class PipelineRun(Base):
    """Track one execution attempt so users can inspect run history."""

    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pipeline_id: Mapped[int] = mapped_column(ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[PipelineStatus] = mapped_column(SAEnum(PipelineStatus), nullable=False, default=PipelineStatus.running)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    log_message: Mapped[str | None] = mapped_column(Text)
