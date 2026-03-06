/*
 * Programme ESP8266 - Système de contrôle qualité de flacons
 * Basé sur GRAFCET fourni
 *
 * CONFIGURATION WIFI ET MQTT À MODIFIER CI-DESSOUS
 */

#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "HX711.h"

// ============================================================================
// CONFIGURATION - À MODIFIER SELON VOTRE INSTALLATION
// ============================================================================

// Configuration WiFi
#define WIFI_SSID "VOTRE_SSID"
#define WIFI_PASSWORD "VOTRE_MOT_DE_PASSE"

// Configuration MQTT Broker
#define MQTT_BROKER "192.168.1.100"  // Adresse IP de votre broker
#define MQTT_PORT 1883
#define MQTT_USER ""                 // Laisser vide si pas d'authentification
#define MQTT_PASSWORD ""             // Laisser vide si pas d'authentification
#define MQTT_CLIENT_ID "ESP8266_IOT"

// ============================================================================
// CONFIGURATION MATÉRIELLE - Pins GPIO
// ============================================================================

// Capteur ultrason HC-SR04
#define TRIG_PIN D1
#define ECHO_PIN D2

// Capteur de poids HX711
#define HX711_DOUT D5
#define HX711_SCK D6

// Moteurs (via L298N)
#define MOTOR1_IN1 D7
#define MOTOR1_IN2 D8
#define MOTOR2_IN3 D3
#define MOTOR2_IN4 D4

// LEDs de statut
#define LED_VERT_CONV D0      // LED verte convoyeur marche
#define LED_ROUGE_CAMERA D9   // LED rouge analyse caméra
#define LED_ROUGE_POIDS D10   // LED rouge analyse poids
#define LED_VERT_CONV2 RX     // LED verte convoyeur 2

// Boutons
#define BTN_MARCHE 3          // Bouton de démarrage
#define BTN_URGENCE 1         // Bouton d'arrêt d'urgence

// ============================================================================
// TOPICS MQTT
// ============================================================================

// Topics de publication (ESP8266 → Broker)
#define TOPIC_DISTANCE "esp8266/capteurs/distance"
#define TOPIC_POIDS "esp8266/capteurs/poids"
#define TOPIC_MOTEUR1 "esp8266/actionneurs/moteur1"
#define TOPIC_MOTEUR2 "esp8266/actionneurs/moteur2"
#define TOPIC_LED_VERT_CONV "esp8266/actionneurs/led_vert_conv"
#define TOPIC_LED_ROUGE_CAM "esp8266/actionneurs/led_rouge_camera"
#define TOPIC_LED_ROUGE_POIDS "esp8266/actionneurs/led_rouge_poids"
#define TOPIC_LED_VERT_CONV2 "esp8266/actionneurs/led_vert_conv2"
#define TOPIC_ETAT_SYSTEME "esp8266/systeme/etat"
#define TOPIC_URGENCE "esp8266/systeme/urgence"
#define TOPIC_BOUTON_MARCHE "esp8266/boutons/marche"
#define TOPIC_TRIGGER_CAMERA "raspberry/camera/trigger"
#define TOPIC_TRIGGER_POIDS "esp8266/analyse/trigger_poids"

// Topics de souscription (Broker → ESP8266)
#define TOPIC_SUB_RESULTAT_CAMERA "raspberry/camera/resultat"
#define TOPIC_SUB_RESULTAT_POIDS "esp8266/analyse/resultat_poids"
#define TOPIC_SUB_COMMANDE "esp8266/commandes/#"

// ============================================================================
// CONSTANTES DE CONFIGURATION
// ============================================================================

#define DISTANCE_DETECTION 10.0  // Distance de détection en cm
#define POIDS_MIN 50.0           // Poids minimum acceptable en grammes
#define POIDS_MAX 500.0          // Poids maximum acceptable en grammes
#define CALIBRATION_FACTOR 2280  // Facteur de calibration HX711 (à ajuster)

#define PUBLISH_INTERVAL 500     // Intervalle de publication en ms
#define RECONNECT_DELAY 5000     // Délai de reconnexion en ms

// ============================================================================
// ÉTATS DU GRAFCET
// ============================================================================

