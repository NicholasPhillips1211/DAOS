def test_quality_endpoint_returns_404_when_dataset_has_no_report(client) -> None:
    workspace_response = client.post("/api/v1/workspaces", json={"name": "quality-ws", "description": "quality tests"})
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    dataset_response = client.post(
        "/api/v1/datasets",
        json={
            "workspace_id": workspace_id,
            "name": "manual-dataset",
            "source_type": "file",
            "storage_path": None,
        },
    )
    assert dataset_response.status_code == 201
    dataset_id = dataset_response.json()["id"]

    quality_response = client.get(f"/api/v1/datasets/{dataset_id}/quality")
    assert quality_response.status_code == 404
    assert quality_response.json()["error"]["message"] == "No quality report found for this dataset"


def test_profile_endpoint_returns_400_without_storage_path(client) -> None:
    workspace_response = client.post("/api/v1/workspaces", json={"name": "quality-path", "description": "quality tests"})
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    dataset_response = client.post(
        "/api/v1/datasets",
        json={
            "workspace_id": workspace_id,
            "name": "manual-dataset-2",
            "source_type": "file",
            "storage_path": None,
        },
    )
    assert dataset_response.status_code == 201
    dataset_id = dataset_response.json()["id"]

    profile_response = client.get(f"/api/v1/datasets/{dataset_id}/profile")
    assert profile_response.status_code == 400
    assert profile_response.json()["error"]["message"] == "Dataset has no storage path for profiling"
