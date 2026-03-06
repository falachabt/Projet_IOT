import { useState } from 'react';
import { Power, AlertOctagon } from 'lucide-react';
import '../styles/ButtonControl.css';

export default function ButtonControl({ boutons, onControl, disabled }) {
  const [pressing, setPressing] = useState({ marche: false, urgence: false });

  const handleButtonPress = async (button, etat) => {
    setPressing(prev => ({ ...prev, [button]: etat }));

    try {
      await onControl(button, etat);
    } catch (error) {
      console.error(`Erreur envoi bouton ${button}:`, error);
    }
  };

  const isMarcheActive = boutons?.bouton_marche || pressing.marche;
  const isUrgenceActive = boutons?.bouton_urgence || pressing.urgence;

  return (
    <div className="card button-control-card">
      <h3>🎮 Contrôle Virtuel</h3>

      <div className="virtual-buttons">
        {/* Bouton MARCHE */}
        <div className="button-wrapper">
          <button
            className={`virtual-button button-marche ${isMarcheActive ? 'active' : ''}`}
            onMouseDown={() => handleButtonPress('marche', true)}
            onMouseUp={() => handleButtonPress('marche', false)}
            onMouseLeave={() => pressing.marche && handleButtonPress('marche', false)}
            onTouchStart={() => handleButtonPress('marche', true)}
            onTouchEnd={() => handleButtonPress('marche', false)}
            disabled={disabled}
            title="Appuyer pour démarrer le système"
          >
            <Power size={32} />
            <span className="button-label">MARCHE</span>
            {isMarcheActive && <div className="button-glow green"></div>}
          </button>
          <div className="button-status">
            {isMarcheActive ? (
              <span className="status-badge active">🟢 Actif</span>
            ) : (
              <span className="status-badge">⚪ Inactif</span>
            )}
          </div>
        </div>

        {/* Bouton URGENCE */}
        <div className="button-wrapper">
          <button
            className={`virtual-button button-urgence ${isUrgenceActive ? 'active' : ''}`}
            onMouseDown={() => handleButtonPress('urgence', true)}
            onMouseUp={() => handleButtonPress('urgence', false)}
            onMouseLeave={() => pressing.urgence && handleButtonPress('urgence', false)}
            onTouchStart={() => handleButtonPress('urgence', true)}
            onTouchEnd={() => handleButtonPress('urgence', false)}
            disabled={disabled}
            title="Arrêt d'urgence"
          >
            <AlertOctagon size={32} />
            <span className="button-label">URGENCE</span>
            {isUrgenceActive && <div className="button-glow red"></div>}
          </button>
          <div className="button-status">
            {isUrgenceActive ? (
              <span className="status-badge danger">🔴 ACTIVÉ</span>
            ) : (
              <span className="status-badge">⚪ Inactif</span>
            )}
          </div>
        </div>
      </div>

      {disabled && (
        <div className="disabled-overlay">
          <span>⚠️ Contrôles désactivés</span>
        </div>
      )}

      <div className="button-info">
        <p>💡 Maintenez le bouton appuyé comme sur un vrai panneau de contrôle</p>
        <p className="timestamp">
          {boutons?.timestamp && `Dernière MAJ: ${new Date(boutons.timestamp).toLocaleTimeString()}`}
        </p>
      </div>
    </div>
  );
}
