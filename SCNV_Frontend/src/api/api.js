import axios from 'axios';
import { API_URL, STORAGE_KEYS } from '../config/constants';
import { supabase } from '../config/supabase';

function getAuthHeaders() {
  const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Register a new user using Supabase Auth.
 * @param {{ email: string, password: string, role: string }} payload
 */
export async function register({ email, password, role }) {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: { role } // Store custom role in Supabase user_metadata
    }
  });
  if (error) throw error;
  return data;
}

/**
 * Login an existing user using Supabase Auth.
 * @param {{ email: string, password: string }} payload
 * @returns {{ access_token: string, role: string }}
 */
export async function login({ email, password }) {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });
  if (error) throw error;
  return {
    access_token: data.session.access_token,
    role: data.user.user_metadata?.role || 'User'
  };
}

export async function fetchSessions(agentId = null) {
  const url = agentId ? `${API_URL}/api/history/sessions?agent_id=${agentId}` : `${API_URL}/api/history/sessions`;
  const res = await axios.get(url, {
    headers: getAuthHeaders(),
  });
  // Backend returns { sessions: [...] }
  // Normalize: map 'id' -> 'session_id' and 'timestamp' -> 'updated_at'
  const sessions = res.data.sessions || [];
  return sessions.map((s) => ({
    ...s,
    session_id: s.id,
    updated_at: s.timestamp,
  }));
}

/**
 * Load a specific session by ID.
 * @param {string} sessionId
 */
export async function loadSession(sessionId) {
  const res = await axios.get(`${API_URL}/api/history/sessions/${sessionId}`, {
    headers: getAuthHeaders(),
  });
  const data = res.data;
  // Normalize if single session object also uses 'id' instead of 'session_id'
  return {
    ...data,
    session_id: data.id || sessionId,
    updated_at: data.timestamp || data.updated_at,
  };
}

/**
 * Save the current session to the server.
 * @param {{ sessionId: string, messages: Array }} payload
 */
export async function saveSession({ sessionId, messages, agentId }) {
  await axios.post(
    `${API_URL}/api/history/sessions/new`,
    { 
      session_id: sessionId, 
      messages, 
      title: messages[0]?.content?.substring(0, 30) || 'New Chat',
      agent_id: agentId 
    },
    { headers: getAuthHeaders() },
  );
}

/**
 * Send a chat message and receive a response.
 * @param {string} query
 * @returns {{ answer: string, sources: Array }}
 */
export async function sendMessage(message, sessionId, agentId) {
  const res = await axios.post(`${API_URL}/api/chat/`, { 
    message, 
    session_id: sessionId,
    agent_id: agentId 
  }, {
    headers: getAuthHeaders(),
  });
  return res.data;
}

/**
 * Upload a document file.
 * @param {File} file
 */
export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await axios.post(`${API_URL}/api/documents/upload`, formData, {
    headers: {
      ...getAuthHeaders(),
      'Content-Type': 'multipart/form-data',
    },
  });
  return res.data;
}
