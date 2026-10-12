import React, { useState } from 'react';
import { Session, Step } from '../types';
import { apiClient } from '../api/client';

interface TraceViewerProps {
  activeSession: Session | null;
  steps: Step[];
}

export const TraceViewer: React.FC<TraceViewerProps> = ({ activeSession, steps }) => {
  const [selectedStep, setSelectedStep] = useState<Step | null>(steps[0] || null);
  const [traceData, setTraceData] = useState<Record<string, any> | null>(null);
  const [exporting, setExporting] = useState(false);

  const handleExportTrace = async () => {
    if (!activeSession) return;
    setExporting(true);
    try {
      const data = await apiClient.exportTrace(activeSession.id);
      setTraceData(data);
    } catch (err: any) {
      alert(`Trace export failed: ${err.message}`);
    } finally {
      setExporting(false);
    }
  };

  if (!activeSession) {
    return (
      <div className="card">
        <h2 className="card-title">Trace & Artifact Inspector</h2>
        <div className="state-box">Please select or launch a session in the Runner Console first.</div>
      </div>
    );
  }

  const currentStep = selectedStep || steps[0];
  const domArtifact = currentStep?.artifacts.find((a) => a.artifact_type === 'dom_snapshot');
  const screenshotArtifact = currentStep?.artifacts.find((a) => a.artifact_type === 'screenshot');

  return (
    <div className="grid-2">
      {/* Left: Step Timeline */}
      <div className="card">
        <h2 className="card-title">
          <span>Session Trace: {activeSession.name}</span>
          <button className="btn btn-primary" onClick={handleExportTrace} disabled={exporting} style={{ fontSize: '0.75rem' }}>
            {exporting ? 'Exporting...' : 'Export Trace JSON'}
          </button>
        </h2>

        {traceData && (
          <div className="alert-box alert-info" style={{ maxHeight: '160px', overflowY: 'auto' }}>
            <strong>Trace Export Ready:</strong>
            <pre style={{ fontSize: '0.7rem', marginTop: '0.25rem' }}>
              {JSON.stringify(traceData.summary, null, 2)}
            </pre>
          </div>
        )}

        <h3 style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
          Steps Timeline ({steps.length})
        </h3>

        {steps.length === 0 ? (
          <div className="state-box">No steps recorded in this session.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '450px', overflowY: 'auto' }}>
            {steps.map((st) => (
              <div
                key={st.id}
                onClick={() => setSelectedStep(st)}
                style={{
                  padding: '0.75rem',
                  borderRadius: '0.5rem',
                  cursor: 'pointer',
                  border: currentStep?.id === st.id ? '1px solid var(--accent-cyan)' : '1px solid var(--border-color)',
                  backgroundColor: currentStep?.id === st.id ? 'var(--bg-tertiary)' : 'var(--bg-primary)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <strong>
                    #{st.step_index} {st.action}
                  </strong>
                  <span className={`badge ${st.status === 'passed' ? 'badge-green' : 'badge-red'}`}>
                    {st.status}
                  </span>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                  Duration: {st.duration_ms}ms · Artifacts: {st.artifacts.length}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Right: Step Artifact & Visual Inspector */}
      <div className="card">
        <h2 className="card-title">
          <span>Artifact Inspector {currentStep ? `(#${currentStep.step_index})` : ''}</span>
          {currentStep && (
            <span className={`badge ${currentStep.status === 'passed' ? 'badge-green' : 'badge-red'}`}>
              {currentStep.status}
            </span>
          )}
        </h2>

        {!currentStep ? (
          <div className="state-box">Select a step on the left to inspect its artifacts and DOM state.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {/* Screenshot Rendering */}
            {screenshotArtifact && (
              <div>
                <h4 style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                  Screen Visual State (SVG Artifact)
                </h4>
                <div
                  style={{
                    backgroundColor: '#0f172a',
                    padding: '0.5rem',
                    borderRadius: '0.5rem',
                    border: '1px solid var(--border-color)',
                    maxHeight: '220px',
                    overflow: 'hidden',
                  }}
                  dangerouslySetInnerHTML={{ __html: screenshotArtifact.content }}
                />
              </div>
            )}

            {/* DOM Snapshot */}
            <div>
              <h4 style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                DOM / Accessibility State
              </h4>
              <pre
                style={{
                  backgroundColor: 'var(--bg-primary)',
                  padding: '0.75rem',
                  borderRadius: '0.5rem',
                  fontSize: '0.75rem',
                  color: '#38bdf8',
                  maxHeight: '180px',
                  overflowY: 'auto',
                }}
              >
                {domArtifact ? JSON.stringify(domArtifact.content, null, 2) : 'No DOM snapshot recorded'}
              </pre>
            </div>

            {/* Sanitized Output */}
            <div>
              <h4 style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                Sanitized Step Output Payload
              </h4>
              <pre
                style={{
                  backgroundColor: 'var(--bg-primary)',
                  padding: '0.75rem',
                  borderRadius: '0.5rem',
                  fontSize: '0.75rem',
                  color: '#a7f3d0',
                  maxHeight: '140px',
                  overflowY: 'auto',
                }}
              >
                {JSON.stringify(currentStep.output_payload, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
