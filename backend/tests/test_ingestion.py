from io import BytesIO


def test_csv_upload_creates_dataset_and_report(client, complete_upload) -> None:
    response = client.post(
        "/api/v1/ingestion/upload",
        data={"workspace_id": 1, "dataset_name": "sales"},
        files={"file": ("sales.csv", BytesIO(b"id,amount\n1,10\n2,20\n"), "text/csv")},
    )

    assert response.status_code == 404

    workspace_response = client.post("/api/v1/workspaces", json={"name": "analysis", "description": "team workspace"})
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    response = client.post(
        "/api/v1/ingestion/upload",
        data={"workspace_id": workspace_id, "dataset_name": "sales"},
        files={"file": ("sales.csv", BytesIO(b"id,amount\n1,10\n2,20\n"), "text/csv")},
    )

    assert response.status_code == 202
    accepted = response.json()
    assert accepted["status"] == "queued"
    assert accepted["work_item_id"] > 0
    body = complete_upload(response)
    assert body["workspace_id"] == workspace_id
    assert body["dataset_name"] == "sales"
    assert body["job_id"] > 0
    assert body["status"] == "completed"
    assert body["finished_at"] is not None
    assert body["progress_percent"] == 100
    assert body["row_count"] == 2
    assert body["quality_score"] == 100
    assert body["rejected_rows"] == 0
    assert body["report_id"] > 0

    job_response = client.get(f"/api/v1/ingestion/jobs/{body['job_id']}")
    assert job_response.status_code == 200
    job_body = job_response.json()
    assert job_body["status"] == "completed"
    assert job_body["dataset_id"] == body["dataset_id"]
    assert job_body["source_name"] == "sales.csv"
    assert job_body["finished_at"] is not None

    job_list_response = client.get(f"/api/v1/ingestion/jobs?workspace_id={workspace_id}")
    assert job_list_response.status_code == 200
    assert job_list_response.headers["X-Total-Count"] == "1"
    assert job_list_response.json()[0]["id"] == body["job_id"]

    quality_response = client.get(f"/api/v1/datasets/{body['dataset_id']}/quality")
    assert quality_response.status_code == 200
    quality_body = quality_response.json()
    assert quality_body["metadata"]["profile_version"] == "1.2"
    assert quality_body["metadata"]["ingestion_job_id"] == body["job_id"]
    assert quality_body["metadata"]["source_name"] == "sales.csv"
    assert quality_body["metadata"]["column_count"] == 2
    assert quality_body["metadata"]["profile_fingerprint"]

    query_response = client.post(
        f"/api/v1/lakehouse/{body['dataset_id']}/query",
        json={"sql": "SELECT id, amount FROM dataset ORDER BY id"},
    )

    assert query_response.status_code == 200
    query_body = query_response.json()
    assert query_body["row_count"] == 2
    assert query_body["columns"] == ["id", "amount"]
    assert query_body["rows"][0]["id"] == 1
    assert query_body["rows"][0]["amount"] == 10

    datasets_query_response = client.post(
        f"/api/v1/datasets/{body['dataset_id']}/query",
        json={"sql": "SELECT id, amount FROM dataset ORDER BY id"},
    )
    assert datasets_query_response.status_code == 200
    assert datasets_query_response.json()["row_count"] == 2

    stats_response = client.get(f"/api/v1/analytics/datasets/{body['dataset_id']}/statistics")
    assert stats_response.status_code == 200
    stats_body = stats_response.json()
    assert stats_body["dataset_id"] == body["dataset_id"]
    assert stats_body["row_count"] == 2
    assert stats_body["column_count"] == 2
    assert stats_body["columns"][0]["name"] == "id"

    dashboard_response = client.post(
        "/api/v1/visualizations/dashboards",
        json={"workspace_id": workspace_id, "name": "Sales Overview", "description": "Revenue tracking"},
    )
    assert dashboard_response.status_code == 201

    audit_response = client.get(f"/api/v1/governance/audit?workspace_id={workspace_id}")
    assert audit_response.status_code == 200
    audit_types = [event["event_type"] for event in audit_response.json()]
    assert "dataset.uploaded" in audit_types
    assert "dataset.query_executed" in audit_types
    assert "dashboard.created" in audit_types
