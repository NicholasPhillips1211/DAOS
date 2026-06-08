from datetime import datetime, timedelta, timezone
from io import BytesIO

from app.core.database import SessionLocal
from app.core.workflow_jobs import INGESTION_CLEAN_PROFILE_JOB, LEGACY_INGESTION_PROFILE_JOB
from app.models.metadata import Dataset
from app.models.work_item import WorkItem
from app.services.ingestion_workflow_service import IngestionWorkflowService
from app.services.work_queue_service import WorkQueueService
from app.workers.runner import WorkerRunner


def test_ingestion_upload_creates_visible_work_item(client, run_worker) -> None:
    workspace_response = client.post("/api/v1/workspaces", json={"name": "work-queue-ws", "description": "queue tests"})
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    upload_response = client.post(
        "/api/v1/ingestion/upload",
        data={"workspace_id": workspace_id, "dataset_name": "sales"},
        files={"file": ("sales.csv", BytesIO(b"id,amount\n1,10\n2,20\n"), "text/csv")},
    )
    assert upload_response.status_code == 202
    accepted = upload_response.json()
    assert accepted["status"] == "queued"
    assert accepted["work_item_id"] > 0

    work_item_response = client.get(f"/api/v1/work-items/{accepted['work_item_id']}")
    assert work_item_response.status_code == 200
    work_item = work_item_response.json()
    assert work_item["job_type"] == INGESTION_CLEAN_PROFILE_JOB
    assert work_item["status"] == "queued"
    assert work_item["payload"]["ingestion_job_id"] == accepted["job_id"]

    run_worker()

    completed_item_response = client.get(f"/api/v1/work-items/{accepted['work_item_id']}")
    assert completed_item_response.status_code == 200
    completed_item = completed_item_response.json()
    assert completed_item["status"] == "succeeded"
    assert completed_item["result"]["dataset_id"] > 0
    assert completed_item["result"]["quality_score"] == 100


def test_legacy_ingestion_profile_work_item_still_runs_with_clean_profile_filter(client) -> None:
    workspace_response = client.post(
        "/api/v1/workspaces",
        json={"name": "legacy-work-queue-ws", "description": "queue tests"},
    )
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    upload_response = client.post(
        "/api/v1/ingestion/upload",
        data={"workspace_id": workspace_id, "dataset_name": "legacy-sales"},
        files={"file": ("legacy-sales.csv", BytesIO(b"id,amount\n1,10\n2,20\n"), "text/csv")},
    )
    assert upload_response.status_code == 202
    accepted = upload_response.json()

    with SessionLocal() as db:
        work_item = db.get(WorkItem, accepted["work_item_id"])
        assert work_item is not None
        work_item.job_type = LEGACY_INGESTION_PROFILE_JOB
        db.add(work_item)
        db.commit()

    item = WorkerRunner(worker_id="legacy-filter-worker").run_once(job_types={INGESTION_CLEAN_PROFILE_JOB})
    assert item is not None
    assert item.status == "succeeded"
    assert item.job_type == LEGACY_INGESTION_PROFILE_JOB

    job_response = client.get(f"/api/v1/ingestion/jobs/{accepted['job_id']}")
    assert job_response.status_code == 200
    job = job_response.json()
    assert job["status"] == "completed"
    assert job["dataset_id"] is not None


def test_work_item_list_rejects_unknown_status_filter(client) -> None:
    response = client.get("/api/v1/work-items?workspace_id=1&status=done")

    assert response.status_code == 400
    assert response.json()["error"]["message"] == "Unknown workflow status"


def test_completed_ingestion_job_reuses_existing_dataset(client, complete_upload) -> None:
    workspace_response = client.post("/api/v1/workspaces", json={"name": "idempotent-ws", "description": "retry tests"})
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    upload_response = client.post(
        "/api/v1/ingestion/upload",
        data={"workspace_id": workspace_id, "dataset_name": "retry-safe-sales"},
        files={"file": ("retry-safe-sales.csv", BytesIO(b"id,amount\n1,10\n2,20\n"), "text/csv")},
    )
    accepted = complete_upload(upload_response)

    with SessionLocal() as db:
        dataset_count = db.query(Dataset).filter(Dataset.workspace_id == workspace_id).count()
        result = IngestionWorkflowService().process_queued_job(db, job_id=accepted["job_id"])
        assert result.dataset.id == accepted["dataset_id"]
        assert result.job.status == "completed"
        assert db.query(Dataset).filter(Dataset.workspace_id == workspace_id).count() == dataset_count


