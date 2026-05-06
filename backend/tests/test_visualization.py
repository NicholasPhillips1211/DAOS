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
