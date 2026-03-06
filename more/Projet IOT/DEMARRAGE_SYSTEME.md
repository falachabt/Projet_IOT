# 🚀 DÉMARRAGE DU SYSTÈME IoT - Guide Complet

## ✅ Checklist de démarrage rapide

### 1️⃣ **Démarrer le Broker MQTT (Mosquitto)**

```bash
# Démarrer Docker Compose
docker-compose up -d

# Vérifier que Mosquitto fonctionne
docker ps
# Devrait afficher : mosquitto running sur le port 1883
```

### 2️⃣ **Démarrer le Backend (Jumeau Numérique)**

```bash
# Aller dans le dossier backend
cd digital-twin-backend

# Installer les dépendances (première fois seulement)
npm install

# Démarrer le serveur
npm start
```

**✅ Vérifications** :
- Console affiche : `✓ Serveur démarré sur http://localhost:3000`
- Console affiche : `✓ Connecté au broker MQTT`
- Console affiche : `✓ WebSocket server ready`

### 3️⃣ **Démarrer le Frontend (Interface Web)**

```bash
# Ouvrir un nouveau terminal
cd digital-twin-frontend

# Installer les dépendances (première fois seulement)
npm install

# Démarrer le serveur de développement
npm run dev
```

**✅ Vérifications** :
- Console affiche : `Local: http://localhost:5173/`
- Navigateur ouvert automatiquement sur `http://localhost:5173`
- Interface web chargée avec design premium

### 4️⃣ **Flasher et démarrer l'ESP8266**

```bash
# Dans PlatformIO
1. Ouvrir le projet : c:\Users\walid\OneDrive\Documents\PlatformIO\Projects\iot
2. Connecter l'ESP8266 en USB
3. Cliquer sur "Upload" (flèche →)
4. Ouvrir le "Serial Monitor" (prise électrique)
```

**✅ Vérifications dans le Serial Monitor** :
```
====================================
   SYSTÈME IOT - CONTRÔLE FLACONS
====================================
[WiFi]   📡 Connexion à TestIphone...
[WiFi]   ✓ Connecté ! IP: 172.20.10.X
[MQTT]   🔌 Connexion au broker...
[MQTT]   ✓ Connecté au broker MQTT !
```

---

## 🔍 VÉRIFICATION COMPLÈTE

### A) ESP8266 communique avec le Broker

**Dans le terminal, exécuter** :
```bash
# Écouter TOUS les messages de l'ESP8266
docker exec -it mosquitto mosquitto_sub -h localhost -t "esp8266/#" -v
```

**Vous devriez voir** :
```
esp8266/ultrason {"distance_cm":25.3,"flacon_detecte":false,"timestamp":"2026-03-03T..."}
esp8266/moteur {"etat":"ARRET","vitesse":0,"timestamp":"2026-03-03T..."}
esp8266/leds {"rouge_camera":0,"rouge_poids":0,"vert":0,"timestamp":"2026-03-03T..."}
esp8266/systeme/etat {"etat_grafcet":"E1_MARCHE_CONV","moteur1_actif":true,...}
```

### B) Backend reçoit les données

**Dans les logs du backend**, vous devriez voir :
```
📨 [esp8266/ultrason] Distance: 25.3 cm
📨 [esp8266/moteur] État: ARRET
📨 [esp8266/leds] LEDs mises à jour
📨 [esp8266/systeme/etat] Grafcet: E1_MARCHE_CONV
```

### C) Frontend affiche les données en temps réel

**Ouvrir** : http://localhost:5173

**Vérifier** :
- ✅ Statistiques en haut montrent des valeurs
- ✅ Carte "Détection d'Objet" affiche la distance ou l'état
- ✅ Carte "État du Système" affiche l'état Grafcet
- ✅ Carte "Moteur" affiche l'état du moteur
- ✅ Carte "LEDs" affiche l'état des LEDs
- ✅ Status "Connecté" en vert dans le header

---

## 🧪 TESTER LES COMMANDES

### 1. Tester le bouton MARCHE virtuel

**Dans le frontend** :
- Cliquer et maintenir le bouton **MARCHE** (vert)
- ESP8266 devrait passer en état `E1_MARCHE_CONV`
- Moteur 1 devrait démarrer

**Ou via MQTT** :
```bash
docker exec -it mosquitto mosquitto_pub -h localhost -t "esp8266/boutons/marche/cmd" -m '{"etat":true}'
```

### 2. Tester le bouton URGENCE virtuel

**Dans le frontend** :
- Cliquer et maintenir le bouton **URGENCE** (rouge)
- Tout devrait s'arrêter
- LED rouge devrait s'allumer

**Ou via MQTT** :
```bash
docker exec -it mosquitto mosquitto_pub -h localhost -t "esp8266/boutons/urgence/cmd" -m '{"etat":true}'
```

### 3. Tester le contrôle du moteur

**Dans le frontend** :
- Utiliser les boutons de la carte "Moteur"
- Démarrer / Arrêter
- Changer la vitesse avec le slider

**Ou via MQTT** :
```bash
# Démarrer le moteur à pleine vitesse
docker exec -it mosquitto mosquitto_pub -h localhost -t "esp8266/moteur/cmd" -m '{"etat":"MARCHE","vitesse":255}'

# Arrêter le moteur
docker exec -it mosquitto mosquitto_pub -h localhost -t "esp8266/moteur/cmd" -m '{"etat":"ARRET","vitesse":0}'
```

