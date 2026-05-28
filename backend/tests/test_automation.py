import json

from app.api.routes import automation as automation_routes


def test_automation_plan_generation_uses_local_llm_payload(client, monkeypatch) -> None:
    workspace_response = client.post("/api/v1/workspaces", json={"name": "automation-ws", "description": "automation tests"})
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    monkeypatch.setattr(
        automation_routes.automation_service,
        "_call_local_llm",
        lambda objective, signals: {
            "title": "Automate workspace triage",
            "summary": "Use local AI to summarize workspace health and trigger daily checks.",
            "automation_score": 88,
            "triggers": [{"name": "Daily run", "description": "Every morning at 8am."}],
            "actions": [{"name": "Refresh dashboards", "description": "Update the executive overview before standup."}],
            "next_steps": ["Schedule the automation", "Notify the workspace owner"],
            "provider_notes": "Generated with a local LM Studio model.",
        },
    )

    response = client.post(
        "/api/v1/automation/generate",
        json={"workspace_id": workspace_id, "objective": "Automate workspace triage"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["workspace_id"] == workspace_id
    assert body["objective"] == "Automate workspace triage"
    assert body["provider"] == "lm-studio"
    assert body["model_name"] == "local-model"

    payload = json.loads(body["automation_json"])
    assert payload["automation_score"] == 88
    assert payload["actions"][0]["name"] == "Refresh dashboards"
    assert 0 <= payload["confidence_score"] <= 1
    assert payload["trace"]["trace_id"].startswith("auto-")
    assert payload["trace"]["provider"] == "lm-studio"
    assert payload["trace"]["grounding"]["signal_snapshot"]


def test_automation_plan_generation_falls_back_without_llm(client, monkeypatch) -> None:
    workspace_response = client.post("/api/v1/workspaces", json={"name": "fallback-ws", "description": "automation fallback tests"})
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    monkeypatch.setattr(automation_routes.automation_service, "_call_local_llm", lambda objective, signals: None)

    response = client.post(
        "/api/v1/automation/generate",
        json={"workspace_id": workspace_id, "objective": "Reduce manual reporting work"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["workspace_id"] == workspace_id
    assert body["provider"] == "heuristic"

    payload = json.loads(body["automation_json"])
    assert payload["summary"]
    assert len(payload["actions"]) > 0
    assert len(payload["next_steps"]) > 0
    assert 0 <= payload["confidence_score"] <= 1
    assert payload["trace"]["provider"] == "heuristic"
    assert payload["trace"]["grounding"]["evidence"]


def test_automation_plan_execution_updates_status(client, monkeypatch) -> None:
    """Test that executing an automation plan updates its execution status and results."""
    workspace_response = client.post("/api/v1/workspaces", json={"name": "exec-ws", "description": "execution tests"})
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    monkeypatch.setattr(
        automation_routes.automation_service,
        "_call_local_llm",
        lambda objective, signals: {
            "title": "Create dashboard",
            "summary": "Create an executive overview dashboard.",
            "automation_score": 75,
            "triggers": [{"name": "Manual trigger", "description": "Triggered manually by user."}],
            "actions": [{"name": "create_dashboard", "description": "Create the dashboard."}],
            "next_steps": [],
            "provider_notes": "",
        },
    )

    gen_response = client.post(
        "/api/v1/automation/generate",
        json={"workspace_id": workspace_id, "objective": "Create a dashboard"},
    )
    assert gen_response.status_code == 201
    plan_id = gen_response.json()["id"]

    exec_response = client.post(f"/api/v1/automation/{plan_id}/execute")
    assert exec_response.status_code == 200
    body = exec_response.json()
    assert body["execution_status"] == "completed"
    assert body["executed_at"] is not None
    assert body["execution_results_json"] is not None

    results = json.loads(body["execution_results_json"])
    assert results["status"] == "completed"
    assert len(results["actions_executed"]) > 0
    assert results["actions_executed"][0]["status"] in ["executed", "skipped"]


def test_automation_plan_execution_handles_unknown_action(client, monkeypatch) -> None:
    """Test that execution handles unknown action names gracefully."""
    workspace_response = client.post("/api/v1/workspaces", json={"name": "unknown-action-ws", "description": "unknown action tests"})
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]

    monkeypatch.setattr(
        automation_routes.automation_service,
        "_call_local_llm",
        lambda objective, signals: {
            "title": "Unknown action plan",
            "summary": "Plan with unknown action.",
            "automation_score": 50,
            "triggers": [],
            "actions": [{"name": "unknown_action", "description": "This action does not exist."}],
            "next_steps": [],
            "provider_notes": "",
        },
    )

    gen_response = client.post(
        "/api/v1/automation/generate",
        json={"workspace_id": workspace_id, "objective": "Test unknown actions"},
    )
    assert gen_response.status_code == 201
    plan_id = gen_response.json()["id"]

    exec_response = client.post(f"/api/v1/automation/{plan_id}/execute")
    assert exec_response.status_code == 200
    body = exec_response.json()
    assert body["execution_status"] == "completed"

    results = json.loads(body["execution_results_json"])
    assert results["status"] == "completed"
    assert len(results["actions_executed"]) > 0
    assert results["actions_executed"][0]["action"] == "unknown_action"
    assert results["actions_executed"][0]["status"] == "skipped"


def test_automation_plan_execution_returns_404_for_missing_plan(client) -> None:
    """Test that executing a non-existent plan returns 404."""
    response = client.post("/api/v1/automation/999999/execute")
    assert response.status_code == 404