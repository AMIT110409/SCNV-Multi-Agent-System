import React from 'react';
import { Send } from 'lucide-react';

/**
 * Chat input bar: textarea + send button.
 *
 * @param {{
 *   value: string,
 *   onChange: (val: string) => void,
 *   onSend: () => void,
 *   disabled: boolean
 * }} props
 */
function ChatInput({ value, onChange, onSend, disabled }) {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  const canSend = !disabled && value.trim().length > 0;

  return (
    <div className="chat-input-bar">
      <div className="chat-input-bar__inner">
        <div className="chat-input-wrapper">
          <textarea
            className="chat-textarea"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder="Ask about supply chain routes, classifications, optimization strategies, or process analytics..."
            rows={1}
            onInput={(e) => {
              e.target.style.height = 'auto';
              e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
            }}
          />

          <button
            className={`chat-send-btn ${canSend ? 'chat-send-btn--active' : 'chat-send-btn--inactive'}`}
            onClick={onSend}
            disabled={!canSend}
            aria-label="Send message"
          >
            <Send size={16} color={canSend ? '#fff' : 'var(--color-muted)'} />
          </button>
        </div>

        <p className="chat-input-hint">
          AI-powered multi-agent system · Verify critical supply chain decisions · Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}

export default ChatInput;
