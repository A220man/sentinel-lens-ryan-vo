"""Audit service for logging operational events and user actions."""

import json
import uuid
from typing import Any, Dict
from sqlalchemy.orm import Session

from app.models.database import AuditModel, utcnow


def record_audit_event(
    db: Session,
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    details: Dict[str, Any],
    ip_address: str = "127.0.0.1",
) -> AuditModel:
    """Writes an immutable audit log record to persistent storage."""
    event = AuditModel(
        id=f"audit-{uuid.uuid4().hex[:12]}",
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details_json=json.dumps(details),
        ip_address=ip_address,
        timestamp=utcnow(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
