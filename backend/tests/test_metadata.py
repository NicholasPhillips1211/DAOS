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
