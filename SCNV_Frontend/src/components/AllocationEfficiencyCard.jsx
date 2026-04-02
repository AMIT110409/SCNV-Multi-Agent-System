import React, { useState, useEffect } from 'react';
import { Gauge, TrendingDown, Target } from 'lucide-react';
import { API_URL, STORAGE_KEYS } from '../config/constants';
import StarBorder from './StarBorder';

function AllocationEfficiencyCard({ selectedCountry }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
    const url = selectedCountry
      ? `${API_URL}/api/kpi/allocation-efficiency?country=${selectedCountry}`
      : `${API_URL}/api/kpi/allocation-efficiency`;

    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.json())
      .then((d) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [selectedCountry]);

  if (loading) {
    return (
      <div className="kpi-efficiency-grid" style={{ display: 'flex', gap: '1.5rem' }}>
        {[1, 2, 3].map((i) => (
          <div key={i} className="kpi-card kpi-card--loading" style={{ flex: 1 }}>
            <div className="kpi-card__shimmer" />
          </div>
        ))}
      </div>
    );
  }
  if (!data) return null;

  const metrics = [
    {
      label: 'Allocation Efficiency',
      value: `${data.allocation_efficiency_pct}%`,
      icon: <Gauge size={20} />,
      color: data.allocation_efficiency_pct >= 70 ? '#10b981' : data.allocation_efficiency_pct >= 50 ? '#f59e0b' : '#ef4444',
      description: 'Avg efficiency score across all orders',
    },
    {
      label: 'Unproductive Transfer',
      value: `${data.unproductive_transfer_ratio}%`,
      icon: <TrendingDown size={20} />,
      color: data.unproductive_transfer_ratio <= 30 ? '#10b981' : data.unproductive_transfer_ratio <= 50 ? '#f59e0b' : '#ef4444',
      description: 'Ratio of unproductive volume vs total',
    },
    {
      label: 'Optimal Allocation',
      value: `${data.optimal_allocation_ratio}%`,
      icon: <Target size={20} />,
      color: data.optimal_allocation_ratio >= 60 ? '#10b981' : data.optimal_allocation_ratio >= 40 ? '#f59e0b' : '#ef4444',
      description: 'Orders allocated to optimal plant',
    },
  ];

  return (
    <div className="kpi-efficiency-grid" style={{ display: 'flex', gap: '1.5rem' }}>
      {metrics.map((m) => (
        <StarBorder 
          key={m.label} 
          color={m.color} 
          speed="10s" 
          thickness={2} 
          style={{ flex: 1, borderRadius: '16px' }}
        >
          <div className="kpi-card" id={`kpi-${m.label.replace(/\s/g, '-').toLowerCase()}`} style={{ height: '100%', margin: 0, border: 'none' }}>
            <div className="kpi-card__header">
              <div className="kpi-card__icon" style={{ background: `${m.color}15`, color: m.color }}>
                {m.icon}
              </div>
              <div className="kpi-card__trend-badge" style={{ background: `${m.color}15`, color: m.color }}>
                {m.label.includes('Unproductive')
                  ? (data.unproductive_transfer_ratio <= 30 ? '● Low' : '● High')
                  : (parseFloat(m.value) >= 60 ? '● Good' : '● Needs Attention')}
              </div>
            </div>
            <div className="kpi-card__value" style={{ color: m.color }}>
              {m.value}
            </div>
            <div className="kpi-card__label">{m.label}</div>
            <div className="kpi-card__desc">{m.description}</div>

            <div className="kpi-card__progress">
              <div
                className="kpi-card__progress-fill"
                style={{
                  width: `${Math.min(parseFloat(m.value), 100)}%`,
                  background: `linear-gradient(90deg, ${m.color}, ${m.color}80)`,
                }}
              />
            </div>
          </div>
        </StarBorder>
      ))}
    </div>
  );
}

export default AllocationEfficiencyCard;
