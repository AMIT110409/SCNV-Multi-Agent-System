import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { BarChart3 } from 'lucide-react';
import { API_URL, STORAGE_KEYS } from '../config/constants';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip" style={{
      background: 'rgba(255, 255, 255, 0.95)',
      backdropFilter: 'blur(8px)',
      border: '1px solid rgba(0,0,0,0.05)',
      borderRadius: '12px',
      padding: '12px 16px',
      boxShadow: '0 10px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1)'
    }}>
      <p className="chart-tooltip__title" style={{ fontSize: '13px', fontWeight: '700', color: '#1f2937', marginBottom: '8px' }}>{label}</p>
      {payload.map((entry, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: i === 0 ? '4px' : 0 }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: entry.color }} />
          <p style={{ fontSize: '12px', color: '#4b5563', margin: 0 }}>
            {entry.name}: <strong style={{ color: '#111827' }}>{Number(entry.value).toLocaleString()} HL</strong>
          </p>
        </div>
      ))}
    </div>
  );
};

const renderCustomLegend = (props) => {
  const { payload } = props;
  return (
    <div style={{ display: 'flex', gap: '20px', justifyContent: 'flex-end', marginBottom: '20px' }}>
      {payload.map((entry, index) => (
        <div key={`item-${index}`} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{ 
            width: '10px', 
            height: '10px', 
            borderRadius: '50%', 
            background: entry.color,
            boxShadow: `0 0 8px ${entry.color}80`
          }} />
          <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--color-muted)' }}>{entry.value}</span>
        </div>
      ))}
    </div>
  );
};

function ProductiveTrendChart({ selectedCountry }) {
  const [trendData, setTrendData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
    const url = selectedCountry
      ? `${API_URL}/api/kpi/productive-trend?country=${selectedCountry}`
      : `${API_URL}/api/kpi/productive-trend`;

    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.json())
      .then((d) => {
        const trend = (d.trend || []).map((t) => ({
          ...t,
          month: formatMonth(t.month),
        }));
        setTrendData(trend);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [selectedCountry]);

  return (
    <section className="chart-section" id="productive-trend-chart">
      <div className="chart-section__header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div className="chart-section__title-group">
          <div className="chart-section__icon">
            <BarChart3 size={20} />
          </div>
          <div>
            <h2 className="chart-section__title">Productive vs Unproductive Volume</h2>
            <p className="chart-section__subtitle">
              Monthly trend {selectedCountry ? `for ${selectedCountry}` : '(all countries)'}
            </p>
          </div>
        </div>
        
        {/* Custom Header Legend */}
        <div style={{ display: 'flex', gap: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div className="status-dot status-dot--green status-dot--blinking" />
            <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--color-text-sec)' }}>Productive</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div className="status-dot status-dot--red status-dot--blinking" />
            <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--color-text-sec)' }}>Unproductive</span>
          </div>
        </div>
      </div>

      <div className="chart-section__body" style={{ height: 380, padding: '1.5rem 1.5rem 1rem 1rem' }}>
        {loading ? (
          <div className="chart-section__loading">Loading chart data…</div>
        ) : trendData.length === 0 ? (
          <div className="chart-section__empty">No trend data available</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={trendData} barGap={8} barCategoryGap="25%">
              <defs>
                <linearGradient id="barGradientProductive" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10b981" stopOpacity={1} />
                  <stop offset="100%" stopColor="#059669" stopOpacity={0.8} />
                </linearGradient>
                <linearGradient id="barGradientUnproductive" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#ef4444" stopOpacity={1} />
                  <stop offset="100%" stopColor="#dc2626" stopOpacity={0.8} />
                </linearGradient>
              </defs>
              <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis 
                dataKey="month" 
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 11, fill: '#64748b' }} 
                dy={10}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 11, fill: '#64748b' }}
                tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                dx={-10}
              />
              <Tooltip cursor={{ fill: 'rgba(241, 245, 249, 0.4)' }} content={<CustomTooltip />} />
              <Bar
                dataKey="productive"
                name="Productive"
                fill="url(#barGradientProductive)"
                radius={[6, 6, 0, 0]}
                animationDuration={1200}
                activeBar={{ fill: '#10b981', stroke: '#059669', strokeWidth: 1 }}
              />
              <Bar
                dataKey="unproductive"
                name="Unproductive"
                fill="url(#barGradientUnproductive)"
                radius={[6, 6, 0, 0]}
                animationDuration={1200}
                animationBegin={300}
                activeBar={{ fill: '#ef4444', stroke: '#dc2626', strokeWidth: 1 }}
              />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </section>
  );
}

function formatMonth(str) {
  if (!str || str === 'Unknown') return str;
  try {
    const [y, m] = str.split('-');
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${months[parseInt(m, 10) - 1]} ${y}`;
  } catch {
    return str;
  }
}

export default ProductiveTrendChart;
