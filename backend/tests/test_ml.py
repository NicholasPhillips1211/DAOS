from io import BytesIO


def test_model_training_produces_artifact_and_metrics(client, complete_upload) -> None:
    workspace_response = client.post("/api/v1/workspaces", json={"name": "ml-team", "description": "ml workspace"})
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    upload_response = client.post(
        "/api/v1/ingestion/upload",
        data={"workspace_id": workspace_id, "dataset_name": "training-data"},
        files={
            "file": (
                "training-data.csv",
                BytesIO(
                    b"feature_1,feature_2,label\n1,0,A\n2,1,A\n3,2,A\n10,9,B\n11,10,B\n12,11,B\n",
                ),
                "text/csv",
            )
        },
    )
    upload_body = complete_upload(upload_response)
    dataset_id = upload_body["dataset_id"]

    train_response = client.post(
        "/api/v1/ml/train",
        json={
            "workspace_id": workspace_id,
            "dataset_id": dataset_id,
            "target_column": "label",
            "task_type": "classification",
            "model_name": "label-classifier",
        },
    )

    assert train_response.status_code == 201
    body = train_response.json()
    assert body["workspace_id"] == workspace_id
    assert body["dataset_id"] == dataset_id
    assert body["name"] == "label-classifier"
    assert body["metric_name"] == "accuracy"
    assert 0.0 <= body["metric_value"] <= 1.0
    assert body["artifact_path"].endswith(".joblib")
    assert len(body["feature_importances"]) > 0
