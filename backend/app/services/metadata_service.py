from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.governance import AuditEvent
from app.models.metadata import (
    MetadataAIContextRecord,
    MetadataLineageRecord,
    MetadataOwnershipRecord,
    MetadataSchemaRecord,
    MetadataUsageEvent,
)
from app.repositories.metadata_repository import MetadataRepository

logger = logging.getLogger("daos.metadata")


class MetadataService:
    """Coordinate lifecycle metadata writes across events, lineage, usage, and AI context.

    Routes and domain workflows call this service instead of touching metadata
    tables directly. That keeps metadata emission consistent as DAOS moves
    information through Collection, Governance, Analysis, Intelligence, and
    Operationalization.
    """

    def __init__(self, repository: MetadataRepository | None = None) -> None:
        """Accept a repository override so tests and future stores can swap persistence cleanly."""

        self.repository = repository or MetadataRepository()

    def emit_event(
        self,
        db: Session,
        *,
        workspace_id: int,
        event_type: str,
        resource_type: str,
        resource_id: int,
        details: dict[str, Any],
        actor: str | None = None,
    ) -> AuditEvent:
        """Persist one metadata event into the shared audit store."""

        event = AuditEvent(
            workspace_id=workspace_id,
            event_type=event_type,
            actor=actor,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details, sort_keys=True),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    def list_events(
        self,
        db: Session,
        *,
        workspace_id: int,
        event_type: str | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Return metadata events newest-first with optional filters."""

        query = db.query(AuditEvent).filter(AuditEvent.workspace_id == workspace_id)
        query = query.filter(AuditEvent.event_type.like("metadata.%"))

        if event_type:
            query = query.filter(AuditEvent.event_type == event_type)
        if resource_type:
            query = query.filter(AuditEvent.resource_type == resource_type)
        if resource_id is not None:
            query = query.filter(AuditEvent.resource_id == resource_id)

        capped_limit = max(1, min(limit, 500))
        return query.order_by(AuditEvent.created_at.desc()).limit(capped_limit).all()

    def count_events(
        self,
        db: Session,
        *,
        workspace_id: int,
        event_type: str | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
    ) -> int:
        """Return the total number of metadata events matching the given filters."""

        query = db.query(AuditEvent).filter(AuditEvent.workspace_id == workspace_id)
        query = query.filter(AuditEvent.event_type.like("metadata.%"))

        if event_type:
            query = query.filter(AuditEvent.event_type == event_type)
        if resource_type:
            query = query.filter(AuditEvent.resource_type == resource_type)
        if resource_id is not None:
            query = query.filter(AuditEvent.resource_id == resource_id)

        return query.count()

    def record_ingestion_profile(
        self,
        db: Session,
        *,
        workspace_id: int,
        dataset_id: int,
        dataset_name: str,
        job_id: int,
        report_id: int,
        source_name: str,
        storage_path: str,
        profile: dict[str, Any],
        actor: str | None = None,
    ) -> AuditEvent:
        """Persist ingestion metadata across schema, lineage, usage, AI context, and events."""

        metadata = profile.get("metadata", {})
        schema = metadata.get("schema") or self._schema_from_profile(profile)
        profile_fingerprint = metadata.get("profile_fingerprint")
        stewardship_status = "active" if actor else "unassigned"
        event_details = {
            "job_id": job_id,
            "dataset_name": dataset_name,
            "report_id": report_id,
            "row_count": profile.get("row_count", 0),
            "rejected_rows": profile.get("rejected_rows", 0),
            "quality_score": profile.get("quality_score", 0),
            "owner_email": actor,
            "steward_email": actor,
            "stewardship_status": stewardship_status,
            "status": "completed",
        }

        self.repository.add_schema_record(
            db,
            workspace_id=workspace_id,
            asset_type="dataset",
            asset_id=dataset_id,
            schema=schema,
            profile_fingerprint=profile_fingerprint,
            source=source_name,
        )
        self.repository.add_lineage_record(
            db,
            workspace_id=workspace_id,
            upstream_type="ingestion_job",
            upstream_id=job_id,
            downstream_type="dataset",
            downstream_id=dataset_id,
            relation_type="created_dataset",
            details={
                "dataset_name": dataset_name,
                "source_name": source_name,
                "storage_path": storage_path,
                "profile_fingerprint": profile_fingerprint,
            },
        )
        self.repository.add_usage_event(
            db,
            workspace_id=workspace_id,
            asset_type="dataset",
            asset_id=dataset_id,
            action="information_collected",
            actor=actor,
            details={
                "job_id": job_id,
                "source_name": source_name,
                "row_count": profile.get("row_count", 0),
                "quality_score": profile.get("quality_score", 0),
            },
        )
        self.repository.add_ownership_record(
            db,
            workspace_id=workspace_id,
            asset_type="dataset",
            asset_id=dataset_id,
            owner_email=actor,
            steward_email=actor,
            stewardship_status=stewardship_status,
            details={
                "job_id": job_id,
                "dataset_name": dataset_name,
                "source_name": source_name,
                "profile_fingerprint": profile_fingerprint,
            },
        )
        self.repository.add_ai_context_record(
            db,
            workspace_id=workspace_id,
            context_type="dataset_profile",
            resource_type="dataset",
            resource_id=dataset_id,
            actor=actor,
            context={
                "dataset_name": dataset_name,
                "schema": schema,
                "row_count": profile.get("row_count", 0),
                "rejected_rows": profile.get("rejected_rows", 0),
                "quality_score": profile.get("quality_score", 0),
                "issues": profile.get("issues", []),
                "owner_email": actor,
                "steward_email": actor,
                "stewardship_status": stewardship_status,
                "profile_fingerprint": profile_fingerprint,
            },
        )

        event = AuditEvent(
            workspace_id=workspace_id,
            event_type="metadata.ingestion.profile_created",
            actor=actor,
            resource_type="dataset",
            resource_id=dataset_id,
            details=json.dumps(event_details, sort_keys=True),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    def record_usage_event(
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
        """Record how governed information was consumed by a workflow."""

        record = self.repository.add_usage_event(
            db,
            workspace_id=workspace_id,
            asset_type=asset_type,
            asset_id=asset_id,
            action=action,
            actor=actor,
            details=details,
        )
        db.commit()
        db.refresh(record)
        return record

    def record_ownership_record(
        self,
        db: Session,
        *,
        workspace_id: int,
        asset_type: str,
        asset_id: int,
        owner_email: str | None = None,
        steward_email: str | None = None,
        stewardship_status: str = "unassigned",
        details: dict[str, Any] | None = None,
    ) -> MetadataOwnershipRecord:
        """Record ownership and stewardship facts for a governed asset."""

        record = self.repository.add_ownership_record(
            db,
            workspace_id=workspace_id,
            asset_type=asset_type,
            asset_id=asset_id,
            owner_email=owner_email,
            steward_email=steward_email,
            stewardship_status=stewardship_status,
            details=details,
        )
        db.commit()
        db.refresh(record)
        return record

    def record_lineage_record(
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
        """Record a dependency edge between lifecycle assets."""

        record = self.repository.add_lineage_record(
            db,
            workspace_id=workspace_id,
            upstream_type=upstream_type,
            upstream_id=upstream_id,
            downstream_type=downstream_type,
            downstream_id=downstream_id,
            relation_type=relation_type,
            details=details,
        )
        db.commit()
        db.refresh(record)
        return record

    def record_query_execution_metadata(
        self,
        db: Session,
        *,
        workspace_id: int,
        dataset_id: int,
        query_execution_id: int,
        actor: str | None,
        details: dict[str, Any],
    ) -> None:
        """Record usage and lineage for one executed SQL query."""

        self.repository.add_usage_event(
            db,
            workspace_id=workspace_id,
            asset_type="dataset",
            asset_id=dataset_id,
            action="dataset.query_executed",
            actor=actor,
            details={"query_execution_id": query_execution_id, **details},
        )
        self.repository.add_lineage_record(
            db,
            workspace_id=workspace_id,
            upstream_type="dataset",
            upstream_id=dataset_id,
            downstream_type="query_execution",
            downstream_id=query_execution_id,
            relation_type="queried_by",
            details=details,
        )
        event = AuditEvent(
            workspace_id=workspace_id,
            event_type="metadata.analysis.query_executed",
            actor=actor,
            resource_type="query_execution",
            resource_id=query_execution_id,
            details=json.dumps({"dataset_id": dataset_id, **details}, sort_keys=True),
        )
        db.add(event)
        db.commit()

    def record_ai_context(
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
        """Persist a grounding snapshot for AI-assisted workflows."""

        record = self.repository.add_ai_context_record(
            db,
            workspace_id=workspace_id,
            context_type=context_type,
            context=context,
            resource_type=resource_type,
            resource_id=resource_id,
            actor=actor,
        )
        db.commit()
        db.refresh(record)
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
        """Delegate schema reads through the service boundary used by API routes."""

        return self.repository.list_schema_records(
            db,
            workspace_id=workspace_id,
            asset_type=asset_type,
            asset_id=asset_id,
            limit=limit,
            offset=offset,
        )

    def count_schema_records(
        self,
        db: Session,
        *,
        workspace_id: int,
        asset_type: str | None = None,
        asset_id: int | None = None,
    ) -> int:
        """Count schema records here so routes do not know repository details."""

        return self.repository.count_schema_records(db, workspace_id=workspace_id, asset_type=asset_type, asset_id=asset_id)

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
        """Delegate lineage reads so callers use one metadata facade."""

        return self.repository.list_lineage_records(
            db,
            workspace_id=workspace_id,
            asset_type=asset_type,
            asset_id=asset_id,
            limit=limit,
            offset=offset,
        )

    def count_lineage_records(
        self,
        db: Session,
        *,
        workspace_id: int,
        asset_type: str | None = None,
        asset_id: int | None = None,
    ) -> int:
        """Count lineage records using the same filters exposed by the API."""

        return self.repository.count_lineage_records(db, workspace_id=workspace_id, asset_type=asset_type, asset_id=asset_id)

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
        """Delegate usage reads so operational and AI workflows share one access path."""

        return self.repository.list_usage_events(
            db,
            workspace_id=workspace_id,
            asset_type=asset_type,
            asset_id=asset_id,
            action=action,
            limit=limit,
            offset=offset,
        )

    def count_usage_events(
        self,
        db: Session,
        *,
        workspace_id: int,
        asset_type: str | None = None,
        asset_id: int | None = None,
        action: str | None = None,
    ) -> int:
        """Count usage events using the same filters exposed by the API."""

        return self.repository.count_usage_events(
            db,
            workspace_id=workspace_id,
            asset_type=asset_type,
            asset_id=asset_id,
            action=action,
        )

    def list_ownership_records(
        self,
        db: Session,
        *,
        workspace_id: int,
        asset_type: str | None = None,
        asset_id: int | None = None,
        owner_email: str | None = None,
        steward_email: str | None = None,
        stewardship_status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MetadataOwnershipRecord]:
        """Delegate ownership reads so governance and AI workflows share one access path."""

        return self.repository.list_ownership_records(
            db,
            workspace_id=workspace_id,
            asset_type=asset_type,
            asset_id=asset_id,
            owner_email=owner_email,
            steward_email=steward_email,
            stewardship_status=stewardship_status,
            limit=limit,
            offset=offset,
        )

    def count_ownership_records(
        self,
        db: Session,
        *,
        workspace_id: int,
        asset_type: str | None = None,
        asset_id: int | None = None,
        owner_email: str | None = None,
        steward_email: str | None = None,
        stewardship_status: str | None = None,
    ) -> int:
        """Count ownership records using the same filters exposed by the API."""

        return self.repository.count_ownership_records(
            db,
            workspace_id=workspace_id,
            asset_type=asset_type,
            asset_id=asset_id,
            owner_email=owner_email,
            steward_email=steward_email,
            stewardship_status=stewardship_status,
        )

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
        """Delegate AI context reads for reusable intelligence grounding."""

        return self.repository.list_ai_context_records(
            db,
            workspace_id=workspace_id,
            context_type=context_type,
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit,
            offset=offset,
        )

    def count_ai_context_records(
        self,
        db: Session,
        *,
        workspace_id: int,
        context_type: str | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
    ) -> int:
        """Count AI context records using the same filters exposed by the API."""

        return self.repository.count_ai_context_records(
            db,
            workspace_id=workspace_id,
            context_type=context_type,
            resource_type=resource_type,
            resource_id=resource_id,
        )

    def parse_details(self, event: AuditEvent) -> dict[str, Any]:
        """Parse JSON details safely for API response rendering."""

        if not event.details:
            return {}
        try:
            parsed = json.loads(event.details)
            return parsed if isinstance(parsed, dict) else {"value": parsed}
        except json.JSONDecodeError:
            logger.warning("metadata_event_unparseable id=%s", event.id)
            return {"raw": event.details}

    def parse_record_json(self, value: str | None) -> dict[str, Any] | list[dict[str, Any]]:
        """Parse JSON stored on first-class metadata records."""

        if not value:
            return {}
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, (dict, list)) else {"value": parsed}
        except json.JSONDecodeError:
            logger.warning("metadata_record_unparseable")
            return {"raw": value}

    @staticmethod
    def _schema_from_profile(profile: dict[str, Any]) -> list[dict[str, Any]]:
        """Derive a minimal schema when profile metadata predates schema snapshots."""

        return [
            {"name": column.get("name", ""), "inferred_type": column.get("inferred_type", "unknown")}
            for column in profile.get("columns", [])
        ]
