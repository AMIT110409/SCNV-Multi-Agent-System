export function renderMarkdown(text) {
  if (!text) return '';
  let html = text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/^#### (.+)$/gm, '<h4>$1</h4>').replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>').replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/^[-*] (.+)$/gm, '<li>$1</li>')
    .replace(/^\d+\. (.+)$/gm, '<li class="ordered">$1</li>');

  html = html.replace(/(<li(?! class)[\s\S]*?<\/li>\n?)+/g, (m) =>
    m.includes('class="ordered"')
      ? '<ol>' + m.replace(/ class="ordered"/g, '') + '</ol>'
      : '<ul>' + m + '</ul>',
  );

  html = html
    .split(/\n{2,}/)
    .map((b) => {
      const t = b.trim();
      if (!t) return '';
      if (/^<(h[1-4]|ul|ol)/.test(t)) return t;
      return '<p>' + t.replace(/\n/g, '<br/>') + '</p>';
    })
    .join('');

  return html;
}

export function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
}

/**
 * Return a human-readable relative time label for a timestamp.
 * @param {number|string} ts - Unix timestamp in ms or ISO string.
 */
export function getTimeLabel(ts) {
  if (!ts) return '';
  const d = new Date(ts);
  const diff = Date.now() - d.getTime();
  if (diff < 60_000) return 'Just now';
  if (diff < 3_600_000) return Math.floor(diff / 60_000) + 'm ago';
  if (diff < 86_400_000) return Math.floor(diff / 3_600_000) + 'h ago';
  if (diff < 604_800_000) return Math.floor(diff / 86_400_000) + 'd ago';
  return d.toLocaleDateString();
}
