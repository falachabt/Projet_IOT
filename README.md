# Bottle Checker — Contrôle Qualité par Vision Artificielle

Système de contrôle qualité de bouteilles par vision artificielle, tournant sur **Raspberry Pi** avec caméra.  
Détecte automatiquement la présence d'une bouteille, d'un bouchon et d'une étiquette via YOLO + analyse OpenCV.

---

## Structure du projet

```
Projet_IOT/
├── __main__.py        # Point d'entrée principal
├── config.py          # Configuration centralisée
├── camera.py          # Abstraction caméra (Webcam / PiCamera2)
├── detector.py        # Moteur de détection (YOLO + heuristiques OpenCV)
├── app_web.py         # Interface Web (Flask + streaming MJPEG)
├── app_tkinter.py     # Interface desktop Tkinter
├── app_mqtt.py        # Mode MQTT headless (trigger → résultat)
├── templates/
│   └── index.html     # Page web
├── requirements.txt   # Dépendances Python
├── yolo11n.pt         # Modèle YOLO préentraîné
└── archive/           # Anciens fichiers
```

---

## Installation

```bash
# Cloner le projet
git clone https://github.com/falachabt/Projet_IOT.git
cd Projet_IOT

# Créer un environnement virtuel (obligatoire sur Raspberry Pi OS)
python3 -m venv venv --system-site-packages
source venv/bin/activate          # Linux / Raspberry Pi
# .\venv\Scripts\Activate.ps1    # Windows

# Installer les dépendances
pip install -r requirements.txt
```

> `--system-site-packages` permet d'hériter de `picamera2` déjà installé en système sur le Raspberry Pi.

---

## Lancement

### Mode MQTT — headless (Raspberry Pi, production)
```bash
python __main__.py mqtt
```
Attend un message sur `esp8266/capteur/distance`, analyse, publie le résultat JSON sur `rapsberry/camera/resultat`.

Options :
```bash
python __main__.py mqtt --broker 172.20.10.3 --port 1883
python __main__.py mqtt --topic-trigger "mon/topic" --topic-result "mon/resultat"
```

### Interface Web (recommandé pour le debug / Raspberry Pi)
```bash
python __main__.py web
```
Ouvrir **http://\<ip\>:5000** — streaming temps réel + bouton d'analyse + résultats.  
**Écoute aussi les triggers MQTT** : chaque message sur `esp8266/capteur/distance` déclenche une analyse automatique visible en direct dans le navigateur.

### Interface Tkinter (desktop Windows)
```bash
python __main__.py tkinter
```
**Écoute aussi les triggers MQTT** : l'analyse se déclenche automatiquement et le résultat est publié sur `rapsberry/camera/resultat`.

### Analyse unique (one-shot)
```bash
python __main__.py analyze
```
Capture une image, analyse et affiche le JSON puis quitte.

---

## Configuration

Modifier `config.py` :

| Paramètre | Description | Valeur actuelle |
|-----------|-------------|-----------------|
| `YOLO_MODEL_PATH` | Chemin vers le modèle YOLO | `yolo11n.pt` |
| `YOLO_CONFIDENCE` | Seuil de confiance détection | `0.40` |
| `CAMERA_INDEX` | Index webcam (si non PiCamera) | `0` |
| `MQTT_BROKER` | IP du broker MQTT | `172.20.10.3` |
| `MQTT_PORT` | Port MQTT | `1883` |
| `MQTT_TOPIC_TRIGGER` | Topic déclenchement (ESP → Pi) | `esp8266/capteur/distance` |
| `MQTT_TOPIC_RESULT` | Topic résultat (Pi → ESP) | `rapsberry/camera/resultat` |
| `WEB_PORT` | Port serveur Flask | `5000` |

---

## Architecture MQTT

```
┌──────────────┐  esp8266/capteur/distance   ┌─────────────────┐  rapsberry/camera/resultat  ┌──────────────┐
│   ESP8266    │ ───────────────────────────▶│  Raspberry Pi   │ ──────────────────────────▶│   ESP8266    │
│  Capteur     │                             │  Caméra + YOLO  │                             │  LED/Moteur  │
│  ultrason    │                             │  (app_mqtt.py)  │                             │              │
└──────────────┘                             └────────┬────────┘                             └──────────────┘
                                                      │
                                               Broker MQTT
                                             Eclipse Mosquitto
                                              172.20.10.3:1883
```

---

## Format de la réponse JSON

```json
{
  "timestamp":  "2026-03-03 14:30:00",
  "bottle":     { "detected": true,  "confidence": 0.92 },
  "cap":        { "detected": true,  "confidence": 0.75 },
  "label":      { "detected": false, "confidence": 0.30 },
  "status":     "MISSING_LABEL",
  "image_path": "./output/20260303_143000_MISSING_LABEL.jpg",
  "elapsed_ms": 245.3
}
```

| Statut | Signification |
|--------|---------------|
| `OK` | Bouteille + bouchon + étiquette présents |
| `MISSING_BOTTLE` | Aucune bouteille détectée |
| `MISSING_CAP` | Bouteille sans bouchon |
| `MISSING_LABEL` | Bouteille sans étiquette |
| `INCOMPLETE` | Ni bouchon ni étiquette |

---

## Test rapide MQTT

```bash
# Terminal 1 — Lancer le checker
python __main__.py mqtt --broker localhost

# Terminal 2 — Simuler un déclenchement
mosquitto_pub -h localhost -t esp8266/capteur/distance -m "1"

# Terminal 3 — Écouter les résultats
mosquitto_sub -h localhost -t rapsberry/camera/resultat
```

---

## Compatibilité

| Plateforme | Caméra | Statut |
|------------|--------|--------|
| Raspberry Pi OS | Module caméra Pi (PiCamera2) | Recommandé |
| Raspberry Pi OS | Webcam USB | Fonctionne |
| Windows | Webcam | Fonctionne (Tkinter / Web) |
