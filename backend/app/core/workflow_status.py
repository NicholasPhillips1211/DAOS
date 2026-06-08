from __future__ import annotations

from enum import Enum
from typing import Iterable


class WorkflowStatus(str, Enum):
    """Shared workflow status vocabulary used across durable operations."""

    draft = "draft"
    generated = "generated"
    pending = "pending"
    staging = "staging"
    queued = "queued"
    scheduled = "scheduled"
    running = "running"
    succeeded = "succeeded"
    completed = "completed"
    partial = "partial"
    skipped = "skipped"
    deferred = "deferred"
    failed = "failed"


ACTIVE_WORKFLOW_STATUSES = {
    WorkflowStatus.pending.value,
    WorkflowStatus.staging.value,
    WorkflowStatus.queued.value,
    WorkflowStatus.scheduled.value,
    WorkflowStatus.running.value,
}

TERMINAL_WORKFLOW_STATUSES = {
    WorkflowStatus.succeeded.value,
    WorkflowStatus.completed.value,
    WorkflowStatus.partial.value,
    WorkflowStatus.skipped.value,
    WorkflowStatus.deferred.value,
    WorkflowStatus.failed.value,
}

KNOWN_WORKFLOW_STATUSES = ACTIVE_WORKFLOW_STATUSES | TERMINAL_WORKFLOW_STATUSES | {
    WorkflowStatus.draft.value,
    WorkflowStatus.generated.value,
}


def workflow_status_value(status: WorkflowStatus | str) -> str:
    """Return the storage/API value for a workflow status."""

    return status.value if isinstance(status, WorkflowStatus) else status


def is_terminal_workflow_status(status: WorkflowStatus | str) -> bool:
    """Return true when a workflow status represents no further automatic work."""

    return workflow_status_value(status) in TERMINAL_WORKFLOW_STATUSES


def is_known_workflow_status(status: WorkflowStatus | str) -> bool:
    """Return true when a status is part of the shared DAOS workflow vocabulary."""

    return workflow_status_value(status) in KNOWN_WORKFLOW_STATUSES


def summarize_action_statuses(results: Iterable[dict[str, object]]) -> str:
    """Collapse action-level statuses into one honest workflow-level outcome."""

    statuses = {str(result.get("status") or "unknown") for result in results}
    if not statuses:
        return WorkflowStatus.failed.value
    executed_statuses = {WorkflowStatus.succeeded.value, "executed"}
    if WorkflowStatus.failed.value in statuses:
        return WorkflowStatus.failed.value if statuses <= {WorkflowStatus.failed.value} else WorkflowStatus.partial.value
    if statuses <= executed_statuses:
        return WorkflowStatus.completed.value
    if statuses & executed_statuses:
        return WorkflowStatus.partial.value
    if statuses <= {WorkflowStatus.skipped.value}:
        return WorkflowStatus.skipped.value
    if statuses <= {WorkflowStatus.deferred.value}:
        return WorkflowStatus.deferred.value
    if statuses <= {WorkflowStatus.skipped.value, WorkflowStatus.deferred.value}:
        return WorkflowStatus.deferred.value
    return WorkflowStatus.partial.value
