from io import BytesIO

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


def test_core_data_routes_require_workspace_membership(client) -> None:
    original_enabled = settings.auth_enabled
    original_keys = settings.api_keys_csv
    settings.auth_enabled = True
    settings.api_keys_csv = "secret-key"
    try:
        owner_headers = {"X-API-Key": "secret-key", "X-User-Email": "owner@example.com"}
        outsider_headers = {"X-API-Key": "secret-key", "X-User-Email": "outsider@example.com"}

        workspace_response = client.post(
            "/api/v1/workspaces",
            json={"name": "protected-ws", "description": "rbac protected data"},
            headers=owner_headers,
        )
        assert workspace_response.status_code == 201
        workspace_id = workspace_response.json()["id"]

        upload_response = client.post(
            "/api/v1/ingestion/upload",
            data={"workspace_id": workspace_id, "dataset_name": "sales"},
            files={"file": ("sales.csv", BytesIO(b"id,amount\n1,10\n2,20\n"), "text/csv")},
            headers=owner_headers,
        )
        assert upload_response.status_code == 201
        dataset_id = upload_response.json()["dataset_id"]
        job_id = upload_response.json()["job_id"]

        blocked_upload = client.post(
            "/api/v1/ingestion/upload",
            data={"workspace_id": workspace_id, "dataset_name": "blocked"},
            files={"file": ("blocked.csv", BytesIO(b"id\n1\n"), "text/csv")},
            headers=outsider_headers,
        )
        assert blocked_upload.status_code == 403

        blocked_jobs = client.get(f"/api/v1/ingestion/jobs?workspace_id={workspace_id}", headers=outsider_headers)
        assert blocked_jobs.status_code == 403
        blocked_job_detail = client.get(f"/api/v1/ingestion/jobs/{job_id}", headers=outsider_headers)
        assert blocked_job_detail.status_code == 403

        assert client.get("/api/v1/datasets", headers=owner_headers).status_code == 400
        assert client.get(f"/api/v1/datasets?workspace_id={workspace_id}", headers=outsider_headers).status_code == 403
        assert client.get(f"/api/v1/datasets/{dataset_id}/quality", headers=outsider_headers).status_code == 403
        assert client.get("/api/v1/analytics/query-executions", headers=owner_headers).status_code == 400
        assert client.get(f"/api/v1/analytics/query-executions?workspace_id={workspace_id}", headers=outsider_headers).status_code == 403
        assert client.get("/api/v1/analytics/saved-queries", headers=owner_headers).status_code == 400
        assert client.get(f"/api/v1/analytics/saved-queries?workspace_id={workspace_id}", headers=outsider_headers).status_code == 403
        blocked_saved_query = client.post(
            "/api/v1/analytics/saved-queries",
            json={
                "workspace_id": workspace_id,
                "dataset_id": dataset_id,
                "name": "Blocked",
                "sql_text": "SELECT id FROM dataset",
            },
            headers=outsider_headers,
        )
        assert blocked_saved_query.status_code == 403

        blocked_dataset_query = client.post(
            f"/api/v1/datasets/{dataset_id}/query",
            json={"sql": "SELECT id FROM dataset"},
            headers=outsider_headers,
        )
        assert blocked_dataset_query.status_code == 403

        blocked_lakehouse_query = client.post(
            f"/api/v1/lakehouse/{dataset_id}/query",
            json={"sql": "SELECT id FROM dataset"},
            headers=outsider_headers,
        )
        assert blocked_lakehouse_query.status_code == 403

        blocked_chart = client.post(
            "/api/v1/visualizations/recommend-chart",
            json={"dataset_id": dataset_id, "x_column": "id", "y_column": "amount", "goal": "compare"},
            headers=outsider_headers,
        )
        assert blocked_chart.status_code == 403

        assert client.get("/api/v1/visualizations/dashboards", headers=owner_headers).status_code == 400
        blocked_dashboard_list = client.get(
            f"/api/v1/visualizations/dashboards?workspace_id={workspace_id}",
            headers=outsider_headers,
        )
        assert blocked_dashboard_list.status_code == 403

        dashboard_response = client.post(
            "/api/v1/visualizations/dashboards",
            json={"workspace_id": workspace_id, "name": "Protected", "description": "Owner dashboard"},
            headers=owner_headers,
        )
        assert dashboard_response.status_code == 201
        dashboard_id = dashboard_response.json()["id"]

        blocked_dashboard_create = client.post(
            "/api/v1/visualizations/dashboards",
            json={"workspace_id": workspace_id, "name": "Blocked", "description": "Should not create"},
            headers=outsider_headers,
        )
        assert blocked_dashboard_create.status_code == 403
        blocked_impact = client.get(
            "/api/v1/visualizations/dashboards/impact",
            params={"workspace_id": workspace_id, "dataset_id": dataset_id},
            headers=outsider_headers,
        )
        assert blocked_impact.status_code == 403
        blocked_dependency_list = client.get(
            f"/api/v1/visualizations/dashboards/{dashboard_id}/dependencies",
            headers=outsider_headers,
        )
        assert blocked_dependency_list.status_code == 403
        blocked_dependency_create = client.post(
            f"/api/v1/visualizations/dashboards/{dashboard_id}/dependencies",
            json={"dataset_id": dataset_id},
            headers=outsider_headers,
        )
        assert blocked_dependency_create.status_code == 403
        blocked_kpi_owner_list = client.get(
            f"/api/v1/visualizations/dashboards/{dashboard_id}/kpi-owners",
            headers=outsider_headers,
        )
        assert blocked_kpi_owner_list.status_code == 403
        blocked_kpi_owner_create = client.post(
            f"/api/v1/visualizations/dashboards/{dashboard_id}/kpi-owners",
            json={"kpi_name": "Revenue", "owner_email": "owner@example.com"},
            headers=outsider_headers,
        )
        assert blocked_kpi_owner_create.status_code == 403

        blocked_metadata = client.get(
            "/api/v1/metadata/events",
            params={"workspace_id": workspace_id},
            headers=outsider_headers,
        )
        assert blocked_metadata.status_code == 403
        for metadata_path in (
            "/api/v1/metadata/schemas",
            "/api/v1/metadata/lineage",
            "/api/v1/metadata/usage",
            "/api/v1/metadata/ai-context",
        ):
            blocked_metadata = client.get(
                metadata_path,
                params={"workspace_id": workspace_id},
                headers=outsider_headers,
            )
            assert blocked_metadata.status_code == 403
        blocked_context_build = client.post(
            "/api/v1/metadata/ai-context/build",
            json={"workspace_id": workspace_id, "objective": "Summarize protected workspace"},
            headers=outsider_headers,
        )
        assert blocked_context_build.status_code == 403
    finally:
        settings.auth_enabled = original_enabled
        settings.api_keys_csv = original_keys
