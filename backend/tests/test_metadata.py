from io import BytesIO


def test_ingestion_emits_queryable_metadata_event(client) -> None:
    workspace_response = client.post(
        "/api/v1/workspaces",
        json={"name": "metadata-ws", "description": "metadata event tests"},
    )
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    upload_response = client.post(
        "/api/v1/ingestion/upload",
        data={"workspace_id": workspace_id, "dataset_name": "sales"},
        files={"file": ("sales.csv", BytesIO(b"id,amount\n1,10\n2,20\n"), "text/csv")},
    )
    assert upload_response.status_code == 201
    upload_body = upload_response.json()

    metadata_response = client.get(
        "/api/v1/metadata/events",
        params={
            "workspace_id": workspace_id,
            "event_type": "metadata.ingestion.profile_created",
            "resource_type": "dataset",
            "resource_id": upload_body["dataset_id"],
        },
    )
    assert metadata_response.status_code == 200

    events = metadata_response.json()
    assert len(events) == 1

    event = events[0]
    assert event["workspace_id"] == workspace_id
    assert event["event_type"] == "metadata.ingestion.profile_created"
    assert event["resource_type"] == "dataset"
    assert event["resource_id"] == upload_body["dataset_id"]
    assert event["details"]["job_id"] == upload_body["job_id"]
    assert event["details"]["dataset_name"] == "sales"
    assert event["details"]["row_count"] == 2
    assert event["details"]["quality_score"] == 100
    assert event["details"]["status"] == "completed"


def test_ingestion_registers_lifecycle_metadata_records(client) -> None:
    workspace_response = client.post(
        "/api/v1/workspaces",
        json={"name": "metadata-core-ws", "description": "metadata core tests"},
    )
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    upload_response = client.post(
        "/api/v1/ingestion/upload",
        data={"workspace_id": workspace_id, "dataset_name": "sales"},
        files={"file": ("sales.csv", BytesIO(b"id,amount\n1,10\n2,20\n"), "text/csv")},
    )
    assert upload_response.status_code == 201
    upload_body = upload_response.json()
    dataset_id = upload_body["dataset_id"]
    job_id = upload_body["job_id"]

    schema_response = client.get(
        "/api/v1/metadata/schemas",
        params={"workspace_id": workspace_id, "asset_type": "dataset", "asset_id": dataset_id},
    )
    assert schema_response.status_code == 200
    assert schema_response.headers["X-Total-Count"] == "1"
    schema_record = schema_response.json()[0]
    assert schema_record["source"] == "sales.csv"
    assert schema_record["profile_fingerprint"]
    assert schema_record["schema"] == [
        {"name": "id", "inferred_type": "integer"},
        {"name": "amount", "inferred_type": "integer"},
    ]

    lineage_response = client.get(
        "/api/v1/metadata/lineage",
        params={"workspace_id": workspace_id, "asset_type": "dataset", "asset_id": dataset_id},
    )
    assert lineage_response.status_code == 200
    lineage_record = lineage_response.json()[0]
    assert lineage_record["upstream_type"] == "ingestion_job"
    assert lineage_record["upstream_id"] == job_id
    assert lineage_record["downstream_type"] == "dataset"
    assert lineage_record["downstream_id"] == dataset_id
    assert lineage_record["relation_type"] == "created_dataset"
    assert lineage_record["details"]["dataset_name"] == "sales"

    usage_response = client.get(
        "/api/v1/metadata/usage",
        params={
            "workspace_id": workspace_id,
            "asset_type": "dataset",
            "asset_id": dataset_id,
            "action": "information_collected",
        },
    )
    assert usage_response.status_code == 200
    usage_record = usage_response.json()[0]
    assert usage_record["details"]["job_id"] == job_id
    assert usage_record["details"]["quality_score"] == 100

    ai_context_response = client.get(
        "/api/v1/metadata/ai-context",
        params={
            "workspace_id": workspace_id,
            "context_type": "dataset_profile",
            "resource_type": "dataset",
            "resource_id": dataset_id,
        },
    )
    assert ai_context_response.status_code == 200
    ai_context = ai_context_response.json()[0]["context"]
    assert ai_context["dataset_name"] == "sales"
    assert ai_context["quality_score"] == 100
    assert ai_context["schema"][0]["name"] == "id"


