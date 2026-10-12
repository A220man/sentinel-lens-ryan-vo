"""Session service coordinating runner execution, database persistence, and trace export."""

import json
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.runner import RunnerSession, open_session, StepRecord
from app.models.database import SessionModel, StepModel, ArtifactModel, utcnow
from app.models.schemas import SessionCreateRequest, StepActionRequest
from app.services.audit_service import record_audit_event


# Active in-memory runner sessions keyed by session_id
_ACTIVE_SESSIONS: Dict[str, RunnerSession] = {}


async def create_session(db: Session, req: SessionCreateRequest, user_id: str) -> SessionModel:
    """Creates a new programmatic runner session, saves to database, and registers in active pool."""
    session = await open_session(
        cwd=req.cwd,
        config=req.config,
        target=req.target,
    )
    _ACTIVE_SESSIONS[session.session_id] = session

    model = SessionModel(
        id=session.session_id,
        name=req.name,
        target=req.target,
        status="running",
        cwd=req.cwd,
        config_json=json.dumps(req.config),
        summary_json="{}",
        step_count=0,
        artifact_count=0,
        created_at=utcnow(),
    )
    db.add(model)
    db.commit()
    db.refresh(model)

    record_audit_event(
        db,
        user_id=user_id,
        action="SESSION_CREATE",
        resource_type="session",
        resource_id=session.session_id,
        details={"name": req.name, "target": req.target, "cwd": req.cwd},
    )
    return model


async def execute_step(
    db: Session,
    session_id: str,
    action_req: StepActionRequest,
    user_id: str,
) -> Tuple[StepModel, List[ArtifactModel]]:
    """Dispatches test action to the agent fixture in the active session and stores step/artifacts."""
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    runner = _ACTIVE_SESSIONS.get(session_id)
    if not runner or runner.is_closed:
        # Re-attach an active runner instance if process restarted
        runner = await open_session(
            cwd=db_session.cwd,
            config=json.loads(db_session.config_json or "{}"),
            target=db_session.target,
        )
        runner.session_id = session_id
        _ACTIVE_SESSIONS[session_id] = runner

    action = action_req.action
    step_record: StepRecord
    if action == "act":
        step_record = await runner.fixtures.agent.act(action_req.instruction or "verify UI state")
    elif action == "assert_visible":
        step_record = await runner.fixtures.agent.assert_visible(action_req.selector or action_req.instruction or "")
    elif action == "click":
        step_record = await runner.fixtures.agent.click(action_req.selector or "#btn-run-suite")
    else:
        step_record = await runner.fixtures.agent.act(f"{action} {action_req.selector or ''}")

    # Persist StepModel
    step_model = StepModel(
        id=step_record.step_id,
        session_id=session_id,
        step_index=step_record.step_index,
        action=step_record.action,
        selector=step_record.selector,
        status=step_record.status,
        duration_ms=step_record.duration_ms,
        input_json=json.dumps(step_record.input_payload),
        output_json=json.dumps(step_record.output_payload),
        error_message=step_record.error,
        timestamp=utcnow(),
    )
    db.add(step_model)

    # Persist ArtifactModels
    artifact_models: List[ArtifactModel] = []
    for art in step_record.artifacts:
        art_content = art["content"]
        serialized_content = json.dumps(art_content) if isinstance(art_content, (dict, list)) else str(art_content)
        art_model = ArtifactModel(
            id=art["artifact_id"],
            session_id=session_id,
            step_id=step_record.step_id,
            artifact_type=art["type"],
            mime_type=art["mime_type"],
            content=serialized_content,
            size_bytes=len(serialized_content),
            created_at=utcnow(),
        )
        db.add(art_model)
        artifact_models.append(art_model)

    # Update session counts
    db_session.step_count += 1
    db_session.artifact_count += len(artifact_models)
    db.commit()
    db.refresh(step_model)

    record_audit_event(
        db,
        user_id=user_id,
        action="STEP_EXECUTE",
        resource_type="step",
        resource_id=step_record.step_id,
        details={"session_id": session_id, "action": action, "status": step_record.status},
    )
    return step_model, artifact_models


async def close_session(db: Session, session_id: str, user_id: str) -> Dict[str, Any]:
    """Closes runner session, frees leased fixtures, and updates database state."""
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    runner = _ACTIVE_SESSIONS.pop(session_id, None)
    if runner:
        cleanup_report = await runner.close()
    else:
        cleanup_report = {
            "session_id": session_id,
            "target": db_session.target,
            "steps_executed": db_session.step_count,
            "artifacts_collected": db_session.artifact_count,
            "status": "closed",
        }

    db_session.status = "completed"
    db_session.completed_at = utcnow()
    db_session.summary_json = json.dumps(cleanup_report)
    db.commit()
    db.refresh(db_session)

    record_audit_event(
        db,
        user_id=user_id,
        action="SESSION_CLOSE",
        resource_type="session",
        resource_id=session_id,
        details={"status": "completed", "steps_count": db_session.step_count},
    )
    return cleanup_report


def get_session(db: Session, session_id: str) -> SessionModel:
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return db_session


def list_sessions(
    db: Session,
    target: Optional[str] = None,
    status_filter: Optional[str] = None,
    page: int = 1,
    size: int = 20,
) -> Tuple[List[SessionModel], int]:
    query = db.query(SessionModel)
    if target:
        query = query.filter(SessionModel.target == target)
    if status_filter:
        query = query.filter(SessionModel.status == status_filter)
    total = query.count()
    items = query.order_by(SessionModel.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return items, total


def get_session_steps(db: Session, session_id: str) -> List[Tuple[StepModel, List[ArtifactModel]]]:
    steps = db.query(StepModel).filter(StepModel.session_id == session_id).order_by(StepModel.step_index.asc()).all()
    results = []
    for step in steps:
        artifacts = db.query(ArtifactModel).filter(ArtifactModel.step_id == step.id).all()
        results.append((step, artifacts))
    return results


def export_session_trace(db: Session, session_id: str) -> Dict[str, Any]:
    session = get_session(db, session_id)
    step_tuples = get_session_steps(db, session_id)
    
    trace_steps = []
    for step, artifacts in step_tuples:
        trace_steps.append({
            "step_id": step.id,
            "step_index": step.step_index,
            "action": step.action,
            "selector": step.selector,
            "status": step.status,
            "duration_ms": step.duration_ms,
            "input": json.loads(step.input_json or "{}"),
            "output": json.loads(step.output_json or "{}"),
            "error_message": step.error_message,
            "timestamp": step.timestamp.isoformat(),
            "artifacts": [
                {
                    "artifact_id": a.id,
                    "type": a.artifact_type,
                    "mime_type": a.mime_type,
                    "size_bytes": a.size_bytes,
                }
                for a in artifacts
            ],
        })

    return {
        "session_id": session.id,
        "name": session.name,
        "target": session.target,
        "status": session.status,
        "cwd": session.cwd,
        "created_at": session.created_at.isoformat(),
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "step_count": session.step_count,
        "artifact_count": session.artifact_count,
        "config": json.loads(session.config_json or "{}"),
        "summary": json.loads(session.summary_json or "{}"),
        "steps": trace_steps,
    }
