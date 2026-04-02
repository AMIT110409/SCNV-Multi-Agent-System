import React, { useState, useEffect } from 'react';
import { X, FileText, Download, Loader2, AlertCircle } from 'lucide-react';
import { API_URL } from '../config/constants';

function PreviewModal({ filename, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!filename) return;
    setLoading(true);
    setError(null);

    fetch(`${API_URL}/api/documents/preview/${filename}`)
      .then(res => res.json())
      .then(d => {
        if (d.type === 'error') {
          setError(d.message);
        } else {
          setData(d);
        }
        setLoading(false);
      })
      .catch(err => {
        setError("Failed to connect to preview service.");
        setLoading(false);
      });
  }, [filename]);

  if (!filename) return null;

  return (
    <div className="preview-modal-overlay" onClick={onClose}>
      <div className="preview-modal-content" onClick={e => e.stopPropagation()}>
        <header className="preview-modal-header">
          <div className="preview-title">
            <FileText size={18} />
            <span>Document Preview: {filename}</span>
          </div>
          <div className="preview-actions">
            <button className="preview-close-btn" onClick={onClose}>
              <X size={20} />
            </button>
          </div>
        </header>

        <div className="preview-modal-body">
          {loading ? (
            <div className="preview-placeholder">
              <Loader2 className="spin" size={32} />
              <p>Fetching document snapshot...</p>
            </div>
          ) : error ? (
            <div className="preview-placeholder preview-error">
              <AlertCircle size={32} />
              <p>{error}</p>
            </div>
          ) : data?.type === 'table' ? (
            <div className="preview-table-wrapper">
              <table className="preview-table">
                <thead>
                  <tr>
                    {data.columns.map((col, i) => <th key={i}>{col}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {data.rows.map((row, i) => (
                    <tr key={i}>
                      {data.columns.map((col, j) => <td key={j}>{row[col]}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="preview-footer-note">Showing first 20 rows of the document.</div>
            </div>
          ) : (
            <div className="preview-text-content">
              <pre>{data?.content || "No preview available for this file type."}</pre>
            </div>
          )}
        </div>
      </div>

      <style>{`
        .preview-modal-overlay {
          position: fixed;
          top: 0; left: 0; right: 0; bottom: 0;
          background: rgba(0,0,0,0.7);
          backdrop-filter: blur(4px);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 10000;
          padding: 2rem;
        }
        .preview-modal-content {
          background: white;
          width: 100%;
          max-width: 1000px;
          max-height: 85vh;
          border-radius: 1rem;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        }
        .preview-modal-header {
          padding: 1.25rem 1.5rem;
          border-bottom: 1px solid var(--color-border);
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: #f8fafc;
        }
        .preview-title {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          font-weight: 600;
          color: var(--color-primary);
        }
        .preview-modal-body {
          flex: 1;
          overflow: auto;
          padding: 1.5rem;
          background: #fff;
        }
        .preview-placeholder {
          height: 300px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 1rem;
          color: var(--color-muted);
        }
        .preview-error { color: #ef4444; }
        
        .preview-table-wrapper {
          overflow-x: auto;
        }
        .preview-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.875rem;
        }
        .preview-table th {
          background: #f1f5f9;
          text-align: left;
          padding: 0.75rem;
          border: 1px solid #e2e8f0;
          position: sticky; top: 0;
        }
        .preview-table td {
          padding: 0.75rem;
          border: 1px solid #e2e8f0;
        }
        .preview-footer-note {
          margin-top: 1rem;
          font-size: 0.75rem;
          color: var(--color-muted);
          font-style: italic;
        }
        .preview-text-content pre {
          white-space: pre-wrap;
          font-family: inherit;
          line-height: 1.6;
          color: #334155;
        }
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .preview-close-btn {
          border: none; background: transparent; cursor: pointer; color: var(--color-muted);
          padding: 4px; border-radius: 4px; transition: background 0.2s;
        }
        .preview-close-btn:hover { background: #e2e8f0; color: #000; }
      `}</style>
    </div>
  );
}

export default PreviewModal;
