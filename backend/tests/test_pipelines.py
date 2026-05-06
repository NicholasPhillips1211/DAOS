def test_pipeline_schedule_and_version(client) -> None:
    workspace_response = client.post("/api/v1/workspaces", json={"name": "pipelines", "description": "pipeline team"})
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    pipeline_response = client.post(
        "/api/v1/pipelines",
        json={"workspace_id": workspace_id, "name": "daily-sales", "description": "daily refresh"},
    )
    assert pipeline_response.status_code == 201
    pipeline_id = pipeline_response.json()["id"]

    schedule_response = client.post(
        f"/api/v1/pipelines/{pipeline_id}/schedule",
        json={"schedule_cron": "0 6 * * *"},
    )
    assert schedule_response.status_code == 200
    schedule_body = schedule_response.json()
    assert schedule_body["schedule_cron"] == "0 6 * * *"
    assert schedule_body["status"] == "scheduled"

    version_response = client.post(
        f"/api/v1/pipelines/{pipeline_id}/versions",
        json={"definition_json": '{"nodes": [{"id": "source"}, {"id": "transform"}], "edges": [{"from": "source", "to": "transform"}]}'},
    )
    assert version_response.status_code == 201
    assert version_response.json() == {"pipeline_id": pipeline_id, "version": 1}

    invalid_response = client.post(
        f"/api/v1/pipelines/{pipeline_id}/versions",
        json={"definition_json": '{"nodes": [], "edges": []}'},
    )
    assert invalid_response.status_code == 400
