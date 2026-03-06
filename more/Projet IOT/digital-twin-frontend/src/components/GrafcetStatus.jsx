import { Cpu, CheckCircle, AlertCircle, PlayCircle } from 'lucide-react';

export default function GrafcetStatus({ systemState }) {
  const getEtatLabel = (etat) => {
    const labels = {
      'E0_INIT': 'Initialisation',
      'E1_MARCHE_CONV': 'Convoyeur en marche',
      'E2_DETECTION_OBJET': 'Objet détecté',
      'E3_CONTROL_CAMERA': 'Analyse caméra',
      'E6_LED_ROUGE_CAMERA': 'Défaut visuel',
      'E8_LED_VERT_CONV2': 'Produit conforme',
      'E9_STOP_CONV': 'Arrêt convoyeur',
      'E11_STOP_CONV2': 'Évacuation terminée'
    };
    return labels[etat] || etat;
  };

  const getEtatColor = (etat) => {
    if (etat?.includes('INIT')) return '#64748b';
    if (etat?.includes('MARCHE') || etat?.includes('VERT')) return '#10b981';
    if (etat?.includes('ROUGE') || etat?.includes('DEFAUT')) return '#ef4444';
    if (etat?.includes('CONTROL') || etat?.includes('CAMERA')) return '#f59e0b';
    return '#8b92b0';
  };

  return (
    <div className="card grafcet-status">
      <div className="grafcet-header">
        <Cpu size={24} />
        <h3>État du Système</h3>
      </div>

      <div className="grafcet-main" style={{
        borderLeft: `4px solid ${getEtatColor(systemState?.etat_grafcet)}`
      }}>
        <div className="etat-current">
          <PlayCircle size={20} color={getEtatColor(systemState?.etat_grafcet)} />
          <span className="etat-name">{getEtatLabel(systemState?.etat_grafcet)}</span>
        </div>
        <div className="etat-code">{systemState?.etat_grafcet || 'N/A'}</div>
      </div>

      <div className="grafcet-details">
        <div className="detail-row">
          <span className="detail-label">Moteur 1</span>
          <span className={`detail-badge ${systemState?.moteur1_actif ? 'active' : ''}`}>
            {systemState?.moteur1_actif ? '▶ ACTIF' : '■ ARRÊTÉ'}
          </span>
        </div>

        <div className="detail-row">
          <span className="detail-label">Moteur 2</span>
          <span className={`detail-badge ${systemState?.moteur2_actif ? 'active' : ''}`}>
            {systemState?.moteur2_actif ? '▶ ACTIF' : '■ ARRÊTÉ'}
          </span>
        </div>

        <div className="detail-row">
          <span className="detail-label">Objet détecté</span>
          <span className={`detail-badge ${systemState?.objet_detecte ? 'detected' : ''}`}>
            {systemState?.objet_detecte ? '🔴 OUI' : '🟢 NON'}
          </span>
        </div>
      </div>

      <style jsx>{`
        .grafcet-status {
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
        }

        .grafcet-header {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .grafcet-header h3 {
          margin: 0;
          font-size: 1.1rem;
          font-weight: 700;
          color: var(--text-primary);
        }

        .grafcet-main {
          background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%);
          padding: 1.5rem;
          border-radius: var(--radius-md);
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          border: 1px solid var(--border-color);
          box-shadow: var(--shadow-sm);
          transition: all var(--transition-base);
        }

        .grafcet-main:hover {
          background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%);
          box-shadow: var(--shadow-md), var(--glow-primary);
        }

        .etat-current {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          font-size: 1.15rem;
          font-weight: 700;
          color: var(--text-primary);
        }

        .etat-code {
          font-size: 0.875rem;
          color: var(--text-secondary);
          font-family: 'Fira Code', 'Courier New', monospace;
          margin-left: 2rem;
          background: rgba(99, 102, 241, 0.1);
          padding: 0.25rem 0.75rem;
          border-radius: var(--radius-sm);
        }

        .grafcet-details {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .detail-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.75rem 1rem;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: var(--radius-sm);
          transition: all var(--transition-base);
        }

        .detail-row:hover {
          background: rgba(255, 255, 255, 0.06);
          transform: translateX(4px);
          border-color: var(--border-color);
        }

        .detail-label {
          font-size: 0.9rem;
          color: var(--text-secondary);
          font-weight: 500;
        }

        .detail-badge {
          font-size: 0.85rem;
          font-weight: 700;
          padding: 0.375rem 0.875rem;
          border-radius: var(--radius-sm);
          background: rgba(100, 116, 139, 0.25);
          color: var(--text-tertiary);
          border: 1px solid rgba(100, 116, 139, 0.3);
          transition: all var(--transition-base);
        }

        .detail-badge.active {
          background: rgba(16, 185, 129, 0.15);
          color: var(--success-light);
          border: 1px solid rgba(16, 185, 129, 0.5);
          box-shadow: var(--glow-success);
        }

        .detail-badge.detected {
          background: rgba(239, 68, 68, 0.15);
          color: var(--danger-light);
          border: 1px solid rgba(239, 68, 68, 0.5);
          box-shadow: var(--glow-danger);
        }
      `}</style>
    </div>
  );
}
