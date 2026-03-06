import axios from 'axios';

const API_BASE_URL = 'http://localhost:3000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Intercepteur pour logger les erreurs
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.message);
    return Promise.reject(error);
  }
);

// État du système
export const getSystemState = async () => {
  const response = await api.get('/state');
  return response.data;
};

export const getUltrasonState = async () => {
  const response = await api.get('/state/ultrason');
  return response.data;
};

export const getPoidsState = async () => {
  const response = await api.get('/state/poids');
  return response.data;
};

export const getMoteurState = async () => {
  const response = await api.get('/state/moteur');
  return response.data;
};

export const getLedsState = async () => {
  const response = await api.get('/state/leds');
  return response.data;
};

export const getCameraState = async () => {
  const response = await api.get('/state/camera');
  return response.data;
};

export const getStatistics = async () => {
  const response = await api.get('/state/statistics');
  return response.data;
};

// Historique
export const getHistory = async (measurement, start = '-1h', end = 'now()') => {
  const response = await api.get(`/history/${measurement}`, {
    params: { start, end }
  });
  return response.data;
};

export const getHistoryStats = async (hours = 24) => {
  const response = await api.get('/history/stats/summary', {
    params: { hours }
  });
  return response.data;
};

// Contrôle
export const controlMotor = async (action, vitesse = 80) => {
  const response = await api.post('/control/motor', {
    action: action.toUpperCase(),
    vitesse
  });
  return response.data;
};

export const controlLED = async (led, etat) => {
  const response = await api.post('/control/led', {
    led: led.toLowerCase(),
    etat
  });
  return response.data;
};

export const triggerAnalysis = async () => {
  const response = await api.post('/control/trigger-analysis');
  return response.data;
};

export const controlButton = async (button, etat) => {
  const response = await api.post('/control/button', {
    button: button.toLowerCase(),
    etat
  });
  return response.data;
};

// Santé du serveur
export const checkHealth = async () => {
  const response = await api.get('/health', {
    baseURL: 'http://localhost:3000'
  });
  return response.data;
};

export default api;
