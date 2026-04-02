import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bot, Loader2, Plus, MessageSquare, ChevronLeft, Upload, Bell, X } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import WelcomeScreen from '../components/WelcomeScreen';
import MessageBubble from '../components/MessageBubble';
import ChatInput from '../components/ChatInput';
import SOReroutingCard from '../components/SOReroutingCard';
import { fetchSessions, loadSession, saveSession, sendMessage, uploadDocument } from '../api/api';
import { generateId, getTimeLabel } from '../utils/helpers';
import PreviewModal from '../components/PreviewModal';
import { STORAGE_KEYS, API_URL } from '../config/constants';
import '../styles/chat.css';
import '../styles/sidebar.css';
import '../styles/components.css';
import '../styles/dashboard.css';
import StarBorder from '../components/StarBorder';

function ChatPage({ sidebarCollapsed, setSidebarCollapsed, selectedAgent, setSelectedAgent }) {
  const navigate = useNavigate();

  // ── Auth data from localStorage ──────────────────────────────────────────────
  const authData = {
    token: localStorage.getItem(STORAGE_KEYS.TOKEN),
    role: localStorage.getItem(STORAGE_KEYS.ROLE),
    email: localStorage.getItem(STORAGE_KEYS.EMAIL),
  };

  // ── State ────────────────────────────────────────────────────────────────────
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [soAlerts, setSoAlerts] = useState([]);
  const [showSOPanel, setShowSOPanel] = useState(false);
  const [previewFile, setPreviewFile] = useState(null);

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // ── Helpers ──────────────────────────────────────────────────────────────────
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // ── Data fetching ────────────────────────────────────────────────────────────
  const refreshSessions = useCallback(async () => {
    try {
      const list = await fetchSessions(selectedAgent?.id);
      setSessions(list);
    } catch (err) {
      console.error('Failed to fetch sessions:', err);
    }
  }, [selectedAgent]);

  const handleLoadSession = useCallback(async (sessionId) => {
    try {
      const data = await loadSession(sessionId);
      setCurrentSessionId(sessionId);
      setMessages(data.messages || []);
    } catch (err) {
      console.error('Failed to load session:', err);
    }
  }, []);

  const persistSession = useCallback(
    async (sessionId, msgs) => {
      if (!sessionId || msgs.length === 0) return;
      try {
        await saveSession({ sessionId, messages: msgs, agentId: selectedAgent?.id });
        await refreshSessions();
      } catch (err) {
        console.error('Failed to save session:', err);
      }
    },
    [refreshSessions],
  );

  // ── Send message ─────────────────────────────────────────────────────────────
  const handleSend = useCallback(async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    const sessionId = currentSessionId || generateId();

    if (!currentSessionId) setCurrentSessionId(sessionId);
    setInput('');

    const userMsg = { role: 'user', content: userMessage, timestamp: Date.now() };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const data = await sendMessage(userMessage, sessionId, selectedAgent?.id);
      const botMsg = {
        role: 'assistant',
        content: data.answer || 'No response',
        sources: data.sources || [],
        timestamp: Date.now(),
      };

      setMessages((prev) => {
        const updated = [...prev, botMsg];
        persistSession(sessionId, updated);
        return updated;
      });
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'system',
          content: 'Error: ' + (err.response?.data?.detail || 'Failed to get response'),
          timestamp: Date.now(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }, [input, isLoading, currentSessionId, persistSession]);

  // ── File upload ──────────────────────────────────────────────────────────────
  const handleFileUpload = useCallback(async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      await uploadDocument(file);
      setMessages((prev) => [
        ...prev,
        {
          role: 'system',
          content: `✅ Successfully uploaded "${file.name}". Processing in progress.`,
          timestamp: Date.now(),
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'system',
          content: `❌ Upload failed: ${err.response?.data?.detail || 'Unknown error'}`,
          timestamp: Date.now(),
        },
      ]);
    }

    e.target.value = '';
  }, []);

  // ── New chat ─────────────────────────────────────────────────────────────────
  const handleNewChat = useCallback(() => {
    setCurrentSessionId(null);
    setMessages([]);
  }, []);

  // ── Logout ───────────────────────────────────────────────────────────────────
  const handleLogout = useCallback(() => {
    Object.values(STORAGE_KEYS).forEach((k) => localStorage.removeItem(k));
    navigate('/login');
  }, [navigate]);

  // ── Effects ──────────────────────────────────────────────────────────────────
  useEffect(() => { refreshSessions(); }, [refreshSessions]);
  useEffect(() => { scrollToBottom(); }, [messages, scrollToBottom]);

  // Reset chat state whenever a new agent is selected to prevent "leakage"
  useEffect(() => {
    setCurrentSessionId(null);
    setMessages([]);
  }, [selectedAgent]);

  // Fetch SO re-routing alerts
  useEffect(() => {
    const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
    if (!token) return;
    fetch(`${API_URL}/api/alerts/pending-so`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((d) => setSoAlerts(d.alerts || []))
      .catch(console.error);
  }, []);

  // ── Render ───────────────────────────────────────────────────────────────────
  return (
    <div className="chat-page">
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.txt,.md,.csv,.doc,.docx,.json,.xlsx"
        onChange={handleFileUpload}
        style={{ display: 'none' }}
      />

      {/* Global Sidebar (Dashboard/Chat only) */}
      <Sidebar
        authData={authData}
        onLogout={handleLogout}
        onUploadClick={() => fileInputRef.current?.click()}
        collapsed={sidebarCollapsed}
        setCollapsed={setSidebarCollapsed}
        onSelectAgent={setSelectedAgent}
      />

      {/* Main Container */}
      <main className="chat-main" style={{ flexDirection: selectedAgent ? 'row' : 'column' }}>
        {!selectedAgent ? (
          /* Initial View: Agent Selection */
          <div className="explore-agents-wrapper">
            <WelcomeScreen onSelectAgent={setSelectedAgent} />
          </div>
        ) : (
          /* Chat View: Specific Agent active */
          <>
            {/* Inner Local Sidebar for Session History */}
            <aside className="chat-sub-sidebar">
              <div className="sub-sidebar__header">
                <StarBorder
                  color={selectedAgent?.color || '#008CCA'}
                  speed="6s"
                  thickness={2}
                  style={{ background: 'rgba(255, 255, 255, 0.05)', borderRadius: '12px', width: '100%' }}
                >
                  <div className="agent-identity" style={{ padding: '12px' }}>
                    <div className="agent-icon-v2" style={{ backgroundColor: 'rgba(255, 255, 255, 0.2)' }}>
                      {selectedAgent?.icon}
                    </div>
                    <div className="agent-info-v2">
                      <div className="agent-name-v2">{selectedAgent?.title}</div>
                      <div className="agent-status-v2">Online & Ready</div>
                    </div>
                  </div>
                </StarBorder>
              </div>

              {/* Spacer to push everything to the bottom */}
              <div style={{ flex: 1 }} />

              <div className="sidebar__new-btn-wrapper" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <button className="btn btn-full btn-light-solid" onClick={handleNewChat}>
                  <Plus size={16} /> New Session
                </button>
                {authData && authData.role === 'Admin' && (
                  <button className="btn btn-outline btn-full btn-light-outline" onClick={() => fileInputRef.current?.click()}>
                    <Upload size={14} /> Upload Data
                  </button>
                )}
              </div>

              <div className="sidebar__history sidebar__history--light">
                <div className="section-label section-label--light">Recent Sessions</div>
                {sessions.length === 0 ? (
                  <div className="sidebar__empty sidebar__empty--light">No session history yet</div>
                ) : (
                  sessions.map((session) => (
                    <div
                      key={session.session_id}
                      className={`session-item session-item--light ${session.session_id === currentSessionId ? ' session-item--active-light' : ''}`}
                      onClick={() => handleLoadSession(session.session_id)}
                    >
                      <div className="session-item__header">
                        <MessageSquare
                          size={14}
                          color={session.session_id === currentSessionId ? '#fff' : 'rgba(255,255,255,0.7)'}
                        />
                        <div className="session-item__title">{session.title || 'Untitled Session'}</div>
                      </div>
                      <div className="session-item__time">{getTimeLabel(session.updated_at)}</div>
                    </div>
                  ))
                )}
              </div>
            </aside>

            {/* Actual Chat Content */}
            <div className="chat-content-v2">
              <div className="chat-topbar">
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div className="agent-avatar-small" style={{ backgroundColor: selectedAgent.bgColor }}>{selectedAgent.icon}</div>
                  <div>
                    <div className="chat-topbar__title">
                      {currentSessionId ? 'Active Session' : 'New Session'}
                    </div>
                    <div className="chat-topbar__subtitle">
                      Powered by {selectedAgent.title}
                    </div>
                  </div>
                </div>
              </div>

              <div className="chat-messages">
                <div className="chat-messages__inner">
                  {messages.length === 0 && (
                    <div style={{ textAlign: 'center', paddingTop: '4rem', color: 'var(--color-muted)' }}>
                      <p style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Start a conversation with <strong>{selectedAgent.title}</strong></p>
                      <p>Type your query below to get intelligent insights on your supply chain.</p>
                    </div>
                  )}
                  {messages.map((msg, idx) => (
                    <MessageBubble key={idx} msg={msg} onPreview={setPreviewFile} />
                  ))}

                  {isLoading && (
                    <div className="message-row message-row--system">
                      <div className="msg-avatar msg-avatar--bot">
                        <Loader2 size={16} color="#fff" style={{ animation: 'spin 1s linear infinite' }} />
                      </div>
                      <div className="typing-bubble">
                        <div className="typing-dot" />
                        <div className="typing-dot" />
                        <div className="typing-dot" />
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              </div>

              <div className="chat-input-section">
                <ChatInput
                  value={input}
                  onChange={setInput}
                  onSend={handleSend}
                  disabled={isLoading}
                />
              </div>
            </div>
          </>
        )}
      </main>

      {/* SO Re-routing Alert Toggle Button */}
      {soAlerts.length > 0 && (
        <button
          className="so-alerts-panel__toggle"
          onClick={() => setShowSOPanel(!showSOPanel)}
          title="SO Re-routing Alerts"
          id="so-alerts-toggle"
        >
          <Bell size={24} />
          <span className="so-alerts-panel__toggle-count">{soAlerts.length}</span>
        </button>
      )}

      {/* SO Alerts Slide-in Panel */}
      {showSOPanel && (
        <div className="so-alerts-panel">
          <div className="so-alerts-panel__header">
            <div className="so-alerts-panel__title">
              <Bell size={18} />
              SO Re-routing Decisions
              <span className="so-alerts-panel__badge">{soAlerts.length} pending</span>
            </div>
            <button
              onClick={() => setShowSOPanel(false)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-muted)' }}
            >
              <X size={20} />
            </button>
          </div>
          <div className="so-alerts-panel__body">
            {soAlerts.map((alert) => (
              <SOReroutingCard
                key={alert.id}
                alert={alert}
                onActionComplete={(id, action) => {
                  console.log(`SO ${id} ${action}`);
                }}
              />
            ))}
          </div>
        </div>
      )}

      {/* Document Preview Modal */}
      {previewFile && (
        <PreviewModal
          filename={previewFile}
          onClose={() => setPreviewFile(null)}
        />
      )}

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        
        .chat-sub-sidebar {
          width: 280px;
          border-right: 1px solid rgba(255, 255, 255, 0.05);
          background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0F172A 100%),
                      radial-gradient(circle at top right, rgba(0, 140, 202, 0.15), transparent 60%),
                      radial-gradient(circle at bottom left, rgba(79, 70, 229, 0.15), transparent 60%);
          display: flex;
          flex-direction: column;
          flex-shrink: 0;
          color: white;
          box-shadow: inset -10px 0 20px -10px rgba(0,0,0,0.3);
        }

        .chat-content-v2 {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          background: var(--color-bg);
          position: relative;
        }

        .chat-messages {
          flex: 1;
          overflow-y: auto;
          padding: 32px 24px;
          background: transparent;
          z-index: 1;
        }

        .sub-sidebar__header {
          padding: 24px 16px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .back-btn-v2 {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 11px;
          font-weight: 700;
          color: white;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 20px;
          padding: 5px 12px;
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
          width: fit-content;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .back-btn-v2:hover {
          background: rgba(255, 255, 255, 0.1);
          border-color: rgba(255, 255, 255, 0.2);
          transform: translateX(-2px);
        }

        .agent-identity {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 8px 4px;
        }

        .agent-icon-v2 {
          width: 40px;
          height: 40px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 18px;
          color: white;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .agent-info-v2 {
          display: flex;
          flex-direction: column;
          gap: 1px;
        }

        .agent-name-v2 {
          font-size: 15px;
          font-weight: 600;
          color: #F8FAFC;
          letter-spacing: -0.01em;
        }

        .agent-status-v2 {
          font-size: 10px;
          color: #10B981;
          font-weight: 500;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .agent-status-v2::before {
          content: '';
          display: inline-block;
          width: 5px;
          height: 5px;
          background-color: #10B981;
          border-radius: 50%;
        }

        .btn-light-solid {
          background-color: #FFFFFF;
          color: #0F172A;
          font-weight: 600;
          border-radius: 8px;
          padding: 10px;
          font-size: 14px;
          box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }

        .btn-light-solid:hover {
          background-color: #F1F5F9;
          transform: translateY(-1px);
        }

        .btn-light-outline {
          background-color: transparent;
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: #CBD5E1;
          font-weight: 500;
          border-radius: 8px;
          padding: 8px;
          font-size: 13px;
        }

        .btn-light-outline:hover {
          background-color: rgba(255, 255, 255, 0.05);
          border-color: rgba(255, 255, 255, 0.2);
          color: #F8FAFC;
        }

        .sidebar__history--light .section-label--light {
          padding: 0 12px 12px;
          font-size: 11px;
          font-weight: 600;
          color: #64748B;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .sidebar__empty--light {
          padding: 20px 12px;
          font-size: 13px;
          color: #475569;
          text-align: left;
        }

        .session-item--light {
          padding: 10px 12px;
          margin-bottom: 2px;
          background: transparent;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.15s ease;
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .session-item--light:hover {
          background: rgba(255, 255, 255, 0.05);
        }

        .session-item--active-light {
          background: rgba(255, 255, 255, 0.1) !important;
        }

        .session-item--light .session-item__title {
          font-size: 13px;
          font-weight: 400;
          color: #E2E8F0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .session-item--active-light .session-item__title {
          color: #FFFFFF;
          font-weight: 500;
        }

        .session-item--light .session-item__time {
          display: none;
        }

        .agent-avatar-small {
          width: 32px;
          height: 32px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 16px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
      `}</style>
    </div>
  );
}

export default ChatPage;
