# 📡 Guide ESP8266 - Topics MQTT & Câblage

## 🎯 Vue d'Ensemble

Votre ESP8266 communique avec le jumeau numérique via MQTT. Voici **TOUS** les topics nécessaires.

## 📊 Architecture de Communication

```
┌──────────────┐           MQTT            ┌───────────────────┐
│   ESP8266    │  ◄──────────────────────► │ Jumeau Numérique  │
│              │                            │   (Backend)       │
│ - Ultrason   │  Publications →           │                   │
│ - Poids      │  Souscriptions ←          │ - Dashboard       │
│ - Moteurs    │                            │ - Vue 3D          │
│ - LEDs       │                            │ - API REST        │
│ - Urgence    │                            │                   │
└──────────────┘                            └───────────────────┘
```

## 📡 TOPICS MQTT - Liste Complète

### 🟢 PUBLICATION (ESP8266 → Jumeau Numérique)

#### 1. **Capteur Ultrason - Détection Flacon**
```
Topic: esp8266/ultrason/distance
Format: JSON
```
```json
{
  "distance": 5.2,
  "flacon_detecte": true,
  "timestamp": 123456
}
```

**Fréquence**: Toutes les 300ms
**Utilité**: Déclenche le processus de contrôle

---

#### 2. **Capteur de Poids**
```
Topic: esp8266/poids/valeur
Format: JSON
```
```json
{
  "poids_g": 350.5,
  "timestamp": 123456
}
```

**Fréquence**: Toutes les 1000ms (1 seconde)
**Utilité**: Vérifier le remplissage du flacon

---

#### 3. **État Moteurs**
```
Topic: esp8266/moteur/etat
Format: JSON
```
```json
{
  "etat": "ON",
  "vitesse": 80,
  "timestamp": 123456
}
```

**Valeurs possibles**:
- `etat`: "ON" ou "OFF"
- `vitesse`: 0-100 (pourcentage)

**Fréquence**: Toutes les 2 secondes + lors de changement d'état
**Utilité**: Visualiser l'état du convoyeur en temps réel

---

#### 4. **État LEDs**
```
Topic: esp8266/led/etat
Format: JSON
```
```json
{
  "verte": false,
  "rouge": false,
  "orange": true
}
```

**Valeurs**: `true` (allumée) ou `false` (éteinte)

**Signification**:
- 🟢 **Verte**: Flacon OK
- 🔴 **Rouge**: Flacon KO/Rejeté
- 🟠 **Orange**: Analyse en cours

**Fréquence**: Lors de changement d'état
**Utilité**: Synchroniser les LEDs physiques avec le jumeau numérique 3D

---

#### 5. **Bouton Arrêt d'Urgence**
```
Topic: esp8266/urgence/etat
Format: JSON
```
```json
{
  "active": false,
  "timestamp": 123456
}
```

**Valeurs**:
- `active`: `true` (urgence activée) ou `false` (normale)

**Fréquence**: Lors de changement d'état
**Utilité**: Arrêt immédiat du système

---

### 🔴 SOUSCRIPTION (Jumeau Numérique → ESP8266)

#### 1. **Résultat Analyse Caméra**
```
Topic: esp8266/bouteille/etat
Format: Texte simple
```

**Messages possibles**:
- `OK` - Flacon validé
- `KO` - Flacon rejeté
- `ERREUR` - Problème détection

**Source**: Script Python `main.py` du Raspberry Pi
**Utilité**: ESP8266 allume LED verte (OK) ou rouge (KO)

---

#### 2. **Commande Moteur depuis Dashboard**
```
Topic: esp8266/commande/moteur
Format: JSON
```
```json
{
  "action": "START",
  "vitesse": 80
}
```

**Valeurs `action`**:
- `START` - Démarrer moteurs
- `STOP` - Arrêter moteurs

**Valeurs `vitesse`**: 0-100 (pourcentage)

**Source**: Interface web du jumeau numérique
**Utilité**: Contrôler les moteurs à distance

---

#### 3. **Commande LED depuis Dashboard**
```
Topic: esp8266/commande/led
Format: JSON
```
```json
{
  "led": "verte",
  "etat": true
}
```

**Valeurs `led`**:
- `verte`
- `rouge`
- `orange`

**Valeurs `etat`**: `true` (allumer) ou `false` (éteindre)

**Source**: Interface web du jumeau numérique
**Utilité**: Contrôler les LEDs à distance

---

## 🔌 CÂBLAGE COMPLET ESP8266

### 📦 Matériel Nécessaire

