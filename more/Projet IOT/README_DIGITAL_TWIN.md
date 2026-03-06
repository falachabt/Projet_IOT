# Jumeau Numérique - Système IoT de Contrôle de Flacons

## 📋 Vue d'Ensemble

Ce projet implémente un **jumeau numérique (digital twin)** en temps réel pour un système IoT de contrôle qualité de flacons sur une ligne de production. Le jumeau numérique permet de visualiser et contrôler le système physique via une interface web 3D interactive.

## 🏗️ Architecture Complète

```
┌─────────────────────────────────────────────────────────────┐
│                    SYSTÈME PHYSIQUE                          │
├─────────────────────────────────────────────────────────────┤
│  Raspberry Pi              ESP8266                           │
│  - Caméra + IA YOLO        - Capteur ultrason HC-SR04       │
│  - main.py                 - Capteur poids HX711             │
│                            - 2 Moteurs DC (L298N)            │
│                            - 3 LEDs (vert/rouge/orange)      │
│                            - Bouton arrêt urgence            │
└─────────────────┬───────────────────────────────────────────┘
                  │ MQTT bidirectionnel
                  │
┌─────────────────▼───────────────────────────────────────────┐
│              MQTT BROKER (Mosquitto)                         │
│              - Port 1883 (MQTT)                              │
│              - Port 9001 (WebSocket MQTT)                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│           BACKEND JUMEAU NUMÉRIQUE                           │
│  (Node.js + Express + Socket.io)                            │
│  - Port 3000 (API REST + WebSocket)                         │
│  - Écoute MQTT et synchronise état                          │
│  - Enregistre dans InfluxDB                                 │
└─────────────────┬───────────────────────────────────────────┘
                  │ WebSocket
                  │
┌─────────────────▼───────────────────────────────────────────┐
│         FRONTEND WEB (React + Three.js)                      │
│  - Port 5173 (dev) ou 80 (prod)                            │
│  - Visualisation 3D du système                              │
│  - Dashboard temps réel                                     │
│  - Contrôle moteurs, LEDs                                   │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Composants

### 1. ESP8266 Controller
**Fichier**: `esp8266_controller/esp8266_controller.ino`

**Matériel géré**:
- Capteur ultrason HC-SR04 (détection présence)
- Capteur poids HX711
- 2 moteurs DC via L298N
- 3 LEDs (verte, rouge, orange)
- Bouton d'arrêt d'urgence

**Topics MQTT publiés**:
- `esp8266/ultrason/distance` - Distance mesurée + détection flacon
- `esp8266/poids/valeur` - Poids en grammes
- `esp8266/moteur/etat` - État moteurs (ON/OFF + vitesse)
- `esp8266/led/etat` - État des 3 LEDs
- `esp8266/urgence/etat` - État bouton urgence

**Topics MQTT écoutés**:
- `esp8266/bouteille/etat` - Résultat caméra (OK/KO)
- `esp8266/commande/moteur` - Commande moteur
- `esp8266/commande/led` - Commande LED

### 2. Raspberry Pi (Caméra + IA)
**Fichier**: `main.py`

**Fonctionnalités**:
- Détection bouteille avec YOLO
- Vérification présence bouchon
- Interface GUI Tkinter
- Publication MQTT:
  - Topic simple: `esp8266/bouteille/etat` (OK/KO)
  - Topic détaillé: `raspberry/camera/resultat` (JSON complet)

**Message JSON publié**:
```json
{
  "timestamp": "2026-02-06T10:30:45.123Z",
  "status": "OK",
  "bouteille_detectee": true,
  "bouchon_present": true,
  "niveau_liquide": null,
  "confiance": 0.92,
  "image_path": "./output/20260206_103045_OK.jpg",
  "trigger": "5.2",
  "detail": "Bouteille avec bouchon → Validé"
}
```

### 3. Backend Node.js
**Répertoire**: `digital-twin-backend/`

**Structure**:
```
digital-twin-backend/
├── server.js              # Serveur Express principal
├── mqtt-handler.js        # Gestion MQTT
├── websocket-handler.js   # Gestion WebSocket
├── influxdb-handler.js    # Gestion InfluxDB
├── routes/
│   ├── state.js          # Endpoints état
│   ├── history.js        # Endpoints historique
│   └── control.js        # Endpoints contrôle
├── package.json
├── .env
└── Dockerfile
```

**API REST Endpoints**:
- `GET /api/state` - État complet du système
- `GET /api/state/:component` - État d'un composant
- `GET /api/history/:measurement` - Historique InfluxDB
- `GET /api/history/stats/summary` - Statistiques
- `POST /api/control/motor` - Contrôle moteur
- `POST /api/control/led` - Contrôle LED
- `POST /api/control/trigger-analysis` - Déclencher analyse
- `GET /health` - Santé du serveur

**WebSocket Events**:
- `state_update` - Mise à jour état complet
- `mqtt_update` - Nouveau message MQTT
- `command` - Commande depuis frontend
- `command_ack` - Accusé réception commande

### 4. Frontend React
**Répertoire**: `digital-twin-frontend/`

**Composants**:
- `Dashboard.jsx` - Vue principale avec cartes
- `Scene3D.jsx` - Visualisation 3D avec Three.js
- `SensorCard.jsx` - Carte affichage capteur
- `MotorControl.jsx` - Contrôle moteurs
- `LEDIndicator.jsx` - Indicateurs LEDs interactifs
- `CameraFeed.jsx` - Résultat caméra
- `WeightGauge.jsx` - Jauge de poids
- `HistoryChart.jsx` - Graphique historique
- `LogViewer.jsx` - Logs temps réel

**Fonctionnalités**:
- ✅ Visualisation 3D temps réel
- ✅ Dashboard avec toutes les données
- ✅ Contrôle à distance (moteurs, LEDs)
- ✅ Graphiques historiques
- ✅ Logs système
- ✅ Statistiques (taux OK/KO)

## 🚀 Installation

### Prérequis
- **Hardware**: Raspberry Pi, ESP8266, capteurs, moteurs, LEDs
- **Software**: Node.js 18+, Python 3.8+, Arduino IDE, Docker (optionnel)

### Option 1: Installation Manuelle

#### 1. Backend
```bash
cd digital-twin-backend
npm install
cp .env.example .env
# Éditer .env avec vos paramètres
npm start
```

#### 2. Frontend
```bash
cd digital-twin-frontend
npm install
npm run dev
```

#### 3. MQTT Broker (Mosquitto)
```bash
# Linux/macOS
sudo apt install mosquitto mosquitto-clients
sudo systemctl start mosquitto

