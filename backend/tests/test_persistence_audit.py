"""Tests for persistent SQLite storage, pagination, filtering, and audit log."""

from app.models.database import SessionModel, utcnow
from app.services import session_service


def test_session_pagination_and_filtering(db_session):
    for i in range(15):
        target = "mobile_android" if i % 2 == 0 else "web"
        s = SessionModel(
            id=f"sess-test-{i}",
            name=f"Session {i}",
            target=target,
            status="running" if i < 10 else "completed",
            created_at=utcnow(),
        )
        db_session.add(s)
    db_session.commit()

    # Filter by target
    web_items, web_total = session_service.list_sessions(db_session, target="web", page=1, size=10)
    assert web_total == 7
    assert len(web_items) == 7
    assert all(item.target == "web" for item in web_items)

    # Filter by status and paginate
    running_items, running_total = session_service.list_sessions(
        db_session, status_filter="running", page=1, size=5
    )
    assert running_total == 10
    assert len(running_items) == 5


def test_system_health_and_audit_api(client, operator_token):
    headers = {"Authorization": f"Bearer {operator_token}"}
    health_resp = client.get("/api/v1/system/health")
    assert health_resp.status_code == 200
    data = health_resp.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "Sentinel Lens"
    assert data["version"] == "1.0.0"

    # Query audit logs
    audit_resp = client.get("/api/v1/system/audit", headers=headers)
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()
    assert "items" in audit_data
    assert "total" in audit_data
