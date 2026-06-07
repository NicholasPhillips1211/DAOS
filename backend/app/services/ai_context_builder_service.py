from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.analysis import QueryExecution, SavedQuery
from app.models.automation import AutomationPlan
from app.models.governance import AuditEvent, DataMask
from app.models.metadata import Dataset, MetadataAIContextRecord, Workspace
from app.models.visualization import Dashboard, DashboardDependency, DashboardKpiOwner
from app.services.metadata_service import MetadataService


@dataclass(slots=True)
class BuiltAIContext:
    """Return both persisted record metadata and the JSON context payload."""

    record: MetadataAIContextRecord
    context: dict[str, Any]


class AIContextBuilderService:
    """Build reusable AI context from the management information lifecycle.

    This service is deliberately separate from automation generation. Automation,
    recommendations, summaries, and future copilots can all consume the same
    governed context instead of each feature querying metadata tables in its own
    shape.
    """

    def __init__(self, metadata_service: MetadataService | None = None) -> None:
        """Inject metadata access so persistence and context assembly stay decoupled."""

        self.metadata_service = metadata_service or MetadataService()

    def build_workspace_context(
        self,
        db: Session,
        *,
        workspace_id: int,
        objective: str | None,
        actor: str | None,
    ) -> BuiltAIContext:
        """Assemble and persist a workspace-level grounding snapshot for AI workflows."""

        workspace = db.get(Workspace, workspace_id)
        if workspace is None:
            raise HTTPException(status_code=404, detail="Workspace not found")

        context = {
            "objective": objective.strip() if objective else None,
            "generated_at": datetime.utcnow().isoformat(),
            "workspace": self._workspace_payload(workspace),
            "lifecycle": {
                "information_collection": self._collection_payload(db, workspace_id),
                "information_governance": self._governance_payload(db, workspace_id),
                "information_analysis": self._analysis_payload(db, workspace_id),
                "information_intelligence": self._intelligence_payload(db, workspace_id),
                "information_operationalization": self._operationalization_payload(db, workspace_id),
            },
        }
        context["summary"] = self._summary(context)
        context["sources"] = self._sources(context)
        context["recommended_next_actions"] = self._recommended_next_actions(context)
        context["confidence_score"] = self._confidence_score(context)

        record = self.metadata_service.record_ai_context(
            db,
            workspace_id=workspace_id,
            context_type="workspace_context",
            resource_type="workspace",
            resource_id=workspace_id,
            actor=actor,
            context=context,
        )
        return BuiltAIContext(record=record, context=context)

    @staticmethod
    def _workspace_payload(workspace: Workspace) -> dict[str, Any]:
        """Keep workspace identity small so AI prompts are grounded but not bloated."""

        return {
            "id": workspace.id,
            "name": workspace.name,
            "description": workspace.description,
            "created_at": workspace.created_at.isoformat() if workspace.created_at else None,
        }

    def _collection_payload(self, db: Session, workspace_id: int) -> dict[str, Any]:
        """Summarize collected assets because collection is the start of the lifecycle."""

        datasets = (
            db.query(Dataset)
            .filter(Dataset.workspace_id == workspace_id)
            .order_by(Dataset.created_at.desc())
            .limit(10)
            .all()
        )
        return {
            "dataset_count": db.query(Dataset).filter(Dataset.workspace_id == workspace_id).count(),
            "recent_datasets": [
                {
                    "id": dataset.id,
                    "name": dataset.name,
                    "source_type": dataset.source_type,
                    "state": dataset.state.value if hasattr(dataset.state, "value") else str(dataset.state),
                    "created_at": self._iso(dataset.created_at),
                }
                for dataset in datasets
            ],
        }

    def _governance_payload(self, db: Session, workspace_id: int) -> dict[str, Any]:
        """Collect governance signals so AI can explain trust, lineage, and controls."""

        schema_records = self.metadata_service.list_schema_records(db, workspace_id=workspace_id, limit=10)
        lineage_records = self.metadata_service.list_lineage_records(db, workspace_id=workspace_id, limit=25)
        usage_events = self.metadata_service.list_usage_events(db, workspace_id=workspace_id, limit=25)
        ownership_records = self.metadata_service.list_ownership_records(db, workspace_id=workspace_id, limit=25)
        audit_events = (
            db.query(AuditEvent)
            .filter(AuditEvent.workspace_id == workspace_id)
            .order_by(AuditEvent.created_at.desc())
            .limit(10)
            .all()
        )
        masks = (
            db.query(DataMask)
            .filter(DataMask.workspace_id == workspace_id)
            .order_by(DataMask.created_at.desc())
            .limit(10)
            .all()
        )
        return {
            "schema_record_count": self.metadata_service.count_schema_records(db, workspace_id=workspace_id),
            "lineage_record_count": self.metadata_service.count_lineage_records(db, workspace_id=workspace_id),
            "usage_event_count": self.metadata_service.count_usage_events(db, workspace_id=workspace_id),
            "ownership_record_count": self.metadata_service.count_ownership_records(db, workspace_id=workspace_id),
            "recent_schemas": [
                {
                    "asset_type": record.asset_type,
                    "asset_id": record.asset_id,
                    "source": record.source,
                    "schema": self.metadata_service.parse_record_json(record.schema_json),
                }
                for record in schema_records
            ],
            "recent_lineage": [
                {
                    "upstream": {"type": record.upstream_type, "id": record.upstream_id},
                    "downstream": {"type": record.downstream_type, "id": record.downstream_id},
                    "relation_type": record.relation_type,
                    "details": self.metadata_service.parse_record_json(record.details_json),
                }
                for record in lineage_records
            ],
            "recent_usage": [
                {
                    "asset_type": record.asset_type,
                    "asset_id": record.asset_id,
                    "action": record.action,
                    "actor": record.actor,
                    "details": self.metadata_service.parse_record_json(record.details_json),
                }
                for record in usage_events
            ],
            "recent_ownership": [
                {
                    "asset_type": record.asset_type,
                    "asset_id": record.asset_id,
                    "owner_email": record.owner_email,
                    "steward_email": record.steward_email,
                    "stewardship_status": record.stewardship_status,
                    "details": self.metadata_service.parse_record_json(record.details_json),
                }
                for record in ownership_records
            ],
            "recent_audit_events": [
                {
                    "event_type": event.event_type,
                    "resource_type": event.resource_type,
                    "resource_id": event.resource_id,
                    "actor": event.actor,
                    "created_at": self._iso(event.created_at),
                }
                for event in audit_events
            ],
            "data_masks": [
                {
                    "dataset_id": mask.dataset_id,
                    "column_name": mask.column_name,
                    "mask_type": mask.mask_type,
                }
                for mask in masks
            ],
        }

    def _analysis_payload(self, db: Session, workspace_id: int) -> dict[str, Any]:
        """Collect analysis history so AI recommendations can cite actual analytical work."""

        executions = (
            db.query(QueryExecution)
            .filter(QueryExecution.workspace_id == workspace_id)
            .order_by(QueryExecution.created_at.desc())
            .limit(10)
            .all()
        )
        saved_queries = (
            db.query(SavedQuery)
            .filter(SavedQuery.workspace_id == workspace_id)
            .order_by(SavedQuery.created_at.desc())
            .limit(10)
            .all()
        )
        return {
            "query_execution_count": db.query(QueryExecution).filter(QueryExecution.workspace_id == workspace_id).count(),
            "saved_query_count": db.query(SavedQuery).filter(SavedQuery.workspace_id == workspace_id).count(),
            "recent_query_executions": [
                {
                    "id": execution.id,
                    "dataset_id": execution.dataset_id,
                    "route": execution.route,
                    "row_count": execution.row_count,
                    "column_count": execution.column_count,
                    "duration_ms": execution.duration_ms,
                    "created_at": self._iso(execution.created_at),
                }
                for execution in executions
            ],
            "saved_queries": [
                {
                    "id": saved_query.id,
                    "dataset_id": saved_query.dataset_id,
                    "name": saved_query.name,
                    "created_by": saved_query.created_by,
                    "created_at": self._iso(saved_query.created_at),
                }
                for saved_query in saved_queries
            ],
        }

    def _intelligence_payload(self, db: Session, workspace_id: int) -> dict[str, Any]:
        """Collect prior AI artifacts so new AI output can avoid starting cold."""

        context_records = self.metadata_service.list_ai_context_records(db, workspace_id=workspace_id, limit=10)
        automation_plans = (
            db.query(AutomationPlan)
            .filter(AutomationPlan.workspace_id == workspace_id)
            .order_by(AutomationPlan.created_at.desc())
            .limit(5)
            .all()
        )
        return {
            "ai_context_record_count": self.metadata_service.count_ai_context_records(db, workspace_id=workspace_id),
            "recent_context_types": [record.context_type for record in context_records],
            "recent_automation_plans": [
                {
                    "id": plan.id,
                    "objective": plan.objective,
                    "provider": plan.provider,
                    "status": plan.status,
                    "summary": plan.summary,
                    "created_at": self._iso(plan.created_at),
                }
                for plan in automation_plans
            ],
        }

    def _operationalization_payload(self, db: Session, workspace_id: int) -> dict[str, Any]:
        """Collect dashboard dependencies and ownership because they turn insight into action."""

        dashboards = (
            db.query(Dashboard)
            .filter(Dashboard.workspace_id == workspace_id)
            .order_by(Dashboard.created_at.desc())
            .limit(10)
            .all()
        )
        payload: list[dict[str, Any]] = []
        for dashboard in dashboards:
            dependencies = (
                db.query(DashboardDependency)
                .filter(DashboardDependency.dashboard_id == dashboard.id)
                .order_by(DashboardDependency.created_at.desc())
                .all()
            )
            owners = (
                db.query(DashboardKpiOwner)
                .filter(DashboardKpiOwner.dashboard_id == dashboard.id)
                .order_by(DashboardKpiOwner.created_at.desc())
                .all()
            )
            payload.append(
                {
                    "id": dashboard.id,
                    "name": dashboard.name,
                    "description": dashboard.description,
                    "dependencies": [
                        {
                            "dataset_id": dependency.dataset_id,
                            "query_execution_id": dependency.query_execution_id,
                            "dependency_type": dependency.dependency_type,
                        }
                        for dependency in dependencies
                    ],
                    "kpi_owners": [
                        {
                            "kpi_name": owner.kpi_name,
                            "owner_email": owner.owner_email,
                            "description": owner.description,
                        }
                        for owner in owners
                    ],
                }
            )
        return {
            "dashboard_count": db.query(Dashboard).filter(Dashboard.workspace_id == workspace_id).count(),
            "dashboards": payload,
        }

    @staticmethod
    def _summary(context: dict[str, Any]) -> str:
        """Create a deterministic summary so AI consumers have a stable headline."""

        lifecycle = context["lifecycle"]
        return (
            f"Workspace has {lifecycle['information_collection']['dataset_count']} datasets, "
            f"{lifecycle['information_analysis']['query_execution_count']} query executions, "
            f"and {lifecycle['information_operationalization']['dashboard_count']} dashboards."
        )

    @staticmethod
    def _sources(context: dict[str, Any]) -> list[str]:
        """Name the evidence groups so downstream AI output can cite its grounding."""

        sources = ["workspace"]
        lifecycle = context["lifecycle"]
        if lifecycle["information_collection"]["dataset_count"]:
            sources.append("datasets")
        if lifecycle["information_governance"]["schema_record_count"]:
            sources.append("metadata.schemas")
        if lifecycle["information_governance"]["lineage_record_count"]:
            sources.append("metadata.lineage")
        if lifecycle["information_governance"]["ownership_record_count"]:
            sources.append("metadata.ownership")
        if lifecycle["information_analysis"]["query_execution_count"]:
            sources.append("query_executions")
        if lifecycle["information_operationalization"]["dashboard_count"]:
            sources.append("dashboards")
        return sources

    @staticmethod
    def _recommended_next_actions(context: dict[str, Any]) -> list[str]:
        """Suggest lifecycle-aware next actions without requiring an LLM call."""

        lifecycle = context["lifecycle"]
        actions: list[str] = []
        if lifecycle["information_collection"]["dataset_count"] == 0:
            actions.append("Collect the first governed dataset for this workspace.")
        if lifecycle["information_governance"]["schema_record_count"] == 0:
            actions.append("Register schema metadata so AI outputs can cite trusted fields.")
        if (
            lifecycle["information_collection"]["dataset_count"] > 0
            and lifecycle["information_governance"]["ownership_record_count"] == 0
        ):
            actions.append("Assign dataset owners and stewards so governed assets have accountable operators.")
        if lifecycle["information_analysis"]["query_execution_count"] == 0:
            actions.append("Run an initial SQL analysis to create analytical evidence.")
        if lifecycle["information_operationalization"]["dashboard_count"] == 0:
            actions.append("Create an operational dashboard for decision delivery.")
        elif not any(item["kpi_owners"] for item in lifecycle["information_operationalization"]["dashboards"]):
            actions.append("Assign KPI owners to operational dashboards.")
        return actions or ["Review existing metadata and refresh operational outputs."]

    @staticmethod
    def _confidence_score(context: dict[str, Any]) -> float:
        """Estimate context strength from available lifecycle evidence."""

        lifecycle = context["lifecycle"]
        score = 0.45
        if lifecycle["information_collection"]["dataset_count"]:
            score += 0.12
        if lifecycle["information_governance"]["schema_record_count"]:
            score += 0.12
        if lifecycle["information_governance"]["lineage_record_count"]:
            score += 0.12
        if lifecycle["information_analysis"]["query_execution_count"]:
            score += 0.1
        if lifecycle["information_operationalization"]["dashboard_count"]:
            score += 0.09
        return round(min(score, 0.98), 2)

    @staticmethod
    def _iso(value: datetime | None) -> str | None:
        """Normalize datetimes for JSON payloads that may be reused outside the API."""

        return value.isoformat() if value else None
