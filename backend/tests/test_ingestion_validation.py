from io import BytesIO


def test_upload_rejects_non_csv(client) -> None:
    workspace_response = client.post("/api/v1/workspaces", json={"name": "ingestion-ext", "description": "validation tests"})
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    response = client.post(
        "/api/v1/ingestion/upload",
        data={"workspace_id": workspace_id, "dataset_name": "sales"},
        files={"file": ("sales.json", BytesIO(b"{}"), "application/json")},
    )

    assert response.status_code == 400
    body = response.json()
    assert "Only CSV uploads are supported" in body["error"]["message"]

    jobs_response = client.get(f"/api/v1/ingestion/jobs?workspace_id={workspace_id}")
    assert jobs_response.status_code == 200
    jobs = jobs_response.json()
    assert len(jobs) == 1
    assert jobs[0]["status"] == "failed"
    assert jobs[0]["source_name"] == "sales.json"
    assert "Only CSV uploads are supported" in jobs[0]["error_message"]


def test_upload_rejects_blank_dataset_name(client) -> None:
    workspace_response = client.post("/api/v1/workspaces", json={"name": "ingestion-name", "description": "validation tests"})
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    response = client.post(
        "/api/v1/ingestion/upload",
        data={"workspace_id": workspace_id, "dataset_name": "   "},
        files={"file": ("sales.csv", BytesIO(b"id,amount\n1,10\n"), "text/csv")},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["message"] == "Dataset name is required"

    jobs_response = client.get(f"/api/v1/ingestion/jobs?workspace_id={workspace_id}")
    assert jobs_response.status_code == 200
    jobs = jobs_response.json()
    assert len(jobs) == 1
    assert jobs[0]["status"] == "failed"
    assert jobs[0]["source_name"] == "sales.csv"
    assert jobs[0]["error_message"] == "Dataset name is required"