| Composant | Quantité | Notes |
|-----------|----------|-------|
| ESP8266 (NodeMCU) | 1 | Version avec USB intégré |
| HC-SR04 (Ultrason) | 1 | Alimentation 5V |
| HX711 + Balance | 1 | Capteur de poids |
| L298N | 1 | Driver moteurs |
| Moteurs DC 6V | 2 | Pour convoyeur |
| LEDs (V, R, O) | 3 | Avec résistances 220Ω |
| Bouton poussoir | 1 | NO (Normalement Ouvert) |
| Résistance 10kΩ | 1 | Pull-down bouton |
| Breadboard | 1 | Pour prototypage |
| Câbles Dupont | 20+ | M-M, M-F |
| Alimentation 5V/2A | 1 | Pour ESP8266 + capteurs |
| Alimentation 12V | 1 | Pour moteurs (si nécessaire) |

### 📌 Schéma de Connexion

```
ESP8266 (NodeMCU)
┌────────────────────────────────────┐
│                                    │
│  3.3V ───┬─→ HX711 VCC            │
│          └─→ Résistance Pull-down  │
│                                    │
│  5V (VU) ──→ HC-SR04 VCC          │
│                                    │
│  GND ────┬─→ Tous les GND         │
│          └─→ LEDs cathodes         │
│                                    │
│  D1 (GPIO5)  ──→ HC-SR04 TRIG     │
│  D2 (GPIO4)  ──→ HC-SR04 ECHO     │
│                                    │
│  D5 (GPIO14) ──→ HX711 DOUT       │
│  D6 (GPIO12) ──→ HX711 SCK        │
│                                    │
│  D7 (GPIO13) ──→ L298N IN1        │
│  D8 (GPIO15) ──→ L298N IN2        │
│  D3 (GPIO0)  ──→ L298N IN3        │
│  D4 (GPIO2)  ──→ L298N IN4        │
│                                    │
│  D0 (GPIO16) ──→ LED Verte (+)    │
│  TX (GPIO1)  ──→ LED Rouge (+)    │
│  RX (GPIO3)  ──→ LED Orange (+)   │
│                                    │
│  A0 ─────────→ Bouton (via R 10k) │
│                                    │
└────────────────────────────────────┘
```

### ⚡ Câblage Détaillé

#### HC-SR04 (Ultrason)
```
HC-SR04      →  ESP8266
─────────────────────────
VCC          →  5V (VU)
GND          →  GND
TRIG         →  D1 (GPIO5)
ECHO         →  D2 (GPIO4)
```

#### HX711 (Capteur Poids)
```
HX711        →  ESP8266
─────────────────────────
VCC          →  3.3V
GND          →  GND
DOUT (DT)    →  D5 (GPIO14)
SCK (SCK)    →  D6 (GPIO12)

Cellule de Charge → HX711
E+ (Rouge)    → E+
E- (Noir)     → E-
A+ (Vert)     → A+
A- (Blanc)    → A-
```

#### L298N (Moteurs)
```
L298N        →  ESP8266          L298N        →  Moteur
────────────────────────         ──────────────────────────
IN1          →  D7 (GPIO13)      OUT1, OUT2   →  Moteur 1
IN2          →  D8 (GPIO15)      OUT3, OUT4   →  Moteur 2
IN3          →  D3 (GPIO0)
IN4          →  D4 (GPIO2)       12V          →  Alim 12V
                                  GND          →  GND commun
VCC (5V)     →  Jumper ON        5V           →  Peut alimenter ESP
GND          →  GND ESP
```

#### LEDs
```
LED          →  Résistance 220Ω  →  ESP8266     →  GND
───────────────────────────────────────────────────────
LED Verte +  →  R 220Ω          →  D0 (GPIO16) →  GND
LED Rouge +  →  R 220Ω          →  TX (GPIO1)  →  GND
LED Orange + →  R 220Ω          →  RX (GPIO3)  →  GND
```

**⚠️ ATTENTION**: L'utilisation des pins TX et RX désactive le Serial Monitor!

#### Bouton Arrêt d'Urgence
```
Bouton       →  ESP8266
──────────────────────────
PIN 1        →  3.3V
PIN 2        →  A0 ───┬─→ Résistance 10kΩ → GND
                      └─→ Lecture analogique
```

**Alternative (digital)**:
```
Bouton NO    →  D0 (via résistance pullup interne)
PIN 1        →  D0
PIN 2        →  GND
```

---

## 🔧 Configuration du Code

### 1. Ouvrir le fichier `.ino`
```
esp8266_iot_complet.ino
```

### 2. Modifier les paramètres WiFi
```cpp
const char* WIFI_SSID = "VotreSSID";
const char* WIFI_PASSWORD = "VotreMotDePasse";
```

### 3. Modifier l'adresse MQTT
```cpp
const char* MQTT_BROKER = "192.168.1.100";  // IP de votre PC/Raspberry
```

**Comment trouver l'IP?**

