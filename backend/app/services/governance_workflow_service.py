from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.governance import AuditEvent, DataMask
from app.models.metadata import Workspace


class GovernanceWorkflowService:
    """Group governance persistence/query workflows behind a stable API."""

    def list_audit_events(self, db: Session, workspace_id: int) -> list[AuditEvent]:
        """Return workspace audit events newest-first for review surfaces."""
        return (
            db.query(AuditEvent)
            .filter(AuditEvent.workspace_id == workspace_id)
            .order_by(AuditEvent.created_at.desc())
            .limit(50)
            .offset(0)
            .all()
        )

    def list_audit_events_paginated(self, db: Session, workspace_id: int, limit: int = 50, offset: int = 0) -> list[AuditEvent]:
        return (
            db.query(AuditEvent)
            .filter(AuditEvent.workspace_id == workspace_id)
            .order_by(AuditEvent.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def count_audit_events(self, db: Session, workspace_id: int) -> int:
        return db.query(AuditEvent).filter(AuditEvent.workspace_id == workspace_id).count()

    def create_data_mask(self, db: Session, *, workspace_id: int, dataset_id: int, column_name: str, mask_type: str) -> DataMask:
        """Persist a masking rule after verifying the workspace parent exists."""

        if db.get(Workspace, workspace_id) is None:
            raise HTTPException(status_code=404, detail="Workspace not found")

        mask = DataMask(
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            column_name=column_name,
            mask_type=mask_type,
        )
        db.add(mask)
        db.commit()
        db.refresh(mask)
        return mask
