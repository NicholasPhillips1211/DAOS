from io import BytesIO


def test_recommendation_generation_for_new_workspace(client) -> None:
    ws_resp = client.post("/api/v1/workspaces", json={"name": "rec-new", "description": "recommendations"})
    assert ws_resp.status_code == 201
    workspace_id = ws_resp.json()["id"]

    gen_resp = client.post(f"/api/v1/recommendations/generate?workspace_id={workspace_id}")
    assert gen_resp.status_code == 200
    body = gen_resp.json()
    assert body["created_count"] >= 1

    titles = {item["title"] for item in body["recommendations"]}
    assert "Ingest your first dataset" in titles


def test_recommendation_generation_for_maturing_workspace(client, complete_upload) -> None:
    ws_resp = client.post("/api/v1/workspaces", json={"name": "rec-mature", "description": "recommendations"})
    assert ws_resp.status_code == 201
    workspace_id = ws_resp.json()["id"]

    upload_resp = client.post(
        "/api/v1/ingestion/upload",
        data={"workspace_id": workspace_id, "dataset_name": "sales"},
        files={
            "file": (
                "sales.csv",
                BytesIO(b"feature,target\n1,yes\n2,no\n3,yes\n4,no\n"),
                "text/csv",
            )
        },
    )
    upload_body = complete_upload(upload_resp)
    dataset_id = upload_body["dataset_id"]

    insight_resp = client.post(
        "/api/v1/analytics/insights",
        json={
            "workspace_id": workspace_id,
            "title": "Target variance",
            "summary": "Target fluctuates across rows.",
            "evidence_json": "{\"field\":\"target\"}",
        },
    )
    assert insight_resp.status_code == 201

    gen_resp = client.post(f"/api/v1/recommendations/generate?workspace_id={workspace_id}")
    assert gen_resp.status_code == 200
    body = gen_resp.json()

    rec_types = {item["recommendation_type"] for item in body["recommendations"]}
    assert "pipeline" in rec_types
    assert "ml" in rec_types
    assert "visualization" in rec_types
    assert "business" in rec_types

    # Listing should return stored recommendations for the workspace.
    list_resp = client.get(f"/api/v1/recommendations?workspace_id={workspace_id}")
    assert list_resp.status_code == 200
    listed = list_resp.json()
    assert len(listed) == body["created_count"]

    # Sanity: dataset has been created and tied to workspace path for later pipeline/ml work.
    assert isinstance(dataset_id, int)
