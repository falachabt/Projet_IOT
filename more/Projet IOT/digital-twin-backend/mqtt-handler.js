const mqtt = require('mqtt');
const websocketHandler = require('./websocket-handler');
const influxdbHandler = require('./influxdb-handler');

let client = null;
let connected = false;

function init() {
  const brokerUrl = `mqtt://${process.env.MQTT_BROKER}:${process.env.MQTT_PORT}`;

  global.logger.info(`Connexion au broker MQTT: ${brokerUrl}`);

  client = mqtt.connect(brokerUrl, {
    clientId: process.env.MQTT_CLIENT_ID || 'DigitalTwin_Backend',
    clean: true,
    reconnectPeriod: 5000,
    connectTimeout: 30000
  });

  client.on('connect', () => {
    connected = true;
    global.logger.info('✓ Connecté au broker MQTT');

    // Souscrire à tous les topics
    const topics = (process.env.MQTT_TOPICS || 'esp8266/#,raspberry/#').split(',');

    topics.forEach(topic => {
      client.subscribe(topic.trim(), (err) => {
        if (err) {
          global.logger.error(`Erreur souscription ${topic}: ${err.message}`);
        } else {
          global.logger.info(`✓ Souscrit au topic: ${topic.trim()}`);
        }
      });
    });
  });

  client.on('message', (topic, payload) => {
    handleMessage(topic, payload.toString());
  });

  client.on('error', (error) => {
    global.logger.error(`Erreur MQTT: ${error.message}`);
    connected = false;
  });

  client.on('close', () => {
    connected = false;
    global.logger.warn('Connexion MQTT fermée');
  });

  client.on('reconnect', () => {
    global.logger.info('Reconnexion MQTT...');
  });
}

function handleMessage(topic, message) {
  try {
    global.logger.info(`MQTT [${topic}]: ${message}`);

    let data;
    try {
      data = JSON.parse(message);
    } catch (e) {
      // Message simple (non-JSON)
      data = { value: message };
    }

    // Mettre à jour l'état global
    updateSystemState(topic, data);

    // Envoyer aux clients WebSocket
    websocketHandler.broadcast('mqtt_update', {
      topic,
      data,
      timestamp: new Date().toISOString()
    });

    // Enregistrer dans InfluxDB
    influxdbHandler.writeData(topic, data);

  } catch (error) {
    global.logger.error(`Erreur traitement message MQTT: ${error.message}`);
  }
}

