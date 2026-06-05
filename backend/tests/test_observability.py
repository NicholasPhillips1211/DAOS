def test_metrics_snapshot_tracks_requests_and_errors(client) -> None:
    health_response = client.get("/api/v1/health")
    assert health_response.status_code == 200

    not_found_response = client.get("/api/v1/does-not-exist")
    assert not_found_response.status_code == 404

    metrics_response = client.get("/api/v1/observability/metrics")
    assert metrics_response.status_code == 200

    payload = metrics_response.json()
    assert payload["request_count"] >= 2
    assert payload["error_count"] >= 1
    assert "404" in payload["status_counts"]
    assert any(request["path"] == "/api/v1/health" for request in payload["recent_requests"])
    assert any(err_type.startswith("http_") for err_type in payload["error_types"]) 
