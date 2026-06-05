from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.metadata import (
    MetadataAIContextRecord,
    MetadataLineageRecord,
    MetadataSchemaRecord,
    MetadataUsageEvent,
)


class MetadataRepository:
    """Persistence boundary for lifecycle metadata records."""

    def add_schema_record(
        self,
        db: Session,
        *,
        workspace_id: int,
        asset_type: str,
        asset_id: int,
        schema: list[dict[str, Any]],
        profile_fingerprint: str | None = None,
        source: str | None = None,
    ) -> MetadataSchemaRecord:
        record = MetadataSchemaRecord(
            workspace_id=workspace_id,
            asset_type=asset_type,
            asset_id=asset_id,
            schema_json=self._dump_json(schema),
            profile_fingerprint=profile_fingerprint,
            source=source,
        )
        db.add(record)
        return record

    def add_lineage_record(
        self,
        db: Session,
        *,
        workspace_id: int,
        upstream_type: str,
        upstream_id: int,
        downstream_type: str,
        downstream_id: int,
        relation_type: str,
        details: dict[str, Any] | None = None,
    ) -> MetadataLineageRecord:
        record = MetadataLineageRecord(
            workspace_id=workspace_id,
            upstream_type=upstream_type,
            upstream_id=upstream_id,
            downstream_type=downstream_type,
            downstream_id=downstream_id,
            relation_type=relation_type,
            details_json=self._dump_json(details or {}),
        )
        db.add(record)
        return record

    def add_usage_event(
        self,
        db: Session,
        *,
        workspace_id: int,
        asset_type: str,
        asset_id: int,
        action: str,
        actor: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> MetadataUsageEvent:
        record = MetadataUsageEvent(
            workspace_id=workspace_id,
            asset_type=asset_type,
            asset_id=asset_id,
            action=action,
            actor=actor,
            details_json=self._dump_json(details or {}),
        )
        db.add(record)
        return record

    def add_ai_context_record(
        self,
        db: Session,
        *,
        workspace_id: int,
        context_type: str,
        context: dict[str, Any],
        resource_type: str | None = None,
        resource_id: int | None = None,
        actor: str | None = None,
    ) -> MetadataAIContextRecord:
        record = MetadataAIContextRecord(
            workspace_id=workspace_id,
            context_type=context_type,
            resource_type=resource_type,
            resource_id=resource_id,
            actor=actor,
            context_json=self._dump_json(context),
        )
        db.add(record)
        return record

    def list_schema_records(
        self,
        db: Session,
        *,
        workspace_id: int,
        asset_type: str | None = None,
        asset_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MetadataSchemaRecord]:
        query = db.query(MetadataSchemaRecord).filter(MetadataSchemaRecord.workspace_id == workspace_id)
        if asset_type:
            query = query.filter(MetadataSchemaRecord.asset_type == asset_type)
        if asset_id is not None:
            query = query.filter(MetadataSchemaRecord.asset_id == asset_id)
        return query.order_by(MetadataSchemaRecord.created_at.desc()).limit(limit).offset(offset).all()

    def count_schema_records(
        self,
        db: Session,
        *,
        workspace_id: int,
        asset_type: str | None = None,
        asset_id: int | None = None,
    ) -> int:
        query = db.query(MetadataSchemaRecord).filter(MetadataSchemaRecord.workspace_id == workspace_id)
        if asset_type:
            query = query.filter(MetadataSchemaRecord.asset_type == asset_type)
        if asset_id is not None:
            query = query.filter(MetadataSchemaRecord.asset_id == asset_id)
        return query.count()

    def list_lineage_records(
        self,
        db: Session,
        *,
        workspace_id: int,
        asset_type: str | None = None,
        asset_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MetadataLineageRecord]:
        query = db.query(MetadataLineageRecord).filter(MetadataLineageRecord.workspace_id == workspace_id)
        if asset_type and asset_id is not None:
            query = query.filter(
                (
                    (MetadataLineageRecord.upstream_type == asset_type)
                    & (MetadataLineageRecord.upstream_id == asset_id)
                )
                | (
                    (MetadataLineageRecord.downstream_type == asset_type)
                    & (MetadataLineageRecord.downstream_id == asset_id)
                )
            )
        return query.order_by(MetadataLineageRecord.created_at.desc()).limit(limit).offset(offset).all()

    def count_lineage_records(
        self,
        db: Session,
        *,
        workspace_id: int,
        asset_type: str | None = None,
        asset_id: int | None = None,
    ) -> int:
        query = db.query(MetadataLineageRecord).filter(MetadataLineageRecord.workspace_id == workspace_id)
        if asset_type and asset_id is not None:
            query = query.filter(
                (
                    (MetadataLineageRecord.upstream_type == asset_type)
                    & (MetadataLineageRecord.upstream_id == asset_id)
                )
                | (
                    (MetadataLineageRecord.downstream_type == asset_type)
                    & (MetadataLineageRecord.downstream_id == asset_id)
                )
            )
        return query.count()

    def list_usage_events(
        self,
        db: Session,
        *,
        workspace_id: int,
        asset_type: str | None = None,
        asset_id: int | None = None,
        action: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MetadataUsageEvent]:
        query = db.query(MetadataUsageEvent).filter(MetadataUsageEvent.workspace_id == workspace_id)
        if asset_type:
            query = query.filter(MetadataUsageEvent.asset_type == asset_type)
        if asset_id is not None:
            query = query.filter(MetadataUsageEvent.asset_id == asset_id)
        if action:
            query = query.filter(MetadataUsageEvent.action == action)
        return query.order_by(MetadataUsageEvent.created_at.desc()).limit(limit).offset(offset).all()

    def count_usage_events(
        self,
        db: Session,
        *,
        workspace_id: int,
        asset_type: str | None = None,
        asset_id: int | None = None,
        action: str | None = None,
    ) -> int:
        query = db.query(MetadataUsageEvent).filter(MetadataUsageEvent.workspace_id == workspace_id)
        if asset_type:
            query = query.filter(MetadataUsageEvent.asset_type == asset_type)
        if asset_id is not None:
            query = query.filter(MetadataUsageEvent.asset_id == asset_id)
        if action:
            query = query.filter(MetadataUsageEvent.action == action)
        return query.count()

    def list_ai_context_records(
        self,
        db: Session,
        *,
        workspace_id: int,
        context_type: str | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MetadataAIContextRecord]:
        query = db.query(MetadataAIContextRecord).filter(MetadataAIContextRecord.workspace_id == workspace_id)
        if context_type:
            query = query.filter(MetadataAIContextRecord.context_type == context_type)
        if resource_type:
            query = query.filter(MetadataAIContextRecord.resource_type == resource_type)
        if resource_id is not None:
            query = query.filter(MetadataAIContextRecord.resource_id == resource_id)
        return query.order_by(MetadataAIContextRecord.created_at.desc()).limit(limit).offset(offset).all()

    def count_ai_context_records(
        self,
        db: Session,
        *,
        workspace_id: int,
        context_type: str | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
    ) -> int:
        query = db.query(MetadataAIContextRecord).filter(MetadataAIContextRecord.workspace_id == workspace_id)
        if context_type:
            query = query.filter(MetadataAIContextRecord.context_type == context_type)
        if resource_type:
            query = query.filter(MetadataAIContextRecord.resource_type == resource_type)
        if resource_id is not None:
            query = query.filter(MetadataAIContextRecord.resource_id == resource_id)
        return query.count()

    @staticmethod
    def _dump_json(payload: Any) -> str:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))
