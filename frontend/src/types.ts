/** Type definitions for Sentinel Lens API contracts and domain entities. */

export type TargetPlatform = 'web' | 'mobile_android' | 'mobile_ios' | 'desktop';

export interface Artifact {
  id: string;
  session_id: string;
  step_id: string;
  artifact_type: string;
  mime_type: string;
  content: any;
  size_bytes: number;
  created_at: string;
}

export interface Step {
  id: string;
  session_id: string;
  step_index: number;
  action: string;
  selector: string | null;
  status: 'passed' | 'failed';
  duration_ms: number;
  input_payload: any;
  output_payload: any;
  error_message: string | null;
  timestamp: string;
  artifacts: Artifact[];
}

export interface Session {
  id: string;
  name: string;
  target: TargetPlatform;
  status: 'running' | 'completed' | 'failed';
  cwd: string;
  step_count: number;
  artifact_count: number;
  created_at: string;
  completed_at: string | null;
  summary: Record<string, any>;
}

export interface SessionListResponse {
  items: Session[];
  total: number;
  page: number;
  size: number;
}

export interface SessionCreatePayload {
  name: string;
  target: TargetPlatform;
  cwd?: string;
  config?: Record<string, any>;
}

export interface StepActionPayload {
  action: 'act' | 'assert_visible' | 'click' | 'type_text';
  instruction?: string;
  selector?: string;
  value?: string;
}

export interface ScenarioResult {
  scenario_id: string;
  name: string;
  category: string;
  expected_element: string;
  resolved_element: string;
  confidence: number;
  ambiguity_detected: boolean;
  passed: boolean;
  latency_ms: number;
}

export interface Evaluation {
  id: string;
  benchmark_name: string;
  target: string;
  total_scenarios: number;
  accuracy: number;
  ambiguity_resolution_rate: number;
  latency_p95_ms: number;
  scenarios: ScenarioResult[];
  timestamp: string;
}

export interface AuditEvent {
  id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  details: Record<string, any>;
  ip_address: string;
  timestamp: string;
}

export interface AuditListResponse {
  items: AuditEvent[];
  total: number;
  page: number;
  size: number;
}

export interface SystemHealth {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  demo_mode: boolean;
  oidc_configured: boolean;
  llm_provider: string;
  llm_model: string;
}

export interface AuthUser {
  user_id: string;
  username: string;
  email: string | null;
  roles: string[];
  is_demo: boolean;
}
