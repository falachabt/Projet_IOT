import SensorCard from './SensorCard';
import MotorControl from './MotorControl';
import LEDIndicator from './LEDIndicator';
import CameraFeed from './CameraFeed';
import HistoryChart from './HistoryChart';
import ButtonControl from './ButtonControl';
import GrafcetStatus from './GrafcetStatus';
import { Activity, Camera, Gauge, Cpu, AlertTriangle, TrendingUp } from 'lucide-react';

export default function Dashboard({ systemState, controlMotor, controlLED, controlButton }) {
  if (!systemState) {
    return (
      <div className="dashboard loading">
        <div className="spinner"></div>
        <p>Chargement des données...</p>
      </div>
    );
  }

  const {
    ultrason,
    moteur,
    leds,
    urgence,
    boutons,
    camera,
    statistics
  } = systemState;

  return (
    <div className="dashboard">
      {/* Alerte Urgence */}
      {urgence?.active && (
        <div className="alert alert-danger">
          <AlertTriangle size={24} />
          <strong>ARRÊT D'URGENCE ACTIVÉ</strong>
        </div>
      )}

      {/* Statistiques en haut */}
      <div className="stats-bar">
        <div className="stat-item">
          <Activity className="stat-icon" size={20} />
          <div>
            <p className="stat-label">Total Analyses</p>
            <p className="stat-value">{statistics?.total_analyses || 0}</p>
          </div>
        </div>

        <div className="stat-item success">
          <TrendingUp className="stat-icon" size={20} />
          <div>
            <p className="stat-label">Taux OK</p>
            <p className="stat-value">{statistics?.taux_ok_pourcent || 0}%</p>
          </div>
        </div>

        <div className="stat-item">
          <span className="stat-icon">✓</span>
          <div>
            <p className="stat-label">OK</p>
            <p className="stat-value">{statistics?.analyses_ok || 0}</p>
          </div>
        </div>

        <div className="stat-item">
          <span className="stat-icon">✗</span>
          <div>
            <p className="stat-label">KO</p>
            <p className="stat-value">{statistics?.analyses_ko || 0}</p>
          </div>
        </div>
      </div>

      {/* Grille principale */}
      <div className="dashboard-grid">
        {/* Ligne 1 : Détection, Grafcet, Caméra */}
        <div className="grid-row-3">
          {/* Détection d'Objet (Capteur IR) */}
          <SensorCard
            title="Détection d'Objet"
            icon={<Activity size={24} />}
            value={ultrason?.flacon_detecte || ultrason?.objet_detecte ? 'OBJET DÉTECTÉ' : 'ZONE LIBRE'}
            status={ultrason?.flacon_detecte || ultrason?.objet_detecte ? 'ok' : 'normal'}
            timestamp={ultrason?.timestamp}
            extra={
              <div style={{
                fontSize: '3rem',
                textAlign: 'center',
                margin: '1rem 0'
              }}>
                {ultrason?.flacon_detecte || ultrason?.objet_detecte ? '🔴' : '🟢'}
              </div>
            }
          />

          {/* État du Système Grafcet */}
          <GrafcetStatus systemState={systemState} />

          {/* Caméra / Résultat */}
          <CameraFeed
            status={camera?.status}
            bouteille_detectee={camera?.bouteille_detectee}
            bouteille_confiance={camera?.bouteille_confiance}
            bouchon_present={camera?.bouchon_present}
            bouchon_confiance={camera?.bouchon_confiance}
            etiquette_presente={camera?.etiquette_presente}
            etiquette_confiance={camera?.etiquette_confiance}
            niveau_liquide={camera?.niveau_liquide}
            confiance={camera?.confiance}
            elapsed_ms={camera?.elapsed_ms}
            timestamp={camera?.timestamp}
          />
        </div>

        {/* Ligne 2 : Boutons, LEDs, Moteur */}
        <div className="grid-row-3">
          {/* Boutons Virtuels */}
          <ButtonControl
            boutons={boutons}
            onControl={controlButton}
            disabled={false}
          />

          {/* LEDs */}
          <LEDIndicator
            leds={leds}
            onControl={controlLED}
            disabled={urgence?.active}
          />

          {/* Moteurs */}
          <MotorControl
            etat={moteur?.etat}
            vitesse={moteur?.vitesse}
            timestamp={moteur?.timestamp}
            onControl={controlMotor}
            disabled={urgence?.active}
          />
        </div>

        {/* Ligne 3 : Historique pleine largeur */}
        <div className="grid-row-full">
          <div className="card chart-card">
            <h3>📊 Historique des Détections (dernière heure)</h3>
            <HistoryChart measurement="ultrason" />
          </div>
        </div>
      </div>

      <style jsx>{`
        .dashboard-grid {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
          animation: fadeIn 0.6s ease;
        }

        .grid-row-3 {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 1.5rem;
        }

        .grid-row-full {
          width: 100%;
        }

        .chart-card h3 {
          margin: 0 0 1.25rem 0;
          font-size: 1.2rem;
          font-weight: 700;
          background: linear-gradient(135deg, var(--text-primary), var(--accent-primary));
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .alert {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 1.25rem;
          border-radius: var(--radius-lg);
          margin-bottom: 1.5rem;
          animation: slideIn 0.5s ease;
          backdrop-filter: var(--blur-md);
        }

        .alert-danger {
          background: rgba(239, 68, 68, 0.15);
          border: 2px solid var(--danger);
          color: var(--danger-light);
          box-shadow: var(--shadow-lg), var(--glow-danger);
        }

        @media (max-width: 1200px) {
          .grid-row-3 {
            grid-template-columns: repeat(2, 1fr);
          }
        }

        @media (max-width: 768px) {
          .grid-row-3 {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}