Sur PC (Windows):
```cmd
ipconfig
```
Chercher "Adresse IPv4"

Sur Raspberry Pi:
```bash
hostname -I
```

### 4. Calibrer le capteur de poids

Dans le code:
```cpp
#define CALIBRATION_POIDS -7050.0  // À ajuster
```

**Procédure de calibration**:
1. Placer le capteur sans poids
2. Lancer le code → il fait `tare()` automatiquement
3. Placer un poids connu (ex: 500g)
4. Ajuster `CALIBRATION_POIDS` jusqu'à obtenir 500g dans le Serial Monitor

---

## 📚 Bibliothèques Arduino Nécessaires

### Installation via Arduino IDE

**Menu**: `Croquis → Inclure une bibliothèque → Gérer les bibliothèques`

Chercher et installer:

1. **ESP8266WiFi** (intégré avec board ESP8266)
2. **PubSubClient** par Nick O'Leary
   Version: 2.8+
3. **ArduinoJson** par Benoit Blanchon
   Version: 6.x (PAS 7.x!)
4. **HX711** par Bogdan Necula
   Version: 0.7.5+

### Ajout de la carte ESP8266

**Menu**: `Fichier → Préférences`

**URL de gestionnaire de cartes supplémentaires**:
```
http://arduino.esp8266.com/stable/package_esp8266com_index.json
```

**Menu**: `Outils → Type de carte → Gestionnaire de cartes`

Chercher: **ESP8266** par ESP8266 Community
Installer la dernière version

**Sélectionner**: `NodeMCU 1.0 (ESP-12E Module)`

---

## 🧪 Tests

### Test 1: Connexion WiFi
```
✅ WiFi OK - IP: 192.168.1.XXX
```

### Test 2: Connexion MQTT
```
📡 MQTT... ✅
```

### Test 3: Publier les topics
Sur votre PC, installer `mosquitto-clients`:
```bash
# Windows: Télécharger depuis mosquitto.org
# Linux: apt install mosquitto-clients

# Écouter tous les topics ESP8266
mosquitto_sub -h localhost -t "esp8266/#" -v
```

Vous devez voir:
```
esp8266/ultrason/distance {"distance":999.0,"flacon_detecte":false,"timestamp":...}
esp8266/poids/valeur {"poids_g":0.0,"timestamp":...}
esp8266/moteur/etat {"etat":"OFF","vitesse":0,"timestamp":...}
esp8266/led/etat {"verte":false,"rouge":false,"orange":false}
esp8266/urgence/etat {"active":false,"timestamp":...}
```

### Test 4: Commandes depuis PC
```bash
# Démarrer moteur
mosquitto_pub -h localhost -t esp8266/commande/moteur -m '{"action":"START","vitesse":80}'

# Allumer LED verte
mosquitto_pub -h localhost -t esp8266/commande/led -m '{"led":"verte","etat":true}'

# Simuler résultat caméra
mosquitto_pub -h localhost -t esp8266/bouteille/etat -m 'OK'
```

---

## 🌐 Interaction avec le Jumeau Numérique

### Le Jumeau Numérique va automatiquement:

✅ **Afficher** toutes les données ESP8266 en temps réel
✅ **Visualiser** l'état en 3D (moteurs, LEDs, flacon)
✅ **Permettre le contrôle** via l'interface web
✅ **Enregistrer** l'historique dans InfluxDB
✅ **Afficher** les statistiques (taux OK/KO)

### Aucune configuration supplémentaire requise!

Le backend écoute déjà tous les topics `esp8266/#`.

---

## ❓ FAQ

**Q: Les LEDs TX/RX ne fonctionnent pas?**
R: Normal si Serial est actif. Utilisez D0 à la place, ou désactivez Serial.

**Q: Le poids est instable?**
R: Ajuster `CALIBRATION_POIDS` et s'assurer que la balance est stable.

**Q: MQTT ne se connecte pas?**
R: Vérifier l'IP du broker, vérifier que le broker est démarré.

**Q: Les moteurs ne tournent pas?**
R: Vérifier l'alimentation 12V du L298N et les connexions.

**Q: Le capteur ultrason retourne toujours 999?**
R: Vérifier les connexions TRIG/ECHO, et que le capteur a 5V.

---

## 📖 Documentation Complète

- [README_DIGITAL_TWIN.md](README_DIGITAL_TWIN.md) - Guide complet du jumeau numérique
- [GUIDE_RASPBERRY_PI.md](GUIDE_RASPBERRY_PI.md) - Déploiement sur Raspberry Pi
- [DEMARRAGE_RAPIDE.md](DEMARRAGE_RAPIDE.md) - Démarrage rapide

---

**🎉 Votre ESP8266 est prêt à communiquer avec le jumeau numérique!**
