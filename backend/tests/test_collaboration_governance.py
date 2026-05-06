def test_collaboration_and_governance_endpoints(client) -> None:
    # create workspace
    ws_resp = client.post("/api/v1/workspaces", json={"name": "collab-ws", "description": "workspace for collab tests"})
    assert ws_resp.status_code == 201
    workspace_id = ws_resp.json()["id"]

    # create a comment
    comment_resp = client.post(
        "/api/v1/collaboration/comments",
        json={
            "workspace_id": workspace_id,
            "resource_type": "dashboard",
            "resource_id": 1,
            "user_email": "alice@example.com",
            "message": "Looks good!",
        },
    )
    assert comment_resp.status_code == 201
    comment_body = comment_resp.json()
    assert comment_body["workspace_id"] == workspace_id
    assert comment_body["message"] == "Looks good!"

    # create a share
    share_resp = client.post(
        "/api/v1/collaboration/shares",
        json={
            "workspace_id": workspace_id,
            "resource_type": "dashboard",
            "resource_id": 1,
            "target_email": "bob@example.com",
            "permission": "view",
        },
    )
    assert share_resp.status_code == 201
    share_body = share_resp.json()
    assert share_body["workspace_id"] == workspace_id
    assert share_body["permission"] == "view"

    # list audit events (should include comment and share)
    audit_resp = client.get(f"/api/v1/governance/audit?workspace_id={workspace_id}")
    assert audit_resp.status_code == 200
    audit_list = audit_resp.json()
    assert len(audit_list) >= 2
    types = {e["event_type"] for e in audit_list}
    assert "comment.created" in types
    assert "share.created" in types

    # create a data mask
    mask_resp = client.post(
        "/api/v1/governance/masks",
        json={
            "workspace_id": workspace_id,
            "dataset_id": 1,
            "column_name": "email",
            "mask_type": "redact",
        },
    )
    assert mask_resp.status_code == 201
    mask_body = mask_resp.json()
    assert mask_body["workspace_id"] == workspace_id
    assert mask_body["column_name"] == "email"