enum EtatGrafcet {
  E0_INIT,                    // État initial
  E1_MARCHE_CONV,            // Convoyeur 1 en marche
  E2_DETECTION_OBJET,        // Objet détecté - Stop convoyeur
  E3_CONTROL_CAMERA,         // Contrôle caméra en cours
  E4_CONTROL_POIDS,          // Contrôle poids en cours
  E5_LED_VERT_MARCHE,        // LED verte - Marche conv
  E6_LED_ROUGE_CAMERA,       // LED rouge - Caméra
  E7_LED_ROUGE_POIDS,        // LED rouge - Poids
  E8_LED_VERT_CONV2,         // LED verte - Conv2 sans hazards
  E9_STOP_CONV,              // Stop convoyeur
  E10_LED_ROUGE_MARCHE_CONV, // LED rouge - Marche conv
  E11_STOP_CONV2,            // Stop convoyeur 2
  E12_MARCHE_CONV2           // Marche conv2 sans hazards
};

// ============================================================================
// VARIABLES GLOBALES
// ============================================================================

WiFiClient espClient;
PubSubClient mqttClient(espClient);
HX711 scale;

EtatGrafcet etatActuel = E0_INIT;
EtatGrafcet etatPrecedent = E0_INIT;

// Variables capteurs
float distance = 0.0;
float poids = 0.0;
bool boutonMarcheAppuye = false;
bool boutonUrgenceAppuye = false;
bool objetDetecte = false;

// Variables résultats
bool resultatCameraOK = false;
bool resultatPoidsOK = false;
bool resultatCameraRecu = false;
bool resultatPoidsRecu = false;

// Variables de timing
unsigned long dernierPublish = 0;
unsigned long derniereMesure = 0;

// États des actionneurs
bool moteur1Actif = false;
bool moteur2Actif = false;
bool ledVertConvActif = false;
bool ledRougeCameraActif = false;
bool ledRougePoidsActif = false;
bool ledVertConv2Actif = false;

// ============================================================================
// SETUP
// ============================================================================

void setup() {
  Serial.begin(115200);
  Serial.println("\n\n=== Démarrage ESP8266 - Système IoT ===");

  // Configuration des pins
  configurerPins();

  // Initialisation du capteur de poids
  scale.begin(HX711_DOUT, HX711_SCK);
  scale.set_scale(CALIBRATION_FACTOR);
  scale.tare(); // Reset de la balance
  Serial.println("Balance HX711 initialisée");

  // Connexion WiFi
  connecterWiFi();

  // Configuration MQTT
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(callbackMQTT);
  mqttClient.setBufferSize(512);

  // Connexion MQTT
  connecterMQTT();

  // État initial
  etatActuel = E0_INIT;
  Serial.println("Système prêt - En attente du bouton de démarrage");

  publierEtatSysteme();
}

// ============================================================================
// LOOP PRINCIPAL
// ============================================================================

void loop() {
  // Maintien de la connexion MQTT
  if (!mqttClient.connected()) {
    connecterMQTT();
  }
  mqttClient.loop();

  // Lecture des capteurs
  lireCapteurs();

  // Vérification arrêt d'urgence
  if (boutonUrgenceAppuye) {
    arreterTout();
    publierUrgence();
    return;
  }

  // Machine à états GRAFCET
  executerGrafcet();

  // Publication périodique des données
  if (millis() - dernierPublish > PUBLISH_INTERVAL) {
    publierDonnees();
    dernierPublish = millis();
  }
}

// ============================================================================
// CONFIGURATION DES PINS
// ============================================================================

void configurerPins() {
  // Capteur ultrason
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  // Moteurs
  pinMode(MOTOR1_IN1, OUTPUT);
  pinMode(MOTOR1_IN2, OUTPUT);
  pinMode(MOTOR2_IN3, OUTPUT);
  pinMode(MOTOR2_IN4, OUTPUT);

  // LEDs
  pinMode(LED_VERT_CONV, OUTPUT);
  pinMode(LED_ROUGE_CAMERA, OUTPUT);
  pinMode(LED_ROUGE_POIDS, OUTPUT);
  pinMode(LED_VERT_CONV2, OUTPUT);

  // Boutons
  pinMode(BTN_MARCHE, INPUT_PULLUP);
  pinMode(BTN_URGENCE, INPUT_PULLUP);

  // État initial - tout éteint
  arreterTout();
}

