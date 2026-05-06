def test_guidance_plan_generation_and_fetch(client) -> None:
    ws_resp = client.post("/api/v1/workspaces", json={"name": "guide-ws", "description": "guidance tests"})
    assert ws_resp.status_code == 201
    workspace_id = ws_resp.json()["id"]

    gen_resp = client.post(
        "/api/v1/guidance/generate",
        json={
            "workspace_id": workspace_id,
            "objective": "Improve quarterly planning with reliable metrics",
        },
    )
    assert gen_resp.status_code == 201
    body = gen_resp.json()
    assert body["workspace_id"] == workspace_id
    assert body["objective"] == "Improve quarterly planning with reliable metrics"
    assert body["kpis_json"]
    assert body["milestones_json"]
    assert body["risks_json"]

    plan_id = body["id"]
    get_resp = client.get(f"/api/v1/guidance/{plan_id}")
    assert get_resp.status_code == 200
    get_body = get_resp.json()
    assert get_body["id"] == plan_id
