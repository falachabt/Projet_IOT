const { Server } = require('socket.io');

let io = null;

function init(server) {
  io = new Server(server, {
    cors: {
      origin: process.env.WS_CORS_ORIGIN || 'http://localhost:5173',
      methods: ['GET', 'POST'],
      credentials: true
    }
  });

  io.on('connection', (socket) => {
    global.logger.info(`WebSocket client connecté: ${socket.id}`);

    // Envoyer l'état actuel au nouveau client
    socket.emit('state_update', global.systemState);

    // Ping/Pong pour vérifier connexion
    socket.on('ping', () => {
      socket.emit('pong', { timestamp: new Date().toISOString() });
    });

    // Commandes depuis le frontend
    socket.on('command', (data) => {
      handleCommand(socket, data);
    });

    socket.on('disconnect', () => {
      global.logger.info(`WebSocket client déconnecté: ${socket.id}`);
    });

    socket.on('error', (error) => {
      global.logger.error(`WebSocket erreur: ${error.message}`);
    });
  });

  global.logger.info('✓ WebSocket initialisé');
}

function handleCommand(socket, data) {
  global.logger.info(`Commande reçue de ${socket.id}: ${JSON.stringify(data)}`);

  const mqttHandler = require('./mqtt-handler');

  // Commande moteur
  if (data.type === 'motor_control') {
    const payload = JSON.stringify({
      action: data.action,  // START | STOP
      vitesse: data.vitesse || 80
    });

    mqttHandler.publish('esp8266/commande/moteur', payload);

    socket.emit('command_ack', {
      success: true,
      message: 'Commande moteur envoyée'
    });
  }

  // Commande LED
  else if (data.type === 'led_control') {
    const payload = JSON.stringify({
      led: data.led,      // verte | rouge | orange
      etat: data.etat     // true | false
    });

    mqttHandler.publish('esp8266/commande/led', payload);

    socket.emit('command_ack', {
      success: true,
      message: 'Commande LED envoyée'
    });
  }

  else {
    socket.emit('command_ack', {
      success: false,
      message: 'Type de commande inconnu'
    });
  }
}

function broadcast(event, data) {
  if (io) {
    io.emit(event, data);
  }
}

function getConnectedClients() {
  if (io) {
    return io.sockets.sockets.size;
  }
  return 0;
}

module.exports = {
  init,
  broadcast,
  getConnectedClients
};
