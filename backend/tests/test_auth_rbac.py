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


def test_workspace_listing_is_scoped_to_authenticated_member(client) -> None:
    original_enabled = settings.auth_enabled
    original_keys = settings.api_keys_csv
    settings.auth_enabled = True
    settings.api_keys_csv = "secret-key"
    try:
        owner_headers = {"X-API-Key": "secret-key", "X-User-Email": "owner@example.com"}
        analyst_headers = {"X-API-Key": "secret-key", "X-User-Email": "analyst@example.com"}

        first_workspace = client.post(
            "/api/v1/workspaces",
            json={"name": "owner-ws", "description": "owned by owner"},
            headers=owner_headers,
        )
        assert first_workspace.status_code == 201

        second_workspace = client.post(
            "/api/v1/workspaces",
            json={"name": "analyst-ws", "description": "owned by analyst"},
            headers=analyst_headers,
        )
        assert second_workspace.status_code == 201

        list_response = client.get("/api/v1/workspaces", headers=analyst_headers)
        assert list_response.status_code == 200
        workspaces = list_response.json()
        assert [workspace["name"] for workspace in workspaces] == ["analyst-ws"]
    finally:
        settings.auth_enabled = original_enabled
        settings.api_keys_csv = original_keys


def test_rbac_allows_generate_for_member_and_blocks_admin_only_action(client) -> None:
    original_enabled = settings.auth_enabled
    original_keys = settings.api_keys_csv
    settings.auth_enabled = True
    settings.api_keys_csv = "secret-key"
    try:
        owner_headers = {"X-API-Key": "secret-key", "X-User-Email": "owner@example.com"}
        headers = {"X-API-Key": "secret-key", "X-User-Email": "analyst@example.com"}

        workspace_response = client.post(
            "/api/v1/workspaces",
            json={"name": "rbac-ws", "description": "rbac checks"},
            headers=owner_headers,
        )
        assert workspace_response.status_code == 201
        workspace_id = workspace_response.json()["id"]

        member_response = client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            json={"user_email": "analyst@example.com", "role": "analyst"},
            headers=owner_headers,
        )
        assert member_response.status_code == 201

        member_response = client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            json={"user_email": "analyst@example.com", "role": "analyst"},
            headers=headers,
        )
        assert member_response.status_code == 403

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
        assert any(event["event_type"] == "workspace.created" for event in audit_events)
        assert any(event["event_type"] == "workspace.member_added" for event in audit_events)
        assert any(event["event_type"] == "security.access_denied" for event in audit_events)
    finally:
        settings.auth_enabled = original_enabled
        settings.api_keys_csv = original_keys
