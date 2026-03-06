/*
 * ═══════════════════════════════════════════════════════════════════════════
 * ESP8266 Controller - Système IoT Contrôle de Flacons
 * Compatible avec Jumeau Numérique
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * CÂBLAGE ESP8266 (NodeMCU):
 *
 * HC-SR04 (Ultrason):
 *   VCC  → 5V (VU)
 *   GND  → GND
 *   TRIG → D1 (GPIO5)
 *   ECHO → D2 (GPIO4)
 *
 * HX711 (Capteur poids):
 *   VCC  → 3.3V
 *   GND  → GND
 *   DOUT → D5 (GPIO14)
 *   SCK  → D6 (GPIO12)
 *
 * L298N (Moteurs):
 *   IN1 (Moteur 1) → D7 (GPIO13)
 *   IN2 (Moteur 1) → D8 (GPIO15)
 *   IN3 (Moteur 2) → D3 (GPIO0)
 *   IN4 (Moteur 2) → D4 (GPIO2)
 *
 * LEDs (avec résistances 220Ω):
 *   LED Verte  → D0 (GPIO16) → GND
 *   LED Rouge  → TX (GPIO1)  → GND  (⚠️ Désactiver Serial pour utiliser)
 *   LED Orange → RX (GPIO3)  → GND  (⚠️ Désactiver Serial pour utiliser)
 *
 * Bouton Urgence:
 *   PIN 1 → 3.3V
 *   PIN 2 → A0 (via résistance 10kΩ vers GND)
 *
 * ═══════════════════════════════════════════════════════════════════════════
 */

#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <HX711.h>

// ═══════════════════════════════════════════════════════════
// ⚙️  CONFIGURATION - À MODIFIER
// ═══════════════════════════════════════════════════════════
const char* WIFI_SSID = "VOTRE_SSID";                    // ← MODIFIER
const char* WIFI_PASSWORD = "VOTRE_MOT_DE_PASSE";        // ← MODIFIER
const char* MQTT_BROKER = "192.168.1.100";               // ← IP du PC/Raspberry avec jumeau numérique
const int MQTT_PORT = 1883;

// ═══════════════════════════════════════════════════════════
// 📡 TOPICS MQTT
// ═══════════════════════════════════════════════════════════
// PUBLICATION (ESP8266 → Jumeau Numérique)
const char* TOPIC_ULTRASON = "esp8266/ultrason/distance";
const char* TOPIC_POIDS    = "esp8266/poids/valeur";
const char* TOPIC_MOTEUR   = "esp8266/moteur/etat";
const char* TOPIC_LED      = "esp8266/led/etat";
const char* TOPIC_URGENCE  = "esp8266/urgence/etat";

// SOUSCRIPTION (Jumeau Numérique → ESP8266)
const char* TOPIC_BOUTEILLE_ETAT = "esp8266/bouteille/etat";       // Résultat caméra OK/KO
const char* TOPIC_CMD_MOTEUR     = "esp8266/commande/moteur";      // Contrôle moteur
const char* TOPIC_CMD_LED        = "esp8266/commande/led";         // Contrôle LED

// ═══════════════════════════════════════════════════════════
// 📌 PINS GPIO
// ═══════════════════════════════════════════════════════════
#define PIN_TRIG        D1    // GPIO5
#define PIN_ECHO        D2    // GPIO4
#define PIN_HX711_DOUT  D5    // GPIO14
#define PIN_HX711_SCK   D6    // GPIO12
#define PIN_MOTOR1_IN1  D7    // GPIO13
#define PIN_MOTOR1_IN2  D8    // GPIO15
#define PIN_MOTOR2_IN1  D3    // GPIO0
#define PIN_MOTOR2_IN2  D4    // GPIO2
#define PIN_LED_VERTE   D0    // GPIO16
#define PIN_LED_ROUGE   TX    // GPIO1
#define PIN_LED_ORANGE  RX    // GPIO3
#define PIN_URGENCE     A0    // Analogique

// ═══════════════════════════════════════════════════════════
// ⚙️  PARAMÈTRES
// ═══════════════════════════════════════════════════════════
#define SEUIL_DETECTION_CM  10.0
#define CALIBRATION_POIDS   -7050.0    // À ajuster
#define INTERVAL_ULTRASON   300
#define INTERVAL_POIDS      1000

