"""API routes for system health, operational status, and audit log inspection."""

import json
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import AuthUser, require_role
from app.models.database import get_db, AuditModel
from app.models.schemas import SystemHealthResponse, AuditListResponse, AuditResponse


router = APIRouter(prefix="/system", tags=["System"])


@router.get("/health", response_model=SystemHealthResponse)
def health_check():
    """System health check endpoint for monitoring, Docker, and Kubernetes probes."""
    return SystemHealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        demo_mode=settings.demo_mode,
        oidc_configured=bool(settings.oidc_issuer_url),
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
    )


@router.get("/audit", response_model=AuditListResponse)
def list_audit_events(
    action: Optional[str] = Query(None, description="Filter by audit action"),
    user_id: Optional[str] = Query(None, description="Filter by user id"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_role("operator")),
):
    """Retrieves immutable audit trail entries with pagination."""
    query = db.query(AuditModel)
    if action:
        query = query.filter(AuditModel.action == action)
    if user_id:
        query = query.filter(AuditModel.user_id == user_id)

    total = query.count()
    items = query.order_by(AuditModel.timestamp.desc()).offset((page - 1) * size).limit(size).all()

    responses = [
        AuditResponse(
            id=i.id,
            user_id=i.user_id,
            action=i.action,
            resource_type=i.resource_type,
            resource_id=i.resource_id,
            details=json.loads(i.details_json or "{}"),
            ip_address=i.ip_address,
            timestamp=i.timestamp,
        )
        for i in items
    ]
    return AuditListResponse(items=responses, total=total, page=page, size=size)
