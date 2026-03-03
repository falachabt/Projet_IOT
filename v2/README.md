# Bottle Checker V2 — Documentation

## 🎯 Objectif

Système de contrôle qualité de bouteilles par vision artificielle.  
Détecte automatiquement :
- **Présence d'une bouteille** (YOLO préentraîné)
- **Présence d'un bouchon** (analyse heuristique zone haute)
- **Présence d'une étiquette** (analyse heuristique zone corps)

Retourne un **JSON structuré** + **image annotée** :

```json
{
  "timestamp": "2026-02-11 14:30:00",
  "bottle":  { "detected": true,  "confidence": 0.92 },
  "cap":     { "detected": true,  "confidence": 0.75 },
  "label":   { "detected": false, "confidence": 0.30 },
  "status":  "MISSING_LABEL",
  "image_path": "./v2/output/20260211_143000_MISSING_LABEL.jpg",
  "elapsed_ms": 245.3
}
```

## 📁 Structure

```
v2/
├── __init__.py        # Package
├── __main__.py        # Point d'entrée (python -m v2 <mode>)
├── config.py          # Configuration centralisée
├── camera.py          # Abstraction caméra (Webcam / PiCamera2)
├── detector.py        # Moteur de détection (YOLO + heuristiques OpenCV)
├── app_web.py         # Interface Web (Flask + streaming MJPEG)
├── app_tkinter.py     # Interface desktop Tkinter
├── app_mqtt.py        # Mode MQTT (headless, trigger → résultat)
├── requirements.txt   # Dépendances Python
├── templates/
│   └── index.html     # Page web
└── output/            # Images annotées sauvegardées
```

## 🚀 Installation

```bash
# Depuis la racine du projet
cd Projet_IOT

# Installer les dépendances
pip install -r v2/requirements.txt
```

## 🖥️ Lancement

### 1. Interface Web (recommandé)
```bash
python -m v2 web
```
→ Ouvrez **http://localhost:5000** dans le navigateur  
→ Streaming temps réel + bouton d'analyse + résultats en direct

### 2. Interface Tkinter (desktop)
```bash
python -m v2 tkinter
```
→ Fenêtre desktop avec vidéo live, bouton d'analyse, résultats, compteurs

### 3. Mode MQTT (headless, utilisé avec Arduino/ESP)
```bash
python -m v2 mqtt
```
→ Attend un message sur `iot/bottle/trigger`  
→ Analyse et publie le résultat JSON sur `iot/bottle/result`

Options :
```bash
python -m v2 mqtt --broker 192.168.1.100 --port 1883
python -m v2 mqtt --topic-trigger "mon/topic" --topic-result "mon/resultat"
```

### 4. Analyse unique (one-shot)
```bash
python -m v2 analyze
```
→ Capture une image, analyse, affiche le JSON et quitte

## 🔧 Configuration

Modifiez `v2/config.py` pour adapter :

| Paramètre | Description | Défaut |
|-----------|-------------|--------|
| `YOLO_MODEL_PATH` | Chemin vers le modèle YOLO | `yolo11n.pt` |
| `YOLO_CONFIDENCE` | Seuil de confiance | `0.40` |
| `CAMERA_INDEX` | Index webcam | `0` |
| `MQTT_BROKER` | Adresse broker MQTT | `172.20.10.3` |
| `MQTT_PORT` | Port MQTT | `1883` |
| `MQTT_TOPIC_TRIGGER` | Topic déclenchement | `iot/bottle/trigger` |
| `MQTT_TOPIC_RESULT` | Topic résultat | `iot/bottle/result` |
| `WEB_PORT` | Port serveur Flask | `5000` |

## 📡 Architecture MQTT

```
┌──────────────┐    trigger     ┌─────────────────┐    result     ┌──────────────┐
│  Arduino/ESP │ ──────────────→│  Raspberry Pi   │──────────────→│  Arduino/ESP │
│              │  iot/bottle/   │  (app_mqtt.py)  │  iot/bottle/  │              │
│  Capteur     │   trigger      │  Caméra + YOLO  │   result      │  LED/Moteur  │
└──────────────┘                └─────────────────┘               └──────────────┘
```

### Format du message trigger
```json
{"action": "check"}
```
Ou n'importe quel message texte — tout message reçu déclenche l'analyse.

### Format de la réponse
```json
{
  "timestamp": "2026-02-11 14:30:00",
  "bottle":  { "detected": true, "confidence": 0.92 },
  "cap":     { "detected": true, "confidence": 0.75 },
  "label":   { "detected": true, "confidence": 0.65 },
  "status":  "OK",
  "trigger": "{\"action\": \"check\"}",
  "image_path": "./v2/output/20260211_143000_OK.jpg",
  "elapsed_ms": 245.3
}
```

### Statuts possibles
| Statut | Signification |
|--------|---------------|
| `OK` | Bouteille + bouchon + étiquette présents |
| `MISSING_BOTTLE` | Aucune bouteille détectée |
| `MISSING_CAP` | Bouteille sans bouchon |
| `MISSING_LABEL` | Bouteille sans étiquette |
| `INCOMPLETE` | Ni bouchon ni étiquette |

## 🧪 Test rapide MQTT (avec Mosquitto)

```bash
# Terminal 1 — Lancer le checker
python -m v2 mqtt --broker localhost

# Terminal 2 — Simuler un trigger
mosquitto_pub -h localhost -t iot/bottle/trigger -m '{"action":"check"}'

# Terminal 3 — Écouter les résultats
mosquitto_sub -h localhost -t iot/bottle/result
```

## 📝 Notes techniques

- **Détection bouteille** : utilise YOLO avec la classe `bottle` du dataset COCO
- **Détection bouchon** : analyse de la zone haute (18%) de la bouteille — densité d'arêtes, contours, variance couleur
- **Détection étiquette** : analyse du corps (25-85%) — rectangles, texture Laplacien, saturation couleur
- Les seuils sont ajustables dans `config.py` pour adapter à votre environnement (éclairage, type de bouteille)
- Compatible **Windows** (webcam) et **Raspberry Pi** (PiCamera2)