function updateSystemState(topic, data) {
  const now = new Date().toISOString();

  // État système ESP8266 (topic consolidé)
  if (topic.includes('systeme/etat')) {
    // Mettre à jour tous les états depuis le topic système
    global.systemState = {
      ...global.systemState,
      etat_grafcet: data.etat_grafcet,
      etat_numero: data.etat_numero,
      moteur1_actif: data.moteur1_actif || false,
      moteur2_actif: data.moteur2_actif || false,
      objet_detecte: data.objet_detecte || false,
      ultrason: {
        ...global.systemState.ultrason,
        objet_detecte: data.objet_detecte || false,
        flacon_detecte: data.objet_detecte || false,
        timestamp: now
      },
      moteur: {
        ...global.systemState.moteur,
        etat: data.moteur1_actif ? 'ON' : 'OFF',
        timestamp: now
      },
      boutons: {
        ...global.systemState.boutons,
        bouton_marche: data.bouton_marche || false,
        bouton_urgence: data.bouton_urgence || false,
        timestamp: now
      }
    };
  }

  // Ultrason/Distance
  else if (topic.includes('ultrason/distance') || topic.includes('capteurs/distance')) {
    global.systemState.ultrason = {
      distance: data.distance || 0,
      objet_detecte: data.objet_detecte || data.flacon_detecte || false,
      flacon_detecte: data.objet_detecte || data.flacon_detecte || false,
      capteur: data.capteur || 'infrarouge',
      timestamp: now
    };
  }

  // Poids
  else if (topic.includes('poids/valeur')) {
    global.systemState.poids = {
      valeur_g: data.poids_g || 0,
      timestamp: now
    };
  }

  // Moteur
  else if (topic.includes('moteur/etat')) {
    global.systemState.moteur = {
      etat: data.etat || 'OFF',
      vitesse: data.vitesse || 0,
      timestamp: now
    };
  }

  // LEDs
  else if (topic.includes('led/etat')) {
    global.systemState.leds = {
      verte: data.verte || false,
      rouge: data.rouge || false,
      orange: data.orange || false,
      timestamp: now
    };
  }

  // Urgence
  else if (topic.includes('urgence/etat')) {
    global.systemState.urgence = {
      active: data.active || false,
      timestamp: now
    };

    // Si urgence activée, arrêter moteur
    if (data.active) {
      publish('esp8266/commande/moteur', JSON.stringify({
        action: 'STOP'
      }));
    }
  }

  // Boutons
  else if (topic.includes('boutons/marche')) {
    global.systemState.boutons = global.systemState.boutons || {};
    global.systemState.boutons.bouton_marche = data.bouton_marche || false;
    global.systemState.boutons.timestamp = now;
  }

  else if (topic.includes('boutons/urgence')) {
    global.systemState.boutons = global.systemState.boutons || {};
    global.systemState.boutons.bouton_urgence = data.bouton_urgence || false;
    global.systemState.boutons.timestamp = now;
  }

  // Caméra (Raspberry Pi)
  else if (topic.includes('camera/resultat') || topic.includes('bouteille/etat')) {
    // Format détaillé avec bottle, cap, label
    if (data.bottle || data.cap || data.label) {
      global.systemState.camera = {
        status: data.status || 'INCONNU',
        bouteille_detectee: data.bottle?.detected || false,
        bouteille_confiance: data.bottle?.confidence || 0,
        bouchon_present: data.cap?.detected || false,
        bouchon_confiance: data.cap?.confidence || 0,
        etiquette_presente: data.label?.detected || false,
        etiquette_confiance: data.label?.confidence || 0,
        image_path: data.image_path,
        elapsed_ms: data.elapsed_ms,
        timestamp: data.timestamp || now
      };

      // Statistiques
      global.systemState.statistics.total_analyses++;
      global.systemState.statistics.derniere_analyse = now;

      if (data.status === 'OK') {
        global.systemState.statistics.analyses_ok++;
      } else if (data.status === 'KO' || data.status === 'ERREUR') {
        global.systemState.statistics.analyses_ko++;
      }

      if (global.systemState.statistics.total_analyses > 0) {
        global.systemState.statistics.taux_ok_pourcent = Math.round(
          (global.systemState.statistics.analyses_ok / global.systemState.statistics.total_analyses) * 100
        );
      }
    }
    // Format simple "OK" / "KO"
    else if (typeof data.value === 'string') {
      const status = data.value.toUpperCase();

      global.systemState.camera.status = status;
      global.systemState.camera.timestamp = now;

      // Statistiques
      global.systemState.statistics.total_analyses++;
      global.systemState.statistics.derniere_analyse = now;

      if (status === 'OK') {
        global.systemState.statistics.analyses_ok++;
      } else {
        global.systemState.statistics.analyses_ko++;
      }

      // Recalculer taux
      if (global.systemState.statistics.total_analyses > 0) {
        global.systemState.statistics.taux_ok_pourcent = Math.round(
          (global.systemState.statistics.analyses_ok / global.systemState.statistics.total_analyses) * 100
        );
      }
    }
    // Format JSON basique
    else {
      global.systemState.camera = {
        status: data.status || 'INCONNU',
        bouteille_detectee: data.bouteille_detectee,
        bouchon_present: data.bouchon_present,
        niveau_liquide: data.niveau_liquide,
        confiance: data.confiance,
        image_path: data.image_path,
        timestamp: now
      };

      // Statistiques
      if (data.status) {
        global.systemState.statistics.total_analyses++;
        global.systemState.statistics.derniere_analyse = now;

        if (data.status === 'OK') {
          global.systemState.statistics.analyses_ok++;
        } else if (data.status === 'KO' || data.status === 'ERREUR') {
          global.systemState.statistics.analyses_ko++;
        }

        if (global.systemState.statistics.total_analyses > 0) {
          global.systemState.statistics.taux_ok_pourcent = Math.round(
            (global.systemState.statistics.analyses_ok / global.systemState.statistics.total_analyses) * 100
          );
        }
      }
    }
  }

  // Broadcast état complet
  websocketHandler.broadcast('state_update', global.systemState);
}

function publish(topic, message) {
  if (!client || !connected) {
    global.logger.warn(`Impossible de publier: MQTT non connecté`);
    return false;
  }

  client.publish(topic, message, { qos: 1 }, (err) => {
    if (err) {
      global.logger.error(`Erreur publication ${topic}: ${err.message}`);
    } else {
      global.logger.info(`Publié ${topic}: ${message}`);
    }
  });

  return true;
}

function isConnected() {
  return connected;
}

function disconnect() {
  if (client) {
    client.end();
    global.logger.info('Client MQTT déconnecté');
  }
}

module.exports = {
  init,
  publish,
  isConnected,
  disconnect
};
