import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';
import { Terminal } from 'lucide-react';

export default function LogViewer({ logs }) {
  const getLogIcon = (type) => {
    switch (type) {
      case 'success':
        return '✓';
      case 'error':
        return '✗';
      case 'warning':
        return '⚠';
      default:
        return '●';
    }
  };

  const getLogClass = (type) => {
    switch (type) {
      case 'success':
        return 'log-success';
      case 'error':
        return 'log-error';
      case 'warning':
        return 'log-warning';
      default:
        return 'log-info';
    }
  };

  return (
    <div className="log-viewer">
      <div className="log-header">
        <Terminal size={20} />
        <h3>Logs Système</h3>
      </div>

      <div className="log-list">
        {logs.length === 0 ? (
          <div className="log-empty">Aucun log pour le moment</div>
        ) : (
          logs.map((log) => (
            <div key={log.id} className={`log-item ${getLogClass(log.type)}`}>
              <span className="log-icon">{getLogIcon(log.type)}</span>
              <div className="log-content">
                <p className="log-message">{log.message}</p>
                <span className="log-time">
                  {formatDistanceToNow(log.timestamp, { addSuffix: true, locale: fr })}
                </span>
              </div>
            </div>
          ))
        )}
      </div>

      <style jsx>{`
        .log-viewer {
          padding: 1.5rem;
          height: 100%;
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .log-header {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding-bottom: 0.75rem;
          border-bottom: 1px solid var(--border-color);
        }

        .log-header h3 {
          margin: 0;
          font-size: 1rem;
          font-weight: 600;
        }

        .log-list {
          flex: 1;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .log-empty {
          text-align: center;
          color: var(--text-secondary);
          padding: 2rem 0;
        }

        .log-item {
          display: flex;
          gap: 0.75rem;
          padding: 0.75rem;
          background: rgba(255, 255, 255, 0.05);
          border-radius: 8px;
          border-left: 3px solid;
          transition: all 0.2s ease;
        }

        .log-item:hover {
          background: rgba(255, 255, 255, 0.08);
        }

        .log-info { border-color: #3b82f6; }
        .log-success { border-color: #10b981; }
        .log-warning { border-color: #f59e0b; }
        .log-error { border-color: #ef4444; }

        .log-icon {
          font-size: 1.25rem;
          flex-shrink: 0;
        }

        .log-content {
          flex: 1;
          min-width: 0;
        }

        .log-message {
          margin: 0 0 0.25rem 0;
          font-size: 0.875rem;
          color: var(--text-primary);
          word-wrap: break-word;
        }

        .log-time {
          font-size: 0.75rem;
          color: var(--text-secondary);
        }
      `}</style>
    </div>
  );
}