// ═══════════════════════════════════════════════════════════
// 💾 VARIABLES GLOBALES
// ═══════════════════════════════════════════════════════════
WiFiClient espClient;
PubSubClient mqttClient(espClient);
HX711 scale;

bool moteurEnMarche = false;
int vitesseMoteur = 80;
bool ledVerte = false, ledRouge = false, ledOrange = false;
bool urgenceActive = false;
bool flaconDetecte = false;
float dernierePoids = 0.0, derniereDistance = 999.0;

unsigned long derniereMesureUltrason = 0;
unsigned long derniereMesurePoids = 0;

enum EtatProcessus { ATTENTE, FLACON_DETECTE, PESAGE, ANALYSE, RESULTAT_OK, RESULTAT_KO };
EtatProcessus etatActuel = ATTENTE;

// ═══════════════════════════════════════════════════════════
// 🚀 SETUP
// ═══════════════════════════════════════════════════════════
void setup() {
  Serial.begin(115200);
  delay(100);

  Serial.println("\n\n╔══════════════════════════════════════╗");
  Serial.println("║  ESP8266 Contrôleur IoT Flacons     ║");
  Serial.println("║  🤖 Jumeau Numérique                ║");
  Serial.println("╚══════════════════════════════════════╝\n");

  setupPins();

  Serial.println("⚖️  Init HX711...");
  scale.begin(PIN_HX711_DOUT, PIN_HX711_SCK);
  scale.set_scale(CALIBRATION_POIDS);
  scale.tare();
  Serial.println("✅ HX711 OK\n");

  connectWiFi();

  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  mqttClient.setBufferSize(512);

  animationDemarrage();

  Serial.println("✅ Système prêt!\n");
  afficherTopics();
}

// ═══════════════════════════════════════════════════════════
// 🔄 LOOP PRINCIPAL
// ═══════════════════════════════════════════════════════════
void loop() {
  if (!mqttClient.connected()) reconnectMQTT();
  mqttClient.loop();

  checkUrgence();
  if (urgenceActive) { if (moteurEnMarche) stopMoteurs(); return; }

  if (millis() - derniereMesureUltrason >= INTERVAL_ULTRASON) {
    derniereMesureUltrason = millis();
    mesureEtPublishUltrason();
  }

  if (millis() - derniereMesurePoids >= INTERVAL_POIDS) {
    derniereMesurePoids = millis();
    mesureEtPublishPoids();
  }

  gererProcessus();
}

// ═══════════════════════════════════════════════════════════
// 🔧 FONCTIONS
// ═══════════════════════════════════════════════════════════
void setupPins() {
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  pinMode(PIN_MOTOR1_IN1, OUTPUT);
  pinMode(PIN_MOTOR1_IN2, OUTPUT);
  pinMode(PIN_MOTOR2_IN1, OUTPUT);
  pinMode(PIN_MOTOR2_IN2, OUTPUT);
  pinMode(PIN_LED_VERTE, OUTPUT);
  pinMode(PIN_LED_ROUGE, OUTPUT);
  pinMode(PIN_LED_ORANGE, OUTPUT);
  pinMode(PIN_URGENCE, INPUT_PULLUP);
  stopMoteurs();
  eteindreLEDs();
}

