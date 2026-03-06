const express = require('express');
const router = express.Router();
const mqttHandler = require('../mqtt-handler');

// POST /api/control/motor
// Body: { action: "START" | "STOP", vitesse: 0-100 }
router.post('/motor', (req, res) => {
  try {
    const { action, vitesse } = req.body;

    if (!action || !['START', 'STOP'].includes(action.toUpperCase())) {
      return res.status(400).json({
        success: false,
        error: 'Action invalide. Valeurs possibles: START, STOP'
      });
    }

    const payload = JSON.stringify({
      action: action.toUpperCase(),
      vitesse: vitesse || 80
    });

    const published = mqttHandler.publish('esp8266/commande/moteur', payload);

    if (published) {
      global.logger.info(`Commande moteur envoyée: ${action}`);
      res.json({
        success: true,
        message: `Commande moteur ${action} envoyée`,
        payload: JSON.parse(payload)
      });
    } else {
      res.status(503).json({
        success: false,
        error: 'MQTT non connecté'
      });
    }

  } catch (error) {
    global.logger.error(`Erreur /api/control/motor: ${error.message}`);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// POST /api/control/led
// Body: { led: "verte" | "rouge" | "orange", etat: true | false }
router.post('/led', (req, res) => {
  try {
    const { led, etat } = req.body;

    if (!led || !['verte', 'rouge', 'orange'].includes(led.toLowerCase())) {
      return res.status(400).json({
        success: false,
        error: 'LED invalide. Valeurs possibles: verte, rouge, orange'
      });
    }

    if (typeof etat !== 'boolean') {
      return res.status(400).json({
        success: false,
        error: 'État invalide. Doit être true ou false'
      });
    }

    const payload = JSON.stringify({
      led: led.toLowerCase(),
      etat
    });

    const published = mqttHandler.publish('esp8266/commande/led', payload);

    if (published) {
      global.logger.info(`Commande LED envoyée: ${led} = ${etat}`);
      res.json({
        success: true,
        message: `LED ${led} ${etat ? 'allumée' : 'éteinte'}`,
        payload: JSON.parse(payload)
      });
    } else {
      res.status(503).json({
        success: false,
        error: 'MQTT non connecté'
      });
    }

  } catch (error) {
    global.logger.error(`Erreur /api/control/led: ${error.message}`);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// POST /api/control/trigger-analysis
// Déclencher manuellement une analyse caméra
router.post('/trigger-analysis', (req, res) => {
  try {
    const payload = JSON.stringify({
      action: 'check',
      trigger: 'manual',
      timestamp: Date.now()
    });

    const published = mqttHandler.publish('iot/bottle/trigger', payload);

    if (published) {
      global.logger.info('Analyse caméra déclenchée manuellement');
      res.json({
        success: true,
        message: 'Analyse déclenchée'
      });
    } else {
      res.status(503).json({
        success: false,
        error: 'MQTT non connecté'
      });
    }

  } catch (error) {
    global.logger.error(`Erreur /api/control/trigger-analysis: ${error.message}`);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// POST /api/control/button
// Body: { button: "marche" | "urgence", etat: true | false }
router.post('/button', (req, res) => {
  try {
    const { button, etat } = req.body;

    if (!button || !['marche', 'urgence'].includes(button.toLowerCase())) {
      return res.status(400).json({
        success: false,
        error: 'Bouton invalide. Valeurs possibles: marche, urgence'
      });
    }

    if (typeof etat !== 'boolean') {
      return res.status(400).json({
        success: false,
        error: 'État invalide. Doit être true ou false'
      });
    }

    const payload = JSON.stringify({ etat });
    const topic = button.toLowerCase() === 'marche'
      ? 'esp8266/boutons/marche/cmd'
      : 'esp8266/boutons/urgence/cmd';

    const published = mqttHandler.publish(topic, payload);

    if (published) {
      global.logger.info(`Commande bouton ${button}: ${etat ? 'APPUYÉ' : 'RELÂCHÉ'}`);
      res.json({
        success: true,
        message: `Bouton ${button} ${etat ? 'appuyé' : 'relâché'}`,
        payload: { button, etat }
      });
    } else {
      res.status(503).json({
        success: false,
        error: 'MQTT non connecté'
      });
    }

  } catch (error) {
    global.logger.error(`Erreur /api/control/button: ${error.message}`);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

module.exports = router;