// ============================================================================
// CONNEXION WIFI
// ============================================================================

void connecterWiFi() {
  Serial.print("Connexion WiFi à: ");
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
    Serial.println("\nWiFi connecté!");
    Serial.print("Adresse IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nÉchec de connexion WiFi!");
  }
}

// ============================================================================
// CONNEXION MQTT
// ============================================================================

void connecterMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Connexion au broker MQTT...");

    bool connecte;
    if (strlen(MQTT_USER) > 0) {
      connecte = mqttClient.connect(MQTT_CLIENT_ID, MQTT_USER, MQTT_PASSWORD);
    } else {
      connecte = mqttClient.connect(MQTT_CLIENT_ID);
    }

    if (connecte) {
      Serial.println("Connecté!");

      // Souscription aux topics
      mqttClient.subscribe(TOPIC_SUB_RESULTAT_CAMERA);
      mqttClient.subscribe(TOPIC_SUB_RESULTAT_POIDS);
      mqttClient.subscribe(TOPIC_SUB_COMMANDE);

      Serial.println("Souscriptions actives");

      // Publication du statut
      publierEtatSysteme();

    } else {
      Serial.print("Échec, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" Nouvelle tentative dans 5s");
      delay(RECONNECT_DELAY);
    }
  }
}

// ============================================================================
// CALLBACK MQTT
// ============================================================================

void callbackMQTT(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.print("Message reçu [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.println(message);

  // Traitement du résultat caméra
  if (strcmp(topic, TOPIC_SUB_RESULTAT_CAMERA) == 0) {
    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, message);

    if (!error) {
      String status = doc["status"] | "KO";
      resultatCameraOK = (status == "OK");
      resultatCameraRecu = true;

      Serial.print("Résultat caméra: ");
      Serial.println(resultatCameraOK ? "OK" : "KO");
    }
  }

  // Traitement du résultat poids
  if (strcmp(topic, TOPIC_SUB_RESULTAT_POIDS) == 0) {
    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, message);

    if (!error) {
      String status = doc["status"] | "KO";
      resultatPoidsOK = (status == "OK");
      resultatPoidsRecu = true;

      Serial.print("Résultat poids: ");
      Serial.println(resultatPoidsOK ? "OK" : "KO");
    }
  }

  // Traitement des commandes
  if (strncmp(topic, "esp8266/commandes/", 18) == 0) {
    traiterCommande(topic, message);
  }
}

// ============================================================================
// LECTURE DES CAPTEURS
// ============================================================================

void lireCapteurs() {
  // Lecture du bouton marche
  boutonMarcheAppuye = (digitalRead(BTN_MARCHE) == LOW);

  // Lecture du bouton urgence
  boutonUrgenceAppuye = (digitalRead(BTN_URGENCE) == LOW);

  // Lecture distance ultrason
  distance = mesurerDistance();
  objetDetecte = (distance > 0 && distance < DISTANCE_DETECTION);

  // Lecture poids (si balance stable)
  if (scale.is_ready()) {
    poids = scale.get_units(3); // Moyenne de 3 lectures
    if (poids < 0) poids = 0;
  }
}

// ============================================================================
// MESURE DISTANCE ULTRASON
// ============================================================================

float mesurerDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duree = pulseIn(ECHO_PIN, HIGH, 30000); // Timeout 30ms

  if (duree == 0) {
    return -1; // Pas de réponse
  }

  float dist = duree * 0.034 / 2.0;
  return dist;
}

// ============================================================================
// MACHINE À ÉTATS GRAFCET
// ============================================================================

