def test_business_translation_generation(client) -> None:
    # create workspace
    ws_resp = client.post("/api/v1/workspaces", json={"name": "biz-ws", "description": "business translation tests"})
    assert ws_resp.status_code == 201
    workspace_id = ws_resp.json()["id"]

    # create an insight
    insight_resp = client.post(
        "/api/v1/analytics/insights",
        json={
            "workspace_id": workspace_id,
            "title": "Revenue spike in Q1",
            "summary": "Revenue increased 25% in Q1 compared to Q4, driven by promotions.",
            "evidence_json": "{\"metric\": \"revenue\", \"delta\": 25}",
        },
    )
    assert insight_resp.status_code == 201
    insight_id = insight_resp.json()["id"]

    # generate business translation
    bt_resp = client.post(
        "/api/v1/business/translate",
        json={"workspace_id": workspace_id, "insight_id": insight_id, "audience": "executive"},
    )
    assert bt_resp.status_code == 201
    body = bt_resp.json()
    assert body["workspace_id"] == workspace_id
    assert body["insight_id"] == insight_id
    assert "executive" in body["summary"]

    # fetch the translation
    get_resp = client.get(f"/api/v1/business/{body['id']}")
    assert get_resp.status_code == 200
    get_body = get_resp.json()
    assert get_body["id"] == body["id"]