# Windows
# Télécharger depuis https://mosquitto.org/download/
```

#### 4. InfluxDB
```bash
# Docker
docker run -d -p 8086:8086 \
  -v influxdb_data:/var/lib/influxdb2 \
  -e DOCKER_INFLUXDB_INIT_MODE=setup \
  -e DOCKER_INFLUXDB_INIT_USERNAME=admin \
  -e DOCKER_INFLUXDB_INIT_PASSWORD=adminpassword \
  -e DOCKER_INFLUXDB_INIT_ORG=iot-flacons \
  -e DOCKER_INFLUXDB_INIT_BUCKET=iot_flacons \
  -e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=my-super-secret-auth-token \
  influxdb:2.7
```

#### 5. ESP8266
1. Ouvrir `esp8266_controller/esp8266_controller.ino` dans Arduino IDE
2. Modifier WiFi SSID/password et adresse MQTT broker
3. Installer librairies: PubSubClient, ESP8266WiFi, HX711, ArduinoJson
4. Flasher sur ESP8266

#### 6. Raspberry Pi
```bash
cd Projet_IOT
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Option 2: Installation Docker (Recommandée)

```bash
# Démarrer tous les services
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Arrêter
docker-compose down
```

**Services démarrés**:
- Mosquitto MQTT: `localhost:1883`
- InfluxDB: `localhost:8086`
- Backend API: `localhost:3000`
- Frontend: `localhost:80`
- Grafana (optionnel): `localhost:3001`

