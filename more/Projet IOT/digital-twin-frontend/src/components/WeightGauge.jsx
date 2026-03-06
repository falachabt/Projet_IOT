export default function WeightGauge({ weight, max }) {
  const percentage = Math.min((weight / max) * 100, 100);

  return (
    <div className="weight-gauge">
      <div className="gauge-bar">
        <div
          className="gauge-fill"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="gauge-labels">
        <span>0g</span>
        <span>{max}g</span>
      </div>

      <style jsx>{`
        .weight-gauge {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .gauge-bar {
          width: 100%;
          height: 20px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 10px;
          overflow: hidden;
          position: relative;
        }

        .gauge-fill {
          height: 100%;
          background: linear-gradient(90deg, #10b981 0%, #3b82f6 100%);
          transition: width 0.3s ease;
          border-radius: 10px;
        }

        .gauge-labels {
          display: flex;
          justify-content: space-between;
          font-size: 0.75rem;
          color: var(--text-secondary);
        }
      `}</style>
    </div>
  );
}
