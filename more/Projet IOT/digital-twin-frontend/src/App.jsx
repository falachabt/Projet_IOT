import { useState, useEffect } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import Dashboard from './components/Dashboard';
import Scene3D from './components/Scene3D';
import LogViewer from './components/LogViewer';
import { Activity } from 'lucide-react';

import './App.css';

function App() {
  const { connected, systemState, logs, controlMotor, controlLED, controlButton } = useWebSocket();
  const [view, setView] = useState('dashboard'); // 'dashboard' | '3d'

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <Activity size={32} color="#4f46e5" />
          <div>
            <h1>Jumeau Numérique IoT</h1>
            <p className="subtitle">Système de Contrôle Qualité Flacons</p>
          </div>
        </div>

        <div className="header-center">
          <button
            className={`view-btn ${view === 'dashboard' ? 'active' : ''}`}
            onClick={() => setView('dashboard')}
          >
            Dashboard
          </button>
          <button
            className={`view-btn ${view === '3d' ? 'active' : ''}`}
            onClick={() => setView('3d')}
          >
            Vue 3D
          </button>
        </div>

        <div className="header-right">
          <div className="connection-status">
            <span className={`status-indicator ${connected ? 'status-ok' : 'status-error'}`}></span>
            <span>{connected ? 'Connecté' : 'Déconnecté'}</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="app-main">
        {view === 'dashboard' ? (
          <Dashboard
            systemState={systemState}
            controlMotor={controlMotor}
            controlLED={controlLED}
            controlButton={controlButton}
          />
        ) : (
          <Scene3D systemState={systemState} />
        )}

        {/* Logs Sidebar */}
        <aside className="logs-sidebar">
          <LogViewer logs={logs} />
        </aside>
      </main>
    </div>
  );
}

export default App;