void connectWiFi() {
  Serial.print("📶 WiFi: ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int t = 0;
  while (WiFi.status() != WL_CONNECTED && t++ < 30) {
    delay(500);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi OK - IP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\n❌ WiFi ÉCHEC");
  }
}

void reconnectMQTT() {
  if (WiFi.status() != WL_CONNECTED) { connectWiFi(); return; }

  while (!mqttClient.connected()) {
    Serial.print("📡 MQTT...");
    if (mqttClient.connect("ESP8266_Flacon")) {
      Serial.println(" ✅");
      mqttClient.subscribe(TOPIC_BOUTEILLE_ETAT);
      mqttClient.subscribe(TOPIC_CMD_MOTEUR);
      mqttClient.subscribe(TOPIC_CMD_LED);
      publishLEDs();
      publishMoteur();
      publishUrgence();
    } else {
      Serial.print(" ❌("); Serial.print(mqttClient.state()); Serial.println(")");
      delay(5000);
    }
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String msg = "";
  for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];

  Serial.println("📩 [" + String(topic) + "] " + msg);

  if (strcmp(topic, TOPIC_BOUTEILLE_ETAT) == 0) {
    msg.toUpperCase();
    if (msg == "OK") etatActuel = RESULTAT_OK;
    else if (msg == "KO" || msg == "ERREUR") etatActuel = RESULTAT_KO;
  }
  else if (strcmp(topic, TOPIC_CMD_MOTEUR) == 0) {
    StaticJsonDocument<128> doc;
    if (deserializeJson(doc, msg) == DeserializationError::Ok) {
      String action = doc["action"] | "";
      action.toUpperCase();
      if (action == "START") startMoteurs(doc["vitesse"] | 80);
      else if (action == "STOP") stopMoteurs();
    }
  }
  else if (strcmp(topic, TOPIC_CMD_LED) == 0) {
    StaticJsonDocument<128> doc;
    if (deserializeJson(doc, msg) == DeserializationError::Ok) {
      String led = doc["led"] | "";
      bool etat = doc["etat"] | false;
      led.toLowerCase();
      if (led == "verte") setLED(etat, ledRouge, ledOrange);
      else if (led == "rouge") setLED(ledVerte, etat, ledOrange);
      else if (led == "orange") setLED(ledVerte, ledRouge, etat);
    }
  }
}

float mesureDistance() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);
  long duree = pulseIn(PIN_ECHO, HIGH, 30000);
  return (duree == 0) ? 999.0 : (duree / 2.0) * 0.0343;
}

void mesureEtPublishUltrason() {
  float d = mesureDistance();
  derniereDistance = d;
  bool detect = (d > 0 && d < SEUIL_DETECTION_CM);

  if (detect != flaconDetecte) {
    flaconDetecte = detect;
    if (detect) {
      Serial.println("\n🔔 FLACON DÉTECTÉ");
      etatActuel = FLACON_DETECTE;
    } else {
      Serial.println("📤 Flacon parti\n");
      etatActuel = ATTENTE;
    }
  }

  StaticJsonDocument<128> doc;
  doc["distance"] = round(d * 10) / 10.0;
  doc["flacon_detecte"] = detect;
  doc["timestamp"] = millis();
  char buf[128];
  serializeJson(doc, buf);
  mqttClient.publish(TOPIC_ULTRASON, buf);
}

void mesureEtPublishPoids() {
  if (scale.is_ready()) {
    float p = scale.get_units(3);
    if (abs(p) < 2.0) p = 0.0;
    dernierePoids = p;

    StaticJsonDocument<128> doc;
    doc["poids_g"] = round(p * 10) / 10.0;
    doc["timestamp"] = millis();
    char buf[128];
    serializeJson(doc, buf);
    mqttClient.publish(TOPIC_POIDS, buf);
  }
}

void startMoteurs(int v) {
  if (urgenceActive) return;
  moteurEnMarche = true;
  vitesseMoteur = constrain(v, 0, 100);
  digitalWrite(PIN_MOTOR1_IN1, HIGH);
  digitalWrite(PIN_MOTOR1_IN2, LOW);
  digitalWrite(PIN_MOTOR2_IN1, HIGH);
  digitalWrite(PIN_MOTOR2_IN2, LOW);
  Serial.println("🔧 Moteurs ON (" + String(vitesseMoteur) + "%)");
  publishMoteur();
}

void stopMoteurs() {
  moteurEnMarche = false;
  digitalWrite(PIN_MOTOR1_IN1, LOW);
  digitalWrite(PIN_MOTOR1_IN2, LOW);
  digitalWrite(PIN_MOTOR2_IN1, LOW);
  digitalWrite(PIN_MOTOR2_IN2, LOW);
  Serial.println("🛑 Moteurs OFF");
  publishMoteur();
}