def test_ingestion_success_event_failure_does_not_corrupt_completed_job(client, run_worker, monkeypatch) -> None:
    workspace_response = client.post("/api/v1/workspaces", json={"name": "event-safe-ws", "description": "event failure tests"})
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    upload_response = client.post(
        "/api/v1/ingestion/upload",
        data={"workspace_id": workspace_id, "dataset_name": "event-safe-sales"},
        files={"file": ("event-safe-sales.csv", BytesIO(b"id,amount\n1,10\n2,20\n"), "text/csv")},
    )
    assert upload_response.status_code == 202
    accepted = upload_response.json()

    def fail_success_events(*args, **kwargs) -> None:
        raise RuntimeError("metadata sink unavailable")

    monkeypatch.setattr(IngestionWorkflowService, "emit_success_events", fail_success_events)

    run_worker()

    job_response = client.get(f"/api/v1/ingestion/jobs/{accepted['job_id']}")
    assert job_response.status_code == 200
    job = job_response.json()
    assert job["status"] == "completed"
    assert job["dataset_id"] is not None

    work_item_response = client.get(f"/api/v1/work-items/{accepted['work_item_id']}")
    assert work_item_response.status_code == 200
    assert work_item_response.json()["status"] == "succeeded"


def test_stale_work_item_is_reclaimed_by_next_worker(client) -> None:
    service = WorkQueueService()

    with SessionLocal() as db:
        queued = service.enqueue(db, job_type="test.noop", payload={"value": 1})
        claimed = service.claim_next(db, worker_id="stale-worker")
        assert claimed is not None
        assert claimed.id == queued.id
        assert claimed.attempts == 1

        claimed.locked_at = datetime.now(timezone.utc) - timedelta(seconds=120)
        db.add(claimed)
        db.commit()

        reclaimed = service.claim_next(db, worker_id="fresh-worker", stale_after_seconds=60)
        assert reclaimed is not None
        assert reclaimed.id == queued.id
        assert reclaimed.status == "running"
        assert reclaimed.locked_by == "fresh-worker"
        assert reclaimed.attempts == 2
        assert reclaimed.error_message is None


def test_async_query_ml_automation_and_dashboard_jobs(client, complete_upload, run_worker, monkeypatch) -> None:
    from app.core.config import settings

    workspace_response = client.post("/api/v1/workspaces", json={"name": "async-phase-four", "description": "worker tests"})
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    upload_response = client.post(
        "/api/v1/ingestion/upload",
        data={"workspace_id": workspace_id, "dataset_name": "training-data"},
        files={
            "file": (
                "training-data.csv",
                BytesIO(b"feature_1,feature_2,label\n1,0,A\n2,1,A\n3,2,A\n10,9,B\n11,10,B\n12,11,B\n"),
                "text/csv",
            )
        },
    )
    dataset_id = complete_upload(upload_response)["dataset_id"]

    query_job_response = client.post(
        f"/api/v1/datasets/{dataset_id}/query-jobs",
        json={"sql": "SELECT feature_1, label FROM dataset ORDER BY feature_1"},
    )
    assert query_job_response.status_code == 202
    query_work_item_id = query_job_response.json()["work_item_id"]
    run_worker()
    query_item = client.get(f"/api/v1/work-items/{query_work_item_id}").json()
    assert query_item["status"] == "succeeded"
    assert query_item["result"]["row_count"] == 6
    assert query_item["result"]["preview_row_count"] == 6
    assert query_item["result"]["preview_rows"][0] == {"feature_1": 1, "label": "A"}
    assert query_item["result"]["truncated"] is False
    assert "rows" not in query_item["result"]

    training_job_response = client.post(
        "/api/v1/ml/train-jobs",
        json={
            "workspace_id": workspace_id,
            "dataset_id": dataset_id,
            "target_column": "label",
            "task_type": "classification",
            "model_name": "async-label-classifier",
        },
    )
    assert training_job_response.status_code == 202
    training_work_item_id = training_job_response.json()["work_item_id"]
    run_worker()
    training_item = client.get(f"/api/v1/work-items/{training_work_item_id}").json()
    assert training_item["status"] == "succeeded"
    assert training_item["result"]["trained_model_id"] > 0
    assert training_item["result"]["metric_name"] == "accuracy"

    monkeypatch.setattr(settings, "llm_base_url", "")
    automation_job_response = client.post(
        "/api/v1/automation/generate-jobs",
        json={"workspace_id": workspace_id, "objective": "Keep reports healthy"},
    )
    assert automation_job_response.status_code == 202
    automation_work_item_id = automation_job_response.json()["work_item_id"]
    run_worker()
    automation_item = client.get(f"/api/v1/work-items/{automation_work_item_id}").json()
    assert automation_item["status"] == "succeeded"
    assert automation_item["result"]["automation_plan_id"] > 0

    dashboard_response = client.post(
        "/api/v1/visualizations/dashboards",
        json={"workspace_id": workspace_id, "name": "Async Dashboard", "description": "refresh target"},
    )
    assert dashboard_response.status_code == 201
    dashboard_id = dashboard_response.json()["id"]

    refresh_job_response = client.post(f"/api/v1/visualizations/dashboards/{dashboard_id}/refresh-jobs")
    assert refresh_job_response.status_code == 202
    refresh_work_item_id = refresh_job_response.json()["work_item_id"]
    run_worker()
    refresh_item = client.get(f"/api/v1/work-items/{refresh_work_item_id}").json()
    assert refresh_item["status"] == "succeeded"
    assert refresh_item["result"]["dashboard_id"] == dashboard_id
