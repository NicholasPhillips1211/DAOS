from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.analysis import QueryExecution
from app.models.metadata import Dataset
from app.models.visualization import Dashboard, DashboardDependency, DashboardKpiOwner
from app.schemas.visualization import ChartRecommendationRead, DashboardImpactItem, DashboardImpactRead, DashboardKpiOwnerRead
from app.services.metadata_service import MetadataService
from app.services.analytics_service import AnalyticsService
from app.services.visualization_service import VisualizationService


class VisualizationWorkflowService:
    """Coordinate dashboard and visualization workflows across operational assets.

    Dashboards now carry dependencies, KPI ownership, and impact analysis, so
    the route layer delegates here instead of mixing validation, persistence,
    and metadata emission in HTTP handlers.
    """

    def __init__(
        self,
        visualization_service: VisualizationService,
        analytics_service: AnalyticsService,
        metadata_service: MetadataService | None = None,
    ) -> None:
        """Inject collaborators to keep chart logic, metadata, and workflow rules separable."""

        self.visualization_service = visualization_service
        self.analytics_service = analytics_service
        self.metadata_service = metadata_service or MetadataService()

    def recommend_chart(self, db: Session, payload: object) -> ChartRecommendationRead:
        """Load dataset statistics and transform them into a chart recommendation."""

        request = payload
        dataset_id = getattr(request, "dataset_id")
        x_column = getattr(request, "x_column")
        y_column = getattr(request, "y_column")
        goal = getattr(request, "goal")

        dataset = db.get(Dataset, dataset_id)
        if dataset is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
        if not dataset.storage_path:
            raise HTTPException(status_code=400, detail="Dataset has no storage path")

        try:
            stats = self.analytics_service.dataset_statistics(dataset.storage_path)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Dataset file not found") from None

        stats_map = {column["name"]: column for column in stats["columns"]}
        x_kind = stats_map.get(x_column, {}).get("data_type", "string")
        y_kind = stats_map.get(y_column, {}).get("data_type", None) if y_column else None
        recommendation = self.visualization_service.recommend_chart(x_kind, y_kind, goal)
        return ChartRecommendationRead(**asdict(recommendation))

    def create_dashboard_dependency(
        self,
        db: Session,
        *,
        dashboard_id: int,
        dataset_id: int,
        query_execution_id: int | None,
        dependency_type: str,
        details: dict[str, Any] | None,
        actor: str | None,
    ) -> DashboardDependency:
        """Register a governed information dependency for a dashboard."""

        dashboard = self._get_dashboard(db, dashboard_id)
        dataset = self._get_dataset(db, dataset_id)
        if dataset.workspace_id != dashboard.workspace_id:
            raise HTTPException(status_code=400, detail="Dataset does not belong to dashboard workspace")

        query_execution: QueryExecution | None = None
        if query_execution_id is not None:
            query_execution = db.get(QueryExecution, query_execution_id)
            if query_execution is None:
                raise HTTPException(status_code=404, detail="Query execution not found")
            if query_execution.workspace_id != dashboard.workspace_id or query_execution.dataset_id != dataset_id:
                raise HTTPException(status_code=400, detail="Query execution does not match dashboard dataset")

        clean_dependency_type = dependency_type.strip() or "source_dataset"
        dependency = DashboardDependency(
            workspace_id=dashboard.workspace_id,
            dashboard_id=dashboard.id,
            dataset_id=dataset.id,
            query_execution_id=query_execution.id if query_execution else None,
            dependency_type=clean_dependency_type,
            details_json=json.dumps(details or {}, sort_keys=True),
        )
        db.add(dependency)
        db.commit()
        db.refresh(dependency)

        lineage_details = {
            "dependency_id": dependency.id,
            "dependency_type": clean_dependency_type,
            "query_execution_id": dependency.query_execution_id,
            "details": details or {},
        }
        self.metadata_service.record_lineage_record(
            db,
            workspace_id=dashboard.workspace_id,
            upstream_type="dataset",
            upstream_id=dataset.id,
            downstream_type="dashboard",
            downstream_id=dashboard.id,
            relation_type="powers_dashboard",
            details=lineage_details,
        )
        if query_execution is not None:
            self.metadata_service.record_lineage_record(
                db,
                workspace_id=dashboard.workspace_id,
                upstream_type="query_execution",
                upstream_id=query_execution.id,
                downstream_type="dashboard",
                downstream_id=dashboard.id,
                relation_type="feeds_dashboard",
                details=lineage_details,
            )
        self.metadata_service.record_usage_event(
            db,
            workspace_id=dashboard.workspace_id,
            asset_type="dashboard",
            asset_id=dashboard.id,
            action="dashboard.dependency_registered",
            actor=actor,
            details={
                "dependency_id": dependency.id,
                "dataset_id": dataset.id,
                "query_execution_id": dependency.query_execution_id,
                "dependency_type": clean_dependency_type,
            },
        )
        return dependency

    def list_dashboard_dependencies(self, db: Session, *, dashboard_id: int) -> list[DashboardDependency]:
        """Return dependencies for a dashboard newest-first."""

        dashboard = self._get_dashboard(db, dashboard_id)
        return (
            db.query(DashboardDependency)
            .filter(DashboardDependency.dashboard_id == dashboard.id)
            .order_by(DashboardDependency.created_at.desc())
            .all()
        )

    def create_kpi_owner(
        self,
        db: Session,
        *,
        dashboard_id: int,
        kpi_name: str,
        owner_email: str,
        description: str | None,
        actor: str | None,
    ) -> DashboardKpiOwner:
        """Assign an accountable owner to a dashboard KPI."""

        dashboard = self._get_dashboard(db, dashboard_id)
        clean_kpi_name = kpi_name.strip()
        clean_owner_email = owner_email.strip().lower()
        if not clean_kpi_name:
            raise HTTPException(status_code=400, detail="KPI name is required")
        if not clean_owner_email:
            raise HTTPException(status_code=400, detail="Owner email is required")

        owner = DashboardKpiOwner(
            workspace_id=dashboard.workspace_id,
            dashboard_id=dashboard.id,
            kpi_name=clean_kpi_name,
            owner_email=clean_owner_email,
            description=description,
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)

        self.metadata_service.record_usage_event(
            db,
            workspace_id=dashboard.workspace_id,
            asset_type="dashboard",
            asset_id=dashboard.id,
            action="dashboard.kpi_owner_assigned",
            actor=actor,
            details={
                "kpi_owner_id": owner.id,
                "kpi_name": owner.kpi_name,
                "owner_email": owner.owner_email,
            },
        )
        return owner

    def list_kpi_owners(self, db: Session, *, dashboard_id: int) -> list[DashboardKpiOwner]:
        """Return KPI ownership assignments for a dashboard newest-first."""

        dashboard = self._get_dashboard(db, dashboard_id)
        return (
            db.query(DashboardKpiOwner)
            .filter(DashboardKpiOwner.dashboard_id == dashboard.id)
            .order_by(DashboardKpiOwner.created_at.desc())
            .all()
        )

    def dataset_impact(self, db: Session, *, workspace_id: int, dataset_id: int) -> DashboardImpactRead:
        """Return dashboards that depend on a dataset and would be affected by changes."""

        dataset = self._get_dataset(db, dataset_id)
        if dataset.workspace_id != workspace_id:
            raise HTTPException(status_code=400, detail="Dataset does not belong to workspace")

        dependencies = (
            db.query(DashboardDependency)
            .filter(
                DashboardDependency.workspace_id == workspace_id,
                DashboardDependency.dataset_id == dataset_id,
            )
            .order_by(DashboardDependency.created_at.desc())
            .all()
        )
        dashboard_ids = {dependency.dashboard_id for dependency in dependencies}
        owners_by_dashboard: dict[int, list[DashboardKpiOwner]] = {
            dashboard_id: (
                db.query(DashboardKpiOwner)
                .filter(DashboardKpiOwner.dashboard_id == dashboard_id)
                .order_by(DashboardKpiOwner.created_at.desc())
                .all()
            )
            for dashboard_id in dashboard_ids
        }

        impact_items: list[DashboardImpactItem] = []
        for dependency in dependencies:
            dashboard = db.get(Dashboard, dependency.dashboard_id)
            if dashboard is None:
                continue
            impact_items.append(
                DashboardImpactItem(
                    dashboard_id=dashboard.id,
                    dashboard_name=dashboard.name,
                    dependency_id=dependency.id,
                    dependency_type=dependency.dependency_type,
                    query_execution_id=dependency.query_execution_id,
                    kpi_owners=[
                        DashboardKpiOwnerRead.model_validate(owner)
                        for owner in owners_by_dashboard.get(dashboard.id, [])
                    ],
                )
            )

        return DashboardImpactRead(
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            impacted_dashboard_count=len({item.dashboard_id for item in impact_items}),
            dashboards=impact_items,
        )

    @staticmethod
    def parse_details(value: str | None) -> dict[str, Any]:
        """Parse dependency JSON details for API responses."""

        if not value:
            return {}
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {"value": parsed}
        except json.JSONDecodeError:
            return {"raw": value}

    @staticmethod
    def _get_dashboard(db: Session, dashboard_id: int) -> Dashboard:
        """Centralize dashboard lookup so every workflow returns the same 404 shape."""

        dashboard = db.get(Dashboard, dashboard_id)
        if dashboard is None:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        return dashboard

    @staticmethod
    def _get_dataset(db: Session, dataset_id: int) -> Dataset:
        """Centralize dataset lookup for dependency and impact workflows."""

        dataset = db.get(Dataset, dataset_id)
        if dataset is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
        return dataset
