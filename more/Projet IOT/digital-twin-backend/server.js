const express = require('express');
const http = require('http');
const cors = require('cors');
const dotenv = require('dotenv');
const winston = require('winston');

// Charger configuration
dotenv.config();

// Initialiser logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    winston.format.printf(({ timestamp, level, message }) => {
      return `[${timestamp}] ${level.toUpperCase()}: ${message}`;
    })
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' })
  ]
});

// Créer dossier logs
const fs = require('fs');
if (!fs.existsSync('./logs')) {
  fs.mkdirSync('./logs');
}

// Initialiser Express
const app = express();
const server = http.createServer(app);

// Middleware
app.use(cors({
  origin: process.env.WS_CORS_ORIGIN || 'http://localhost:5173',
  credentials: true
}));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// État global du système
global.systemState = {
  ultrason: {
    distance: 0,
    flacon_detecte: false,
    timestamp: null
  },
  poids: {
    valeur_g: 0,
    timestamp: null
  },
  moteur: {
    etat: 'OFF',
    vitesse: 0,
    timestamp: null
  },
  leds: {
    verte: false,
    rouge: false,
    orange: false,
    timestamp: null
  },
  urgence: {
    active: false,
    timestamp: null
  },
  boutons: {
    bouton_marche: false,
    bouton_urgence: false,
    timestamp: null
  },
  camera: {
    status: 'ATTENTE',
    bouteille_detectee: null,
    bouchon_present: null,
    niveau_liquide: null,
    confiance: null,
    image_path: null,
    timestamp: null
  },
  statistics: {
    total_analyses: 0,
    analyses_ok: 0,
    analyses_ko: 0,
    taux_ok_pourcent: 0,
    derniere_analyse: null
  }
};

global.logger = logger;

// Initialiser les handlers
const mqttHandler = require('./mqtt-handler');
const websocketHandler = require('./websocket-handler');
const influxdbHandler = require('./influxdb-handler');

// Routes API
const stateRoutes = require('./routes/state');
const historyRoutes = require('./routes/history');
const controlRoutes = require('./routes/control');

app.use('/api/state', stateRoutes);
app.use('/api/history', historyRoutes);
app.use('/api/control', controlRoutes);

// Route de santé
app.get('/health', (req, res) => {
  res.json({
    status: 'OK',
    timestamp: new Date().toISOString(),
    mqtt_connected: mqttHandler.isConnected(),
    influxdb_connected: influxdbHandler.isConnected()
  });
});

// Route racine
app.get('/', (req, res) => {
  res.json({
    name: 'Digital Twin Backend - Système IoT Flacons',
    version: '1.0.0',
    endpoints: {
      state: '/api/state',
      history: '/api/history',
      control: '/api/control',
      health: '/health'
    }
  });
});

// Initialiser WebSocket
websocketHandler.init(server);

// Initialiser MQTT
mqttHandler.init();

// Initialiser InfluxDB
influxdbHandler.init();

// Démarrer serveur
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  logger.info(`✓ Backend jumeau numérique démarré sur le port ${PORT}`);
  logger.info(`✓ WebSocket CORS: ${process.env.WS_CORS_ORIGIN}`);
  logger.info(`✓ MQTT Broker: ${process.env.MQTT_BROKER}:${process.env.MQTT_PORT}`);
  logger.info(`✓ InfluxDB: ${process.env.INFLUXDB_URL}`);
});

// Gestion des erreurs
process.on('uncaughtException', (error) => {
  logger.error(`Uncaught Exception: ${error.message}`);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error(`Unhandled Rejection at: ${promise}, reason: ${reason}`);
});

// Arrêt gracieux
process.on('SIGINT', () => {
  logger.info('Arrêt du serveur...');
  mqttHandler.disconnect();
  server.close(() => {
    logger.info('Serveur arrêté');
    process.exit(0);
  });
});

module.exports = app;
