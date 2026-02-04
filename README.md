# Système de Contrôle Qualité Automatisé - Flacons

## Vue d'ensemble
Système IoT de contrôle qualité pour ligne de production de flacons, utilisant vision par ordinateur et capteurs.

---

## Architecture du système

```
[Bouteille arrive] 
      ↓
[Capteur Ultrason HC-SR04] ← ESP8266
      ↓ (détection)
[Publication MQTT: "bouteille détectée"]
      ↓
[Raspberry Pi + Caméra] ← Reçoit trigger MQTT
      ↓
[Capture + Analyse IA]
  - YOLO: Détection bouchon
  - OpenCV: Niveau de liquide
      ↓
[Publication MQTT: Résultat JSON]
      ↓
[ESP8266 reçoit résultat]
      ↓
[Action: OK → Continuer | REJET → Alarme]
```

---

## Étapes du processus

### 1️⃣ Détection bouteille (ESP8266 + Ultrason)
- **Capteur:** HC-SR04 (ultrason)
- **Rôle:** Détecter l'arrivée d'une bouteille sur la ligne
- **Seuil:** Distance < 10cm = bouteille présente
- **Action:** Publier sur MQTT `iot/bottle/trigger`

### 2️⃣ Capture image (Raspberry Pi + Caméra)
- **Hardware:** Raspberry Pi + Picamera2 (ou webcam)
- **Déclenchement:** Message MQTT reçu
- **Action:** Capture photo haute résolution

### 3️⃣ Analyse bouchon (YOLO)
- **Technologie:** YOLOv11 - Deep Learning
- **Vérifications:**
  - ✅ Bouchon présent
  - ✅ Bouchon bien positionné (hauteur correcte)
  - ✅ Forme conforme

### 4️⃣ Analyse niveau liquide (OpenCV)
- **Technologie:** Traitement d'image classique
- **Vérifications:**
  - ✅ Niveau entre 80% et 105%
  - ✅ Pas de débordement
  - ✅ Remplissage suffisant

### 5️⃣ Décision finale
- **Statut:** `OK` ou `REJET`
- **Sauvegarde:** Image horodatée dans `./output/`
- **Publication:** Résultat JSON sur MQTT

### 6️⃣ Action (ESP8266)
- **Si OK:** LED verte + continuer ligne
- **Si REJET:** LED rouge + alarme + arrêt éventuel

---

## Configuration matérielle

### ESP8266 (Détection)
```
HC-SR04 → ESP8266
VCC     → 5V
GND     → GND
TRIG    → D1 (GPIO5)
ECHO    → D2 (GPIO4)
```

### Raspberry Pi (Analyse)
- **Caméra:** Picamera2 (module officiel) ou webcam USB
- **OS:** Raspberry Pi OS
- **Connexion:** WiFi ou Ethernet
- **Alimentation:** 5V 3A minimum

---

## Installation

### Sur Raspberry Pi
```bash
git clone <votre-repo>
cd Projet_IOT

# Créer environnement virtuel
python -m venv venv
source venv/bin/activate

# Installer dépendances
pip install -r requirements.txt

# Lancer mode MQTT
python flacon_checker.py --mqtt --headless
```

### Sur ESP8266
1. Installer Arduino IDE
2. Ajouter carte ESP8266 (Boards Manager)
3. Installer librairies:
   - `PubSubClient` (MQTT)
   - `ESP8266WiFi`
4. Flasher le code [esp8266-sensor.ino](esp8266-sensor.ino)

---

## Topics MQTT

### 🔵 Déclenchement (ESP8266 → Raspberry Pi)
**Topic:** `iot/bottle/trigger`
```json
{
  "action": "check",
  "sensor": "ultrasonic",
  "distance_cm": 5.2,
  "timestamp": 1234567890
}
```

### 🟢 Résultat (Raspberry Pi → ESP8266)
**Topic:** `iot/bottle/result`
```json
{
  "timestamp": "20260119_153045",
  "status": "OK",
  "fill_percent": 85.3,
  "cap_ok": true,
  "image_path": "./output/20260119_153045_OK.jpg"
}
```

---

## Utilisation

### Mode MQTT (Production)
```bash
# Raspberry Pi attend les triggers
python flacon_checker.py --mqtt --headless

# Personnaliser broker
python flacon_checker.py --mqtt --mqtt-broker 192.168.1.100 --mqtt-port 1883
```