## 🔧 Configuration

### MQTT Topics

**Publiés par ESP8266**:
```
esp8266/ultrason/distance    → {"distance": 5.2, "flacon_detecte": true, "timestamp": 123456}
esp8266/poids/valeur         → {"poids_g": 350, "timestamp": 123456}
esp8266/moteur/etat          → {"etat": "ON", "vitesse": 80, "timestamp": 123456}
esp8266/led/etat             → {"verte": false, "rouge": false, "orange": true}
esp8266/urgence/etat         → {"active": false, "timestamp": 123456}
```

**Publiés par Raspberry Pi**:
```
esp8266/bouteille/etat       → "OK" | "KO"  (message simple)
raspberry/camera/resultat    → {JSON détaillé}
```

**Commandes (Frontend → ESP8266)**:
```
esp8266/commande/moteur      → {"action": "START"|"STOP", "vitesse": 80}
esp8266/commande/led         → {"led": "verte"|"rouge"|"orange", "etat": true|false}
```

### Variables d'Environnement Backend (.env)

```env
PORT=3000
NODE_ENV=development
MQTT_BROKER=10.66.108.235
MQTT_PORT=1883
MQTT_CLIENT_ID=DigitalTwin_Backend
MQTT_TOPICS=esp8266/#,raspberry/#
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=my-super-secret-auth-token
INFLUXDB_ORG=iot-flacons
INFLUXDB_BUCKET=iot_flacons
WS_CORS_ORIGIN=http://localhost:5173
LOG_LEVEL=info
```

## 📊 Utilisation

### 1. Démarrage du Système

**Option Docker**:
```bash
docker-compose up -d
```

**Option Manuelle** (dans des terminaux séparés):
```bash
# Terminal 1: MQTT
mosquitto -v

# Terminal 2: InfluxDB
influxd

# Terminal 3: Backend
cd digital-twin-backend && npm start

# Terminal 4: Frontend
cd digital-twin-frontend && npm run dev

# Terminal 5: Raspberry Pi
python main.py

# Terminal 6: ESP8266
# Flasher via Arduino IDE
```

### 2. Accès aux Interfaces

- **Frontend Web**: http://localhost:5173 (dev) ou http://localhost (prod)
- **API Backend**: http://localhost:3000/api/state
- **InfluxDB UI**: http://localhost:8086
- **Grafana**: http://localhost:3001 (admin/admin)

### 3. Contrôle du Système

#### Via Frontend Web
1. Ouvrir http://localhost:5173
2. Cliquer sur "Dashboard" pour vue 2D ou "Vue 3D" pour vue 3D
3. Contrôler moteurs via les boutons Démarrer/Arrêter
4. Contrôler LEDs en cliquant dessus

#### Via API REST
```bash
# Démarrer moteur
curl -X POST http://localhost:3000/api/control/motor \
  -H "Content-Type: application/json" \
  -d '{"action": "START", "vitesse": 80}'

# Allumer LED verte
curl -X POST http://localhost:3000/api/control/led \
  -H "Content-Type: application/json" \
  -d '{"led": "verte", "etat": true}'

# Récupérer état
curl http://localhost:3000/api/state

# Statistiques
curl http://localhost:3000/api/history/stats/summary?hours=24
```

#### Via MQTT Direct
```bash
# Publier commande moteur
mosquitto_pub -h localhost -t esp8266/commande/moteur \
  -m '{"action":"START","vitesse":80}'

# Écouter tous les topics
mosquitto_sub -h localhost -t '#' -v
```

### 4. Scénario de Test Complet

1. **Placer un flacon** devant le capteur ultrason
2. **Vérifier** que:
   - Distance affichée dans Dashboard < 10 cm
   - LED orange s'allume (analyse en cours)
   - Moteur démarre automatiquement
   - Caméra capture et analyse
   - Résultat OK/KO apparaît
   - LED verte (OK) ou rouge (KO) s'allume
   - Visualisation 3D mise à jour
   - Logs affichent les événements
   - Données enregistrées dans InfluxDB

