from io import BytesIO


def test_metrics_snapshot_tracks_requests_and_errors(client) -> None:
    health_response = client.get("/api/v1/health")
    assert health_response.status_code == 200

    not_found_response = client.get("/api/v1/does-not-exist")
    assert not_found_response.status_code == 404

    metrics_response = client.get("/api/v1/observability/metrics")
    assert metrics_response.status_code == 200

    payload = metrics_response.json()
    assert payload["request_count"] >= 2
    assert payload["error_count"] >= 1
    assert "404" in payload["status_counts"]
    assert any(request["path"] == "/api/v1/health" for request in payload["recent_requests"])
    assert any(err_type.startswith("http_") for err_type in payload["error_types"]) 


def test_workflow_snapshot_summarizes_workspace_statuses(client, complete_upload) -> None:
    workspace_response = client.post("/api/v1/workspaces", json={"name": "workflow-observe", "description": "status rollup"})
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    upload_response = client.post(
        "/api/v1/ingestion/upload",
        data={"workspace_id": workspace_id, "dataset_name": "observed-sales"},
        files={"file": ("observed-sales.csv", BytesIO(b"id,amount\n1,10\n2,20\n"), "text/csv")},
    )
    complete_upload(upload_response)

    snapshot_response = client.get(f"/api/v1/observability/workflows?workspace_id={workspace_id}")
    assert snapshot_response.status_code == 200

    payload = snapshot_response.json()
    assert payload["workspace_id"] == workspace_id
    assert payload["work_items"]["succeeded"] == 1
    assert payload["ingestion_jobs"]["completed"] == 1
    assert payload["summary"]["terminal_count"] >= 2
    assert payload["summary"]["failed_or_partial_count"] == 0


def test_workflow_snapshot_counts_pending_automation_and_scheduled_pipeline_as_active(client) -> None:
    workspace_response = client.post("/api/v1/workspaces", json={"name": "workflow-active", "description": "active status rollup"})
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    automation_response = client.post(
        "/api/v1/automation/generate",
        json={"workspace_id": workspace_id, "objective": "Prepare next operational step"},
    )
    assert automation_response.status_code == 201

    pipeline_response = client.post(
        "/api/v1/pipelines",
        json={"workspace_id": workspace_id, "name": "daily-active", "description": "scheduled workflow"},
    )
    assert pipeline_response.status_code == 201
    pipeline_id = pipeline_response.json()["id"]
    schedule_response = client.post(
        f"/api/v1/pipelines/{pipeline_id}/schedule",
        json={"schedule_cron": "0 6 * * *"},
    )
    assert schedule_response.status_code == 200

    snapshot_response = client.get(f"/api/v1/observability/workflows?workspace_id={workspace_id}")
    assert snapshot_response.status_code == 200

    payload = snapshot_response.json()
    assert payload["automation_plans"]["execution_status"]["pending"] == 1
    assert payload["pipelines"]["scheduled"] == 1
    assert payload["summary"]["active_count"] >= 2
