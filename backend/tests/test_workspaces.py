from io import BytesIO


def test_root_endpoint(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "Intelligent DataOps Platform"


def test_workspace_summary_reflects_empty_and_populated_states(client) -> None:
    workspace_response = client.post("/api/v1/workspaces", json={"name": "analysis", "description": "team workspace"})
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    summary_response = client.get(f"/api/v1/workspaces/{workspace_id}/summary")
    assert summary_response.status_code == 200
    summary_body = summary_response.json()
    assert summary_body["workspace_id"] == workspace_id
    assert summary_body["dataset_count"] == 0
    assert summary_body["membership_count"] == 0
    assert summary_body["has_datasets"] is False
    assert summary_body["recent_datasets"] == []
    assert "Upload a CSV" in summary_body["recommended_next_action"]

    upload_response = client.post(
        "/api/v1/ingestion/upload",
        data={"workspace_id": workspace_id, "dataset_name": "sales"},
        files={"file": ("sales.csv", BytesIO(b"id,amount\n1,10\n2,20\n"), "text/csv")},
    )
    assert upload_response.status_code == 201

    refreshed_summary_response = client.get(f"/api/v1/workspaces/{workspace_id}/summary")
    assert refreshed_summary_response.status_code == 200
    refreshed_summary = refreshed_summary_response.json()
    assert refreshed_summary["dataset_count"] == 1
    assert refreshed_summary["has_datasets"] is True
    assert refreshed_summary["latest_dataset"]["name"] == "sales"
    assert refreshed_summary["recent_datasets"][0]["name"] == "sales"
