import React, { useState } from 'react';
import { ArrowRight, Check, X, RotateCcw, Clock, AlertTriangle, Package } from 'lucide-react';
import { API_URL, STORAGE_KEYS } from '../config/constants';

function SOReroutingCard({ alert, onActionComplete }) {
  const [actionLoading, setActionLoading] = useState(null);
  const [overrideReason, setOverrideReason] = useState('');
  const [showOverride, setShowOverride] = useState(false);
  const [resolved, setResolved] = useState(false);

  const handleAction = async (action) => {
    setActionLoading(action);
    try {
      const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
      await fetch(`${API_URL}/api/alerts/so/${alert.id}/execute`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ action, overrideReason: overrideReason || '' }),
      });
      setResolved(true);
      onActionComplete?.(alert.id, action);
    } catch (err) {
      console.error('SO action failed:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const severityColors = {
    high: { bg: '#fef2f2', border: '#fca5a5', text: '#dc2626', badge: '#fee2e2' },
    medium: { bg: '#fffbeb', border: '#fcd34d', text: '#d97706', badge: '#fef3c7' },
    low: { bg: '#f0fdf4', border: '#86efac', text: '#16a34a', badge: '#dcfce7' },
  };
  const sev = severityColors[alert.severity] || severityColors.medium;

  if (resolved) {
    return (
      <div className="so-card so-card--resolved">
        <div className="so-card__resolved-content">
          <Check size={20} color="#10b981" />
          <span>{alert.id} — Action completed</span>
        </div>
      </div>
    );
  }

  return (
    <div className="so-card" style={{ borderLeftColor: sev.text }} id={`so-card-${alert.id}`}>
      {/* Header */}
      <div className="so-card__header">
        <div className="so-card__id-group">
          <Package size={16} style={{ color: sev.text }} />
          <span className="so-card__id">{alert.id}</span>
          <span className="so-card__severity" style={{ background: sev.badge, color: sev.text }}>
            {alert.severity.toUpperCase()}
          </span>
        </div>
        <div className="so-card__time">
          <Clock size={12} />
          <span>{alert.timestamp}</span>
          <span className="so-card__escalation">Escalates in {alert.escalatesIn}</span>
        </div>
      </div>

      {/* Routing info */}
      <div className="so-card__routing">
        <div className="so-card__plant">
          <div className="so-card__plant-label">Assigned</div>
          <div className="so-card__plant-value so-card__plant-value--bad">{alert.assigned_plant}</div>
        </div>
        <ArrowRight size={20} color="var(--color-muted)" />
        <div className="so-card__plant">
          <div className="so-card__plant-label">Optimal</div>
          <div className="so-card__plant-value so-card__plant-value--good">{alert.optimal_plant}</div>
        </div>
        <div className="so-card__meta">
          <div><strong>{alert.customer}</strong></div>
          <div className="so-card__material">{alert.material}</div>
          <div>{alert.quantity_hl} HL · {alert.country}</div>
        </div>
      </div>

      {/* Reason */}
      <div className="so-card__reason">
        <AlertTriangle size={14} style={{ color: sev.text }} />
        <span>{alert.reason}</span>
      </div>

      {/* Efficiency score bar */}
      <div className="so-card__score">
        <span className="so-card__score-label">Efficiency Score</span>
        <div className="so-card__score-bar">
          <div
            className="so-card__score-fill"
            style={{
              width: `${alert.efficiency_score * 100}%`,
              background: alert.efficiency_score >= 0.7 ? '#10b981' : alert.efficiency_score >= 0.5 ? '#f59e0b' : '#ef4444',
            }}
          />
        </div>
        <span className="so-card__score-value">{(alert.efficiency_score * 100).toFixed(0)}%</span>
      </div>

      {/* Actions */}
      <div className="so-card__actions">
        <button
          className="so-card__btn so-card__btn--approve"
          onClick={() => handleAction('approve_reroute')}
          disabled={!!actionLoading}
        >
          {actionLoading === 'approve_reroute' ? '…' : <><Check size={14} /> Approve Re-route</>}
        </button>
        <button
          className="so-card__btn so-card__btn--reject"
          onClick={() => handleAction('reject')}
          disabled={!!actionLoading}
        >
          {actionLoading === 'reject' ? '…' : <><X size={14} /> Reject</>}
        </button>
        <button
          className="so-card__btn so-card__btn--override"
          onClick={() => setShowOverride(!showOverride)}
          disabled={!!actionLoading}
        >
          <RotateCcw size={14} /> Override
        </button>
      </div>

      {/* Override reason */}
      {showOverride && (
        <div className="so-card__override">
          <input
            type="text"
            placeholder="Enter override reason…"
            value={overrideReason}
            onChange={(e) => setOverrideReason(e.target.value)}
            className="so-card__override-input"
          />
          <button
            className="so-card__btn so-card__btn--submit"
            onClick={() => handleAction('override')}
            disabled={!overrideReason.trim() || !!actionLoading}
          >
            {actionLoading === 'override' ? '…' : 'Submit Override'}
          </button>
        </div>
      )}
    </div>
  );
}

export default SOReroutingCard;
