import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import SOReroutingCard from '../components/SOReroutingCard';
import { STORAGE_KEYS, API_URL } from '../config/constants';
import { Bell, Activity, Filter, RefreshCcw } from 'lucide-react';
import '../styles/dashboard.css';

function DecisionsPage({ sidebarCollapsed, setSidebarCollapsed, setSelectedAgent }) {
  const [soAlerts, setSoAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  const authData = {
    token: localStorage.getItem(STORAGE_KEYS.TOKEN),
    role: localStorage.getItem(STORAGE_KEYS.ROLE),
    email: localStorage.getItem(STORAGE_KEYS.EMAIL),
  };

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/alerts/pending-so`, {
        headers: { Authorization: `Bearer ${authData.token}` },
      });
      const data = await res.json();
      setSoAlerts(data.alerts || []);
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const handleLogout = () => {
    Object.values(STORAGE_KEYS).forEach((k) => localStorage.removeItem(k));
    window.location.href = '/login';
  };

  return (
    <div className="chat-page">
      <Sidebar 
        sessions={[]} 
        currentSessionId={null} 
        authData={authData} 
        onLogout={handleLogout}
        activePage="decisions"
        collapsed={sidebarCollapsed}
        setCollapsed={setSidebarCollapsed}
        onSelectAgent={setSelectedAgent}
      />
      
      <main className="chat-main" style={{ padding: '1.5rem 2rem', overflowY: 'auto', backgroundColor: '#f8fafc' }}>
        <header style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1 style={{ fontSize: '2rem', fontWeight: '800', color: '#0f172a', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Bell className="text-primary" size={32} />
              Re-routing Decisions
            </h1>
            <p style={{ color: '#64748b', fontSize: '1.1rem' }}>
              Review and act on sub-optimal sales order allocations across the network.
            </p>
          </div>

          <button 
            onClick={fetchAlerts}
            className="btn btn-outline"
            style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 20px', borderRadius: '12px' }}
          >
            <RefreshCcw size={16} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </header>

        <div className="decisions-container" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', width: '100%' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '4rem', color: '#64748b' }}>
              <div className="loading-spinner" style={{ marginBottom: '1rem' }} />
              <p>Loading pending decisions...</p>
            </div>
          ) : soAlerts.length === 0 ? (
            <div style={{ 
              textAlign: 'center', 
              padding: '5rem 2rem', 
              background: 'white', 
              borderRadius: '24px', 
              border: '1px solid #e2e8f0',
              boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)'
            }}>
              <div style={{ width: '80px', height: '80px', background: '#f0fdf4', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem' }}>
                <Activity size={40} color="#10b981" />
              </div>
              <h3 style={{ fontSize: '1.5rem', fontWeight: '700', color: '#0f172a', marginBottom: '0.5rem' }}>All Clear!</h3>
              <p style={{ color: '#64748b' }}>No pending re-routing decisions found in the network.</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '1.25rem' }}>
              {soAlerts.map(alert => (
                <SOReroutingCard 
                  key={alert.id} 
                  alert={alert} 
                  onActionComplete={() => fetchAlerts()} 
                />
              ))}
            </div>
          )}
        </div>
      </main>

      <style>{`
        .animate-spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        
        .loading-spinner {
          width: 40px;
          height: 40px;
          border: 3px solid #f1f5f9;
          border-top-color: var(--color-primary);
          border-radius: 50%;
          display: inline-block;
          animation: spin 1s linear infinite;
        }

        .decisions-container .so-card {
          background: white;
          border: 1px solid #e2e8f0;
          box-shadow: 0 10px 15px -3px rgba(0,0,0,0.04);
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .decisions-container .so-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1);
          border-color: #cbd5e1;
        }
      `}</style>
    </div>
  );
}

export default DecisionsPage;
