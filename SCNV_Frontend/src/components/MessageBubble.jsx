import React from 'react';
import { Bot, User, FileText } from 'lucide-react';
import { renderMarkdown } from '../utils/helpers';

/**
 * Renders a single chat message bubble (user / assistant / system).
 * @param {{ msg: { role: string, content: string, sources?: Array }, onPreview?: (filename: string) => void }} props
 */
function MessageBubble({ msg, onPreview }) {
  const isUser      = msg.role === 'user';
  const isAssistant = msg.role === 'assistant';
  const isSystem    = msg.role === 'system';

  return (
    <div className={`message-row message-row--${isUser ? 'user' : 'system'}`}>
      {/* Bot/System Avatar */}
      {!isUser && (
        <div className={`msg-avatar msg-avatar--${isSystem ? 'system' : 'bot'}`}>
          {isSystem
            ? <FileText size={16} color="var(--color-muted)" />
            : <Bot size={16} color="#fff" />}
        </div>
      )}

      {/* Bubble */}
      <div className={`msg-bubble msg-bubble--${isUser ? 'user' : isAssistant ? 'assistant' : 'system'}`}>
        {isAssistant ? (
          <div
            className="md-body"
            dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}
          />
        ) : (
          <p className={`msg-text msg-text--${isUser ? 'user' : 'system'}`}>
            {msg.content}
          </p>
        )}

        {/* Sources / Citations */}
        {msg.sources?.length > 0 && (
          <div className="sources-section">
            <div className="sources-label">Data Sources</div>
            <div className="sources-chips">
              {msg.sources.map((s, i) => (
                <button
                  key={i}
                  className="source-chip"
                  title={s.text_snippet}
                  onClick={() => onPreview && onPreview(s.source)}
                  style={{ cursor: onPreview ? 'pointer' : 'default', border: 'none', background: 'var(--color-bg-light)' }}
                >
                  <FileText size={12} />
                  <span>{s.source} · p.{s.page || '1'}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="msg-avatar msg-avatar--user">
          <User size={16} color="var(--color-primary)" />
        </div>
      )}
    </div>
  );
}

export default MessageBubble;
