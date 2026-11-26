"""Tests for authentication, OIDC bearer token verification, and RBAC."""

from unittest.mock import patch
import pytest
from fastapi import HTTPException

import jwt
from app.core.config import Settings, settings
from app.core.security import DEMO_SIGNING_KEY
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


def test_token_with_wrong_issuer_rejected():
    # Token signed with the demo key but carrying a foreign issuer must be rejected
    # even when audience is correct (demo mode disabled to force OIDC path).
    foreign_iss = "https://evil-idp.example.com/realms/attacker"
    payload = {
        "sub": "mallory",
        "preferred_username": "mallory",
        "roles": ["admin"],
        "iss": foreign_iss,
        "aud": settings.oidc_audience,
        "iat": int(__import__("time").time()),
        "exp": int(__import__("time").time()) + 3600,
    }
    token = jwt.encode(payload, DEMO_SIGNING_KEY, algorithm="HS256")
    with patch("app.core.config.settings.demo_mode", False), \
         patch("app.core.config.settings.environment", "production"):
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)
    assert exc_info.value.status_code == 401
    assert "issuer" in exc_info.value.detail.lower()