def test_query_dashboard_and_automation_emit_lifecycle_metadata(client) -> None:
    workspace_response = client.post(
        "/api/v1/workspaces",
        json={"name": "metadata-usage-ws", "description": "metadata usage tests"},
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

    query_usage_response = client.get(
        "/api/v1/metadata/usage",
        params={
            "workspace_id": workspace_id,
            "asset_type": "dataset",
            "asset_id": dataset_id,
            "action": "dataset.query_executed",
        },
    )
    assert query_usage_response.status_code == 200
    query_usage = query_usage_response.json()[0]
    assert query_usage["details"]["route"] == "datasets"
    assert query_usage["details"]["row_count"] == 2

    dashboard_response = client.post(
        "/api/v1/visualizations/dashboards",
        json={"workspace_id": workspace_id, "name": "Sales Overview", "description": "Revenue tracking"},
    )
    assert dashboard_response.status_code == 201
    dashboard_id = dashboard_response.json()["id"]

    dashboard_usage_response = client.get(
        "/api/v1/metadata/usage",
        params={
            "workspace_id": workspace_id,
            "asset_type": "dashboard",
            "asset_id": dashboard_id,
            "action": "dashboard.created",
        },
    )
    assert dashboard_usage_response.status_code == 200
    assert dashboard_usage_response.json()[0]["details"]["name"] == "Sales Overview"

    automation_response = client.post(
        "/api/v1/automation/generate",
        json={"workspace_id": workspace_id, "objective": "Monitor sales quality"},
    )
    assert automation_response.status_code == 201
    plan_id = automation_response.json()["id"]

    ai_context_response = client.get(
        "/api/v1/metadata/ai-context",
        params={
            "workspace_id": workspace_id,
            "context_type": "automation_plan",
            "resource_type": "automation_plan",
            "resource_id": plan_id,
        },
    )
    assert ai_context_response.status_code == 200
    context = ai_context_response.json()[0]["context"]
    assert context["objective"] == "Monitor sales quality"
    assert context["plan"]["trace"]["grounding"]["signal_snapshot"]["dataset_count"] == 1


def test_query_execution_history_records_lineage_and_saved_queries(client) -> None:
    workspace_response = client.post(
        "/api/v1/workspaces",
        json={"name": "query-history-ws", "description": "query lineage tests"},
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

    save_response = client.post(
        "/api/v1/analytics/saved-queries",
        json={
            "workspace_id": workspace_id,
            "dataset_id": dataset_id,
            "name": "Sales by id",
            "sql_text": "SELECT id, amount FROM dataset ORDER BY id",
        },
    )
    assert save_response.status_code == 201
    saved_query = save_response.json()
    assert saved_query["name"] == "Sales by id"
    assert saved_query["dataset_id"] == dataset_id

    saved_list_response = client.get(
        "/api/v1/analytics/saved-queries",
        params={"workspace_id": workspace_id, "dataset_id": dataset_id},
    )
    assert saved_list_response.status_code == 200
    assert saved_list_response.headers["X-Total-Count"] == "1"
    assert saved_list_response.json()[0]["id"] == saved_query["id"]

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
    assert history_response.headers["X-Total-Count"] == "1"
    execution = history_response.json()[0]
    assert execution["dataset_id"] == dataset_id
    assert execution["route"] == "datasets"
    assert execution["row_count"] == 2
    assert execution["column_count"] == 2
    assert execution["duration_ms"] >= 0

    usage_response = client.get(
        "/api/v1/metadata/usage",
        params={
            "workspace_id": workspace_id,
            "asset_type": "dataset",
            "asset_id": dataset_id,
            "action": "dataset.query_executed",
        },
    )
    assert usage_response.status_code == 200
    usage = usage_response.json()[0]
    assert usage["details"]["query_execution_id"] == execution["id"]
    assert usage["details"]["route"] == "datasets"
    assert usage["details"]["row_count"] == 2

    lineage_response = client.get(
        "/api/v1/metadata/lineage",
        params={"workspace_id": workspace_id, "asset_type": "dataset", "asset_id": dataset_id},
    )
    assert lineage_response.status_code == 200
    query_lineage = [
        record
        for record in lineage_response.json()
        if record["downstream_type"] == "query_execution" and record["downstream_id"] == execution["id"]
    ]
    assert len(query_lineage) == 1
    assert query_lineage[0]["upstream_type"] == "dataset"
    assert query_lineage[0]["upstream_id"] == dataset_id
    assert query_lineage[0]["relation_type"] == "queried_by"


def test_ai_context_builder_uses_lifecycle_metadata(client) -> None:
    workspace_response = client.post(
        "/api/v1/workspaces",
        json={"name": "ai-context-ws", "description": "AI context builder tests"},
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
        json={"workspace_id": workspace_id, "name": "Sales Ops", "description": "Operational dashboard"},
    )
    assert dashboard_response.status_code == 201
    dashboard_id = dashboard_response.json()["id"]

    dependency_response = client.post(
        f"/api/v1/visualizations/dashboards/{dashboard_id}/dependencies",
        json={"dataset_id": dataset_id, "query_execution_id": query_execution_id},
    )
    assert dependency_response.status_code == 201
    owner_response = client.post(
        f"/api/v1/visualizations/dashboards/{dashboard_id}/kpi-owners",
        json={"kpi_name": "Revenue", "owner_email": "revenue@example.com"},
    )
    assert owner_response.status_code == 201

    context_response = client.post(
        "/api/v1/metadata/ai-context/build",
        json={"workspace_id": workspace_id, "objective": "Explain revenue dashboard readiness"},
    )
    assert context_response.status_code == 201
    body = context_response.json()
    assert body["context_type"] == "workspace_context"
    assert body["objective"] == "Explain revenue dashboard readiness"
    assert body["confidence_score"] >= 0.8
    assert "datasets" in body["sources"]
    assert "metadata.lineage" in body["sources"]
    assert "query_executions" in body["sources"]
    assert "dashboards" in body["sources"]
    assert body["context"]["lifecycle"]["information_collection"]["dataset_count"] == 1
    assert body["context"]["lifecycle"]["information_analysis"]["query_execution_count"] == 1
    assert body["context"]["lifecycle"]["information_operationalization"]["dashboard_count"] == 1
    assert body["context"]["lifecycle"]["information_operationalization"]["dashboards"][0]["kpi_owners"][0]["owner_email"] == "revenue@example.com"
    assert body["recommended_next_actions"]

    stored_context_response = client.get(
        "/api/v1/metadata/ai-context",
        params={
            "workspace_id": workspace_id,
            "context_type": "workspace_context",
            "resource_type": "workspace",
            "resource_id": workspace_id,
        },
    )
    assert stored_context_response.status_code == 200
    assert stored_context_response.json()[0]["id"] == body["id"]
