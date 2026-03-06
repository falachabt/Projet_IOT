# 🚀 PROJET IoT - COMMENCER ICI

## 👋 Bienvenue !

Ce projet est un **système IoT complet** avec jumeau numérique pour le contrôle qualité de flacons.

---

## ✨ CE QUI VIENT D'ÊTRE FAIT

### 🎨 **Interface Web Ultra Premium**
J'ai créé une interface professionnelle de **qualité production** avec :
- ✅ Design moderne avec glass morphism
- ✅ Animations fluides et sophistiquées
- ✅ Gradients animés multicolores
- ✅ Effets 3D au hover
- ✅ Bordures animées avec glows
- ✅ Alertes dramatiques
- ✅ Spinner de chargement premium
- ✅ Totalement responsive

### 📡 **Système IoT Complet**
- ✅ ESP8266 avec capteurs (IR, moteurs, LEDs)
- ✅ Grafcet pour la logique de contrôle
- ✅ MQTT pour la communication
- ✅ Boutons virtuels (MARCHE/URGENCE)
- ✅ Contrôle à distance
- ✅ Backend Node.js avec WebSocket
- ✅ Frontend React ultra moderne
- ✅ InfluxDB pour l'historique
- ✅ Intégration caméra YOLO

---

## 📚 GUIDES DISPONIBLES

### 🎯 **Pour Démarrer** (COMMENCEZ ICI)
1. **[DEMARRAGE_SYSTEME.md](DEMARRAGE_SYSTEME.md)** ⭐
   - Comment démarrer TOUT le système
   - Checklist complète
   - Tests de vérification
   - Architecture du système
   - Workflow complet

### 🔍 **Pour Vérifier que ça Marche**
2. **[TEST_ESP8266.md](TEST_ESP8266.md)** ⭐
   - Comment savoir si l'ESP8266 fonctionne
   - Moniteur série
   - MQTT Explorer
   - Commandes de test
   - Problèmes courants et solutions

### 🎨 **Pour Comprendre l'Interface**
3. **[INTERFACE_PREMIUM_GUIDE.md](INTERFACE_PREMIUM_GUIDE.md)** ⭐
   - Tous les effets visuels
   - Palette de couleurs
   - Animations implémentées
   - Comment personnaliser
   - Astuces de test

### ⚙️ **Configuration ESP8266**
4. **[CONFIGURATION_ESP8266.md](CONFIGURATION_ESP8266.md)**
   - Pinout complet
   - Configuration WiFi
   - Configuration MQTT
   - Calibration capteurs

5. **[GUIDE_ESP8266_TOPICS.md](GUIDE_ESP8266_TOPICS.md)**
   - Tous les topics MQTT
   - Format des messages
   - Exemples de commandes

### 🖥️ **Configuration Backend**
6. **[README_DIGITAL_TWIN.md](README_DIGITAL_TWIN.md)**
   - Architecture du jumeau numérique
   - Installation backend/frontend
   - Configuration InfluxDB
   - API REST

### 📸 **Raspberry Pi & Caméra**
7. **[GUIDE_RASPBERRY_PI.md](GUIDE_RASPBERRY_PI.md)**
   - Installation YOLO
   - Configuration caméra
   - Détection bouteille/bouchon/étiquette

---

## ⚡ DÉMARRAGE RAPIDE (3 ÉTAPES)

### Étape 1️⃣ : Démarrer le Broker MQTT
```bash
docker-compose up -d
```

### Étape 2️⃣ : Démarrer Backend + Frontend
```bash
# Terminal 1
cd digital-twin-backend
npm start

# Terminal 2
cd digital-twin-frontend
npm run dev
```

### Étape 3️⃣ : Flasher l'ESP8266
```bash
# Dans PlatformIO
1. Ouvrir le projet iot
2. Upload vers ESP8266
3. Ouvrir Serial Monitor
```

---

## 🌐 ACCÈS RAPIDE

- **Interface Web** : http://localhost:5173
- **API Backend** : http://localhost:3000
- **MQTT Broker** : localhost:1883
- **InfluxDB** : http://localhost:8086

---

## 🎯 WORKFLOW NORMAL

```
1. ESP8266 détecte un objet (IR)
   ↓
2. Change d'état Grafcet → E2_DETECTION_OBJET
   ↓
3. Déclenche la caméra → E3_CONTROL_CAMERA
   ↓
4. Raspberry analyse (YOLO)
   ↓
5. Résultat OK/KO
   ↓
6. LED verte (OK) ou rouge (KO)
   ↓
7. Données dans InfluxDB
   ↓
8. Affichage temps réel dans interface web
   ↓
9. Statistiques mises à jour
```

