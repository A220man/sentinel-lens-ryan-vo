"""API routes for authentication metadata, current user context, and demo tokens."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.core.config import settings
from app.core.security import AuthUser, create_demo_token, get_current_user


router = APIRouter(prefix="/auth", tags=["Authentication"])


class DemoTokenRequest(BaseModel):
    user_id: str = "demo-operator"
    role: str = "operator"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str
    is_demo: bool


@router.get("/me")
def get_current_user_profile(user: AuthUser = Depends(get_current_user)):
    """Returns the profile and roles of the authenticated caller."""
    return user


@router.post("/demo-token", response_model=TokenResponse)
def issue_demo_token(payload: DemoTokenRequest):
    """Issues a local signed JWT token for development and offline testing on localhost."""
    if not settings.demo_mode or settings.environment == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo token issuing is disabled in production environments.",
        )
    token = create_demo_token(user_id=payload.user_id, role=payload.role)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=payload.user_id,
        role=payload.role,
        is_demo=True,
    )


@router.get("/config")
def get_auth_configuration():
    """Returns non-secret authentication discovery metadata for SPA login."""
    return {
        "oidc_issuer_url": settings.oidc_issuer_url,
        "oidc_client_id": settings.oidc_client_id,
        "oidc_audience": settings.oidc_audience,
        "demo_mode": settings.demo_mode,
        "environment": settings.environment,
    }
