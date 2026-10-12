import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { SessionConsole } from './components/SessionConsole';
import { TraceViewer } from './components/TraceViewer';
import { EvaluationDashboard } from './components/EvaluationDashboard';
import { AuditLog } from './components/AuditLog';
import { Session, Step, SystemHealth, AuthUser } from './types';
import { apiClient } from './api/client';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('console');
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSession, setActiveSession] = useState<Session | null>(null);
  const [steps, setSteps] = useState<Step[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const initAuth = async () => {
    try {
      // Automatically acquire a demo token in development/demo mode
      await apiClient.issueDemoToken('demo-operator', 'operator');
      const u = await apiClient.getMe();
      setUser(u);
    } catch {
      // Continue unauthenticated or handle OIDC redirect
    }
  };

  const loadHealth = async () => {
    try {
      const h = await apiClient.getHealth();
      setHealth(h);
    } catch {
      // Offline fallback
    }
  };

  const loadSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.listSessions();
      setSessions(data.items);
      if (data.items.length > 0 && !activeSession) {
        setActiveSession(data.items[0]);
        loadSteps(data.items[0].id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load sessions');
    } finally {
      setLoading(false);
    }
  };

  const loadSteps = async (sessionId: string) => {
    try {
      const stepList = await apiClient.getSessionSteps(sessionId);
      setSteps(Array.isArray(stepList) ? stepList : []);
    } catch {
      setSteps([]);
    }
  };

  useEffect(() => {
    loadHealth();
    initAuth().then(() => {
      loadSessions();
    });
  }, []);

  const handleSelectSession = (s: Session) => {
    setActiveSession(s);
    loadSteps(s.id);
  };

  const handleSessionCreated = (s: Session) => {
    setSessions([s, ...sessions]);
    setActiveSession(s);
    setSteps([]);
  };

  const handleStepExecuted = (step: Step) => {
    setSteps([...steps, step]);
    if (activeSession) {
      setActiveSession({
        ...activeSession,
        step_count: activeSession.step_count + 1,
      });
    }
  };

  const handleSessionClosed = () => {
    loadSessions();
    if (activeSession) {
      setActiveSession({
        ...activeSession,
        status: 'completed',
      });
    }
  };

  return (
    <div className="app-container">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        health={health}
        user={user}
        onRefreshAuth={initAuth}
      />

      <main role="main">
        {activeTab === 'console' && (
          <SessionConsole
            sessions={sessions}
            activeSession={activeSession}
            steps={steps}
            loading={loading}
            error={error}
            onSelectSession={handleSelectSession}
            onRefreshSessions={loadSessions}
            onSessionCreated={handleSessionCreated}
            onStepExecuted={handleStepExecuted}
            onSessionClosed={handleSessionClosed}
          />
        )}

        {activeTab === 'trace' && (
          <TraceViewer activeSession={activeSession} steps={steps} />
        )}

        {activeTab === 'evaluation' && <EvaluationDashboard />}

        {activeTab === 'audit' && <AuditLog />}
      </main>

      <footer
        style={{
          marginTop: '2.5rem',
          paddingTop: '1rem',
          borderTop: '1px solid var(--border-color)',
          textAlign: 'center',
          fontSize: '0.8125rem',
          color: 'var(--text-muted)',
        }}
      >
        <p>
          Sentinel Lens — Autonomous E2E Test Session Host & Visual Grounding Engine
        </p>
        <p style={{ marginTop: '0.25rem' }}>
          Ryan Vo · <a href="mailto:ryandtvo@gmail.com" style={{ color: 'var(--accent-cyan)' }}>ryandtvo@gmail.com</a>
        </p>
      </footer>
    </div>
  );
};