### 4. Tester les LEDs

**Dans le frontend** :
- Cliquer sur les boutons LED (Verte, Rouge Caméra, Rouge Poids)

**Ou via MQTT** :
```bash
# Allumer LED verte
docker exec -it mosquitto mosquitto_pub -h localhost -t "esp8266/leds/cmd" -m '{"led":"vert","etat":1}'

# Éteindre LED verte
docker exec -it mosquitto mosquitto_pub -h localhost -t "esp8266/leds/cmd" -m '{"led":"vert","etat":0}'
```

### 5. Simuler une détection caméra

**Via MQTT** :
```bash
# Produit conforme (bouchon + étiquette OK)
docker exec -it mosquitto mosquitto_pub -h localhost -t "raspberry/camera/resultat" -m '{
  "status": "OK",
  "bottle": {"detected": true, "confidence": 0.95},
  "cap": {"detected": true, "confidence": 0.92},
  "label": {"detected": true, "confidence": 0.88},
  "elapsed_ms": 145.5,
  "timestamp": "2026-03-03T10:30:00Z"
}'

# Produit non conforme (pas de bouchon)
docker exec -it mosquitto mosquitto_pub -h localhost -t "raspberry/camera/resultat" -m '{
  "status": "KO",
  "bottle": {"detected": true, "confidence": 0.94},
  "cap": {"detected": false, "confidence": 0.15},
  "label": {"detected": true, "confidence": 0.87},
  "elapsed_ms": 132.8,
  "timestamp": "2026-03-03T10:31:00Z"
}'
```

---

## 🐛 PROBLÈMES COURANTS

### ❌ Backend ne se connecte pas au broker MQTT

**Erreur** : `Connection refused to localhost:1883`

**Solution** :
```bash
# Vérifier que Docker est démarré
docker ps

# Si pas de container mosquitto, démarrer Docker Compose
docker-compose up -d

# Vérifier les logs
docker logs mosquitto
```

### ❌ ESP8266 ne se connecte pas au WiFi

**Solution** :
1. Vérifier le SSID et mot de passe dans `main.cpp`
2. S'assurer que le partage de connexion iPhone est actif
3. Approcher l'ESP8266 du téléphone
4. Vérifier dans le Serial Monitor

### ❌ ESP8266 connecté WiFi mais pas MQTT

**Solution** :
1. Vérifier l'adresse IP du broker dans `main.cpp`
2. Si `localhost`, changer pour l'IP du PC (ex: `192.168.1.X`)
3. L'ESP8266 doit pouvoir ping le PC
4. Vérifier le firewall du PC

### ❌ Frontend affiche "Déconnecté"

**Solution** :
1. Vérifier que le backend tourne sur `http://localhost:3000`
2. Vérifier dans la console du navigateur (F12)
3. Recharger la page (Ctrl+R ou Cmd+R)

### ❌ Données affichées mais pas de mise à jour

**Solution** :
1. Vérifier la connexion WebSocket dans la console navigateur
2. Relancer le backend
3. Vider le cache du navigateur

---

## 📊 ARCHITECTURE DU SYSTÈME

```
┌─────────────┐
│  ESP8266    │  ──(WiFi)──>  📡 Topics MQTT:
│             │                   - esp8266/ultrason
│  Capteurs:  │                   - esp8266/moteur
│  - IR       │                   - esp8266/leds
│  - Moteurs  │                   - esp8266/systeme/etat
│  - LEDs     │
└─────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│    MQTT Broker (Mosquitto)          │
│    localhost:1883                    │
│    (Docker Container)                │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│    Backend (Node.js + Express)      │
│    localhost:3000                    │
│                                      │
│    - MQTT Handler (écoute topics)   │
│    - REST API (/api/control/...)    │
│    - WebSocket Server                │
│    - InfluxDB (historique)           │
└─────────────────────────────────────┘
       │
       ▼ (WebSocket)
┌─────────────────────────────────────┐
│    Frontend (React + Vite)          │
│    localhost:5173                    │
│                                      │
│    🎨 Interface web premium          │
│    - Dashboard en temps réel         │
│    - Contrôles (moteur, LEDs)        │
│    - Boutons virtuels                │
│    - Graphiques historiques          │
└─────────────────────────────────────┘
```

---

## 🎯 WORKFLOW NORMAL

1. **ESP8266 détecte un objet** (capteur IR)
   - Publie sur `esp8266/ultrason`
   - Change d'état Grafcet → `E2_DETECTION_OBJET`

2. **ESP8266 déclenche la caméra** (via GPIO ou MQTT)
   - Passe en état `E3_CONTROL_CAMERA`

3. **Raspberry Pi analyse l'image** (YOLO)
   - Publie le résultat sur `raspberry/camera/resultat`

4. **ESP8266 reçoit le résultat**
   - Si OK → `E8_LED_VERT_CONV2` (LED verte)
   - Si KO → `E6_LED_ROUGE_CAMERA` (LED rouge)

5. **Backend collecte tout**
   - Stocke dans InfluxDB
   - Envoie au Frontend via WebSocket
   - Affiche dans l'interface en temps réel

6. **Statistiques mises à jour**
   - Total analyses
   - Taux OK/KO
   - Graphiques d'historique

---

## ✨ C'EST PRÊT !

Tous les systèmes devraient maintenant communiquer parfaitement ! 🎉

👉 Ouvrir : **http://localhost:5173** pour voir l'interface premium en action !
