# Configuration ESP8266 - Guide complet

## 📋 Table des matières
1. [Configuration WiFi et MQTT](#configuration-wifi-et-mqtt)
2. [Installation des bibliothèques](#installation-des-bibliothèques)
3. [Câblage matériel](#câblage-matériel)
4. [Calibration de la balance](#calibration-de-la-balance)
5. [Topics MQTT publiés](#topics-mqtt-publiés)
6. [Topics MQTT souscrits](#topics-mqtt-souscrits)
7. [Téléversement du code](#téléversement-du-code)
8. [Test et dépannage](#test-et-dépannage)

---

## 🔧 Configuration WiFi et MQTT

### Fichier à modifier: `esp8266_programme_complet.ino`

Ouvrez le fichier et modifiez les lignes suivantes (lignes 15-25):

```cpp
// Configuration WiFi
#define WIFI_SSID "VOTRE_SSID"              // ← Remplacez par le nom de votre WiFi
#define WIFI_PASSWORD "VOTRE_MOT_DE_PASSE"  // ← Remplacez par votre mot de passe WiFi

// Configuration MQTT Broker
#define MQTT_BROKER "192.168.1.100"  // ← Remplacez par l'IP de votre Raspberry Pi
#define MQTT_PORT 1883               // ← Port MQTT (1883 par défaut)
#define MQTT_USER ""                 // ← Utilisateur MQTT (laisser vide si pas d'auth)
#define MQTT_PASSWORD ""             // ← Mot de passe MQTT (laisser vide si pas d'auth)
#define MQTT_CLIENT_ID "ESP8266_IOT" // ← ID unique du client (ne pas modifier)
```

### Exemples de configuration

#### Configuration sans authentification MQTT (recommandé pour débuter)
```cpp
#define WIFI_SSID "MonWiFi"
#define WIFI_PASSWORD "MonMotDePasse123"
#define MQTT_BROKER "192.168.1.50"
#define MQTT_PORT 1883
#define MQTT_USER ""
#define MQTT_PASSWORD ""
```

#### Configuration avec authentification MQTT
```cpp
#define WIFI_SSID "MonWiFi"
#define WIFI_PASSWORD "MonMotDePasse123"
#define MQTT_BROKER "192.168.1.50"
#define MQTT_PORT 1883
#define MQTT_USER "esp8266"
#define MQTT_PASSWORD "secure_password"
```

---

## 📚 Installation des bibliothèques

### Via Arduino IDE

1. Ouvrez **Arduino IDE**
2. Allez dans **Outils > Gérer les bibliothèques**
3. Installez les bibliothèques suivantes:

| Bibliothèque | Version | Description |
|--------------|---------|-------------|
| **ESP8266WiFi** | Incluse | Gestion WiFi pour ESP8266 |
| **PubSubClient** | 2.8+ | Client MQTT |
| **ArduinoJson** | 6.x | Gestion JSON |
| **HX711** | 0.7.5+ | Interface capteur poids |

### Commandes CLI (si vous utilisez PlatformIO)

```ini
[env:nodemcuv2]
platform = espressif8266
board = nodemcuv2
framework = arduino
lib_deps =
    knolleary/PubSubClient@^2.8
    bblanchon/ArduinoJson@^6.21.3
    bogde/HX711@^0.7.5
```

---

## 🔌 Câblage matériel

### Schéma de branchement ESP8266 (NodeMCU)

```
ESP8266 NodeMCU          Composant
================         =========

--- Capteur Ultrason HC-SR04 ---
D1 (GPIO5)      →        TRIG
D2 (GPIO4)      →        ECHO
VCC             →        VCC (5V)
GND             →        GND

--- Capteur Poids HX711 ---
D5 (GPIO14)     →        DOUT (Data)
D6 (GPIO12)     →        SCK (Clock)
VCC             →        VCC (3.3V ou 5V)
GND             →        GND

--- Moteur 1 (L298N Module) ---
D7 (GPIO13)     →        IN1
D8 (GPIO15)     →        IN2
                         OUT1 → Moteur 1+
                         OUT2 → Moteur 1-

--- Moteur 2 (L298N Module) ---
D3 (GPIO0)      →        IN3
D4 (GPIO2)      →        IN4
                         OUT3 → Moteur 2+
                         OUT4 → Moteur 2-

--- LEDs avec résistances 220Ω ---
D0 (GPIO16)     →        LED Verte Conv1 (+)
D9 (GPIO3/RXD0) →        LED Rouge Caméra (+)
D10 (GPIO1/TXD0)→        LED Rouge Poids (+)
RX (GPIO3)      →        LED Verte Conv2 (+)
                         GND → Toutes les LEDs (-)

--- Boutons ---
GPIO3           →        Bouton Marche (autre pin → GND)
GPIO1           →        Bouton Urgence (autre pin → GND)

--- Alimentation ---
VIN (5V)        →        Alimentation externe 5V
GND             →        GND commun
```

### ⚠️ Notes importantes

- **Alimentation**: Les moteurs doivent être alimentés par une source externe (pas par l'USB de l'ESP8266)
- **GND commun**: Tous les GND doivent être reliés ensemble
- **Résistances**: Utilisez des résistances de 220Ω pour chaque LED
- **Level shifter**: Le HC-SR04 fonctionne en 5V, utilisez un diviseur de tension pour ECHO si nécessaire

---

## ⚖️ Calibration de la balance

### Procédure de calibration HX711

1. **Tare (mise à zéro)**
   - Retirez tout poids de la balance
   - Envoyez la commande MQTT: `esp8266/commandes/tare`
   - Ou appuyez sur le bouton Reset

2. **Détermination du facteur de calibration**

   ```cpp
   // Dans le code, ligne 41
   #define CALIBRATION_FACTOR 2280  // ← Valeur à ajuster
   ```

3. **Méthode de calibration**:

   a. Déposez un poids connu (ex: 100g)

   b. Observez la valeur affichée dans le Serial Monitor

   c. Calculez le facteur:
   ```
   Nouveau facteur = Facteur actuel × (Poids connu / Poids affiché)
   ```

   Exemple:
   - Poids connu: 100g
   - Poids affiché: 87.5g
   - Facteur actuel: 2280
   - Nouveau facteur: 2280 × (100 / 87.5) = **2606**

4. **Application**:
   - Modifiez `CALIBRATION_FACTOR` dans le code
   - Ou envoyez via MQTT: `esp8266/commandes/calibration` avec payload `2606`

### Ajustement des seuils de poids

```cpp
// Lignes 42-43
#define POIDS_MIN 50.0   // Poids minimum acceptable (grammes)
#define POIDS_MAX 500.0  // Poids maximum acceptable (grammes)
```

---

## 📤 Topics MQTT publiés par l'ESP8266

| Topic | Fréquence | Format JSON | Description |
|-------|-----------|-------------|-------------|
| `esp8266/capteurs/distance` | 500ms | `{"distance_cm": 5.2, "objet_detecte": true, "timestamp": 12345}` | Distance ultrason et détection |
| `esp8266/capteurs/poids` | 500ms | `{"poids_grammes": 123.5, "timestamp": 12345}` | Poids mesuré |
| `esp8266/actionneurs/moteur1` | Sur changement | `{"actif": true, "timestamp": 12345}` | État moteur convoyeur 1 |
| `esp8266/actionneurs/moteur2` | Sur changement | `{"actif": true, "timestamp": 12345}` | État moteur convoyeur 2 |
| `esp8266/actionneurs/led_vert_conv` | Sur changement | `{"led_vert_conv": 1, "led_rouge_camera": 0, ...}` | États de toutes les LEDs |
| `esp8266/boutons/marche` | 500ms | `{"bouton_marche": true, "timestamp": 12345}` | État bouton démarrage |
| `esp8266/systeme/etat` | Sur changement | `{"etat_grafcet": "E1_MARCHE_CONV", "moteur1_actif": true, ...}` | État complet du système |
| `esp8266/systeme/urgence` | Sur événement | `{"urgence_active": true, "timestamp": 12345}` | Arrêt d'urgence (retained) |
| `raspberry/camera/trigger` | Sur événement | `{"timestamp": 12345, "distance": 5.2, "declencheur": "esp8266"}` | Déclenchement de l'analyse caméra |
| `esp8266/analyse/trigger_poids` | Sur événement | `{"poids": 123.5, "status": "OK", "poids_min": 50, "poids_max": 500}` | Résultat de l'analyse poids |

---

## 📥 Topics MQTT souscrits par l'ESP8266

| Topic | Format attendu | Description |
|-------|----------------|-------------|
| `raspberry/camera/resultat` | `{"status": "OK", "bouteille_detectee": true, ...}` | Résultat de l'analyse caméra |
| `esp8266/analyse/resultat_poids` | `{"status": "OK", "poids": 123.5}` | Résultat externe d'analyse poids (optionnel) |
| `esp8266/commandes/reset` | N/A | Redémarrage de l'ESP8266 |
| `esp8266/commandes/tare` | N/A | Remise à zéro de la balance |
| `esp8266/commandes/calibration` | `2606` (nombre) | Nouveau facteur de calibration |

---

## 🚀 Téléversement du code

### Via Arduino IDE

1. **Configuration de la carte**:
   - Outils > Type de carte > **NodeMCU 1.0 (ESP-12E Module)**
   - Outils > Port > Sélectionnez votre port COM
   - Outils > Upload Speed > **115200**
   - Outils > CPU Frequency > **80 MHz**
   - Outils > Flash Size > **4M (3M SPIFFS)**

2. **Téléversement**:
   - Cliquez sur le bouton **Téléverser** (→)
   - Attendez la fin de la compilation et du téléversement
   - Le message "Téléversement terminé" doit apparaître

3. **Moniteur série**:
   - Outils > Moniteur série
   - Sélectionnez **115200 baud**
   - Vous devriez voir:
     ```
     === Démarrage ESP8266 - Système IoT ===
     Connexion WiFi à: MonWiFi
     .....
     WiFi connecté!
     Adresse IP: 192.168.1.123
     Connexion au broker MQTT...Connecté!
     Souscriptions actives
     Système prêt - En attente du bouton de démarrage
     ```

---

## 🧪 Test et dépannage

### Tests de base

#### 1. Test de connexion WiFi
```
✓ Le moniteur série affiche "WiFi connecté!"
✓ Une adresse IP est affichée
✗ Si échec: Vérifiez WIFI_SSID et WIFI_PASSWORD
```

#### 2. Test de connexion MQTT
```
✓ Le moniteur série affiche "Connecté!"
✓ Message "Souscriptions actives"
✗ Si échec: Vérifiez MQTT_BROKER et que Mosquitto est actif
```

#### 3. Test du capteur ultrason
```bash
# Sur votre PC avec MQTT client
mosquitto_sub -h 192.168.1.50 -t "esp8266/capteurs/distance" -v

# Approchez votre main du capteur
# Vous devriez voir: esp8266/capteurs/distance {"distance_cm": 8.5, "objet_detecte": true, ...}
```

#### 4. Test de la balance
```bash
mosquitto_sub -h 192.168.1.50 -t "esp8266/capteurs/poids" -v

# Posez un objet sur la balance
# Vous devriez voir: esp8266/capteurs/poids {"poids_grammes": 125.3, ...}
```

#### 5. Test du bouton marche
```bash
mosquitto_sub -h 192.168.1.50 -t "esp8266/systeme/etat" -v

# Appuyez sur le bouton marche
# Vous devriez voir l'état passer à "E1_MARCHE_CONV"
```

### Problèmes courants

| Problème | Cause probable | Solution |
|----------|----------------|----------|
| WiFi ne se connecte pas | SSID/Password incorrect | Vérifiez les identifiants WiFi |
| MQTT ne se connecte pas | Broker non accessible | Vérifiez l'IP du broker et que Mosquitto est actif |
| Poids négatif ou aberrant | Balance non calibrée | Effectuez la calibration |
| Moteurs ne tournent pas | Alimentation insuffisante | Utilisez une alimentation externe 5V/2A minimum |
| LEDs ne s'allument pas | Résistances manquantes | Ajoutez des résistances de 220Ω |
| Distance toujours -1 | Câblage ultrason incorrect | Vérifiez TRIG et ECHO |

### Commandes MQTT utiles

```bash
# Surveiller tous les messages de l'ESP8266
mosquitto_sub -h 192.168.1.50 -t "esp8266/#" -v

# Réinitialiser l'ESP8266
mosquitto_pub -h 192.168.1.50 -t "esp8266/commandes/reset" -m ""

# Remettre la balance à zéro
mosquitto_pub -h 192.168.1.50 -t "esp8266/commandes/tare" -m ""

# Changer le facteur de calibration
mosquitto_pub -h 192.168.1.50 -t "esp8266/commandes/calibration" -m "2606"

# Simuler un résultat caméra OK
mosquitto_pub -h 192.168.1.50 -t "raspberry/camera/resultat" -m '{"status":"OK"}'

# Simuler un résultat caméra KO
mosquitto_pub -h 192.168.1.50 -t "raspberry/camera/resultat" -m '{"status":"KO"}'
```

---

## 📊 Cycle de fonctionnement complet

### Séquence normale (produit OK)

1. **E0_INIT**: Système en attente
2. Appui sur bouton marche → **E1_MARCHE_CONV**
3. Moteur 1 démarre, LED verte conv allumée
4. Objet détecté (< 10cm) → **E2_DETECTION_OBJET**
5. Moteur 1 s'arrête
6. **E3_CONTROL_CAMERA**: LED rouge caméra allumée
7. Trigger envoyé à Raspberry Pi
8. Résultat caméra OK reçu → **E4_CONTROL_POIDS**
9. LED rouge poids allumée
10. Poids mesuré et analysé
11. Poids OK → **E8_LED_VERT_CONV2**
12. LED verte conv2 allumée, moteur 2 démarre
13. Objet sort (distance > 10cm) → **E11_STOP_CONV2**
14. Moteur 2 s'arrête, LED éteinte
15. Retour à **E0_INIT**

### Séquence avec défaut caméra

1-7. Idem séquence normale
8. Résultat caméra KO reçu → **E6_LED_ROUGE_CAMERA**
9. LED rouge caméra reste allumée 2s
10. **E9_STOP_CONV**: Arrêt
11. Objet retiré → Retour à **E0_INIT**

### Séquence avec défaut poids

1-10. Idem séquence normale jusqu'au pesage
11. Poids KO → **E7_LED_ROUGE_POIDS**
12. LED rouge poids reste allumée 2s
13. **E9_STOP_CONV**: Arrêt
14. Objet retiré → Retour à **E0_INIT**

---

## 🔗 Intégration avec le jumeau numérique

Votre ESP8266 publie automatiquement tous les états sur MQTT. Le jumeau numérique (backend Node.js + frontend React) se synchronise automatiquement.

### Vérification de l'intégration

1. Démarrez le jumeau numérique: `http://localhost:5173`
2. Téléversez le code sur l'ESP8266
3. Surveillez l'interface web:
   - Les données des capteurs doivent s'afficher en temps réel
   - Le modèle 3D doit réagir aux changements d'état
   - Les LEDs virtuelles doivent correspondre aux LEDs physiques

---

## 📞 Support

Si vous rencontrez des problèmes:

1. Vérifiez le moniteur série (115200 baud)
2. Testez les topics MQTT avec `mosquitto_sub`
3. Vérifiez les connexions matérielles
4. Consultez la section "Problèmes courants" ci-dessus

---

**Créé le**: 2026-02-28
**Version**: 1.0
**Compatible avec**: ESP8266 NodeMCU v2/v3, Arduino IDE 1.8+, PlatformIO
