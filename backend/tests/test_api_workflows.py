"""Integration tests crossing the HTTP boundary for core session and evaluation workflows."""

import pytest


def test_end_to_end_session_lifecycle(client, operator_token, viewer_token):
    headers_op = {"Authorization": f"Bearer {operator_token}"}
    headers_view = {"Authorization": f"Bearer {viewer_token}"}

    # 1. Create a session
    create_payload = {
        "name": "Integration E2E Suite",
        "target": "web",
        "cwd": "/repo",
        "config": {"retries": 0, "timeout": 15},
    }
    create_resp = client.post("/api/v1/sessions", json=create_payload, headers=headers_op)
    assert create_resp.status_code == 201
    session_data = create_resp.json()
    session_id = session_data["id"]
    assert session_data["status"] == "running"
    assert session_data["target"] == "web"

    # 2. Query session by ID
    get_resp = client.get(f"/api/v1/sessions/{session_id}", headers=headers_view)
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Integration E2E Suite"

    # 3. Execute an action step
    step_payload = {
        "action": "act",
        "instruction": "open search and look up tests",
    }
    step_resp = client.post(f"/api/v1/sessions/{session_id}/steps", json=step_payload, headers=headers_op)
    assert step_resp.status_code == 200
    step_data = step_resp.json()
    assert step_data["action"] == "act"
    assert step_data["status"] == "passed"
    assert len(step_data["artifacts"]) == 2

    # 4. Execute an assertion step
    assert_payload = {
        "action": "assert_visible",
        "selector": "Sentinel Lens Dashboard",
    }
    assert_resp = client.post(f"/api/v1/sessions/{session_id}/steps", json=assert_payload, headers=headers_op)
    assert assert_resp.status_code == 200
    assert assert_resp.json()["status"] == "passed"

    # 5. Retrieve steps list
    steps_list_resp = client.get(f"/api/v1/sessions/{session_id}/steps", headers=headers_view)
    assert steps_list_resp.status_code == 200
    steps = steps_list_resp.json()
    assert len(steps) == 2

    # 6. Export trace
    trace_resp = client.get(f"/api/v1/sessions/{session_id}/trace", headers=headers_view)
    assert trace_resp.status_code == 200
    trace = trace_resp.json()
    assert trace["session_id"] == session_id
    assert len(trace["steps"]) == 2

    # 7. Close session
    close_resp = client.post(f"/api/v1/sessions/{session_id}/close", headers=headers_op)
    assert close_resp.status_code == 200
    assert close_resp.json()["status"] == "closed"


def test_evaluation_benchmark_workflow(client, operator_token, viewer_token):
    headers_op = {"Authorization": f"Bearer {operator_token}"}
    headers_view = {"Authorization": f"Bearer {viewer_token}"}

    # Run benchmark
    eval_resp = client.post(
        "/api/v1/evaluations/run",
        json={"benchmark_name": "ci-suite", "target": "web"},
        headers=headers_op,
    )
    assert eval_resp.status_code == 201
    eval_data = eval_resp.json()
    assert eval_data["total_scenarios"] == 8
    assert eval_data["accuracy"] == 100.0
    assert len(eval_data["scenarios"]) == 8

    # List evaluations
    list_resp = client.get("/api/v1/evaluations", headers=headers_view)
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) >= 1


def test_token_propagation_into_authorized_api_request(client):
    # Issue a demo token via auth endpoint
    token_resp = client.post("/api/v1/auth/demo-token", json={"user_id": "bearer-user", "role": "operator"})
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]

    # Propagate token into protected endpoint
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post("/api/v1/sessions", json={"name": "Propagated Session"}, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["status"] == "running"
