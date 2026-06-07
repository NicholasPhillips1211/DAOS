from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.analysis import Insight, QueryExecution, SavedQuery
from app.models.metadata import Dataset, Workspace
from app.services.analytics_service import AnalyticsService
from app.services.metadata_service import MetadataService


class AnalyticsWorkflowService:
    """Own multi-step analysis workflows that routes should not assemble inline.

    Query execution, saved queries, and statistics touch datasets, analysis
    records, and metadata. Keeping that orchestration here preserves thin
    routes and keeps Information Analysis coupled to Governance metadata.
    """

    def __init__(self, analytics_service: AnalyticsService, metadata_service: MetadataService | None = None) -> None:
        """Inject domain services so workflow tests can replace collaborators cleanly."""

        self.analytics_service = analytics_service
        self.metadata_service = metadata_service or MetadataService()

    def create_insight(self, db: Session, *, workspace_id: int, title: str, summary: str, evidence_json: str | None) -> Insight:
        """Persist an insight after verifying its parent workspace exists."""

        if db.get(Workspace, workspace_id) is None:
            raise HTTPException(status_code=404, detail="Workspace not found")
        insight = Insight(
            workspace_id=workspace_id,
            title=title,
            summary=summary,
            evidence_json=evidence_json,
        )
        db.add(insight)
        db.commit()
        db.refresh(insight)
        return insight

    def dataset_statistics(self, db: Session, dataset_id: int) -> tuple[Dataset, dict[str, object]]:
        """Load a dataset and compute statistics from its stored CSV path."""

        dataset = db.get(Dataset, dataset_id)
        if dataset is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
        if not dataset.storage_path:
            raise HTTPException(status_code=400, detail="Dataset has no storage path")
        try:
            payload = self.analytics_service.dataset_statistics(dataset.storage_path)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Dataset file not found") from None
        return dataset, payload

    def record_query_execution(
        self,
        db: Session,
        *,
        dataset: Dataset,
        sql_text: str,
        route: str,
        row_count: int,
        column_count: int,
        duration_ms: int,
        actor: str | None,
    ) -> QueryExecution:
        """Persist query history and emit metadata lineage for a completed query."""

        execution = QueryExecution(
            workspace_id=dataset.workspace_id,
            dataset_id=dataset.id,
            sql_text=sql_text,
            route=route,
            row_count=row_count,
            column_count=column_count,
            duration_ms=max(0, duration_ms),
            actor=actor,
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)

        self.metadata_service.record_query_execution_metadata(
            db,
            workspace_id=dataset.workspace_id,
            dataset_id=dataset.id,
            query_execution_id=execution.id,
            actor=actor,
            details={
                "route": route,
                "row_count": row_count,
                "column_count": column_count,
                "duration_ms": max(0, duration_ms),
            },
        )
        return execution

    def list_query_executions(
        self,
        db: Session,
        *,
        workspace_id: int,
        dataset_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[QueryExecution]:
        """Return query execution history newest-first."""

        query = db.query(QueryExecution).filter(QueryExecution.workspace_id == workspace_id)
        if dataset_id is not None:
            query = query.filter(QueryExecution.dataset_id == dataset_id)
        return query.order_by(QueryExecution.created_at.desc()).limit(limit).offset(offset).all()

    def count_query_executions(self, db: Session, *, workspace_id: int, dataset_id: int | None = None) -> int:
        """Count query history with the same filters used by list endpoints."""

        query = db.query(QueryExecution).filter(QueryExecution.workspace_id == workspace_id)
        if dataset_id is not None:
            query = query.filter(QueryExecution.dataset_id == dataset_id)
        return query.count()

    def create_saved_query(
        self,
        db: Session,
        *,
        workspace_id: int,
        dataset_id: int,
        name: str,
        sql_text: str,
        created_by: str | None,
    ) -> SavedQuery:
        """Validate and persist a reusable SQL statement."""

        if not name.strip():
            raise HTTPException(status_code=400, detail="Saved query name is required")
        if not sql_text.strip():
            raise HTTPException(status_code=400, detail="SQL query is required")

        dataset = db.get(Dataset, dataset_id)
        if dataset is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
        if dataset.workspace_id != workspace_id:
            raise HTTPException(status_code=400, detail="Dataset does not belong to workspace")

        saved_query = SavedQuery(
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            name=name.strip(),
            sql_text=sql_text.strip(),
            created_by=created_by,
        )
        db.add(saved_query)
        db.commit()
        db.refresh(saved_query)
        self.metadata_service.record_saved_query_metadata(
            db,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            saved_query_id=saved_query.id,
            name=saved_query.name,
            sql_text=saved_query.sql_text,
            actor=created_by,
        )
        return saved_query

    def list_saved_queries(
        self,
        db: Session,
        *,
        workspace_id: int,
        dataset_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[SavedQuery]:
        """Return saved SQL statements newest-first."""

        query = db.query(SavedQuery).filter(SavedQuery.workspace_id == workspace_id)
        if dataset_id is not None:
            query = query.filter(SavedQuery.dataset_id == dataset_id)
        return query.order_by(SavedQuery.created_at.desc()).limit(limit).offset(offset).all()

    def count_saved_queries(self, db: Session, *, workspace_id: int, dataset_id: int | None = None) -> int:
        """Count saved SQL statements with the same filters used by list endpoints."""

        query = db.query(SavedQuery).filter(SavedQuery.workspace_id == workspace_id)
        if dataset_id is not None:
            query = query.filter(SavedQuery.dataset_id == dataset_id)
        return query.count()
