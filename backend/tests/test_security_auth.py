"""Tests for authentication, OIDC bearer token verification, and RBAC."""

from unittest.mock import patch
import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.core.security import create_demo_token, verify_token


def test_demo_token_creation_and_verification():
    token = create_demo_token(user_id="alice", role="operator")
    user = verify_token(token)
    assert user.user_id == "alice"
    assert user.has_role("operator")
    assert user.has_role("viewer")
    assert not user.has_role("admin")


def test_production_safety_check_raises():
    prod_settings = Settings(environment="production", demo_mode=True)
    with pytest.raises(RuntimeError) as exc_info:
        prod_settings.check_production_safety()
    assert "DEMO_MODE cannot be enabled when ENVIRONMENT=production" in str(exc_info.value)


def test_unauthenticated_request_rejected(client):
    # Disable demo mode fallback for this check
    with patch("app.core.config.settings.demo_mode", False), \
         patch("app.core.config.settings.environment", "production"):
        resp = client.post("/api/v1/sessions", json={"name": "Test Session"})
        assert resp.status_code == 401
        assert "Authorization" in resp.json()["detail"]


def test_role_denial_forbidden(client, viewer_token):
    # Viewer attempting to create session (which requires operator role)
    headers = {"Authorization": f"Bearer {viewer_token}"}
    resp = client.post("/api/v1/sessions", json={"name": "Forbidden Session"}, headers=headers)
    assert resp.status_code == 403
    assert "operator" in resp.json()["detail"]


def test_demo_token_issuing_forbidden_in_production(client):
    with patch("app.core.config.settings.environment", "production"):
        resp = client.post("/api/v1/auth/demo-token", json={"user_id": "attacker", "role": "admin"})
        assert resp.status_code == 403
