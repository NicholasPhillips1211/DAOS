from io import BytesIO


def test_dashboard_creation_and_chart_recommendation(client) -> None:
    workspace_response = client.post("/api/v1/workspaces", json={"name": "viz-team", "description": "visualization workspace"})
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    dashboard_response = client.post(
        "/api/v1/visualizations/dashboards",
        json={"workspace_id": workspace_id, "name": "Executive Overview", "description": "summary dashboard"},
    )
    assert dashboard_response.status_code == 201
    dashboard_body = dashboard_response.json()
    assert dashboard_body["workspace_id"] == workspace_id
    assert dashboard_body["name"] == "Executive Overview"

    upload_response = client.post(
        "/api/v1/ingestion/upload",
        data={"workspace_id": workspace_id, "dataset_name": "sales-by-region"},
        files={
            "file": (
                "sales-by-region.csv",
                BytesIO(b"region,revenue\nNorth,100\nSouth,150\nWest,130\n"),
                "text/csv",
            )
        },
    )
    assert upload_response.status_code == 201
    dataset_id = upload_response.json()["dataset_id"]

    recommendation_response = client.post(
        "/api/v1/visualizations/recommend-chart",
        json={"dataset_id": dataset_id, "x_column": "region", "y_column": "revenue", "goal": "compare"},
    )
    assert recommendation_response.status_code == 200
    recommendation_body = recommendation_response.json()
    assert recommendation_body["chart_type"] == "bar"
    assert recommendation_body["best_practices"]


def test_dashboard_dependencies_kpi_owners_and_dataset_impact(client) -> None:
    workspace_response = client.post(
        "/api/v1/workspaces",
        json={"name": "operational-dashboard-ws", "description": "dashboard dependency tests"},
    )
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    upload_response = client.post(
        "/api/v1/ingestion/upload",
        data={"workspace_id": workspace_id, "dataset_name": "sales"},
        files={"file": ("sales.csv", BytesIO(b"id,amount\n1,10\n2,20\n"), "text/csv")},
    )
    assert upload_response.status_code == 201
    dataset_id = upload_response.json()["dataset_id"]

    query_response = client.post(
        f"/api/v1/datasets/{dataset_id}/query",
        json={"sql": "SELECT id, amount FROM dataset ORDER BY id"},
    )
    assert query_response.status_code == 200

    history_response = client.get(
        "/api/v1/analytics/query-executions",
        params={"workspace_id": workspace_id, "dataset_id": dataset_id},
    )
    assert history_response.status_code == 200
    query_execution_id = history_response.json()[0]["id"]

    dashboard_response = client.post(
        "/api/v1/visualizations/dashboards",
        json={"workspace_id": workspace_id, "name": "Sales Operations", "description": "Operational KPIs"},
    )
    assert dashboard_response.status_code == 201
    dashboard_id = dashboard_response.json()["id"]

    dependency_response = client.post(
        f"/api/v1/visualizations/dashboards/{dashboard_id}/dependencies",
        json={
            "dataset_id": dataset_id,
            "query_execution_id": query_execution_id,
            "dependency_type": "sales_kpi_source",
            "details": {"metric": "revenue"},
        },
    )
    assert dependency_response.status_code == 201
    dependency = dependency_response.json()
    assert dependency["dashboard_id"] == dashboard_id
    assert dependency["dataset_id"] == dataset_id
    assert dependency["query_execution_id"] == query_execution_id
    assert dependency["dependency_type"] == "sales_kpi_source"
    assert dependency["details"]["metric"] == "revenue"

    dependency_list_response = client.get(f"/api/v1/visualizations/dashboards/{dashboard_id}/dependencies")
    assert dependency_list_response.status_code == 200
    assert dependency_list_response.json()[0]["id"] == dependency["id"]

    kpi_owner_response = client.post(
        f"/api/v1/visualizations/dashboards/{dashboard_id}/kpi-owners",
        json={
            "kpi_name": "Revenue",
            "owner_email": "Revenue.Owner@Example.com",
            "description": "Accountable for monthly revenue reporting",
        },
    )
    assert kpi_owner_response.status_code == 201
    kpi_owner = kpi_owner_response.json()
    assert kpi_owner["dashboard_id"] == dashboard_id
    assert kpi_owner["kpi_name"] == "Revenue"
    assert kpi_owner["owner_email"] == "revenue.owner@example.com"

    impact_response = client.get(
        "/api/v1/visualizations/dashboards/impact",
        params={"workspace_id": workspace_id, "dataset_id": dataset_id},
    )
    assert impact_response.status_code == 200
    impact = impact_response.json()
    assert impact["impacted_dashboard_count"] == 1
    assert impact["dashboards"][0]["dashboard_id"] == dashboard_id
    assert impact["dashboards"][0]["query_execution_id"] == query_execution_id
    assert impact["dashboards"][0]["kpi_owners"][0]["owner_email"] == "revenue.owner@example.com"

    lineage_response = client.get(
        "/api/v1/metadata/lineage",
        params={"workspace_id": workspace_id, "asset_type": "dashboard", "asset_id": dashboard_id},
    )
    assert lineage_response.status_code == 200
    lineage = lineage_response.json()
    assert any(
        record["upstream_type"] == "dataset"
        and record["upstream_id"] == dataset_id
        and record["downstream_type"] == "dashboard"
        and record["relation_type"] == "powers_dashboard"
        for record in lineage
    )
    assert any(
        record["upstream_type"] == "query_execution"
        and record["upstream_id"] == query_execution_id
        and record["downstream_type"] == "dashboard"
        and record["relation_type"] == "feeds_dashboard"
        for record in lineage
    )

    usage_response = client.get(
        "/api/v1/metadata/usage",
        params={"workspace_id": workspace_id, "asset_type": "dashboard", "asset_id": dashboard_id},
    )
    assert usage_response.status_code == 200
    usage_actions = {record["action"] for record in usage_response.json()}
    assert "dashboard.dependency_registered" in usage_actions
    assert "dashboard.kpi_owner_assigned" in usage_actions
