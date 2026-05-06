from app.core.config import settings


def test_auth_enabled_requires_api_key(client) -> None:
    original_enabled = settings.auth_enabled
    original_keys = settings.api_keys_csv
    settings.auth_enabled = True
    settings.api_keys_csv = "secret-key"
    try:
        response = client.post("/api/v1/recommendations/generate?workspace_id=1")
        assert response.status_code == 401
    finally:
        settings.auth_enabled = original_enabled
        settings.api_keys_csv = original_keys


def test_rbac_allows_generate_for_member_and_blocks_admin_only_action(client) -> None:
    original_enabled = settings.auth_enabled
    original_keys = settings.api_keys_csv
    settings.auth_enabled = True
    settings.api_keys_csv = "secret-key"
    try:
        workspace_response = client.post("/api/v1/workspaces", json={"name": "rbac-ws", "description": "rbac checks"})
        assert workspace_response.status_code == 201
        workspace_id = workspace_response.json()["id"]

        member_response = client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            json={"user_email": "analyst@example.com", "role": "analyst"},
        )
        assert member_response.status_code == 201

        headers = {"X-API-Key": "secret-key", "X-User-Email": "analyst@example.com"}

        generate_response = client.post(f"/api/v1/recommendations/generate?workspace_id={workspace_id}", headers=headers)
        assert generate_response.status_code == 200

        # Governance mask creation is admin/owner only, so analyst role should be blocked.
        mask_response = client.post(
            "/api/v1/governance/masks",
            json={
                "workspace_id": workspace_id,
                "dataset_id": 1,
                "column_name": "email",
                "mask_type": "redact",
            },
            headers=headers,
        )
        assert mask_response.status_code == 403

        audit_response = client.get(f"/api/v1/governance/audit?workspace_id={workspace_id}", headers=headers)
        assert audit_response.status_code == 200
        audit_events = audit_response.json()
        assert any(event["event_type"] == "security.access_denied" for event in audit_events)
    finally:
        settings.auth_enabled = original_enabled
        settings.api_keys_csv = original_keys
