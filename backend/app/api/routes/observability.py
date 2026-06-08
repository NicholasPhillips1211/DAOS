from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Query as SqlAlchemyQuery
from sqlalchemy.orm import Session

from app.core.auth import Principal, WORKSPACE_READ_ROLES, get_current_principal, require_workspace_role, require_workspace_scope
from app.core.dependencies import get_db
from app.core.observability import observability_store
from app.core.workflow_status import ACTIVE_WORKFLOW_STATUSES, TERMINAL_WORKFLOW_STATUSES
from app.models.automation import AutomationPlan
from app.models.ingestion import IngestionJob
from app.models.pipeline import Pipeline, PipelineRun
from app.models.work_item import WorkItem

router = APIRouter()


@router.get("/metrics")
def metrics_snapshot() -> dict[str, object]:
    """Return backend telemetry counters and latency distributions."""

    return observability_store.snapshot()


@router.get("/workflows")
def workflow_snapshot(
    workspace_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> dict[str, object]:
    """Return workflow status counters for operational triage."""

    require_workspace_scope(workspace_id)
    if workspace_id is not None:
        require_workspace_role(db, workspace_id, principal, WORKSPACE_READ_ROLES)

    work_items = _count_by_status(_workspace_query(db.query(WorkItem), WorkItem.workspace_id, workspace_id), WorkItem.status)
    ingestion_jobs = _count_by_status(
        _workspace_query(db.query(IngestionJob), IngestionJob.workspace_id, workspace_id),
        IngestionJob.status,
    )
    automation_statuses = _count_by_status(
        _workspace_query(db.query(AutomationPlan), AutomationPlan.workspace_id, workspace_id),
        AutomationPlan.status,
    )
    automation_execution_statuses = _count_by_status(
        _workspace_query(db.query(AutomationPlan), AutomationPlan.workspace_id, workspace_id),
        AutomationPlan.execution_status,
    )
    pipelines = _count_by_status(_workspace_query(db.query(Pipeline), Pipeline.workspace_id, workspace_id), Pipeline.status)

    pipeline_runs_query = db.query(PipelineRun)
    if workspace_id is not None:
        pipeline_runs_query = pipeline_runs_query.join(Pipeline, PipelineRun.pipeline_id == Pipeline.id).filter(
            Pipeline.workspace_id == workspace_id
        )
    pipeline_runs = _count_by_status(pipeline_runs_query, PipelineRun.status)

    failed_count = sum(
        counts.get("failed", 0) + counts.get("partial", 0)
        for counts in (work_items, ingestion_jobs, automation_execution_statuses, pipelines, pipeline_runs)
    )
    active_count = sum(
        _sum_matching(counts, ACTIVE_WORKFLOW_STATUSES)
        for counts in (work_items, ingestion_jobs, automation_execution_statuses, pipelines, pipeline_runs)
    )
    terminal_count = sum(
        _sum_matching(counts, TERMINAL_WORKFLOW_STATUSES)
        for counts in (work_items, ingestion_jobs, automation_execution_statuses, pipelines, pipeline_runs)
    )

    return {
        "workspace_id": workspace_id,
        "summary": {
            "active_count": active_count,
            "terminal_count": terminal_count,
            "failed_or_partial_count": failed_count,
        },
        "work_items": work_items,
        "ingestion_jobs": ingestion_jobs,
        "automation_plans": {
            "status": automation_statuses,
            "execution_status": automation_execution_statuses,
        },
        "pipelines": pipelines,
        "pipeline_runs": pipeline_runs,
    }


def _workspace_query(query: SqlAlchemyQuery, workspace_column: object, workspace_id: int | None) -> SqlAlchemyQuery:
    if workspace_id is None:
        return query
    return query.filter(workspace_column == workspace_id)


def _count_by_status(query: SqlAlchemyQuery, status_column: object) -> dict[str, int]:
    rows = query.with_entities(status_column, func.count()).group_by(status_column).all()
    return {str(status.value if hasattr(status, "value") else status): int(count) for status, count in rows}


def _sum_matching(counts: dict[str, int], statuses: set[str]) -> int:
    return sum(count for status, count in counts.items() if status in statuses)
