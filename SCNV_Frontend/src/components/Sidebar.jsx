import React, { useState } from 'react';
import { Plus, Upload, LogOut, MessageSquare, LayoutDashboard, Bell, Compass, ChevronLeft, ChevronRight, ChevronDown, Network, Search, Activity, PanelLeftOpen, PanelLeftClose } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { getTimeLabel } from '../utils/helpers';
import '../styles/sidebar.css';

import { AGENTS } from '../config/agents.jsx';

function Sidebar({ authData, onLogout, onUploadClick, collapsed = false, setCollapsed, onSelectAgent }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [agentsOpen, setAgentsOpen] = useState(false);
  const activePage = location.pathname === '/' ? 'dashboard' : location.pathname === '/decisions' ? 'decisions' : 'chat';

  const handleAgentClick = (agent) => {
    onSelectAgent(agent);
    navigate('/chat');
  };

  return (
    <aside className={`sidebar ${collapsed ? 'sidebar--collapsed' : ''}`}>
      {/* Header with Logo and Toggle */}
      <div className="sidebar__logo-header">
        {!collapsed && (
          <div className="sidebar__logo" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
            <div className="sidebar__brand-container" style={{ display: 'flex', flexDirection: 'column' }}>
              <div className="sidebar__brand">
                <span className="sidebar__brand-akzo">OFI</span>
                <span className="sidebar__brand-nobel">Services</span>
              </div>
              <div className="sidebar__tagline">SCNV Platform</div>
            </div>
          </div>
        )}

        {collapsed && (
          <div className="sidebar__brand-mini" onClick={() => navigate('/')} style={{ cursor: 'pointer', fontWeight: 'bold', fontSize: '20px' }}>
            <span style={{ color: 'var(--color-primary)' }}>O</span>
            <span style={{ color: 'var(--color-secondary)' }}>F</span>
            <span style={{ color: 'var(--color-secondary)' }}>I</span>
          </div>
        )}

        <button
          className="sidebar__toggle-v2"
          onClick={() => setCollapsed(!collapsed)}
          title={collapsed ? "Open sidebar" : "Close sidebar"}
        >
          {collapsed ? <PanelLeftOpen size={20} /> : <PanelLeftClose size={20} />}
        </button>
      </div>

      {/* Main Navigation */}
      <div className="sidebar__nav">
        <button
          className={`nav-item ${activePage === 'dashboard' ? 'nav-item--active' : ''}`}
          onClick={() => navigate('/')}
          title={collapsed ? "Dashboard" : ""}
        >
          <div className="nav-icon-wrapper">
            <LayoutDashboard size={20} />
          </div>
          {!collapsed && <span>Dashboard</span>}
        </button>

        <button
          className={`nav-item ${activePage === 'decisions' ? 'nav-item--active' : ''}`}
          onClick={() => navigate('/decisions')}
          title={collapsed ? "Re-routing Decisions" : ""}
        >
          <div className="nav-icon-wrapper">
            <Bell size={20} />
          </div>
          {!collapsed && <span>Decisions</span>}
        </button>

        <div className={`nav-dropdown ${agentsOpen ? 'nav-dropdown--open' : ''}`}>
          <button
            className={`nav-item ${activePage === 'chat' ? 'nav-item--active' : ''}`}
            onClick={() => {
              if (collapsed) {
                setCollapsed(false);
                setAgentsOpen(true);
              } else {
                setAgentsOpen(!agentsOpen);
              }
            }}
            title={collapsed ? "Explore Agents" : ""}
          >
            <div className="nav-icon-wrapper">
              <Compass size={20} />
            </div>
            {!collapsed && (
              <>
                <span style={{ flex: 1 }}>Explore Agents</span>
                <ChevronDown size={14} className={`dropdown-arrow ${agentsOpen ? 'dropdown-arrow--rotated' : ''}`} />
              </>
            )}
          </button>

          <AnimatePresence>
            {agentsOpen && (
              <motion.div
                initial={{ height: 0, opacity: 0, overflow: 'hidden' }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3, ease: [0.04, 0.62, 0.23, 0.98] }}
                className={`nav-dropdown__content ${collapsed ? 'nav-dropdown__content--flyout' : ''}`}
              >
                {AGENTS.map(agent => (
                  <button
                    key={agent.id}
                    className="nav-dropdown__item"
                    onClick={() => handleAgentClick(agent)}
                    title={collapsed ? agent.title : ""}
                  >
                    <div className="agent-icon-small" style={{ color: agent.color }}>
                      {agent.icon}
                    </div>
                    <span>{agent.title}</span>
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Spacer to push footer down */}
      <div style={{ flex: 1 }} />

      {/* Footer */}
      <div className="sidebar__footer">
        {/* User Info */}
        {!collapsed && (
          <div className="sidebar__user-card">
            <div className="sidebar__user-email">{authData?.email || 'User'}</div>
            <div className="sidebar__user-role">{authData?.role || 'Guest'}</div>
          </div>
        )}

        {/* Logout */}
        <button className="btn btn-outline btn-full" onClick={onLogout} title="Logout">
          <LogOut size={14} />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;
