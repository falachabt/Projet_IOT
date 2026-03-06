/*
 * ESP32 Controller - Système IoT de Contrôle de Flacons
 * Compatible avec Jumeau Numérique
 *
 * Hardware:
 * - Capteur ultrason HC-SR04 (détection flacon)
 * - Capteur poids HX711
 * - 2 Moteurs DC via L298N
 * - 3 LEDs (Verte, Rouge, Orange)
 * - Bouton arrêt d'urgence
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <HX711.h>

// ═══════════════════════════════════════════════════════════
// CONFIGURATION WIFI & MQTT
// ═══════════════════════════════════════════════════════════
const char* WIFI_SSID = "VOTRE_SSID";              // ← Modifier
const char* WIFI_PASSWORD = "VOTRE_MOT_DE_PASSE";  // ← Modifier
const char* MQTT_BROKER = "192.168.1.100";         // ← IP du Raspberry Pi / PC
const int MQTT_PORT = 1883;
const char* MQTT_CLIENT_ID = "ESP32_Flacon_Controller";

// ═══════════════════════════════════════════════════════════
// TOPICS MQTT - PUBLICATION (ESP32 → Jumeau Numérique)
// ═══════════════════════════════════════════════════════════
const char* TOPIC_ULTRASON = "esp8266/ultrason/distance";
const char* TOPIC_POIDS = "esp8266/poids/valeur";
const char* TOPIC_MOTEUR = "esp8266/moteur/etat";
const char* TOPIC_LED = "esp8266/led/etat";
const char* TOPIC_URGENCE = "esp8266/urgence/etat";

// ═══════════════════════════════════════════════════════════
// TOPICS MQTT - SOUSCRIPTION (Jumeau Numérique → ESP32)
// ═══════════════════════════════════════════════════════════
const char* TOPIC_BOUTEILLE_ETAT = "esp8266/bouteille/etat";
const char* TOPIC_CMD_MOTEUR = "esp8266/commande/moteur";
const char* TOPIC_CMD_LED = "esp8266/commande/led";

// ═══════════════════════════════════════════════════════════
// PINS GPIO ESP32
// ═══════════════════════════════════════════════════════════
// Capteur Ultrason HC-SR04
#define PIN_TRIG 5       // GPIO5
#define PIN_ECHO 18      // GPIO18

// Capteur Poids HX711
#define PIN_HX711_DOUT 19   // GPIO19
#define PIN_HX711_SCK 21    // GPIO21

// Moteurs (L298N)
#define PIN_MOTOR1_IN1 25   // GPIO25
#define PIN_MOTOR1_IN2 26   // GPIO26
#define PIN_MOTOR1_EN 27    // GPIO27 (PWM)
#define PIN_MOTOR2_IN1 32   // GPIO32
#define PIN_MOTOR2_IN2 33   // GPIO33
#define PIN_MOTOR2_EN 14    // GPIO14 (PWM)

// LEDs
#define PIN_LED_VERTE 12    // GPIO12
#define PIN_LED_ROUGE 13    // GPIO13
#define PIN_LED_ORANGE 15   // GPIO15

// Bouton Urgence
#define PIN_URGENCE 4       // GPIO4 (avec pullup interne)

// ═══════════════════════════════════════════════════════════
// CONSTANTES
// ═══════════════════════════════════════════════════════════
#define SEUIL_DETECTION_CM 10.0
#define INTERVAL_ULTRASON 300       // ms
#define INTERVAL_POIDS 1000         // ms
#define INTERVAL_PUBLISH_MOTEUR 2000 // ms
#define CALIBRATION_POIDS -7050.0   // À ajuster selon votre balance
#define PWM_FREQ 5000               // Fréquence PWM moteurs
#define PWM_RESOLUTION 8            // Résolution PWM (0-255)
#define PWM_CHANNEL_1 0
#define PWM_CHANNEL_2 1

// ═══════════════════════════════════════════════════════════
// VARIABLES GLOBALES
// ═══════════════════════════════════════════════════════════
WiFiClient espClient;
PubSubClient mqttClient(espClient);
HX711 scale;

// États système
bool moteurEnMarche = false;
int vitesseMoteur = 80;
bool ledVerte = false;
bool ledRouge = false;
bool ledOrange = false;
bool urgenceActive = false;
bool dernierEtatUrgence = false;
bool flaconDetecte = false;
bool dernierEtatFlacon = false;

float dernierePoids = 0.0;
float derniereDistance = 999.0;

// Timing
unsigned long derniereMesureUltrason = 0;
unsigned long derniereMesurePoids = 0;
unsigned long dernierPublishMoteur = 0;
unsigned long dernierDebounceUrgence = 0;
const unsigned long DEBOUNCE_DELAY = 50;

// État processus
enum EtatProcessus {
  ATTENTE,
  FLACON_DETECTE,
  PESAGE,
  ANALYSE_EN_COURS,
  RESULTAT_OK,
  RESULTAT_KO
};
EtatProcessus etatActuel = ATTENTE;

// ═══════════════════════════════════════════════════════════
// SETUP
// ═══════════════════════════════════════════════════════════
void setup() {
  Serial.begin(115200);
  delay(100);

  Serial.println("\n\n╔════════════════════════════════════════════╗");
  Serial.println("║   ESP32 Contrôleur IoT Flacons            ║");
  Serial.println("║   Jumeau Numérique                        ║");
  Serial.println("╚════════════════════════════════════════════╝\n");

  // Configuration pins
  setupPins();

  // Configuration PWM pour moteurs
  ledcSetup(PWM_CHANNEL_1, PWM_FREQ, PWM_RESOLUTION);
  ledcSetup(PWM_CHANNEL_2, PWM_FREQ, PWM_RESOLUTION);
  ledcAttachPin(PIN_MOTOR1_EN, PWM_CHANNEL_1);
  ledcAttachPin(PIN_MOTOR2_EN, PWM_CHANNEL_2);

  // Initialisation capteur poids
  Serial.println("⚖️  Initialisation HX711...");
  scale.begin(PIN_HX711_DOUT, PIN_HX711_SCK);
  scale.set_scale(CALIBRATION_POIDS);
  scale.tare();
  Serial.println("✅ HX711 prêt\n");

  // Connexion WiFi
  connectWiFi();

  // Configuration MQTT
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  mqttClient.setBufferSize(512);

  // Animation LEDs démarrage
  animationDemarrage();

  Serial.println("✅ Système prêt!\n");
  Serial.println("📡 Topics MQTT:");
  Serial.println("   Publication:");
  Serial.println("   - " + String(TOPIC_ULTRASON));
  Serial.println("   - " + String(TOPIC_POIDS));
  Serial.println("   - " + String(TOPIC_MOTEUR));
  Serial.println("   - " + String(TOPIC_LED));
  Serial.println("   - " + String(TOPIC_URGENCE));
  Serial.println("   Souscription:");
  Serial.println("   - " + String(TOPIC_BOUTEILLE_ETAT));
  Serial.println("   - " + String(TOPIC_CMD_MOTEUR));
  Serial.println("   - " + String(TOPIC_CMD_LED));
  Serial.println("\n════════════════════════════════════════════\n");
}

// ═══════════════════════════════════════════════════════════
// LOOP PRINCIPAL
// ═══════════════════════════════════════════════════════════
void loop() {
  // Maintenir connexion MQTT
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();

  // Vérifier bouton urgence
  checkUrgence();

  // Si urgence, tout arrêter
  if (urgenceActive) {
    if (moteurEnMarche) {
      stopMoteurs();
      publishMoteurEtat();
    }
    return;
  }

  // Mesure ultrason
  if (millis() - derniereMesureUltrason >= INTERVAL_ULTRASON) {
    derniereMesureUltrason = millis();
    mesureEtPublishUltrason();
  }

  // Mesure poids
  if (millis() - derniereMesurePoids >= INTERVAL_POIDS) {
    derniereMesurePoids = millis();
    mesureEtPublishPoids();
  }

  // Publier état moteur périodiquement
  if (millis() - dernierPublishMoteur >= INTERVAL_PUBLISH_MOTEUR) {
    dernierPublishMoteur = millis();
    publishMoteurEtat();
  }

  // Machine à états du processus
  gererEtatProcessus();
}

// ═══════════════════════════════════════════════════════════
// CONFIGURATION PINS
// ═══════════════════════════════════════════════════════════
void setupPins() {
  // Ultrason
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  digitalWrite(PIN_TRIG, LOW);

  // Moteurs
  pinMode(PIN_MOTOR1_IN1, OUTPUT);
  pinMode(PIN_MOTOR1_IN2, OUTPUT);
  pinMode(PIN_MOTOR2_IN1, OUTPUT);
  pinMode(PIN_MOTOR2_IN2, OUTPUT);
  stopMoteurs();

  // LEDs
  pinMode(PIN_LED_VERTE, OUTPUT);
  pinMode(PIN_LED_ROUGE, OUTPUT);
  pinMode(PIN_LED_ORANGE, OUTPUT);
  eteindreToutesLEDs();

  // Bouton urgence (avec pullup interne)
  pinMode(PIN_URGENCE, INPUT_PULLUP);
}

// ═══════════════════════════════════════════════════════════
// WIFI
// ═══════════════════════════════════════════════════════════
void connectWiFi() {
  Serial.print("📶 Connexion WiFi à ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int tentatives = 0;
  while (WiFi.status() != WL_CONNECTED && tentatives < 30) {
    delay(500);
    Serial.print(".");
    tentatives++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi connecté!");
    Serial.print("📍 IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n❌ Échec connexion WiFi!");
  }
}

// ═══════════════════════════════════════════════════════════
// MQTT
// ═══════════════════════════════════════════════════════════
void reconnectMQTT() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
    return;
  }

  while (!mqttClient.connected()) {
    Serial.print("📡 Connexion MQTT...");

    if (mqttClient.connect(MQTT_CLIENT_ID)) {
      Serial.println(" ✅");

      // Souscription aux topics
      mqttClient.subscribe(TOPIC_BOUTEILLE_ETAT);
      mqttClient.subscribe(TOPIC_CMD_MOTEUR);
      mqttClient.subscribe(TOPIC_CMD_LED);

      Serial.println("✅ Abonné aux topics de commande");

      // Publier état initial
      publishLEDEtat();
      publishMoteurEtat();
      publishUrgenceEtat();

    } else {
      Serial.print(" ❌ Échec (");
      Serial.print(mqttClient.state());
      Serial.println(")");
      delay(5000);
    }
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.print("📩 [");
  Serial.print(topic);
  Serial.print("] ");
  Serial.println(message);

  // Résultat caméra
  if (strcmp(topic, TOPIC_BOUTEILLE_ETAT) == 0) {
    handleResultatCamera(message);
  }
  // Commande moteur
  else if (strcmp(topic, TOPIC_CMD_MOTEUR) == 0) {
    handleCommandeMoteur(message);
  }
  // Commande LED
  else if (strcmp(topic, TOPIC_CMD_LED) == 0) {
    handleCommandeLED(message);
  }
}

// ═══════════════════════════════════════════════════════════
// CAPTEUR ULTRASON
// ═══════════════════════════════════════════════════════════
float mesureDistance() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);

  long duree = pulseIn(PIN_ECHO, HIGH, 30000);

  if (duree == 0) {
    return 999.0;
  }

  float distance = (duree / 2.0) * 0.0343;
  return distance;
}

void mesureEtPublishUltrason() {
  float distance = mesureDistance();
  derniereDistance = distance;

  bool flaconDetecteNow = (distance > 0 && distance < SEUIL_DETECTION_CM);

  // Changement d'état
  if (flaconDetecteNow != dernierEtatFlacon) {
    dernierEtatFlacon = flaconDetecteNow;
    flaconDetecte = flaconDetecteNow;

    if (flaconDetecte) {
      Serial.println("\n🔔 ══════ FLACON DÉTECTÉ ══════");
      etatActuel = FLACON_DETECTE;
    } else {
      Serial.println("📤 Flacon parti\n");
      etatActuel = ATTENTE;
    }
  }

  // Publier sur MQTT
  StaticJsonDocument<128> doc;
  doc["distance"] = round(distance * 10) / 10.0;
  doc["flacon_detecte"] = flaconDetecte;
  doc["timestamp"] = millis();

  char buffer[128];
  serializeJson(doc, buffer);
  mqttClient.publish(TOPIC_ULTRASON, buffer);
}

// ═══════════════════════════════════════════════════════════
// CAPTEUR POIDS
// ═══════════════════════════════════════════════════════════
void mesureEtPublishPoids() {
  if (scale.is_ready()) {
    float poids = scale.get_units(3);

    if (abs(poids) < 2.0) {
      poids = 0.0;
    }

    dernierePoids = poids;

    StaticJsonDocument<128> doc;
    doc["poids_g"] = round(poids * 10) / 10.0;
    doc["timestamp"] = millis();

    char buffer[128];
    serializeJson(doc, buffer);
    mqttClient.publish(TOPIC_POIDS, buffer);
  }
}

// ═══════════════════════════════════════════════════════════
// MOTEURS
// ═══════════════════════════════════════════════════════════
void startMoteurs(int vitesse) {
  if (urgenceActive) return;

  moteurEnMarche = true;
  vitesseMoteur = constrain(vitesse, 0, 100);

  int pwmValue = map(vitesseMoteur, 0, 100, 0, 255);

  // Moteur 1: avancer
  digitalWrite(PIN_MOTOR1_IN1, HIGH);
  digitalWrite(PIN_MOTOR1_IN2, LOW);
  ledcWrite(PWM_CHANNEL_1, pwmValue);

  // Moteur 2: avancer
  digitalWrite(PIN_MOTOR2_IN1, HIGH);
  digitalWrite(PIN_MOTOR2_IN2, LOW);
  ledcWrite(PWM_CHANNEL_2, pwmValue);

  Serial.print("🔧 Moteurs ON (");
  Serial.print(vitesseMoteur);
  Serial.println("%)");

  publishMoteurEtat();
}

void stopMoteurs() {
  moteurEnMarche = false;

  digitalWrite(PIN_MOTOR1_IN1, LOW);
  digitalWrite(PIN_MOTOR1_IN2, LOW);
  ledcWrite(PWM_CHANNEL_1, 0);

  digitalWrite(PIN_MOTOR2_IN1, LOW);
  digitalWrite(PIN_MOTOR2_IN2, LOW);
  ledcWrite(PWM_CHANNEL_2, 0);

  Serial.println("🛑 Moteurs OFF");

  publishMoteurEtat();
}

void publishMoteurEtat() {
  StaticJsonDocument<128> doc;
  doc["etat"] = moteurEnMarche ? "ON" : "OFF";
  doc["vitesse"] = vitesseMoteur;
  doc["timestamp"] = millis();

  char buffer[128];
  serializeJson(doc, buffer);
  mqttClient.publish(TOPIC_MOTEUR, buffer);
}

// ═══════════════════════════════════════════════════════════
// LEDS
// ═══════════════════════════════════════════════════════════
void setLED(bool verte, bool rouge, bool orange) {
  ledVerte = verte;
  ledRouge = rouge;
  ledOrange = orange;

  digitalWrite(PIN_LED_VERTE, verte ? HIGH : LOW);
  digitalWrite(PIN_LED_ROUGE, rouge ? HIGH : LOW);
  digitalWrite(PIN_LED_ORANGE, orange ? HIGH : LOW);

  publishLEDEtat();
}

void eteindreToutesLEDs() {
  setLED(false, false, false);
}

void publishLEDEtat() {
  StaticJsonDocument<128> doc;
  doc["verte"] = ledVerte;
  doc["rouge"] = ledRouge;
  doc["orange"] = ledOrange;

  char buffer[128];
  serializeJson(doc, buffer);
  mqttClient.publish(TOPIC_LED, buffer);
}

void animationDemarrage() {
  for (int i = 0; i < 2; i++) {
    setLED(true, false, false);
    delay(150);
    setLED(false, true, false);
    delay(150);
    setLED(false, false, true);
    delay(150);
  }
  eteindreToutesLEDs();
}

// ═══════════════════════════════════════════════════════════
// BOUTON URGENCE
// ═══════════════════════════════════════════════════════════
void checkUrgence() {
  if ((millis() - dernierDebounceUrgence) > DEBOUNCE_DELAY) {
    bool urgenceNow = (digitalRead(PIN_URGENCE) == LOW);

    if (urgenceNow != dernierEtatUrgence) {
      dernierDebounceUrgence = millis();
      dernierEtatUrgence = urgenceNow;
      urgenceActive = urgenceNow;

      if (urgenceActive) {
        Serial.println("\n🚨 ══ ARRÊT D'URGENCE ACTIVÉ ══ 🚨\n");
        stopMoteurs();
        setLED(true, true, true);  // Toutes allumées
        etatActuel = ATTENTE;
      } else {
        Serial.println("✅ Arrêt d'urgence désactivé\n");
        eteindreToutesLEDs();
      }

      publishUrgenceEtat();
    }
  }
}

void publishUrgenceEtat() {
  StaticJsonDocument<128> doc;
  doc["active"] = urgenceActive;
  doc["timestamp"] = millis();

  char buffer[128];
  serializeJson(doc, buffer);
  mqttClient.publish(TOPIC_URGENCE, buffer);
}

// ═══════════════════════════════════════════════════════════
// MACHINE À ÉTATS - PROCESSUS
// ═══════════════════════════════════════════════════════════
void gererEtatProcessus() {
  static unsigned long tempsEtat = 0;

  switch (etatActuel) {
    case ATTENTE:
      // Rien à faire, en attente de détection
      break;

    case FLACON_DETECTE:
      // Flacon détecté → Démarrer processus
      Serial.println("⚙️  Démarrage du processus...");
      setLED(false, false, true);  // Orange
      startMoteurs(vitesseMoteur);
      etatActuel = PESAGE;
      tempsEtat = millis();
      break;

    case PESAGE:
      // Attendre 1 seconde pour stabilisation poids
      if (millis() - tempsEtat > 1000) {
        Serial.print("⚖️  Poids: ");
        Serial.print(dernierePoids);
        Serial.println("g");
        etatActuel = ANALYSE_EN_COURS;
        Serial.println("📷 Attente résultat caméra...");
      }
      break;

    case ANALYSE_EN_COURS:
      // Attente du résultat de la caméra (géré par MQTT callback)
      break;

    case RESULTAT_OK:
      Serial.println("✅ VALIDATION - Flacon OK");
      setLED(true, false, false);  // Verte
      delay(2000);

      // Retour attente
      if (!flaconDetecte) {
        stopMoteurs();
        eteindreToutesLEDs();
        etatActuel = ATTENTE;
      }
      break;

    case RESULTAT_KO:
      Serial.println("❌ REJET - Flacon KO");
      setLED(false, true, false);  // Rouge

      // Optionnel: arrêter moteur en cas de rejet
      // stopMoteurs();

      delay(2000);

      // Retour attente
      if (!flaconDetecte) {
        stopMoteurs();
        eteindreToutesLEDs();
        etatActuel = ATTENTE;
      }
      break;
  }
}

// ═══════════════════════════════════════════════════════════
// HANDLERS MQTT
// ═══════════════════════════════════════════════════════════
void handleResultatCamera(String message) {
  message.trim();
  message.toUpperCase();

  if (message == "OK") {
    etatActuel = RESULTAT_OK;
  } else if (message == "KO" || message == "ERREUR") {
    etatActuel = RESULTAT_KO;
  }
}

void handleCommandeMoteur(String message) {
  StaticJsonDocument<128> doc;
  DeserializationError error = deserializeJson(doc, message);

  if (!error) {
    String action = doc["action"] | "";
    action.toUpperCase();

    if (action == "START") {
      int vitesse = doc["vitesse"] | 80;
      startMoteurs(vitesse);
    } else if (action == "STOP") {
      stopMoteurs();
    }
  }
}

void handleCommandeLED(String message) {
  StaticJsonDocument<128> doc;
  DeserializationError error = deserializeJson(doc, message);

  if (!error) {
    String led = doc["led"] | "";
    bool etat = doc["etat"] | false;

    led.toLowerCase();

    if (led == "verte") {
      setLED(etat, ledRouge, ledOrange);
    } else if (led == "rouge") {
      setLED(ledVerte, etat, ledOrange);
    } else if (led == "orange") {
      setLED(ledVerte, ledRouge, etat);
    }
  }
}