### Mode Demo (Développement)
```bash
# Test simple avec webcam
python flacon_checker.py --demo

# Test continu
python flacon_checker.py --continuous --interval 2
```

### Scripts rapides (Windows)
- [mqtt-mode.bat](mqtt-mode.bat) → Mode MQTT production
- [voir-direct.bat](voir-direct.bat) → Test visuel simple
- [live.bat](live.bat) → Mode continu visuel

---

## Calibration

### Ajuster les seuils dans [flacon_checker.py](flacon_checker.py):
```python
MIN_FILL_PERCENT = 80      # Niveau minimum acceptable
MAX_FILL_PERCENT = 105     # Niveau maximum acceptable
BOTTLE_HEIGHT_PX = 800     # Hauteur flacon en pixels
CAP_HEIGHT_PX = 100        # Hauteur bouchon en pixels
```

### Tester visuellement:
```bash
python flacon_checker.py --demo
```
L'interface affiche les valeurs détectées en temps réel.

---

## Broker MQTT

### Option 1: Mosquitto (recommandé)
```bash
# Linux/Raspberry Pi
sudo apt install mosquitto mosquitto-clients
sudo systemctl start mosquitto

# Windows
# Télécharger: https://mosquitto.org/download/
```

### Option 2: Cloud MQTT
- HiveMQ Cloud (gratuit)
- CloudMQTT
- AWS IoT Core

---

## Tests

### Tester MQTT localement
```bash
# Terminal 1: Lancer le système
python flacon_checker.py --mqtt --headless

# Terminal 2: Simuler ESP8266
mosquitto_pub -h localhost -t iot/bottle/trigger -m '{"action":"check"}'

# Terminal 3: Écouter résultats
mosquitto_sub -h localhost -t iot/bottle/result
```

---

## Dépendances Python
```
opencv-python     # Traitement d'image
numpy            # Calculs numériques
ultralytics      # YOLOv11
paho-mqtt        # Communication MQTT
picamera2        # Caméra Raspberry Pi (optionnel)
Pillow           # Manipulation images
```

---

## Structure du projet
```
Projet_IOT/
├── flacon_checker.py       # Script principal
├── requirements.txt        # Dépendances Python
├── README.md              # Ce fichier
├── MQTT-ARCHITECTURE.md   # Détails architecture MQTT
├── output/                # Images capturées
│   ├── 20260119_153045_OK.jpg
│   └── 20260119_153102_REJET.jpg
├── esp8266-sensor.ino     # Code ESP8266 (à créer)
├── mqtt-mode.bat          # Launcher Windows MQTT
├── voir-direct.bat        # Launcher test visuel
└── live.bat               # Launcher mode continu
```

---

## Paramètres configurables

| Argument | Description | Défaut |
|----------|-------------|--------|
| `--mqtt` | Mode MQTT avec déclenchement | - |
| `--mqtt-broker` | Adresse broker MQTT | localhost |
| `--mqtt-port` | Port broker MQTT | 1883 |
| `--mqtt-topic-trigger` | Topic de déclenchement | iot/bottle/trigger |
| `--mqtt-topic-result` | Topic de résultat | iot/bottle/result |
| `--demo` | Mode démo webcam | - |
| `--continuous` | Mode continu | - |
| `--interval` | Intervalle entre captures (s) | 5 |
| `--headless` | Sans affichage (prod) | - |
| `--output-dir` | Dossier images | ./output |

---

## Résolution des problèmes

### Caméra non détectée
```bash
# Vérifier caméra
libcamera-hello

# Si webcam USB
ls /dev/video*
```

### MQTT ne se connecte pas
```bash
# Tester broker
mosquitto_pub -h <broker-ip> -t test -m "hello"

# Vérifier firewall
sudo ufw allow 1883
```

### Détection YOLO imprécise
- ⚙️ Ajuster `conf` dans le code (actuellement 0.3)
- 🎯 Entraîner modèle custom avec vos bouteilles
- 💡 Améliorer éclairage de la ligne

---

## Améliorations futures

- [ ] Entraîner YOLO custom sur vos bouteilles spécifiques
- [ ] Dashboard web temps réel (Flask/FastAPI)
- [ ] Base de données pour historique (SQLite/PostgreSQL)
- [ ] Alertes email/SMS en cas de taux de rejet élevé
- [ ] API REST pour intégration ERP
- [ ] Support multi-caméras
- [ ] Détection défauts étiquette
- [ ] Reconnaissance code-barres

---

## Auteurs
Projet IoT - ICAM 2026

## Licence
MIT
