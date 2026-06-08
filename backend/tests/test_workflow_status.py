from app.core.workflow_status import (
    WorkflowStatus,
    is_known_workflow_status,
    is_terminal_workflow_status,
    summarize_action_statuses,
)


def test_workflow_status_vocabulary_classifies_terminal_states() -> None:
    assert is_known_workflow_status(WorkflowStatus.queued)
    assert is_known_workflow_status("completed")
    assert not is_known_workflow_status("done")
    assert is_terminal_workflow_status(WorkflowStatus.failed)
    assert is_terminal_workflow_status("partial")
    assert not is_terminal_workflow_status("running")


def test_summarize_action_statuses_preserves_integrity() -> None:
    assert summarize_action_statuses([]) == "failed"
    assert summarize_action_statuses([{"status": "executed"}]) == "completed"
    assert summarize_action_statuses([{"status": "skipped"}]) == "skipped"
    assert summarize_action_statuses([{"status": "deferred"}]) == "deferred"
    assert summarize_action_statuses([{"status": "executed"}, {"status": "deferred"}]) == "partial"
    assert summarize_action_statuses([{"status": "executed"}, {"status": "skipped"}]) == "partial"
    assert summarize_action_statuses([{"status": "executed"}, {"status": "failed"}]) == "partial"
    assert summarize_action_statuses([{"status": "failed"}]) == "failed"
