const express = require('express');
const router = express.Router();

// GET /api/state - Récupérer l'état actuel complet
router.get('/', (req, res) => {
  try {
    res.json({
      success: true,
      data: global.systemState,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// GET /api/state/ultrason - État capteur ultrason
router.get('/ultrason', (req, res) => {
  res.json({
    success: true,
    data: global.systemState.ultrason
  });
});

// GET /api/state/poids - État capteur de poids
router.get('/poids', (req, res) => {
  res.json({
    success: true,
    data: global.systemState.poids
  });
});

// GET /api/state/moteur - État moteurs
router.get('/moteur', (req, res) => {
  res.json({
    success: true,
    data: global.systemState.moteur
  });
});

// GET /api/state/leds - État LEDs
router.get('/leds', (req, res) => {
  res.json({
    success: true,
    data: global.systemState.leds
  });
});

// GET /api/state/urgence - État bouton urgence
router.get('/urgence', (req, res) => {
  res.json({
    success: true,
    data: global.systemState.urgence
  });
});

// GET /api/state/camera - État caméra/analyse
router.get('/camera', (req, res) => {
  res.json({
    success: true,
    data: global.systemState.camera
  });
});

// GET /api/state/statistics - Statistiques
router.get('/statistics', (req, res) => {
  res.json({
    success: true,
    data: global.systemState.statistics
  });
});

module.exports = router;
