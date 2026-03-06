import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';

export default function SensorCard({ title, icon, value, status, timestamp, extra }) {
  const statusClass = status === 'ok' ? 'status-ok' :
                     status === 'warning' ? 'status-warning' :
                     status === 'error' ? 'status-error' : '';

  return (
    <div className="card sensor-card">
      <div className="sensor-header">
        <div className="sensor-icon">{icon}</div>
        <div>
          <h3>{title}</h3>
          {timestamp && (
            <p className="timestamp">
              {formatDistanceToNow(new Date(timestamp), { addSuffix: true, locale: fr })}
            </p>
          )}
        </div>
      </div>

      <div className="sensor-value">
        {statusClass && <span className={`status-indicator ${statusClass}`}></span>}
        <span className="value">{value}</span>
      </div>

      {extra && (
        <div className="sensor-extra">
          {typeof extra === 'string' ? <p>{extra}</p> : extra}
        </div>
      )}

      <style jsx>{`
        .sensor-card {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
          animation: scaleIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
        }

        @keyframes scaleIn {
          from {
            opacity: 0;
            transform: scale(0.9);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }

        .sensor-header {
          display: flex;
          align-items: center;
          gap: 1.25rem;
        }

        .sensor-icon {
          width: 56px;
          height: 56px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #6366f1, #8b5cf6);
          border-radius: 16px;
          color: white;
          box-shadow:
            0 8px 24px rgba(99, 102, 241, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
          transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        }

        .sensor-card:hover .sensor-icon {
          transform: scale(1.1) rotate(5deg);
          box-shadow:
            0 12px 32px rgba(99, 102, 241, 0.6),
            inset 0 1px 0 rgba(255, 255, 255, 0.3);
        }

        .sensor-card h3 {
          font-size: 1.1rem;
          font-weight: 800;
          margin: 0;
          background: linear-gradient(135deg, #f1f5f9, #cbd5e1);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .timestamp {
          font-size: 0.75rem;
          color: var(--text-tertiary);
          margin: 0.35rem 0 0 0;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .sensor-value {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 1.25rem;
          background: rgba(99, 102, 241, 0.05);
          border-radius: 16px;
          border: 1px solid rgba(99, 102, 241, 0.15);
          transition: all 0.3s ease;
        }

        .sensor-card:hover .sensor-value {
          background: rgba(99, 102, 241, 0.1);
          border-color: rgba(99, 102, 241, 0.3);
          transform: translateX(4px);
        }

        .value {
          font-size: 2.25rem;
          font-weight: 900;
          background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          filter: drop-shadow(0 2px 8px rgba(255, 255, 255, 0.1));
        }

        .sensor-extra {
          padding-top: 1rem;
          border-top: 1px solid rgba(99, 102, 241, 0.2);
          font-size: 0.9rem;
          color: var(--text-secondary);
        }
      `}</style>
    </div>
  );
}