void executerGrafcet() {
  // Sauvegarde de l'état pour détecter les changements
  etatPrecedent = etatActuel;

  switch (etatActuel) {

    case E0_INIT:
      // Attente du bouton de démarrage
      if (boutonMarcheAppuye) {
        etatActuel = E1_MARCHE_CONV;
        Serial.println("GRAFCET: E0 → E1 (Bouton marche appuyé)");
      }
      break;

    case E1_MARCHE_CONV:
      // Démarrage du convoyeur 1
      demarrerMoteur1();
      allumerLED(LED_VERT_CONV);

      // Transition si objet détecté
      if (objetDetecte) {
        etatActuel = E2_DETECTION_OBJET;
        Serial.println("GRAFCET: E1 → E2 (Objet détecté)");
      }
      break;

    case E2_DETECTION_OBJET:
      // Arrêt du convoyeur
      arreterMoteur1();
      eteindreLED(LED_VERT_CONV);

      // Passage au contrôle caméra
      etatActuel = E3_CONTROL_CAMERA;
      Serial.println("GRAFCET: E2 → E3 (Arrêt convoyeur)");
      break;

    case E3_CONTROL_CAMERA:
      // Déclenchement de l'analyse caméra
      allumerLED(LED_ROUGE_CAMERA);
      triggerCamera();

      // Attente du résultat
      if (resultatCameraRecu) {
        if (resultatCameraOK) {
          etatActuel = E4_CONTROL_POIDS;
          Serial.println("GRAFCET: E3 → E4 (Caméra OK)");
        } else {
          etatActuel = E6_LED_ROUGE_CAMERA;
          Serial.println("GRAFCET: E3 → E6 (Caméra KO)");
        }
        eteindreLED(LED_ROUGE_CAMERA);
        resultatCameraRecu = false;
      }
      break;

    case E4_CONTROL_POIDS:
      // Déclenchement de l'analyse poids
      allumerLED(LED_ROUGE_POIDS);
      triggerPoids();

      // Attente du résultat
      if (resultatPoidsRecu) {
        if (resultatPoidsOK) {
          etatActuel = E8_LED_VERT_CONV2;
          Serial.println("GRAFCET: E4 → E8 (Poids OK)");
        } else {
          etatActuel = E7_LED_ROUGE_POIDS;
          Serial.println("GRAFCET: E4 → E7 (Poids KO)");
        }
        eteindreLED(LED_ROUGE_POIDS);
        resultatPoidsRecu = false;
      }
      break;

    case E6_LED_ROUGE_CAMERA:
      // Produit défectueux - caméra
      allumerLED(LED_ROUGE_CAMERA);
      delay(2000); // Affichage pendant 2s
      eteindreLED(LED_ROUGE_CAMERA);

      etatActuel = E9_STOP_CONV;
      Serial.println("GRAFCET: E6 → E9");
      break;

    case E7_LED_ROUGE_POIDS:
      // Produit défectueux - poids
      allumerLED(LED_ROUGE_POIDS);
      delay(2000);
      eteindreLED(LED_ROUGE_POIDS);

      etatActuel = E9_STOP_CONV;
      Serial.println("GRAFCET: E7 → E9");
      break;

    case E8_LED_VERT_CONV2:
      // Produit OK - convoyeur 2
      allumerLED(LED_VERT_CONV2);
      demarrerMoteur2();

      // Attente que l'objet parte
      if (!objetDetecte) {
        etatActuel = E11_STOP_CONV2;
        Serial.println("GRAFCET: E8 → E11 (Objet parti)");
      }
      break;

    case E9_STOP_CONV:
      // Arrêt - produit défectueux
      arreterMoteur1();

      // Attente que l'objet parte
      if (!objetDetecte) {
        etatActuel = E0_INIT;
        Serial.println("GRAFCET: E9 → E0 (Retour initial)");
      }
      break;

    case E11_STOP_CONV2:
      // Arrêt convoyeur 2
      arreterMoteur2();
      eteindreLED(LED_VERT_CONV2);

      etatActuel = E0_INIT;
      Serial.println("GRAFCET: E11 → E0 (Retour initial)");
      break;
  }

  // Publication si changement d'état
  if (etatActuel != etatPrecedent) {
    publierEtatSysteme();
  }
}

// ============================================================================
// CONTRÔLE DES MOTEURS
// ============================================================================

void demarrerMoteur1() {
  digitalWrite(MOTOR1_IN1, HIGH);
  digitalWrite(MOTOR1_IN2, LOW);
  moteur1Actif = true;
  publierMoteur1();
}

