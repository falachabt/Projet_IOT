const express = require('express');
const router = express.Router();
const influxdbHandler = require('../influxdb-handler');

// GET /api/history/:measurement?start=...&end=...
// Exemples:
//   /api/history/ultrason?start=-1h
//   /api/history/poids?start=-24h&end=now()
//   /api/history/camera?start=2024-01-01T00:00:00Z&end=2024-01-02T00:00:00Z
router.get('/:measurement', async (req, res) => {
  try {
    const { measurement } = req.params;
    const { start, end } = req.query;

    // Valeurs par défaut
    const startTime = start || '-1h';
    const endTime = end || 'now()';

    // Vérifier que le measurement est valide
    const validMeasurements = ['ultrason', 'poids', 'moteur', 'leds', 'urgence', 'camera'];
    if (!validMeasurements.includes(measurement)) {
      return res.status(400).json({
        success: false,
        error: `Measurement invalide. Valeurs possibles: ${validMeasurements.join(', ')}`
      });
    }

    const data = await influxdbHandler.queryHistory(measurement, startTime, endTime);

    res.json({
      success: true,
      measurement,
      start: startTime,
      end: endTime,
      count: data.length,
      data
    });

  } catch (error) {
    global.logger.error(`Erreur /api/history: ${error.message}`);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// GET /api/history/stats?hours=24
// Statistiques sur une période
router.get('/stats/summary', async (req, res) => {
  try {
    const hours = parseInt(req.query.hours) || 24;

    const stats = await influxdbHandler.getStats(hours);

    res.json({
      success: true,
      data: stats
    });

  } catch (error) {
    global.logger.error(`Erreur /api/history/stats: ${error.message}`);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

module.exports = router;
