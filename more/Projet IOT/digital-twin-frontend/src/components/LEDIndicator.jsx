import { Lightbulb } from 'lucide-react';

export default function LEDIndicator({ leds, onControl, disabled }) {
  const handleToggle = (led) => {
    if (!disabled) {
      onControl(led, !leds[led]);
    }
  };

  return (
    <div className="card led-indicator">
      <div className="led-header">
        <Lightbulb size={24} />
        <h3>Indicateurs LED</h3>
      </div>

      <div className="leds-grid">
        <div className="led-item">
          <div
            className={`led led-green ${leds?.verte ? 'on' : 'off'}`}
            onClick={() => handleToggle('verte')}
            style={{ cursor: disabled ? 'not-allowed' : 'pointer' }}
          >
            <div className="led-glow"></div>
          </div>
          <span>Verte (OK)</span>
        </div>

        <div className="led-item">
          <div
            className={`led led-red ${leds?.rouge ? 'on' : 'off'}`}
            onClick={() => handleToggle('rouge')}
            style={{ cursor: disabled ? 'not-allowed' : 'pointer' }}
          >
            <div className="led-glow"></div>
          </div>
          <span>Rouge (KO)</span>
        </div>

        <div className="led-item">
          <div
            className={`led led-orange ${leds?.orange ? 'on' : 'off'}`}
            onClick={() => handleToggle('orange')}
            style={{ cursor: disabled ? 'not-allowed' : 'pointer' }}
          >
            <div className="led-glow"></div>
          </div>
          <span>Orange (En cours)</span>
        </div>
      </div>

      {disabled && (
        <p className="warning-text">⚠️ Contrôle désactivé</p>
      )}

      <style jsx>{`
        .led-indicator {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .led-header {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .led-header h3 {
          margin: 0;
          font-size: 1rem;
          font-weight: 600;
        }

        .leds-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 1rem;
        }

        .led-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.5rem;
        }

        .led-item span {
          font-size: 0.75rem;
          color: var(--text-secondary);
          text-align: center;
        }

        .led {
          width: 60px;
          height: 60px;
          border-radius: 50%;
          position: relative;
          transition: all 0.3s ease;
          border: 3px solid;
        }

        .led-green { border-color: #10b981; }
        .led-red { border-color: #ef4444; }
        .led-orange { border-color: #f59e0b; }

        .led.off {
          background: rgba(255, 255, 255, 0.1);
          opacity: 0.3;
        }

        .led.on.led-green { background: #10b981; box-shadow: 0 0 20px #10b981; }
        .led.on.led-red { background: #ef4444; box-shadow: 0 0 20px #ef4444; }
        .led.on.led-orange { background: #f59e0b; box-shadow: 0 0 20px #f59e0b; }

        .led.on .led-glow {
          position: absolute;
          width: 100%;
          height: 100%;
          border-radius: 50%;
          animation: pulse-glow 2s infinite;
        }

        .led.on.led-green .led-glow { background: radial-gradient(circle, rgba(16, 185, 129, 0.8) 0%, transparent 70%); }
        .led.on.led-red .led-glow { background: radial-gradient(circle, rgba(239, 68, 68, 0.8) 0%, transparent 70%); }
        .led.on.led-orange .led-glow { background: radial-gradient(circle, rgba(245, 158, 11, 0.8) 0%, transparent 70%); }

        @keyframes pulse-glow {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(1.1); }
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