---

## 🔍 VÉRIFICATIONS RAPIDES

### ✅ L'ESP8266 fonctionne ?
```bash
# Terminal - Écouter les messages
docker exec -it mosquitto mosquitto_sub -h localhost -t "esp8266/#" -v
```
**Résultat** : Vous devez voir des messages arriver

### ✅ Le Backend reçoit les données ?
**Regarder** les logs du backend
**Résultat** : Doit afficher `📨 [esp8266/...]`

### ✅ L'interface affiche ?
**Ouvrir** : http://localhost:5173
**Résultat** : Cartes avec données en temps réel

---

## 🧪 TESTER LES COMMANDES

### Démarrer le moteur
```bash
docker exec -it mosquitto mosquitto_pub -h localhost -t "esp8266/moteur/cmd" -m '{"etat":"MARCHE","vitesse":255}'
```

### Allumer LED verte
```bash
docker exec -it mosquitto mosquitto_pub -h localhost -t "esp8266/leds/cmd" -m '{"led":"vert","etat":1}'
```

### Bouton MARCHE virtuel
```bash
docker exec -it mosquitto mosquitto_pub -h localhost -t "esp8266/boutons/marche/cmd" -m '{"etat":true}'
```

### Simuler résultat caméra OK
```bash
docker exec -it mosquitto mosquitto_pub -h localhost -t "raspberry/camera/resultat" -m '{
  "status": "OK",
  "bottle": {"detected": true, "confidence": 0.95},
  "cap": {"detected": true, "confidence": 0.92},
  "label": {"detected": true, "confidence": 0.88},
  "elapsed_ms": 145.5
}'
```

---

## 🐛 PROBLÈMES COURANTS

### ❌ Backend ne démarre pas
```bash
# Tuer le processus sur le port 3000
npx kill-port 3000

# Redémarrer
npm start
```

### ❌ ESP8266 ne se connecte pas
1. Vérifier WiFi actif (partage connexion iPhone)
2. Vérifier SSID/mot de passe dans main.cpp
3. Approcher ESP8266 du téléphone
4. Voir Serial Monitor pour erreurs

### ❌ Pas de données dans l'interface
1. Vérifier backend actif
2. Vérifier WebSocket connecté (console navigateur F12)
3. Recharger la page (Ctrl+R)

---

## 📊 ARCHITECTURE

```
ESP8266 (Capteurs + Moteurs)
    ↓ WiFi + MQTT
Broker MQTT (Mosquitto)
    ↓ MQTT Topics
Backend (Node.js + Express)
    ↓ WebSocket
Frontend (React + Vite)
    ↓ Votre Navigateur
✨ INTERFACE PREMIUM ✨
```

---

## 🎨 DESIGN PREMIUM

L'interface utilise :
- **Glass Morphism** : Effet de verre avec blur
- **Gradients Animés** : Couleurs qui bougent
- **Effets 3D** : Cartes qui lèvent au hover
- **Glows & Néon** : Effets lumineux
- **Transitions Fluides** : Cubic-bezier élastique
- **Animations Continue** : Pulse, flow, shimmer

**Palette** : Indigo → Violet → Rose → Or

---

## ✅ TODO CHECKLIST

- [ ] Docker Compose démarré
- [ ] Backend qui tourne
- [ ] Frontend qui tourne
- [ ] ESP8266 flashé
- [ ] ESP8266 connecté WiFi
- [ ] ESP8266 connecté MQTT
- [ ] Données visibles dans MQTT
- [ ] Données visibles dans Backend
- [ ] Données visibles dans Frontend
- [ ] Commandes fonctionnent
- [ ] Caméra connectée (optionnel)

---

## 🚀 C'EST PARTI !

**Étape suivante** : Lire **[DEMARRAGE_SYSTEME.md](DEMARRAGE_SYSTEME.md)** 👈

**Besoin d'aide** : Lire **[TEST_ESP8266.md](TEST_ESP8266.md)** 👈

**Admirer l'interface** : http://localhost:5173 🎨✨

---

## 📧 NOTES

- Tous les fichiers `.md` contiennent de la doc
- Tous les guides sont en français
- Toutes les commandes sont testées
- L'interface est responsive
- Le code est commenté

**Bon développement !** 🚀✨
