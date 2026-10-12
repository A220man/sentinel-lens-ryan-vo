import React, { useState, useEffect } from 'react';
import { AuditEvent } from '../types';
import { apiClient } from '../api/client';

export const AuditLog: React.FC = () => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAuditLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.listAuditLogs();
      setEvents(data.items);
    } catch (err: any) {
      setError(err.message || 'Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAuditLogs();
  }, []);

  return (
    <div className="card">
      <h2 className="card-title">
        <span>Security & Operation Audit Trail</span>
        <button className="btn btn-secondary" onClick={loadAuditLogs} style={{ fontSize: '0.75rem' }}>
          Refresh
        </button>
      </h2>

      {error && <div className="alert-box alert-error">{error}</div>}

      {loading ? (
        <div className="state-box">Loading audit trail...</div>
      ) : events.length === 0 ? (
        <div className="state-box">No audit events recorded yet.</div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Event ID</th>
                <th>User / Identity</th>
                <th>Action</th>
                <th>Resource</th>
                <th>IP Address</th>
                <th>UTC Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {events.map((e) => (
                <tr key={e.id}>
                  <td><code>{e.id}</code></td>
                  <td><strong>{e.user_id}</strong></td>
                  <td>
                    <span className="badge badge-blue">{e.action}</span>
                  </td>
                  <td>
                    {e.resource_type}: <code>{e.resource_id}</code>
                  </td>
                  <td>{e.ip_address}</td>
                  <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {new Date(e.timestamp).toUTCString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
