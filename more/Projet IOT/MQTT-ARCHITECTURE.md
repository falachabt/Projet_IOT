# Architecture MQTT - Processus de contrôle qualité

## Principe
L'Arduino déclenche l'analyse quand une bouteille arrive. La Raspberry Pi analyse et renvoie le résultat.

## Topics MQTT

### 1. Topic de déclenchement (Arduino → RaspberryPi)
**Topic:** `iot/bottle/trigger`
**Message:** `{"action": "check"}`

L'Arduino publie ce message quand une bouteille est en position.

### 2. Topic de résultat (RaspberryPi → Arduino)
**Topic:** `iot/bottle/result`
**Message JSON:**
```json
{
  "timestamp": "20260119_153045",
  "status": "OK",
  "fill_percent": 85.3,
  "cap_ok": true,
  "image_path": "./output/20260119_153045_OK.jpg"
}
```

## Utilisation

### Sur Raspberry Pi
```bash
python flacon_checker.py --mqtt --headless
```

Ou double-cliquez sur `mqtt-mode.bat` (Windows)

### Code Arduino exemple
```cpp
#include <WiFi.h>
#include <PubSubClient.h>

const char* mqtt_server = "192.168.1.100";  // IP de la Raspberry Pi
WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  client.setServer(mqtt_server, 1883);
  client.setCallback(onMqttMessage);
  client.connect("Arduino_Client");
  client.subscribe("iot/bottle/result");
}

void loop() {
  if (bottleDetected()) {
    // Déclencher l'analyse
    client.publish("iot/bottle/trigger", "{\"action\":\"check\"}");
    delay(5000);  // Attendre le résultat
  }
  client.loop();
}

void onMqttMessage(char* topic, byte* payload, unsigned int length) {
  // Parser le JSON de résultat
  // {"status": "OK", "fill_percent": 85.3, ...}
  String message = String((char*)payload).substring(0, length);
  
  if (message.indexOf("\"status\":\"OK\"") > 0) {
    // Bouteille OK → continuer la ligne
    digitalWrite(LED_GREEN, HIGH);
  } else {
    // Bouteille REJET → arrêter/alerter
    digitalWrite(LED_RED, HIGH);
  }
}
```

## Configuration du broker MQTT

Options avec `--mqtt-broker` et `--mqtt-port`:
```bash
python flacon_checker.py --mqtt --mqtt-broker 192.168.1.100 --mqtt-port 1883
```

Pour tester localement avec Mosquitto:
```bash
# Installer Mosquitto
# Windows: https://mosquitto.org/download/
# Linux: sudo apt install mosquitto mosquitto-clients

# Terminal 1: Démarrer le script
python flacon_checker.py --mqtt --headless

# Terminal 2: Simuler un message Arduino
mosquitto_pub -h localhost -t iot/bottle/trigger -m '{"action":"check"}'

# Terminal 3: Écouter les résultats
mosquitto_sub -h localhost -t iot/bottle/result
```

## Avantages
- ✅ Déclenchement événementiel (pas de boucle qui tourne dans le vide)
- ✅ Communication bidirectionnelle Arduino ↔ RaspberryPi
- ✅ Économie de ressources (capture uniquement quand nécessaire)
- ✅ Scalable (peut ajouter d'autres capteurs/actionneurs)
- ✅ Résultats en JSON faciles à parser