void arreterMoteur1() {
  digitalWrite(MOTOR1_IN1, LOW);
  digitalWrite(MOTOR1_IN2, LOW);
  moteur1Actif = false;
  publierMoteur1();
}

void demarrerMoteur2() {
  digitalWrite(MOTOR2_IN3, HIGH);
  digitalWrite(MOTOR2_IN4, LOW);
  moteur2Actif = true;
  publierMoteur2();
}

void arreterMoteur2() {
  digitalWrite(MOTOR2_IN3, LOW);
  digitalWrite(MOTOR2_IN4, LOW);
  moteur2Actif = false;
  publierMoteur2();
}

// ============================================================================
// CONTRÔLE DES LEDS
// ============================================================================

void allumerLED(int pin) {
  digitalWrite(pin, HIGH);
  publierEtatLEDs();
}

void eteindreLED(int pin) {
  digitalWrite(pin, LOW);
  publierEtatLEDs();
}

// ============================================================================
// TRIGGERS
// ============================================================================

void triggerCamera() {
  StaticJsonDocument<200> doc;
  doc["timestamp"] = millis();
  doc["distance"] = distance;
  doc["declencheur"] = "esp8266";

  char buffer[200];
  serializeJson(doc, buffer);

  mqttClient.publish(TOPIC_TRIGGER_CAMERA, buffer);
  Serial.println("Trigger caméra envoyé");
}

void triggerPoids() {
  StaticJsonDocument<200> doc;
  doc["timestamp"] = millis();
  doc["poids"] = poids;
  doc["poids_min"] = POIDS_MIN;
  doc["poids_max"] = POIDS_MAX;

  // Analyse locale du poids
  bool poidsOK = (poids >= POIDS_MIN && poids <= POIDS_MAX);
  doc["status"] = poidsOK ? "OK" : "KO";

  char buffer[200];
  serializeJson(doc, buffer);

  mqttClient.publish(TOPIC_TRIGGER_POIDS, buffer);

  // Auto-validation du résultat poids
  resultatPoidsOK = poidsOK;
  resultatPoidsRecu = true;

  Serial.print("Trigger poids envoyé - Résultat: ");
  Serial.println(poidsOK ? "OK" : "KO");
}

// ============================================================================
// ARRÊT D'URGENCE
// ============================================================================

void arreterTout() {
  arreterMoteur1();
  arreterMoteur2();
  eteindreLED(LED_VERT_CONV);
  eteindreLED(LED_ROUGE_CAMERA);
  eteindreLED(LED_ROUGE_POIDS);
  eteindreLED(LED_VERT_CONV2);

  etatActuel = E0_INIT;

  Serial.println("ARRÊT D'URGENCE ACTIVÉ");
}

// ============================================================================
// PUBLICATION MQTT
// ============================================================================

void publierDonnees() {
  publierDistance();
  publierPoids();
  publierMoteur1();
  publierMoteur2();
  publierEtatLEDs();
  publierBoutons();
}

void publierDistance() {
  StaticJsonDocument<100> doc;
  doc["distance_cm"] = distance;
  doc["objet_detecte"] = objetDetecte;
  doc["timestamp"] = millis();

  char buffer[100];
  serializeJson(doc, buffer);
  mqttClient.publish(TOPIC_DISTANCE, buffer);
}

void publierPoids() {
  StaticJsonDocument<100> doc;
  doc["poids_grammes"] = poids;
  doc["timestamp"] = millis();

  char buffer[100];
  serializeJson(doc, buffer);
  mqttClient.publish(TOPIC_POIDS, buffer);
}

void publierMoteur1() {
  StaticJsonDocument<100> doc;
  doc["actif"] = moteur1Actif;
  doc["timestamp"] = millis();

  char buffer[100];
  serializeJson(doc, buffer);
  mqttClient.publish(TOPIC_MOTEUR1, buffer);
}

void publierMoteur2() {
  StaticJsonDocument<100> doc;
  doc["actif"] = moteur2Actif;
  doc["timestamp"] = millis();

  char buffer[100];
  serializeJson(doc, buffer);
  mqttClient.publish(TOPIC_MOTEUR2, buffer);
}

