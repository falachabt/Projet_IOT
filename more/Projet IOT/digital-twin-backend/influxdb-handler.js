const { InfluxDB, Point } = require('@influxdata/influxdb-client');

let influxDB = null;
let writeApi = null;
let queryApi = null;
let connected = false;

function init() {
  try {
    const url = process.env.INFLUXDB_URL || 'http://localhost:8086';
    const token = process.env.INFLUXDB_TOKEN;
    const org = process.env.INFLUXDB_ORG || 'iot-flacons';
    const bucket = process.env.INFLUXDB_BUCKET || 'iot_flacons';

    if (!token || token === 'your-influxdb-token-here') {
      global.logger.warn('InfluxDB token non configuré - BDD désactivée');
      connected = false;
      return;
    }

    influxDB = new InfluxDB({ url, token });
    writeApi = influxDB.getWriteApi(org, bucket, 'ns');
    queryApi = influxDB.getQueryApi(org);

    // Flush automatique toutes les 5 secondes
    writeApi.useDefaultTags({ location: 'factory_line_1' });

    connected = true;
    global.logger.info('✓ InfluxDB initialisé');

  } catch (error) {
    global.logger.error(`Erreur initialisation InfluxDB: ${error.message}`);
    connected = false;
  }
}

function writeData(topic, data) {
  if (!connected || !writeApi) {
    return;
  }

  try {
    let point;

    // Ultrason
    if (topic.includes('ultrason/distance')) {
      point = new Point('ultrason')
        .floatField('distance', data.distance || 0)
        .booleanField('flacon_detecte', data.flacon_detecte || false);
    }

    // Poids
    else if (topic.includes('poids/valeur')) {
      point = new Point('poids')
        .floatField('valeur_grammes', data.poids_g || 0);
    }

    // Moteur
    else if (topic.includes('moteur/etat')) {
      point = new Point('moteur')
        .tag('etat', data.etat || 'OFF')
        .intField('vitesse', data.vitesse || 0);
    }

    // LEDs
    else if (topic.includes('led/etat')) {
      point = new Point('leds')
        .booleanField('verte', data.verte || false)
        .booleanField('rouge', data.rouge || false)
        .booleanField('orange', data.orange || false);
    }

    // Urgence
    else if (topic.includes('urgence/etat')) {
      point = new Point('urgence')
        .booleanField('active', data.active || false);
    }

    // Caméra
    else if (topic.includes('camera/resultat') || topic.includes('bouteille/etat')) {
      if (typeof data.value === 'string') {
        point = new Point('camera')
          .tag('status', data.value.toUpperCase())
          .intField('count', 1);
      } else {
        point = new Point('camera')
          .tag('status', data.status || 'INCONNU')
          .booleanField('bouteille_detectee', data.bouteille_detectee || false)
          .booleanField('bouchon_present', data.bouchon_present || false)
          .floatField('niveau_liquide', data.niveau_liquide || 0)
          .floatField('confiance', data.confiance || 0);
      }
    }

    if (point) {
      writeApi.writePoint(point);
      writeApi.flush();  // Forcer écriture immédiate
    }

  } catch (error) {
    global.logger.error(`Erreur écriture InfluxDB: ${error.message}`);
  }
}

async function queryHistory(measurement, startTime, endTime) {
  if (!connected || !queryApi) {
    throw new Error('InfluxDB non connecté');
  }

  const bucket = process.env.INFLUXDB_BUCKET || 'iot_flacons';

  const query = `
    from(bucket: "${bucket}")
      |> range(start: ${startTime}, stop: ${endTime})
      |> filter(fn: (r) => r._measurement == "${measurement}")
  `;

  const results = [];

  try {
    for await (const { values, tableMeta } of queryApi.iterateRows(query)) {
      const row = tableMeta.toObject(values);
      results.push(row);
    }
    return results;

  } catch (error) {
    global.logger.error(`Erreur query InfluxDB: ${error.message}`);
    throw error;
  }
}

async function getStats(hours = 24) {
  if (!connected || !queryApi) {
    return {
      total_analyses: 0,
      analyses_ok: 0,
      analyses_ko: 0,
      taux_ok_pourcent: 0
    };
  }

  const bucket = process.env.INFLUXDB_BUCKET || 'iot_flacons';
  const startTime = `-${hours}h`;

  const query = `
    from(bucket: "${bucket}")
      |> range(start: ${startTime})
      |> filter(fn: (r) => r._measurement == "camera")
      |> filter(fn: (r) => r._field == "count")
      |> group(columns: ["status"])
      |> sum()
  `;

  try {
    const results = [];
    for await (const { values, tableMeta } of queryApi.iterateRows(query)) {
      const row = tableMeta.toObject(values);
      results.push(row);
    }

    let total = 0;
    let ok = 0;
    let ko = 0;

    results.forEach(row => {
      const count = row._value || 0;
      total += count;

      if (row.status === 'OK') {
        ok = count;
      } else if (row.status === 'KO' || row.status === 'ERREUR') {
        ko = count;
      }
    });

    const taux = total > 0 ? Math.round((ok / total) * 100) : 0;

    return {
      total_analyses: total,
      analyses_ok: ok,
      analyses_ko: ko,
      taux_ok_pourcent: taux,
      periode_heures: hours
    };

  } catch (error) {
    global.logger.error(`Erreur stats InfluxDB: ${error.message}`);
    return {
      total_analyses: 0,
      analyses_ok: 0,
      analyses_ko: 0,
      taux_ok_pourcent: 0
    };
  }
}

function isConnected() {
  return connected;
}

async function close() {
  if (writeApi) {
    try {
      await writeApi.close();
      global.logger.info('InfluxDB fermé');
    } catch (error) {
      global.logger.error(`Erreur fermeture InfluxDB: ${error.message}`);
    }
  }
}

module.exports = {
  init,
  writeData,
  queryHistory,
  getStats,
  isConnected,
  close
};
