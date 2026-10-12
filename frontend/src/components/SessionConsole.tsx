import React, { useState } from 'react';
import { Session, Step, TargetPlatform } from '../types';
import { apiClient } from '../api/client';

interface SessionConsoleProps {
  sessions: Session[];
  activeSession: Session | null;
  steps: Step[];
  loading: boolean;
  error: string | null;
  onSelectSession: (session: Session) => void;
  onRefreshSessions: () => void;
  onSessionCreated: (session: Session) => void;
  onStepExecuted: (step: Step) => void;
  onSessionClosed: () => void;
}

export const SessionConsole: React.FC<SessionConsoleProps> = ({
  sessions,
  activeSession,
  steps,
  loading,
  error,
  onSelectSession,
  onRefreshSessions,
  onSessionCreated,
  onStepExecuted,
  onSessionClosed,
}) => {
  const [newSessionName, setNewSessionName] = useState('E2E Regression Run');
  const [targetPlatform, setTargetPlatform] = useState<TargetPlatform>('web');
  const [actionType, setActionType] = useState<'act' | 'assert_visible' | 'click'>('act');
  const [instructionText, setInstructionText] = useState('open settings and turn on dark mode');
  const [submittingAction, setSubmittingAction] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const handleCreateSession = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    try {
      const created = await apiClient.createSession({
        name: newSessionName,
        target: targetPlatform,
        cwd: '/repo',
        config: { timeout: 30 },
      });
      onSessionCreated(created);
    } catch (err: any) {
      setLocalError(err.message || 'Failed to create session');
    }
  };

  const handleExecuteAction = async () => {
    if (!activeSession) return;
    setSubmittingAction(true);
    setLocalError(null);
    try {
      const step = await apiClient.executeStep(activeSession.id, {
        action: actionType,
        instruction: actionType === 'act' ? instructionText : undefined,
        selector: actionType !== 'act' ? instructionText : undefined,
      });
      onStepExecuted(step);
    } catch (err: any) {
      setLocalError(err.message || 'Failed to execute step');
    } finally {
      setSubmittingAction(false);
    }
  };

  const handleCloseSession = async () => {
    if (!activeSession) return;
    try {
      await apiClient.closeSession(activeSession.id);
      onSessionClosed();
    } catch (err: any) {
      setLocalError(err.message || 'Failed to close session');
    }
  };

  return (
    <div className="grid-2">
      {/* Left Pane: Session Management & Creation */}
      <div className="card">
        <h2 className="card-title">
          <span>Programmatic Runner Sessions</span>
          <button className="btn btn-secondary" onClick={onRefreshSessions} style={{ fontSize: '0.75rem' }}>
            Refresh
          </button>
        </h2>

        {error && <div className="alert-box alert-error">{error}</div>}
        {localError && <div className="alert-box alert-error">{localError}</div>}

        <form onSubmit={handleCreateSession} style={{ marginBottom: '1.5rem' }}>
          <div className="form-group">
            <label className="form-label">Session Name</label>
            <input
              className="form-input"
              value={newSessionName}
              onChange={(e) => setNewSessionName(e.target.value)}
              placeholder="e.g. Host embedded Vitest suite"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Target Platform / Device</label>
            <select
              className="form-select"
              value={targetPlatform}
              onChange={(e) => setTargetPlatform(e.target.value as TargetPlatform)}
            >
              <option value="web">Web Browser (1280x800)</option>
              <option value="mobile_android">Android Emulator (412x915)</option>
              <option value="mobile_ios">iOS Simulator (393x852)</option>
              <option value="desktop">Desktop Electron (1920x1080)</option>
            </select>
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
            openSession() — Initialize Fixtures
          </button>
        </form>

        <h3 style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
          Recent Sessions ({sessions.length})
        </h3>

        {loading ? (
          <div className="state-box">Loading sessions...</div>
        ) : sessions.length === 0 ? (
          <div className="state-box">No test sessions created yet. Launch one above!</div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Session ID</th>
                  <th>Target</th>
                  <th>Status</th>
                  <th>Steps</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((s) => (
                  <tr
                    key={s.id}
                    style={{
                      cursor: 'pointer',
                      backgroundColor: activeSession?.id === s.id ? 'rgba(2, 132, 199, 0.2)' : undefined,
                    }}
                    onClick={() => onSelectSession(s)}
                  >
                    <td>
                      <strong>{s.name}</strong>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{s.id}</div>
                    </td>
                    <td>
                      <span className="badge badge-blue">{s.target}</span>
                    </td>
                    <td>
                      <span className={`badge ${s.status === 'running' ? 'badge-amber' : 'badge-green'}`}>
                        {s.status}
                      </span>
                    </td>
                    <td>{s.step_count}</td>
                    <td>
                      <button
                        className="btn btn-secondary"
                        style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectSession(s);
                        }}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Right Pane: Embedded Session Controller & Live Step Feed */}
      <div className="card">
        <h2 className="card-title">
          <span>
            {activeSession ? `Active Session: ${activeSession.name}` : 'Session Action Dispatcher'}
          </span>
          {activeSession && activeSession.status === 'running' && (
            <button className="btn btn-danger" onClick={handleCloseSession} style={{ fontSize: '0.75rem' }}>
              session.close()
            </button>
          )}
        </h2>

        {!activeSession ? (
          <div className="state-box">
            Select or launch a test session to interact with its fixture graph (agent, screen, device).
          </div>
        ) : (
          <div>
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
              <span className="badge badge-blue">ID: {activeSession.id}</span>
              <span className="badge badge-green">Target: {activeSession.target}</span>
              <span className="badge badge-amber">Status: {activeSession.status}</span>
            </div>

            {activeSession.status === 'running' && (
              <div style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: 'var(--bg-primary)', borderRadius: '0.5rem' }}>
                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <select
                    className="form-select"
                    style={{ width: '160px' }}
                    value={actionType}
                    onChange={(e) => setActionType(e.target.value as any)}
                  >
                    <option value="act">agent.act()</option>
                    <option value="assert_visible">assert_visible()</option>
                    <option value="click">click()</option>
                  </select>
                  <input
                    className="form-input"
                    value={instructionText}
                    onChange={(e) => setInstructionText(e.target.value)}
                    placeholder={actionType === 'act' ? 'Instruction (e.g. click submit)' : 'Selector or Text'}
                  />
                  <button
                    className="btn btn-primary"
                    onClick={handleExecuteAction}
                    disabled={submittingAction}
                  >
                    {submittingAction ? 'Running...' : 'Execute'}
                  </button>
                </div>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Actions pass through secret redaction and capture DOM + SVG visual artifacts automatically.
                </p>
              </div>
            )}

            <h3 style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
              Executed Steps ({steps.length})
            </h3>

            {steps.length === 0 ? (
              <div className="state-box">No steps recorded yet in this session. Dispatch an action above!</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '420px', overflowY: 'auto' }}>
                {steps.map((st) => (
                  <div key={st.id} className="trace-step-item">
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <strong>
                        Step {st.step_index}: {st.action}
                      </strong>
                      <span className={`badge ${st.status === 'passed' ? 'badge-green' : 'badge-red'}`}>
                        {st.status} ({st.duration_ms}ms)
                      </span>
                    </div>

                    <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                      {st.selector ? `Selector: ${st.selector}` : JSON.stringify(st.input_payload)}
                    </p>

                    {st.artifacts && st.artifacts.length > 0 && (
                      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                        {st.artifacts.map((a) => (
                          <span key={a.id} className="badge badge-blue" style={{ fontSize: '0.7rem' }}>
                            Artifact: {a.artifact_type} ({a.size_bytes}B)
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
