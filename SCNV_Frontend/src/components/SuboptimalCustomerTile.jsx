import React, { useState, useEffect } from 'react';
import { UserX, AlertTriangle, CheckCircle } from 'lucide-react';
import { API_URL, STORAGE_KEYS } from '../config/constants';

function SuboptimalCustomerTile({ selectedCountry }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
    const url = selectedCountry
      ? `${API_URL}/api/kpi/suboptimal-customers?country=${selectedCountry}`
      : `${API_URL}/api/kpi/suboptimal-customers`;

    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.json())
      .then((d) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [selectedCountry]);

  if (loading) {
    return (
      <div className="kpi-card kpi-card--loading">
        <div className="kpi-card__shimmer" />
      </div>
    );
  }
  if (!data) return null;

  const pct = data.suboptimal_pct;
  const severity = pct >= 60 ? 'critical' : pct >= 40 ? 'warning' : 'good';
  const colorMap = { critical: '#ef4444', warning: '#f59e0b', good: '#10b981' };
  const iconMap = {
    critical: <AlertTriangle size={22} />,
    warning: <UserX size={22} />,
    good: <CheckCircle size={22} />,
  };
  const color = colorMap[severity];

  return (
    <div className="suboptimal-tile" id="suboptimal-customer-tile">
      <div className="suboptimal-tile__header">
        <div className="suboptimal-tile__icon" style={{ background: `${color}15`, color }}>
          {iconMap[severity]}
        </div>
        <div className="suboptimal-tile__badge" style={{ background: `${color}15`, color }}>
          {severity === 'critical' ? '● Critical' : severity === 'warning' ? '● Warning' : '● Healthy'}
        </div>
      </div>

      <div className="suboptimal-tile__value" style={{ color }}>{pct}%</div>
      <div className="suboptimal-tile__label">Sub-optimal Customer %</div>
      <div className="suboptimal-tile__desc">
        {data.suboptimal_orders} of {data.total_orders} orders allocated sub-optimally
        {selectedCountry ? ` in ${selectedCountry}` : ''}
      </div>

      {/* Progress ring */}
      <div className="suboptimal-tile__ring">
        <svg viewBox="0 0 36 36" className="suboptimal-ring-svg">
          <path
            className="suboptimal-ring-bg"
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          />
          <path
            className="suboptimal-ring-fill"
            strokeDasharray={`${pct}, 100`}
            style={{ stroke: color }}
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          />
        </svg>
      </div>
    </div>
  );
}

export default SuboptimalCustomerTile;