void publishMoteur() {
  StaticJsonDocument<128> doc;
  doc["etat"] = moteurEnMarche ? "ON" : "OFF";
  doc["vitesse"] = vitesseMoteur;
  doc["timestamp"] = millis();
  char buf[128];
  serializeJson(doc, buf);
  mqttClient.publish(TOPIC_MOTEUR, buf);
}

void setLED(bool v, bool r, bool o) {
  ledVerte = v; ledRouge = r; ledOrange = o;
  digitalWrite(PIN_LED_VERTE, v);
  digitalWrite(PIN_LED_ROUGE, r);
  digitalWrite(PIN_LED_ORANGE, o);
  publishLEDs();
}

void eteindreLEDs() {
  setLED(false, false, false);
}

void publishLEDs() {
  StaticJsonDocument<128> doc;
  doc["verte"] = ledVerte;
  doc["rouge"] = ledRouge;
  doc["orange"] = ledOrange;
  char buf[128];
  serializeJson(doc, buf);
  mqttClient.publish(TOPIC_LED, buf);
}

void animationDemarrage() {
  for (int i = 0; i < 2; i++) {
    setLED(true, false, false); delay(150);
    setLED(false, true, false); delay(150);
    setLED(false, false, true); delay(150);
  }
  eteindreLEDs();
}

void checkUrgence() {
  static unsigned long lastDebounce = 0;
  static bool lastState = false;

  if (millis() - lastDebounce > 50) {
    bool state = (digitalRead(PIN_URGENCE) == LOW);
    if (state != lastState) {
      lastDebounce = millis();
      lastState = state;
      urgenceActive = state;
      if (urgenceActive) {
        Serial.println("\n🚨 URGENCE ACTIVÉE 🚨\n");
        stopMoteurs();
        setLED(true, true, true);
        etatActuel = ATTENTE;
      } else {
        Serial.println("✅ Urgence OFF\n");
        eteindreLEDs();
      }
      publishUrgence();
    }
  }
}

void publishUrgence() {
  StaticJsonDocument<128> doc;
  doc["active"] = urgenceActive;
  doc["timestamp"] = millis();
  char buf[128];
  serializeJson(doc, buf);
  mqttClient.publish(TOPIC_URGENCE, buf);
}

void gererProcessus() {
  static unsigned long t = 0;

  switch (etatActuel) {
    case ATTENTE: break;

    case FLACON_DETECTE:
      Serial.println("⚙️  Processus START");
      setLED(false, false, true);
      startMoteurs(vitesseMoteur);
      etatActuel = PESAGE;
      t = millis();
      break;

    case PESAGE:
      if (millis() - t > 1000) {
        Serial.println("⚖️  Poids: " + String(dernierePoids) + "g");
        etatActuel = ANALYSE;
        Serial.println("📷 Attente caméra...");
      }
      break;

    case ANALYSE: break;

    case RESULTAT_OK:
      Serial.println("✅ OK");
      setLED(true, false, false);
      delay(2000);
      if (!flaconDetecte) { stopMoteurs(); eteindreLEDs(); etatActuel = ATTENTE; }
      break;

    case RESULTAT_KO:
      Serial.println("❌ KO");
      setLED(false, true, false);
      delay(2000);
      if (!flaconDetecte) { stopMoteurs(); eteindreLEDs(); etatActuel = ATTENTE; }
      break;
  }
}

void afficherTopics() {
  Serial.println("📡 TOPICS MQTT:");
  Serial.println("   PUBLICATION (ESP8266 → Jumeau):");
  Serial.println("   ✓ " + String(TOPIC_ULTRASON));
  Serial.println("   ✓ " + String(TOPIC_POIDS));
  Serial.println("   ✓ " + String(TOPIC_MOTEUR));
  Serial.println("   ✓ " + String(TOPIC_LED));
  Serial.println("   ✓ " + String(TOPIC_URGENCE));
  Serial.println("   SOUSCRIPTION (Jumeau → ESP8266):");
  Serial.println("   ✓ " + String(TOPIC_BOUTEILLE_ETAT));
  Serial.println("   ✓ " + String(TOPIC_CMD_MOTEUR));
  Serial.println("   ✓ " + String(TOPIC_CMD_LED));
  Serial.println("\n═══════════════════════════════════════\n");
}
