const mqtt = require('mqtt');

// Connexion au broker MQTT
const client = mqtt.connect('mqtt://localhost:1883');

console.log('🤖 Simulateur IoT - Jumeau Numérique');
console.log('Connexion au broker MQTT...');

client.on('connect', () => {
  console.log('✅ Connecté au broker MQTT\n');
  console.log('Simulation en cours...\n');

  // Simuler un cycle complet toutes les 5 secondes
  setInterval(() => {
    simulerCycle();
  }, 5000);

  // Premier cycle immédiat
  setTimeout(() => simulerCycle(), 1000);
});

client.on('error', (err) => {
  console.error('❌ Erreur MQTT:', err.message);
});

function simulerCycle() {
  const timestamp = Date.now();

  // Étape 1: Flacon détecté par ultrason
  console.log('📏 [Ultrason] Flacon détecté!');
  client.publish('esp8266/ultrason/distance', JSON.stringify({
    distance: randomBetween(3, 8),
    flacon_detecte: true,
    timestamp
  }));

  // Étape 2: Mesure du poids
  setTimeout(() => {
    const poids = randomBetween(300, 450);
    console.log(`⚖️  [Poids] ${poids.toFixed(1)}g`);
    client.publish('esp8266/poids/valeur', JSON.stringify({
      poids_g: poids,
      timestamp
    }));
  }, 500);

  // Étape 3: Moteur démarre
  setTimeout(() => {
    console.log('🔧 [Moteur] Démarrage du convoyeur');
    client.publish('esp8266/moteur/etat', JSON.stringify({
      etat: 'ON',
      vitesse: 80,
      timestamp
    }));
  }, 1000);

  // Étape 4: LED orange (analyse en cours)
  setTimeout(() => {
    console.log('🟠 [LED] Analyse en cours...');
    client.publish('esp8266/led/etat', JSON.stringify({
      verte: false,
      rouge: false,
      orange: true
    }));
  }, 1500);

  // Étape 5: Résultat caméra (80% de chance OK)
  setTimeout(() => {
    const isOK = Math.random() > 0.2;
    const status = isOK ? 'OK' : 'KO';

    console.log(`📷 [Caméra] Résultat: ${status}`);

    // Message simple pour ESP8266
    client.publish('esp8266/bouteille/etat', status);

    // Message détaillé pour jumeau numérique
    client.publish('raspberry/camera/resultat', JSON.stringify({
      timestamp: new Date().toISOString(),
      status: status,
      bouteille_detectee: true,
      bouchon_present: isOK,
      niveau_liquide: isOK ? randomBetween(80, 100) : randomBetween(50, 79),
      confiance: randomBetween(0.85, 0.98),
      image_path: `./output/${Date.now()}_${status}.jpg`,
      trigger: '5.2',
      detail: isOK ? 'Bouteille avec bouchon → Validé' : 'Bouteille SANS bouchon !'
    }));

    // LED résultat
    setTimeout(() => {
      if (isOK) {
        console.log('🟢 [LED] Verte - OK');
        client.publish('esp8266/led/etat', JSON.stringify({
          verte: true,
          rouge: false,
          orange: false
        }));
      } else {
        console.log('🔴 [LED] Rouge - KO');
        client.publish('esp8266/led/etat', JSON.stringify({
          verte: false,
          rouge: true,
          orange: false
        }));
      }
    }, 500);
  }, 2000);

  // Étape 6: Flacon parti, moteur s'arrête
  setTimeout(() => {
    console.log('📏 [Ultrason] Flacon parti');
    client.publish('esp8266/ultrason/distance', JSON.stringify({
      distance: randomBetween(100, 200),
      flacon_detecte: false,
      timestamp
    }));

    setTimeout(() => {
      console.log('🔧 [Moteur] Arrêt du convoyeur');
      client.publish('esp8266/moteur/etat', JSON.stringify({
        etat: 'OFF',
        vitesse: 0,
        timestamp
      }));
    }, 300);

    // LEDs éteintes
    setTimeout(() => {
      console.log('💡 [LED] Toutes éteintes\n');
      console.log('─'.repeat(50) + '\n');
      client.publish('esp8266/led/etat', JSON.stringify({
        verte: false,
        rouge: false,
        orange: false
      }));
    }, 600);
  }, 3500);
}

function randomBetween(min, max) {
  return Math.random() * (max - min) + min;
}

// Gestion arrêt propre
process.on('SIGINT', () => {
  console.log('\n\n👋 Arrêt du simulateur...');
  client.end();
  process.exit(0);
});
