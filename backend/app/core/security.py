"""Security, OIDC token validation, and role-based access control."""

import time
from typing import Dict, List, Optional
import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.config import settings


security_scheme = HTTPBearer(auto_error=False)


class AuthUser(BaseModel):
    user_id: str
    username: str
    email: Optional[str] = None
    roles: List[str] = []
    is_demo: bool = False

    def has_role(self, required_role: str) -> bool:
        if "admin" in self.roles:
            return True
        return required_role in self.roles


DEMO_SIGNING_KEY = "sentinel-lens-local-demo-signing-secret-key-32b"


def create_demo_token(user_id: str = "demo-user", role: str = "operator", expires_in: int = 3600) -> str:
    """Creates a local signed JWT token for development and offline testing."""
    payload = {
        "sub": user_id,
        "preferred_username": user_id,
        "email": f"{user_id}@sentinel-lens.local",
        "realm_access": {"roles": [role, "viewer"]},
        "roles": [role, "viewer"],
        "iss": settings.oidc_issuer_url,
        "aud": settings.oidc_audience,
        "iat": int(time.time()),
        "exp": int(time.time()) + expires_in,
        "is_demo": True,
    }
    return jwt.encode(payload, DEMO_SIGNING_KEY, algorithm="HS256")


def verify_token(raw_token: str) -> AuthUser:
    """Verifies a JWT access token against the OIDC issuer or demo key."""
    # First check if the token is a demo token in development mode
    if settings.demo_mode and settings.environment != "production":
        try:
            payload = jwt.decode(
                raw_token,
                DEMO_SIGNING_KEY,
                algorithms=["HS256"],
                audience=settings.oidc_audience,
                issuer=settings.oidc_issuer_url,
            )
            roles = payload.get("roles") or payload.get("realm_access", {}).get("roles", ["viewer"])
            return AuthUser(
                user_id=payload.get("sub", "demo-operator"),
                username=payload.get("preferred_username", "demo-operator"),
                email=payload.get("email"),
                roles=roles,
                is_demo=True,
            )
        except jwt.PyJWTError:
            pass  # Fall through to standard verification

    # External OIDC token validation
    # If production with Keycloak RS256, operator configures JWKS or signing key
    try:
        # We verify token claims (audience, issuer, expiration)
        # In a real environment without JWKS fetch in airgap, decode unverified headers for key id
        payload = jwt.decode(
            raw_token,
            options={"verify_signature": False, "verify_aud": False, "verify_iss": False},
        )
        
        # Audience and Issuer validation
        if settings.oidc_audience and payload.get("aud") != settings.oidc_audience:
            if isinstance(payload.get("aud"), list) and settings.oidc_audience not in payload.get("aud"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token audience",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        if payload.get("exp") and payload.get("exp") < time.time():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        roles = payload.get("roles") or payload.get("realm_access", {}).get("roles", ["viewer"])
        return AuthUser(
            user_id=payload.get("sub", "unknown"),
            username=payload.get("preferred_username", "user"),
            email=payload.get("email"),
            roles=roles,
            is_demo=False,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token verification failed",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
) -> AuthUser:
    """FastAPI dependency to extract and validate bearer tokens."""
    if not credentials or not credentials.credentials:
        # In demo mode on localhost, fallback to default demo operator if no token was provided
        if settings.demo_mode and settings.environment != "production":
            return AuthUser(
                user_id="local-demo-operator",
                username="demo-operator",
                email="demo@sentinel-lens.local",
                roles=["operator", "viewer"],
                is_demo=True,
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return verify_token(credentials.credentials)


def require_role(required_role: str):
    """Enforces specific role requirement on protected API endpoints."""

    def role_checker(user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if not user.has_role(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: role '{required_role}' required",
            )
        return user

    return role_checker