3. **Tester arrêt urgence**:
   - Appuyer sur bouton urgence
   - Vérifier arrêt immédiat moteurs
   - Vérifier message d'alerte dans Dashboard

## 📈 Visualisation des Données

### InfluxDB
Accéder à http://localhost:8086

**Buckets**:
- `iot_flacons` - Toutes les données temps réel

**Measurements**:
- `ultrason` - Distance, détection
- `poids` - Poids en grammes
- `moteur` - État moteurs
- `leds` - État LEDs
- `urgence` - État bouton urgence
- `camera` - Résultats analyses

### Grafana (Optionnel)
1. Accéder à http://localhost:3001
2. Login: admin/admin
3. Ajouter source de données InfluxDB
4. Créer dashboards personnalisés

## 🐛 Dépannage

### Backend ne se connecte pas à MQTT
- Vérifier que Mosquitto est démarré: `mosquitto -v`
- Vérifier IP broker dans `.env`
- Tester connexion: `mosquitto_pub -h <BROKER_IP> -t test -m "hello"`

### Frontend ne reçoit pas de données
- Ouvrir console navigateur (F12)
- Vérifier WebSocket connecté
- Vérifier backend démarré sur port 3000

### ESP8266 ne publie pas sur MQTT
- Vérifier WiFi SSID/password dans code Arduino
- Vérifier adresse broker MQTT
- Ouvrir Serial Monitor pour voir logs

### Raspberry Pi caméra non détectée
```bash
# Tester Picamera2
libcamera-hello

# Tester webcam USB
ls /dev/video*
```

### InfluxDB ne démarre pas
```bash
# Vérifier logs Docker
docker logs iot_influxdb

# Vérifier port libre
netstat -an | grep 8086
```

## 📁 Structure Complète du Projet

```
Projet_IOT/
├── esp8266_controller/
│   └── esp8266_controller.ino
│
├── digital-twin-backend/
│   ├── server.js
│   ├── mqtt-handler.js
│   ├── websocket-handler.js
│   ├── influxdb-handler.js
│   ├── routes/
│   │   ├── state.js
│   │   ├── history.js
│   │   └── control.js
│   ├── package.json
│   ├── .env
│   ├── Dockerfile
│   └── logs/
│
├── digital-twin-frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Scene3D.jsx
│   │   │   ├── SensorCard.jsx
│   │   │   ├── MotorControl.jsx
│   │   │   ├── LEDIndicator.jsx
│   │   │   ├── CameraFeed.jsx
│   │   │   ├── WeightGauge.jsx
│   │   │   ├── HistoryChart.jsx
│   │   │   └── LogViewer.jsx
│   │   ├── hooks/
│   │   │   └── useWebSocket.js
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   ├── Dockerfile
│   ├── nginx.conf
│   └── index.html
│
├── mosquitto/
│   ├── config/
│   │   └── mosquitto.conf
│   ├── data/
│   └── log/
│
├── main.py                      # Raspberry Pi
├── flacon_checker.py
├── requirements.txt
├── docker-compose.yml
├── README.md
├── README_DIGITAL_TWIN.md       # Ce fichier
└── MQTT-ARCHITECTURE.md
```

## 🔒 Sécurité

**⚠️ IMPORTANT**: Cette configuration est pour développement/démo.

**Pour production**:
- ✅ Activer authentification MQTT
- ✅ Utiliser HTTPS/WSS
- ✅ Sécuriser InfluxDB avec authentification
- ✅ Ajouter firewall rules
- ✅ Changer tous les mots de passe par défaut
- ✅ Utiliser secrets management (Docker secrets, etc.)

## 📝 Licence

MIT

## 👥 Auteurs

Projet IoT - ICAM 2026

## 🙏 Remerciements

Technologies utilisées:
- React + Three.js (frontend)
- Node.js + Express + Socket.io (backend)
- MQTT (Mosquitto)
- InfluxDB
- YOLO (détection objets)
- Docker
