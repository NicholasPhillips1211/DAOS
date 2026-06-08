import csv
from io import BytesIO
from pathlib import Path


def test_csv_upload_creates_dataset_and_report(client, complete_upload) -> None:
    response = client.post(
        "/api/v1/ingestion/upload",
        data={"workspace_id": 1, "dataset_name": "sales"},
        files={"file": ("sales.csv", BytesIO(b"id,amount\n1,10\n2,20\n"), "text/csv")},
    )

    assert response.status_code == 404

    workspace_response = client.post("/api/v1/workspaces", json={"name": "analysis", "description": "team workspace"})
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    response = client.post(
        "/api/v1/ingestion/upload",
        data={"workspace_id": workspace_id, "dataset_name": "sales"},
        files={"file": ("sales.csv", BytesIO(b"id,amount\n1,10\n2,20\n"), "text/csv")},
    )

    assert response.status_code == 202
    accepted = response.json()
    assert accepted["status"] == "queued"
    assert accepted["work_item_id"] > 0
    body = complete_upload(response)
    assert body["workspace_id"] == workspace_id
    assert body["dataset_name"] == "sales"
    assert body["job_id"] > 0
    assert body["status"] == "completed"
    assert body["current_step"] == "cleaned_and_profiled"
    assert body["finished_at"] is not None
    assert body["progress_percent"] == 100
    assert body["row_count"] == 2
    assert body["quality_score"] == 100
    assert body["rejected_rows"] == 0
    assert body["report_id"] > 0

    job_response = client.get(f"/api/v1/ingestion/jobs/{body['job_id']}")
    assert job_response.status_code == 200
    job_body = job_response.json()
    assert job_body["status"] == "completed"
    assert job_body["dataset_id"] == body["dataset_id"]
    assert job_body["source_name"] == "sales.csv"
    assert job_body["finished_at"] is not None

    datasets_response = client.get(f"/api/v1/datasets?workspace_id={workspace_id}")
    assert datasets_response.status_code == 200
    dataset_body = next(dataset for dataset in datasets_response.json() if dataset["id"] == body["dataset_id"])
    assert dataset_body["state"] == "cleansed"
    assert dataset_body["storage_path"].endswith("_cleaned.csv")

    job_list_response = client.get(f"/api/v1/ingestion/jobs?workspace_id={workspace_id}")
    assert job_list_response.status_code == 200
    assert job_list_response.headers["X-Total-Count"] == "1"
    assert job_list_response.json()[0]["id"] == body["job_id"]

    quality_response = client.get(f"/api/v1/datasets/{body['dataset_id']}/quality")
    assert quality_response.status_code == 200
    quality_body = quality_response.json()
    assert quality_body["metadata"]["profile_version"] == "1.4"
    assert quality_body["metadata"]["ingestion_job_id"] == body["job_id"]
    assert quality_body["metadata"]["source_name"] == "sales.csv"
    assert quality_body["metadata"]["column_count"] == 2
    assert quality_body["metadata"]["profile_fingerprint"]
    assert quality_body["metadata"]["raw_storage_path"] == body["storage_path"]
    assert quality_body["metadata"]["cleaned_storage_path"] == dataset_body["storage_path"]
    assert quality_body["metadata"]["rejected_storage_path"].endswith("_rejected.csv")
    assert Path(quality_body["metadata"]["raw_storage_path"]).exists()
    assert Path(quality_body["metadata"]["cleaned_storage_path"]).exists()
    assert Path(quality_body["metadata"]["rejected_storage_path"]).exists()
    assert quality_body["metadata"]["cleaning"]["raw_row_count"] == 2
    assert quality_body["metadata"]["cleaning"]["cleaned_row_count"] == 2
    assert quality_body["metadata"]["cleaning"]["engine"] == "duckdb"
    assert quality_body["metadata"]["cleaning"]["artifact_fingerprints"]["raw"]
    assert quality_body["metadata"]["quality_delta"]["score_delta"] == 0

    query_response = client.post(
        f"/api/v1/lakehouse/{body['dataset_id']}/query",
        json={"sql": "SELECT id, amount FROM dataset ORDER BY id"},
    )

    assert query_response.status_code == 200
    query_body = query_response.json()
    assert query_body["row_count"] == 2
    assert query_body["columns"] == ["id", "amount"]
    assert query_body["rows"][0]["id"] == 1
    assert query_body["rows"][0]["amount"] == 10

    datasets_query_response = client.post(
        f"/api/v1/datasets/{body['dataset_id']}/query",
        json={"sql": "SELECT id, amount FROM dataset ORDER BY id"},
    )
    assert datasets_query_response.status_code == 200
    assert datasets_query_response.json()["row_count"] == 2

    stats_response = client.get(f"/api/v1/analytics/datasets/{body['dataset_id']}/statistics")
    assert stats_response.status_code == 200
    stats_body = stats_response.json()
    assert stats_body["dataset_id"] == body["dataset_id"]
    assert stats_body["row_count"] == 2
    assert stats_body["column_count"] == 2
    assert stats_body["columns"][0]["name"] == "id"

    dashboard_response = client.post(
        "/api/v1/visualizations/dashboards",
        json={"workspace_id": workspace_id, "name": "Sales Overview", "description": "Revenue tracking"},
    )
    assert dashboard_response.status_code == 201

    audit_response = client.get(f"/api/v1/governance/audit?workspace_id={workspace_id}")
    assert audit_response.status_code == 200
    audit_types = [event["event_type"] for event in audit_response.json()]
    assert "dataset.uploaded" in audit_types
    assert "dataset.query_executed" in audit_types
    assert "dashboard.created" in audit_types


