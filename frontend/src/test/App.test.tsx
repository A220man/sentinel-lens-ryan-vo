import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { App } from '../App';

describe('Sentinel Lens App Component', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn((url: string) => {
      if (url.includes('/system/health')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            status: 'healthy',
            app_name: 'Sentinel Lens',
            version: '1.0.0',
            environment: 'development',
            demo_mode: true,
            oidc_configured: true,
            llm_provider: 'openai-compatible',
            llm_model: 'gpt-4o-mini',
          }),
        });
      }
      if (url.includes('/auth/demo-token')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ access_token: 'mock-token-xyz' }),
        });
      }
      if (url.includes('/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            user_id: 'demo-operator',
            username: 'demo-operator',
            email: 'demo@sentinel-lens.local',
            roles: ['operator', 'viewer'],
            is_demo: true,
          }),
        });
      }
      if (url.includes('/steps')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([
            {
              id: 'step-01',
              session_id: 'sess-test-01',
              step_index: 1,
              action: 'act',
              selector: null,
              status: 'passed',
              duration_ms: 15.2,
              input_payload: { instruction: 'initialize' },
              output_payload: { verified: true },
              error_message: null,
              timestamp: new Date().toISOString(),
              artifacts: [],
            },
          ]),
        });
      }
      if (url.includes('/sessions')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            items: [
              {
                id: 'sess-test-01',
                name: 'Playwright Host Suite',
                target: 'web',
                status: 'running',
                cwd: '/repo',
                step_count: 3,
                artifact_count: 6,
                created_at: new Date().toISOString(),
                completed_at: null,
                summary: {},
              },
            ],
            total: 1,
            page: 1,
            size: 20,
          }),
        });
      }
      if (url.includes('/evaluations')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([]),
        });
      }
      if (url.includes('/system/audit')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ items: [], total: 0, page: 1, size: 20 }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
        text: () => Promise.resolve(''),
      });
    }));
  });

  it('renders main navigation and brand identity', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText('Sentinel Lens')).toBeInTheDocument();
    });
    expect(screen.getByText(/Ryan Vo \| AI & Machine Learning/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Runner Console/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Trace Inspector/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /AI\/ML Evaluation/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Audit Log/i })).toBeInTheDocument();
  });

  it('switches navigation tabs on click to AI/ML evaluation suite', async () => {
    render(<App />);
    const evalTabBtn = screen.getByRole('button', { name: /AI\/ML Evaluation/i });
    fireEvent.click(evalTabBtn);

    await waitFor(() => {
      expect(screen.getByText(/AI\/ML Evaluation Suite/i)).toBeInTheDocument();
    });
    expect(screen.getByRole('button', { name: /Run Benchmark/i })).toBeInTheDocument();
  });

  it('renders session console controls and openSession action', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText(/Programmatic Runner Sessions/i)).toBeInTheDocument();
    });
    expect(screen.getByRole('button', { name: /openSession\(\)/i })).toBeInTheDocument();
    expect(screen.getByDisplayValue('E2E Regression Run')).toBeInTheDocument();
  });

  it('switches to audit log tab and displays security trail', async () => {
    render(<App />);
    const auditTabBtn = screen.getByRole('button', { name: /Audit Log/i });
    fireEvent.click(auditTabBtn);

    await waitFor(() => {
      expect(screen.getByText(/Security & Operation Audit Trail/i)).toBeInTheDocument();
    });
  });
});
