"""Core metadata models that anchor workspaces, datasets, and membership."""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class WorkspaceRole(str, Enum):
    """Workspace permission levels used by the RBAC layer."""

    owner = "owner"
    admin = "admin"
    analyst = "analyst"
    viewer = "viewer"


class Workspace(Base):
    """Root container for a team, project, or analyst workspace."""

    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    memberships: Mapped[list["WorkspaceMembership"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")


class WorkspaceMembership(Base):
    """Bind a user email to a workspace and role for authorization checks."""

    __tablename__ = "workspace_memberships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    role: Mapped[WorkspaceRole] = mapped_column(SAEnum(WorkspaceRole), nullable=False, default=WorkspaceRole.viewer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    workspace: Mapped[Workspace] = relationship(back_populates="memberships")


class DatasetState(str, Enum):
    """Lifecycle states for datasets as they move through the platform."""

    raw = "raw"
    cleansed = "cleansed"
    curated = "curated"


class Dataset(Base):
    """Register a dataset and the storage path that backs it."""

    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[DatasetState] = mapped_column(SAEnum(DatasetState), nullable=False, default=DatasetState.raw)
    storage_path: Mapped[str | None] = mapped_column(String(1024))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    workspace: Mapped[Workspace] = relationship()
