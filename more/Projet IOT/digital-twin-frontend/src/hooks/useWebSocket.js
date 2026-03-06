import { useEffect, useState, useCallback } from 'react';
import { io } from 'socket.io-client';

const SOCKET_URL = 'http://localhost:3000';

export function useWebSocket() {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [systemState, setSystemState] = useState(null);
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    const socketInstance = io(SOCKET_URL, {
      transports: ['websocket'],
      reconnectionDelay: 1000,
      reconnection: true,
      reconnectionAttempts: 10
    });

    socketInstance.on('connect', () => {
      console.log('✓ WebSocket connecté');
      setConnected(true);
      addLog('Connecté au serveur');
    });

    socketInstance.on('disconnect', () => {
      console.log('✗ WebSocket déconnecté');
      setConnected(false);
      addLog('Déconnecté du serveur', 'warning');
    });

    socketInstance.on('state_update', (data) => {
      setSystemState(data);
    });

    socketInstance.on('mqtt_update', (data) => {
      addLog(`MQTT: ${data.topic}`, 'info');
    });

    socketInstance.on('command_ack', (data) => {
      if (data.success) {
        addLog(data.message, 'success');
      } else {
        addLog(data.message, 'error');
      }
    });

    setSocket(socketInstance);

    return () => {
      socketInstance.disconnect();
    };
  }, []);

  const addLog = useCallback((message, type = 'info') => {
    setLogs((prev) => {
      const newLog = {
        id: Date.now(),
        message,
        type,
        timestamp: new Date()
      };
      return [newLog, ...prev].slice(0, 100); // Max 100 logs
    });
  }, []);

  const sendCommand = useCallback((type, data) => {
    if (socket && connected) {
      socket.emit('command', { type, ...data });
      return true;
    }
    return false;
  }, [socket, connected]);

  const controlMotor = useCallback((action, vitesse = 80) => {
    return sendCommand('motor_control', { action, vitesse });
  }, [sendCommand]);

  const controlLED = useCallback((led, etat) => {
    return sendCommand('led_control', { led, etat });
  }, [sendCommand]);

  const controlButton = useCallback(async (button, etat) => {
    try {
      const response = await fetch('http://localhost:3000/api/control/button', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ button, etat })
      });
      const data = await response.json();
      if (data.success) {
        addLog(`Bouton ${button}: ${etat ? 'APPUYÉ' : 'RELÂCHÉ'}`, 'success');
      }
      return data.success;
    } catch (error) {
      addLog(`Erreur bouton ${button}: ${error.message}`, 'error');
      return false;
    }
  }, [addLog]);

  return {
    connected,
    systemState,
    logs,
    controlMotor,
    controlLED,
    controlButton,
    addLog
  };
}
