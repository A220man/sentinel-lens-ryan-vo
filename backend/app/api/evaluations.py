"""API routes for AI/ML evaluation benchmarks and locator accuracy tracking."""

import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import AuthUser, require_role
from app.models.database import get_db, EvaluationModel
from app.models.schemas import EvaluationRunRequest, EvaluationResponse, ScenarioResult
from app.services import evaluation_service


router = APIRouter(prefix="/evaluations", tags=["Evaluations"])


@router.post("/run", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
def run_evaluation(
    payload: EvaluationRunRequest,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_role("operator")),
):
    """Executes the AI/ML semantic locator grounding benchmark comparing accuracy vs baseline."""
    model = evaluation_service.record_evaluation_benchmark(
        db, benchmark_name=payload.benchmark_name, target=payload.target
    )
    raw = json.loads(model.results_json or "{}")
    scenarios = [ScenarioResult(**s) for s in raw.get("scenarios", [])]
    return EvaluationResponse(
        id=model.id,
        benchmark_name=model.benchmark_name,
        target=model.target,
        total_scenarios=model.total_scenarios,
        accuracy=model.accuracy,
        ambiguity_resolution_rate=model.ambiguity_resolution_rate,
        latency_p95_ms=model.latency_p95_ms,
        scenarios=scenarios,
        timestamp=model.timestamp,
    )


@router.get("", response_model=List[EvaluationResponse])
def list_evaluations(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_role("viewer")),
):
    """Returns recent evaluation benchmark runs."""
    records = db.query(EvaluationModel).order_by(EvaluationModel.timestamp.desc()).limit(limit).all()
    results = []
    for m in records:
        raw = json.loads(m.results_json or "{}")
        scenarios = [ScenarioResult(**s) for s in raw.get("scenarios", [])]
        results.append(EvaluationResponse(
            id=m.id,
            benchmark_name=m.benchmark_name,
            target=m.target,
            total_scenarios=m.total_scenarios,
            accuracy=m.accuracy,
            ambiguity_resolution_rate=m.ambiguity_resolution_rate,
            latency_p95_ms=m.latency_p95_ms,
            scenarios=scenarios,
            timestamp=m.timestamp,
        ))
    return results


@router.get("/{eval_id}", response_model=EvaluationResponse)
def get_evaluation(
    eval_id: str,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(require_role("viewer")),
):
    """Retrieves detailed metrics and scenario results for a specific evaluation."""
    m = db.query(EvaluationModel).filter(EvaluationModel.id == eval_id).first()
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation record not found")

    raw = json.loads(m.results_json or "{}")
    scenarios = [ScenarioResult(**s) for s in raw.get("scenarios", [])]
    return EvaluationResponse(
        id=m.id,
        benchmark_name=m.benchmark_name,
        target=m.target,
        total_scenarios=m.total_scenarios,
        accuracy=m.accuracy,
        ambiguity_resolution_rate=m.ambiguity_resolution_rate,
        latency_p95_ms=m.latency_p95_ms,
        scenarios=scenarios,
        timestamp=m.timestamp,
    )