void publierEtatLEDs() {
  StaticJsonDocument<200> doc;
  doc["led_vert_conv"] = digitalRead(LED_VERT_CONV);
  doc["led_rouge_camera"] = digitalRead(LED_ROUGE_CAMERA);
  doc["led_rouge_poids"] = digitalRead(LED_ROUGE_POIDS);
  doc["led_vert_conv2"] = digitalRead(LED_VERT_CONV2);
  doc["timestamp"] = millis();

  char buffer[200];
  serializeJson(doc, buffer);

  mqttClient.publish(TOPIC_LED_VERT_CONV, buffer);
}

void publierBoutons() {
  StaticJsonDocument<100> doc;
  doc["bouton_marche"] = boutonMarcheAppuye;
  doc["timestamp"] = millis();

  char buffer[100];
  serializeJson(doc, buffer);
  mqttClient.publish(TOPIC_BOUTON_MARCHE, buffer);
}

void publierEtatSysteme() {
  StaticJsonDocument<300> doc;

  // État GRAFCET
  String nomEtat = getNomEtat(etatActuel);
  doc["etat_grafcet"] = nomEtat;
  doc["etat_numero"] = etatActuel;

  // États actionneurs
  doc["moteur1_actif"] = moteur1Actif;
  doc["moteur2_actif"] = moteur2Actif;

  // États capteurs
  doc["objet_detecte"] = objetDetecte;
  doc["distance"] = distance;
  doc["poids"] = poids;

  // États boutons
  doc["bouton_marche"] = boutonMarcheAppuye;
  doc["bouton_urgence"] = boutonUrgenceAppuye;

  doc["timestamp"] = millis();

  char buffer[300];
  serializeJson(doc, buffer);
  mqttClient.publish(TOPIC_ETAT_SYSTEME, buffer);

  Serial.print("État système publié: ");
  Serial.println(nomEtat);
}

void publierUrgence() {
  StaticJsonDocument<100> doc;
  doc["urgence_active"] = true;
  doc["timestamp"] = millis();

  char buffer[100];
  serializeJson(doc, buffer);
  mqttClient.publish(TOPIC_URGENCE, buffer, true); // Retained message
}

// ============================================================================
// TRAITEMENT DES COMMANDES
// ============================================================================

void traiterCommande(const char* topic, String message) {
  // Commande reset
  if (strstr(topic, "reset")) {
    Serial.println("Commande RESET reçue");
    ESP.restart();
  }

  // Commande tare balance
  if (strstr(topic, "tare")) {
    Serial.println("Commande TARE reçue");
    scale.tare();
  }

  // Commande calibration
  if (strstr(topic, "calibration")) {
    float facteur = message.toFloat();
    if (facteur > 0) {
      scale.set_scale(facteur);
      Serial.print("Nouveau facteur de calibration: ");
      Serial.println(facteur);
    }
  }
}

// ============================================================================
// UTILITAIRES
// ============================================================================

String getNomEtat(EtatGrafcet etat) {
  switch (etat) {
    case E0_INIT: return "E0_INIT";
    case E1_MARCHE_CONV: return "E1_MARCHE_CONV";
    case E2_DETECTION_OBJET: return "E2_DETECTION_OBJET";
    case E3_CONTROL_CAMERA: return "E3_CONTROL_CAMERA";
    case E4_CONTROL_POIDS: return "E4_CONTROL_POIDS";
    case E5_LED_VERT_MARCHE: return "E5_LED_VERT_MARCHE";
    case E6_LED_ROUGE_CAMERA: return "E6_LED_ROUGE_CAMERA";
    case E7_LED_ROUGE_POIDS: return "E7_LED_ROUGE_POIDS";
    case E8_LED_VERT_CONV2: return "E8_LED_VERT_CONV2";
    case E9_STOP_CONV: return "E9_STOP_CONV";
    case E10_LED_ROUGE_MARCHE_CONV: return "E10_LED_ROUGE_MARCHE_CONV";
    case E11_STOP_CONV2: return "E11_STOP_CONV2";
    case E12_MARCHE_CONV2: return "E12_MARCHE_CONV2";
    default: return "INCONNU";
  }
}
