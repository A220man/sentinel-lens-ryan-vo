"""API routes for test session lifecycle, action execution, and trace export."""

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import AuthUser, require_role, get_current_user
from app.models.database import get_db, SessionModel
from app.models.schemas import (
    SessionCreateRequest,
    SessionResponse,
    SessionListResponse,
    StepActionRequest,
    StepResponse,
    ArtifactResponse,
)
from app.services import session_service
from app.services.llm_adapters import llm_advisory_service


router = APIRouter(prefix="/sessions", tags=["Sessions"])


def _map_session(m: SessionModel) -> SessionResponse:
    return SessionResponse(
        id=m.id,
        name=m.name,
        target=m.target,
        status=m.status,
        cwd=m.cwd,
        step_count=m.step_count,
        artifact_count=m.artifact_count,
        created_at=m.created_at,
        completed_at=m.completed_at,
        summary=json.loads(m.summary_json or "{}"),
    )


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreateRequest,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_role("operator")),
):
    """Opens a new programmatic runner session via open_session() and registers fixtures."""
    model = await session_service.create_session(db, payload, user_id=user.user_id)
    return _map_session(model)


@router.get("", response_model=SessionListResponse)
def list_sessions(
    target: Optional[str] = Query(None, description="Filter by target platform"),
    status: Optional[str] = Query(None, description="Filter by status (running, completed)"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_role("viewer")),
):
    """Lists persistent sessions with pagination and filtering."""
    items, total = session_service.list_sessions(db, target=target, status_filter=status, page=page, size=size)
    return SessionListResponse(
        items=[_map_session(i) for i in items],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_role("viewer")),
):
    """Retrieves metadata for a specific runner session."""
    model = session_service.get_session(db, session_id)
    return _map_session(model)


@router.post("/{session_id}/steps", response_model=StepResponse)
async def execute_step(
    session_id: str,
    payload: StepActionRequest,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_role("operator")),
):
    """Executes an action in the embedded runner session and persists step/artifact records."""
    step_model, artifacts = await session_service.execute_step(
        db, session_id, payload, user_id=user.user_id
    )
    art_responses = [
        ArtifactResponse(
            id=a.id,
            session_id=a.session_id,
            step_id=a.step_id,
            artifact_type=a.artifact_type,
            mime_type=a.mime_type,
            content=json.loads(a.content) if a.mime_type == "application/json" else a.content,
            size_bytes=a.size_bytes,
            created_at=a.created_at,
        )
        for a in artifacts
    ]
    return StepResponse(
        id=step_model.id,
        session_id=step_model.session_id,
        step_index=step_model.step_index,
        action=step_model.action,
        selector=step_model.selector,
        status=step_model.status,
        duration_ms=step_model.duration_ms,
        input_payload=json.loads(step_model.input_json or "{}"),
        output_payload=json.loads(step_model.output_json or "{}"),
        error_message=step_model.error_message,
        timestamp=step_model.timestamp,
        artifacts=art_responses,
    )


@router.get("/{session_id}/steps", response_model=List[StepResponse])
def get_session_steps(
    session_id: str,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_role("viewer")),
):
    """Returns chronological steps and telemetry for a session."""
    step_tuples = session_service.get_session_steps(db, session_id)
    results = []
    for step_model, artifacts in step_tuples:
        art_responses = [
            ArtifactResponse(
                id=a.id,
                session_id=a.session_id,
                step_id=a.step_id,
                artifact_type=a.artifact_type,
                mime_type=a.mime_type,
                content=json.loads(a.content) if a.mime_type == "application/json" else a.content,
                size_bytes=a.size_bytes,
                created_at=a.created_at,
            )
            for a in artifacts
        ]
        results.append(StepResponse(
            id=step_model.id,
            session_id=step_model.session_id,
            step_index=step_model.step_index,
            action=step_model.action,
            selector=step_model.selector,
            status=step_model.status,
            duration_ms=step_model.duration_ms,
            input_payload=json.loads(step_model.input_json or "{}"),
            output_payload=json.loads(step_model.output_json or "{}"),
            error_message=step_model.error_message,
            timestamp=step_model.timestamp,
            artifacts=art_responses,
        ))
    return results


@router.post("/{session_id}/close")
async def close_session(
    session_id: str,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_role("operator")),
):
    """Idempotently closes the embedded session and releases fixture leases."""
    return await session_service.close_session(db, session_id, user_id=user.user_id)


@router.get("/{session_id}/trace")
def export_trace(
    session_id: str,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_role("viewer")),
):
    """Exports full session trace JSON with step timeline, artifacts, and configuration."""
    return session_service.export_session_trace(db, session_id)


@router.post("/{session_id}/advisory")
async def request_failure_advisory(
    session_id: str,
    step_id: str = Query(..., description="Target step ID to analyze"),
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_role("operator")),
):
    """Opt-in advisory analysis explaining assertion or locator failures."""
    session = session_service.get_session(db, session_id)
    step_tuples = session_service.get_session_steps(db, session_id)
    target_step = next((s for s, _ in step_tuples if s.id == step_id), None)
    if not target_step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target step not found")

    context = {
        "session_id": session_id,
        "target": session.target,
        "action": target_step.action,
        "selector": target_step.selector,
        "status": target_step.status,
        "error": target_step.error_message,
        "output": json.loads(target_step.output_json or "{}"),
    }
    explanation = await llm_advisory_service.generate_explanation(
        prompt="Explain why this UI assertion failed and suggest a fix.",
        context=context,
    )
    return explanation
