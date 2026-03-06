# 🔍 Comment vérifier que l'ESP8266 fonctionne

## ✅ Étape 1 : Moniteur Série PlatformIO

1. **Ouvrir le moniteur série** dans PlatformIO (icône prise en bas)
2. **Vérifier les messages au démarrage** :
   ```
   ====================================
      SYSTÈME IOT - CONTRÔLE FLACONS
   ====================================
   [WiFi]   📡 Connexion à TestIphone...
   [WiFi]   ✓ Connecté ! IP: 172.20.10.3
   [MQTT]   🔌 Connexion au broker...
   [MQTT]   ✓ Connecté au broker MQTT !
   [MQTT]   📨 Abonné aux topics de commande
   ```

3. **Messages à surveiller** :
   - ✅ Connexion WiFi réussie avec adresse IP
   - ✅ Connexion MQTT réussie
   - ✅ Publications régulières (ultrason, moteur, LEDs)
   - ✅ État Grafcet qui change

## ✅ Étape 2 : Vérifier la connexion MQTT

### Option A : Utiliser MQTT Explorer
1. Télécharger MQTT Explorer : http://mqtt-explorer.com/
2. Se connecter au broker :
   - **Host**: localhost
   - **Port**: 1883
3. Vérifier les topics :
   - `esp8266/ultrason` - Capteur de distance
   - `esp8266/moteur` - État moteur
   - `esp8266/leds` - État des LEDs
   - `esp8266/systeme/etat` - État Grafcet

### Option B : Ligne de commande
```bash
# S'abonner à tous les topics ESP8266
docker exec -it mosquitto mosquitto_sub -h localhost -t "esp8266/#" -v

# Publier une commande de test
docker exec -it mosquitto mosquitto_pub -h localhost -t "esp8266/moteur/cmd" -m '{"etat":"MARCHE","vitesse":255}'
```

## ✅ Étape 3 : Vérifier dans le jumeau numérique

1. **Démarrer le backend** :
   ```bash
   cd digital-twin-backend
   npm start
   ```
   Vérifier : `✓ Connecté au broker MQTT`

2. **Démarrer le frontend** :
   ```bash
   cd digital-twin-frontend
   npm run dev
   ```
   Ouvrir : http://localhost:5173

3. **Observer les données** :
   - Les cartes doivent afficher des valeurs en temps réel
   - L'état Grafcet doit changer
   - Les statistiques doivent s'incrémenter

## 🔴 Problèmes courants

### ESP8266 ne se connecte pas au WiFi
- Vérifier le SSID et mot de passe dans main.cpp
- Vérifier que le téléphone est en mode partage de connexion
- Distance trop grande du point d'accès

### ESP8266 connecté mais pas de données MQTT
- Vérifier l'adresse du broker dans main.cpp
- Si broker = localhost, l'ESP8266 doit pointer vers l'IP du PC
- Vérifier que Mosquitto est démarré : `docker ps`

### Données MQTT mais rien dans le jumeau numérique
- Vérifier que le backend est démarré
- Vérifier les logs du backend pour voir les messages MQTT
- Vérifier que MQTT_TOPICS dans .env contient "esp8266/#"

## 📊 Messages de test

Pour tester l'ESP8266 manuellement :

```bash
# Démarrer le moteur
docker exec -it mosquitto mosquitto_pub -h localhost -t "esp8266/moteur/cmd" -m '{"etat":"MARCHE","vitesse":200}'

# Arrêter le moteur
docker exec -it mosquitto mosquitto_pub -h localhost -t "esp8266/moteur/cmd" -m '{"etat":"ARRET","vitesse":0}'

# Allumer LED verte
docker exec -it mosquitto mosquitto_pub -h localhost -t "esp8266/leds/cmd" -m '{"led":"vert","etat":1}'

# Bouton marche virtuel
docker exec -it mosquitto mosquitto_pub -h localhost -t "esp8266/boutons/marche/cmd" -m '{"etat":true}'
```

## ✅ Checklist rapide

- [ ] ESP8266 se connecte au WiFi (voir IP dans le moniteur série)
- [ ] ESP8266 se connecte au MQTT (voir "✓ Connecté au broker")
- [ ] Messages publiés visibles dans MQTT Explorer
- [ ] Backend reçoit les messages (voir logs backend)
- [ ] Frontend affiche les données en temps réel
- [ ] Commandes depuis le frontend fonctionnent
