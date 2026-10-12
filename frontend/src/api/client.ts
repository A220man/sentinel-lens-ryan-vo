/** Typed API client connecting the React frontend to the Sentinel Lens backend. */

import {
  Session,
  SessionCreatePayload,
  SessionListResponse,
  Step,
  StepActionPayload,
  Evaluation,
  AuditListResponse,
  SystemHealth,
  AuthUser,
} from '../types';

let inMemoryToken: string | null = null;
const API_BASE = 'http://127.0.0.1:8000/api/v1';

export const apiClient = {
  setToken(token: string | null) {
    inMemoryToken = token;
  },

  getToken(): string | null {
    return inMemoryToken;
  },

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    if (inMemoryToken) {
      headers['Authorization'] = `Bearer ${inMemoryToken}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMsg = `HTTP ${response.status}`;
      try {
        const json = JSON.parse(errorText);
        errorMsg = json.detail || errorMsg;
      } catch {
        // Keep raw HTTP status
      }
      throw new Error(errorMsg);
    }

    return response.json() as Promise<T>;
  },

  async getHealth(): Promise<SystemHealth> {
    return this.request<SystemHealth>('/system/health');
  },

  async getMe(): Promise<AuthUser> {
    return this.request<AuthUser>('/auth/me');
  },

  async issueDemoToken(userId: string = 'demo-operator', role: string = 'operator'): Promise<string> {
    const data = await this.request<{ access_token: string }>('/auth/demo-token', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, role }),
    });
    this.setToken(data.access_token);
    return data.access_token;
  },

  async createSession(payload: SessionCreatePayload): Promise<Session> {
    return this.request<Session>('/sessions', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async listSessions(target?: string, status?: string, page = 1, size = 20): Promise<SessionListResponse> {
    const params = new URLSearchParams({ page: String(page), size: String(size) });
    if (target) params.append('target', target);
    if (status) params.append('status', status);
    return this.request<SessionListResponse>(`/sessions?${params.toString()}`);
  },

  async getSession(sessionId: string): Promise<Session> {
    return this.request<Session>(`/sessions/${sessionId}`);
  },

  async executeStep(sessionId: string, payload: StepActionPayload): Promise<Step> {
    return this.request<Step>(`/sessions/${sessionId}/steps`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getSessionSteps(sessionId: string): Promise<Step[]> {
    return this.request<Step[]>(`/sessions/${sessionId}/steps`);
  },

  async closeSession(sessionId: string): Promise<Record<string, any>> {
    return this.request<Record<string, any>>(`/sessions/${sessionId}/close`, {
      method: 'POST',
    });
  },

  async exportTrace(sessionId: string): Promise<Record<string, any>> {
    return this.request<Record<string, any>>(`/sessions/${sessionId}/trace`);
  },

  async runEvaluation(benchmarkName = 'e2e-semantic-grounding-v1', target = 'web'): Promise<Evaluation> {
    return this.request<Evaluation>('/evaluations/run', {
      method: 'POST',
      body: JSON.stringify({ benchmark_name: benchmarkName, target }),
    });
  },

  async listEvaluations(): Promise<Evaluation[]> {
    return this.request<Evaluation[]>('/evaluations');
  },

  async listAuditLogs(action?: string, page = 1, size = 20): Promise<AuditListResponse> {
    const params = new URLSearchParams({ page: String(page), size: String(size) });
    if (action) params.append('action', action);
    return this.request<AuditListResponse>(`/system/audit?${params.toString()}`);
  },
};
