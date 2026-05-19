from io import BytesIO


def test_csv_upload_creates_dataset_and_report(client) -> None:
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

    assert response.status_code == 201
    body = response.json()
    assert body["workspace_id"] == workspace_id
    assert body["dataset_name"] == "sales"
    assert body["row_count"] == 2
    assert body["quality_score"] == 100
    assert body["rejected_rows"] == 0
    assert body["report_id"] > 0

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
