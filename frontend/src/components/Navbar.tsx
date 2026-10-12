import React from 'react';
import { AuthUser, SystemHealth } from '../types';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  health: SystemHealth | null;
  user: AuthUser | null;
  onRefreshAuth: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  health,
  user,
  onRefreshAuth,
}) => {
  return (
    <header className="header-bar" role="banner">
      <div>
        <div className="brand-badge">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <circle cx="12" cy="12" r="4" />
            <line x1="21.17" y1="8" x2="12" y2="8" />
            <line x1="3.95" y1="6.06" x2="8.54" y2="14" />
            <line x1="10.88" y1="21.94" x2="15.46" y2="14" />
          </svg>
          Sentinel Lens
        </div>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Ryan Vo | AI & Machine Learning — Embedded E2E Runner & Visual Grounding Engine
        </p>
      </div>

      <nav className="nav-tabs" aria-label="Main Navigation">
        <button
          className={`tab-btn ${activeTab === 'console' ? 'active' : ''}`}
          onClick={() => setActiveTab('console')}
        >
          Runner Console
        </button>
        <button
          className={`tab-btn ${activeTab === 'trace' ? 'active' : ''}`}
          onClick={() => setActiveTab('trace')}
        >
          Trace Inspector
        </button>
        <button
          className={`tab-btn ${activeTab === 'evaluation' ? 'active' : ''}`}
          onClick={() => setActiveTab('evaluation')}
        >
          AI/ML Evaluation
        </button>
        <button
          className={`tab-btn ${activeTab === 'audit' ? 'active' : ''}`}
          onClick={() => setActiveTab('audit')}
        >
          Audit Log
        </button>
      </nav>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        {health?.demo_mode && (
          <span className="badge badge-amber" title="Demo Mode active on localhost">
            Demo Mode
          </span>
        )}
        <span className="badge badge-green">
          v{health?.version || '1.0.0'}
        </span>
        <button
          className="btn btn-secondary"
          style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
          onClick={onRefreshAuth}
          title="Authenticate with operator token"
        >
          {user ? `Role: ${user.roles[0] || 'operator'}` : 'Get Token'}
        </button>
      </div>
    </header>
  );
};
