import { useState } from 'react';
import { Play, Square, Gauge } from 'lucide-react';

export default function MotorControl({ etat, vitesse, timestamp, onControl, disabled }) {
  const [localVitesse, setLocalVitesse] = useState(vitesse || 80);
  const isRunning = etat === 'ON';

  const handleStart = () => {
    if (!disabled) {
      onControl('START', localVitesse);
    }
  };

  const handleStop = () => {
    if (!disabled) {
      onControl('STOP');
    }
  };

  return (
    <div className="card motor-control">
      <div className="motor-header">
        <Gauge size={24} />
        <h3>Moteurs Convoyeur</h3>
      </div>

      <div className="motor-status">
        <span className={`status-indicator ${isRunning ? 'status-ok' : 'status-warning'}`}></span>
        <span className="status-text">{etat || 'OFF'}</span>
      </div>

      <div className="speed-control">
        <label>Vitesse: {localVitesse}%</label>
        <input
          type="range"
          min="0"
          max="100"
          value={localVitesse}
          onChange={(e) => setLocalVitesse(parseInt(e.target.value))}
          disabled={disabled || isRunning}
          className="speed-slider"
        />
      </div>

      <div className="motor-buttons">
        <button
          className="btn btn-success"
          onClick={handleStart}
          disabled={disabled || isRunning}
        >
          <Play size={16} />
          Démarrer
        </button>
        <button
          className="btn btn-danger"
          onClick={handleStop}
          disabled={disabled || !isRunning}
        >
          <Square size={16} />
          Arrêter
        </button>
      </div>

      {disabled && (
        <p className="warning-text">⚠️ Arrêt d'urgence actif</p>
      )}

      <style jsx>{`
        .motor-control {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .motor-header {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .motor-header h3 {
          margin: 0;
          font-size: 1rem;
          font-weight: 600;
        }

        .motor-status {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 1.5rem;
          font-weight: 700;
        }

        .speed-control {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .speed-control label {
          font-size: 0.875rem;
          font-weight: 600;
          color: var(--text-secondary);
        }

        .speed-slider {
          width: 100%;
          height: 6px;
          border-radius: 3px;
          background: var(--border-color);
          outline: none;
          -webkit-appearance: none;
        }

        .speed-slider::-webkit-slider-thumb {
          -webkit-appearance: none;
          width: 18px;
          height: 18px;
          border-radius: 50%;
          background: var(--accent-primary);
          cursor: pointer;
        }

        .motor-buttons {
          display: flex;
          gap: 0.75rem;
        }

        .motor-buttons button {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
        }

        .warning-text {
          color: var(--warning);
          font-size: 0.875rem;
          text-align: center;
          margin: 0;
        }
      `}</style>
    </div>
  );
}
