import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import AuthPage from './pages/Auth';
import ChatPage from './pages/Chat';
import DashboardPage from './pages/Dashboard';
import DecisionsPage from './pages/Decisions';
import { STORAGE_KEYS } from './config/constants';
import { AGENTS } from './config/agents.jsx';

function ProtectedRoute({ children }) {
  const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function PublicRoute({ children }) {
  const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
  if (token) {
    return <Navigate to="/" replace />;
  }
  return children;
}

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(AGENTS[0]);

  // Auto-collapse sidebar when an agent is selected
  useEffect(() => {
    if (selectedAgent) {
      setSidebarCollapsed(true);
    }
  }, [selectedAgent]);

  return (
    <Routes>
      <Route
        path="/login"
        element={
          <PublicRoute>
            <AuthPage />
          </PublicRoute>
        }
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage
              sidebarCollapsed={sidebarCollapsed}
              setSidebarCollapsed={setSidebarCollapsed}
              setSelectedAgent={setSelectedAgent}
            />
          </ProtectedRoute>
        }
      />
      <Route
        path="/chat"
        element={
          <ProtectedRoute>
            <ChatPage
              sidebarCollapsed={sidebarCollapsed}
              setSidebarCollapsed={setSidebarCollapsed}
              selectedAgent={selectedAgent}
              setSelectedAgent={setSelectedAgent}
            />
          </ProtectedRoute>
        }
      />
      <Route
        path="/decisions"
        element={
          <ProtectedRoute>
            <DecisionsPage
              sidebarCollapsed={sidebarCollapsed}
              setSidebarCollapsed={setSidebarCollapsed}
              setSelectedAgent={setSelectedAgent}
            />
          </ProtectedRoute>
        }
      />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default App;
