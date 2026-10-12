"""Pydantic schemas and typed request/response contracts for Sentinel Lens API."""

import datetime as dt
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    name: str = Field(default="Embedded Test Session", max_length=128)
    target: str = Field(default="web", pattern="^(web|mobile_android|mobile_ios|desktop)$")
    cwd: str = Field(default="/repo", max_length=256)
    config: Dict[str, Any] = Field(default_factory=dict)


class SessionResponse(BaseModel):
    id: str
    name: str
    target: str
    status: str
    cwd: str
    step_count: int
    artifact_count: int
    created_at: dt.datetime
    completed_at: Optional[dt.datetime] = None
    summary: Dict[str, Any] = Field(default_factory=dict)


class SessionListResponse(BaseModel):
    items: List[SessionResponse]
    total: int
    page: int
    size: int


class StepActionRequest(BaseModel):
    action: str = Field(default="act", pattern="^(act|assert_visible|click|type_text)$")
    instruction: Optional[str] = None
    selector: Optional[str] = None
    value: Optional[str] = None


class ArtifactResponse(BaseModel):
    id: str
    session_id: str
    step_id: str
    artifact_type: str
    mime_type: str
    content: Any
    size_bytes: int
    created_at: dt.datetime


class StepResponse(BaseModel):
    id: str
    session_id: str
    step_index: int
    action: str
    selector: Optional[str] = None
    status: str
    duration_ms: float
    input_payload: Any
    output_payload: Any
    error_message: Optional[str] = None
    timestamp: dt.datetime
    artifacts: List[ArtifactResponse] = []


class AuditResponse(BaseModel):
    id: str
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    details: Dict[str, Any]
    ip_address: str
    timestamp: dt.datetime


class AuditListResponse(BaseModel):
    items: List[AuditResponse]
    total: int
    page: int
    size: int


class ScenarioResult(BaseModel):
    scenario_id: str
    name: str
    category: str
    expected_element: str
    resolved_element: str
    confidence: float
    ambiguity_detected: bool
    passed: bool
    latency_ms: float


class EvaluationRunRequest(BaseModel):
    benchmark_name: str = Field(default="e2e-semantic-grounding-v1", max_length=128)
    target: str = Field(default="web", pattern="^(web|mobile_android|mobile_ios)$")
    use_llm_advisory: bool = False


class EvaluationResponse(BaseModel):
    id: str
    benchmark_name: str
    target: str
    total_scenarios: int
    accuracy: float
    ambiguity_resolution_rate: float
    latency_p95_ms: float
    scenarios: List[ScenarioResult]
    timestamp: dt.datetime


class SystemHealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    environment: str
    demo_mode: bool
    oidc_configured: bool
    llm_provider: str
    llm_model: str
