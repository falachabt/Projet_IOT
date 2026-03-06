import { Camera, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

export default function CameraFeed({
  status,
  bouteille_detectee,
  bouteille_confiance,
  bouchon_present,
  bouchon_confiance,
  etiquette_presente,
  etiquette_confiance,
  niveau_liquide,
  confiance,
  elapsed_ms,
  timestamp
}) {
  const getStatusIcon = () => {
    switch (status) {
      case 'OK':
        return <CheckCircle size={32} color="#10b981" />;
      case 'KO':
      case 'ERREUR':
        return <XCircle size={32} color="#ef4444" />;
      default:
        return <AlertCircle size={32} color="#8b92b0" />;
    }
  };

  const getStatusClass = () => {
    switch (status) {
      case 'OK':
        return 'status-ok';
      case 'KO':
      case 'ERREUR':
        return 'status-error';
      default:
        return 'status-warning';
    }
  };

  return (
    <div className="card camera-feed">
      <div className="camera-header">
        <Camera size={24} />
        <h3>Contrôle Caméra</h3>
      </div>

      <div className={`camera-status ${getStatusClass()}`}>
        {getStatusIcon()}
        <span className="status-text">{status || 'ATTENTE'}</span>
      </div>

      {bouteille_detectee !== undefined && (
        <div className="camera-details">
          <div className="detail-item">
            <span className="detail-label">🍾 Bouteille</span>
            <span className={`detail-value ${bouteille_detectee ? 'success' : 'error'}`}>
              {bouteille_detectee ? '✓ Détectée' : '✗ Non détectée'}
              {bouteille_confiance !== undefined && ` (${(bouteille_confiance * 100).toFixed(0)}%)`}
            </span>
          </div>

          <div className="detail-item">
            <span className="detail-label">🎩 Bouchon</span>
            <span className={`detail-value ${bouchon_present ? 'success' : 'error'}`}>
              {bouchon_present ? '✓ Présent' : '✗ Absent'}
              {bouchon_confiance !== undefined && ` (${(bouchon_confiance * 100).toFixed(0)}%)`}
            </span>
          </div>

          {etiquette_presente !== undefined && (
            <div className="detail-item">
              <span className="detail-label">🏷️ Étiquette</span>
              <span className={`detail-value ${etiquette_presente ? 'success' : 'error'}`}>
                {etiquette_presente ? '✓ Présente' : '✗ Absente'}
                {etiquette_confiance !== undefined && ` (${(etiquette_confiance * 100).toFixed(0)}%)`}
              </span>
            </div>
          )}

          {niveau_liquide !== null && niveau_liquide !== undefined && (
            <div className="detail-item">
              <span className="detail-label">💧 Niveau</span>
              <span className="detail-value">{niveau_liquide?.toFixed(1)}%</span>
            </div>
          )}

          {elapsed_ms !== undefined && (
            <div className="detail-item">
              <span className="detail-label">⏱️ Temps d'analyse</span>
              <span className="detail-value">{elapsed_ms?.toFixed(1)} ms</span>
            </div>
          )}

          {confiance !== null && confiance !== undefined && !bouteille_confiance && (
            <div className="detail-item">
              <span className="detail-label">Confiance globale</span>
              <span className="detail-value">{(confiance * 100).toFixed(0)}%</span>
            </div>
          )}
        </div>
      )}

      <style jsx>{`
        .camera-feed {
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
        }

        .camera-header {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .camera-header h3 {
          margin: 0;
          font-size: 1.1rem;
          font-weight: 700;
          color: var(--text-primary);
        }

        .camera-status {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 1rem;
          padding: 2rem;
          border-radius: var(--radius-md);
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.08);
          transition: all var(--transition-base);
        }

        .camera-status.status-ok {
          background: rgba(16, 185, 129, 0.12);
          border: 2px solid rgba(16, 185, 129, 0.4);
          box-shadow: var(--shadow-md), var(--glow-success);
        }

        .camera-status.status-error {
          background: rgba(239, 68, 68, 0.12);
          border: 2px solid rgba(239, 68, 68, 0.4);
          box-shadow: var(--shadow-md), var(--glow-danger);
        }

        .camera-status.status-warning {
          background: rgba(245, 158, 11, 0.12);
          border: 2px solid rgba(245, 158, 11, 0.4);
          box-shadow: var(--shadow-md), 0 0 20px rgba(245, 158, 11, 0.3);
        }

        .status-text {
          font-size: 1.75rem;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: 1px;
        }

        .camera-details {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .detail-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.75rem 1rem;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: var(--radius-sm);
          transition: all var(--transition-base);
        }

        .detail-item:hover {
          background: rgba(255, 255, 255, 0.06);
          transform: translateX(4px);
          border-color: var(--border-color);
        }

        .detail-label {
          font-size: 0.9rem;
          color: var(--text-secondary);
          font-weight: 500;
        }

        .detail-value {
          font-weight: 700;
          font-size: 0.9rem;
        }

        .detail-value.success {
          color: var(--success-light);
          text-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
        }

        .detail-value.error {
          color: var(--danger-light);
          text-shadow: 0 0 8px rgba(239, 68, 68, 0.4);
        }
      `}</style>
    </div>
  );
}