def test_upload_cleans_data_before_dataset_queries(client, complete_upload) -> None:
    workspace_response = client.post("/api/v1/workspaces", json={"name": "cleaning-ws", "description": "cleaning tests"})
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    upload_response = client.post(
        "/api/v1/ingestion/upload",
        data={"workspace_id": workspace_id, "dataset_name": "messy sales"},
        files={
            "file": (
                "messy-sales.csv",
                BytesIO(
                    b" Customer ID , Amount $ ,Customer ID\n"
                    b" 1 , 10.50 ,1\n"
                    b"1,10.50,1\n"
                    b"   ,   ,  \n"
                    b"2, 20 ,2,unexpected\n"
                ),
                "text/csv",
            )
        },
    )

    body = complete_upload(upload_response)
    assert body["rejected_rows"] == 2

    quality_response = client.get(f"/api/v1/datasets/{body['dataset_id']}/quality")
    assert quality_response.status_code == 200
    quality_body = quality_response.json()
    metadata = quality_body["metadata"]
    cleaning = metadata["cleaning"]
    quality_delta = metadata["quality_delta"]
    assert quality_body["rejected_rows"] == 2
    assert metadata["schema"] == [
        {"name": "customer_id", "inferred_type": "integer"},
        {"name": "amount", "inferred_type": "number"},
        {"name": "customer_id_2", "inferred_type": "integer"},
        {"name": "column_4", "inferred_type": "string"},
    ]
    assert cleaning["raw_row_count"] == 4
    assert cleaning["cleaned_row_count"] == 2
    assert cleaning["blank_rows_removed"] == 1
    assert cleaning["duplicate_rows_removed"] == 1
    assert cleaning["rejected_row_count"] == 2
    assert cleaning["extra_columns_preserved"] == 1
    assert cleaning["short_rows_padded"] == 3
    assert cleaning["cells_trimmed"] > 0
    assert cleaning["engine"] == "duckdb"
    assert cleaning["policy"]["id"] == "duckdb_csv_cleaning_v1"
    assert cleaning["policy_fingerprint"]
    assert cleaning["artifact_fingerprints"]["raw"]
    assert cleaning["artifact_fingerprints"]["cleaned"]
    assert cleaning["artifact_fingerprints"]["rejected"]
    assert {"from": " Customer ID ", "to": "customer_id"} in cleaning["headers_normalized"]
    assert {"from": " Amount $ ", "to": "amount"} in cleaning["headers_normalized"]
    assert {"from": "Customer ID", "to": "customer_id_2"} in cleaning["headers_normalized"]
    assert quality_delta["raw_quality_score"] < quality_delta["cleaned_quality_score"]
    assert quality_delta["score_delta"] > 0

    rejected_path = Path(cleaning["rejected_path"])
    assert rejected_path.exists()
    with rejected_path.open(newline="", encoding="utf-8-sig") as handle:
        rejected_rows = list(csv.DictReader(handle))
    assert [row["rejection_reason"] for row in rejected_rows] == ["duplicate_row", "blank_row"]
    assert rejected_rows[0]["customer_id"] == "1"

    query_response = client.post(
        f"/api/v1/datasets/{body['dataset_id']}/query",
        json={"sql": "SELECT customer_id, amount, customer_id_2, column_4 FROM dataset ORDER BY customer_id"},
    )

    assert query_response.status_code == 200
    query_body = query_response.json()
    assert query_body["row_count"] == 2
    assert query_body["columns"] == ["customer_id", "amount", "customer_id_2", "column_4"]
    assert query_body["rows"][0] == {"customer_id": 1, "amount": 10.5, "customer_id_2": 1, "column_4": None}
    assert query_body["rows"][1] == {"customer_id": 2, "amount": 20.0, "customer_id_2": 2, "column_4": "unexpected"}

    lineage_response = client.get(
        "/api/v1/metadata/lineage",
        params={"workspace_id": workspace_id, "asset_type": "dataset", "asset_id": body["dataset_id"]},
    )
    assert lineage_response.status_code == 200
    assert any(record["relation_type"] == "cleaned_into_dataset" for record in lineage_response.json())

    usage_response = client.get(
        "/api/v1/metadata/usage",
        params={
            "workspace_id": workspace_id,
            "asset_type": "dataset",
            "asset_id": body["dataset_id"],
            "action": "information_cleaned",
        },
    )
    assert usage_response.status_code == 200
    assert usage_response.headers["X-Total-Count"] == "1"
