# 🔍 DÉBOGUER LA CONNEXION ESP8266 ↔ PAGE WEB

## ❌ PROBLÈME : La page web n'affiche pas les données de l'ESP8266

Voici comment **diagnostiquer et résoudre** le problème étape par étape :

---

## 📋 CHECKLIST DE DIAGNOSTIC (À FAIRE DANS L'ORDRE)

### ✅ ÉTAPE 1 : Vérifier que l'ESP8266 fonctionne

#### A) Ouvrir le Serial Monitor dans PlatformIO
1. Cliquer sur l'icône "prise" en bas de VSCode
2. Vérifier les messages :

**✅ BON** :
```
[WiFi]   ✓ Connecté ! IP: 172.20.10.3
[MQTT]   ✓ Connecté au broker MQTT !
[Pub]    📤 esp8266/ultrason → {"distance_cm":25.3,...}
[Pub]    📤 esp8266/moteur → {"etat":"ARRET",...}
```

**❌ PROBLÈME** :
```
[MQTT]   ✗ Connexion échouée, rc=-2
[MQTT]   🔄 Nouvelle tentative dans 5s...
```

**SOLUTION si problème** :
- L'ESP8266 ne peut pas se connecter au broker MQTT
- **Vérifier l'adresse du broker dans `main.cpp`**
- Si l'ESP est sur le WiFi iPhone et le PC aussi, changer :
  ```cpp
  // Dans main.cpp, ligne ~40
  const char* mqtt_server = "192.168.X.X";  // IP du PC (pas localhost !)
  ```

---

### ✅ ÉTAPE 2 : Vérifier que le Broker MQTT fonctionne

```bash
# Vérifier que le container Docker tourne
docker ps

# Devrait afficher :
# CONTAINER ID   IMAGE      ... PORTS                    NAMES
# xxxxx          eclipse-mosquitto   0.0.0.0:1883->1883/tcp   mosquitto
```

**❌ Si pas de container mosquitto** :
```bash
# Démarrer Docker Compose
docker-compose up -d

# Vérifier à nouveau
docker ps
```

---

### ✅ ÉTAPE 3 : Écouter les messages MQTT

**Terminal - Écouter TOUS les messages ESP8266** :
```bash
docker exec -it mosquitto mosquitto_sub -h localhost -t "esp8266/#" -v
```

**✅ BON - Tu dois voir** :
```
esp8266/ultrason {"distance_cm":25.3,"flacon_detecte":false,...}
esp8266/moteur {"etat":"ARRET","vitesse":0,...}
esp8266/leds {"rouge_camera":0,"rouge_poids":0,"vert":0,...}
esp8266/systeme/etat {"etat_grafcet":"E1_MARCHE_CONV",...}
```

**❌ RIEN NE S'AFFICHE** ?
➡️ **L'ESP8266 ne publie pas sur MQTT**

**CAUSES POSSIBLES** :
1. ESP8266 pas connecté au broker (voir Étape 1)
2. Mauvaise adresse broker dans `main.cpp`
3. ESP8266 pas sur le même réseau que le broker

**SOLUTION** :
```cpp
// Dans main.cpp, vérifier et corriger :

// Si ESP8266 sur iPhone WiFi ET PC sur iPhone WiFi :
const char* mqtt_server = "172.20.10.1";  // IP de l'iPhone (gateway)

// Si ESP8266 sur WiFi maison ET PC sur WiFi maison :
const char* mqtt_server = "192.168.1.X";  // IP du PC

// Pour trouver l'IP du PC :
// Windows : ipconfig
// Linux/Mac : ifconfig
```

---

### ✅ ÉTAPE 4 : Vérifier que le BACKEND tourne

```bash
cd digital-twin-backend
npm start
```

**✅ BON - Tu dois voir** :
```
✓ Serveur démarré sur http://localhost:3000
✓ Connecté au broker MQTT localhost:1883
✓ Abonné aux topics: esp8266/#,raspberry/#
✓ WebSocket server ready
```

**❌ Erreur : `Connection refused to localhost:1883`** ?
➡️ Le broker MQTT n'est pas démarré (retour Étape 2)

**❌ Erreur : `Port 3000 already in use`** ?
```bash
# Tuer le processus sur le port 3000
npx kill-port 3000

# Redémarrer
npm start
```

---

### ✅ ÉTAPE 5 : Vérifier que le Backend REÇOIT les messages MQTT

**Dans les logs du backend**, tu DOIS voir :
```
📨 [esp8266/ultrason] Message reçu
📨 [esp8266/moteur] Message reçu
📨 [esp8266/leds] Message reçu
```

**❌ RIEN dans les logs** ?
➡️ Le backend ne reçoit pas les messages MQTT

**CAUSES** :
1. Topics mal configurés dans `.env`
2. Backend pas abonné aux bons topics

**SOLUTION** :
```bash
# Vérifier le fichier .env
cd digital-twin-backend
cat .env | grep MQTT_TOPICS

# Doit contenir :
MQTT_TOPICS=esp8266/#,raspberry/#
```

Si ce n'est pas le cas :
```bash
# Éditer .env
code .env

# Vérifier la ligne :
MQTT_TOPICS=esp8266/#,raspberry/#

# Redémarrer le backend
npm start
```

---

### ✅ ÉTAPE 6 : Vérifier que le FRONTEND tourne

```bash
cd digital-twin-frontend
npm run dev
```

**✅ BON** :
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

**Ouvrir** : http://localhost:5173

---

### ✅ ÉTAPE 7 : Vérifier la connexion WebSocket (Frontend ↔ Backend)

**Dans le navigateur** :
1. Ouvrir la page : http://localhost:5173
2. Appuyer sur **F12** (DevTools)
3. Onglet **Console**

**✅ BON - Tu dois voir** :
```
WebSocket connecté ✓
État connecté : true
```

**❌ Tu vois** :
```
WebSocket erreur de connexion
```

**SOLUTION** :
1. Vérifier que le backend tourne (Étape 4)
2. Vérifier l'URL dans `useWebSocket.js` :
   ```javascript
   // Doit être :
   const ws = new WebSocket('ws://localhost:3000');
   ```

---

### ✅ ÉTAPE 8 : Vérifier que les données arrivent dans le Frontend

**Dans la console du navigateur (F12)**, tu DOIS voir :
```
Données reçues: {ultrason: {...}, moteur: {...}, leds: {...}}
```

**❌ WebSocket connecté MAIS pas de données** ?
➡️ Le backend ne TRANSMET pas les données au frontend

**SOLUTION** :
Vérifier le fichier `mqtt-handler.js` :
```javascript
// Après chaque mise à jour de global.systemState, il DOIT y avoir :
if (global.wss) {
  global.wss.clients.forEach((client) => {
    if (client.readyState === 1) {
      client.send(JSON.stringify(global.systemState));
    }
  });
}
```

---

## 🔧 SOLUTION RAPIDE : CONFIGURATION IP

### Si ESP8266 et PC sur le MÊME réseau WiFi :

#### 1. Trouver l'IP du PC
```bash
# Windows
ipconfig
# Chercher "IPv4 Address" → ex: 192.168.1.10

# Linux/Mac
ifconfig
# Chercher "inet" → ex: 192.168.1.10
```

#### 2. Configurer l'ESP8266
```cpp
// Dans main.cpp
const char* mqtt_server = "192.168.1.10";  // IP DU PC
```

#### 3. Flasher l'ESP8266
```
PlatformIO → Upload
```

#### 4. Vérifier le Serial Monitor
```
[MQTT]   ✓ Connecté au broker MQTT !
```

---

## 🧪 TEST COMPLET DE BOUT EN BOUT

### Test 1 : Publier un message MQTT manuellement

```bash
# Terminal - Publier un test
docker exec -it mosquitto mosquitto_pub -h localhost -t "esp8266/moteur" -m '{"etat":"MARCHE","vitesse":255,"timestamp":"2026-03-03T10:00:00Z"}'
```

**Résultat attendu** :
1. Backend affiche : `📨 [esp8266/moteur] Message reçu`
2. Frontend affiche la nouvelle valeur dans la carte "Moteur"

**✅ Si ça marche** : Le problème vient de l'ESP8266 qui ne publie pas
**❌ Si ça ne marche pas** : Le problème est dans Backend → Frontend

---

### Test 2 : Vérifier l'état global du Backend

```bash
# Ouvrir un navigateur
http://localhost:3000/api/state
```

**Résultat attendu** :
```json
{
  "ultrason": {...},
  "moteur": {...},
  "leds": {...},
  "camera": {...},
  "statistics": {...}
}
```

**✅ Si données présentes** : Backend reçoit les messages MQTT
**❌ Si vide** : Backend ne reçoit rien

---

## 📊 SCHÉMA DE DÉBOGAGE

```
ESP8266
  ↓ [1] Publie sur MQTT ?
  |     ✅ Voir Serial Monitor
  |     ✅ Écouter avec mosquitto_sub
  ↓
Broker MQTT (Mosquitto)
  ↓ [2] Reçoit les messages ?
  |     ✅ docker exec mosquitto_sub
  ↓
Backend (Node.js)
  ↓ [3] Reçoit les messages ?
  |     ✅ Voir logs backend
  |
  ↓ [4] Met à jour global.systemState ?
  |     ✅ GET http://localhost:3000/api/state
  |
  ↓ [5] Envoie via WebSocket ?
  |     ✅ Voir logs backend
  ↓
Frontend (React)
  ↓ [6] WebSocket connecté ?
  |     ✅ Console navigateur (F12)
  |
  ↓ [7] Reçoit les données ?
  |     ✅ Console navigateur
  |
  ↓ [8] Affiche dans l'interface ?
  |     ✅ Les cartes se mettent à jour
  ↓
✨ ÇA MARCHE !
```

---

## 🚨 PROBLÈMES COURANTS

### 1. ESP8266 : `rc=-2` (Connection refused)
**Cause** : Mauvaise IP du broker
**Solution** : Vérifier `mqtt_server` dans main.cpp

### 2. ESP8266 : `rc=-4` (Connection timeout)
**Cause** : Broker non accessible (firewall, réseau différent)
**Solution** :
- Ping du PC depuis l'ESP
- Désactiver temporairement le firewall
- Vérifier que PC et ESP sont sur le même réseau

### 3. Backend : `Connection refused to localhost:1883`
**Cause** : Mosquitto pas démarré
**Solution** : `docker-compose up -d`

### 4. Frontend : WebSocket erreur
**Cause** : Backend pas démarré
**Solution** : `cd digital-twin-backend && npm start`

### 5. Données dans Backend mais pas dans Frontend
**Cause** : WebSocket ne broadcast pas
**Solution** : Vérifier `mqtt-handler.js` envoie bien via `global.wss`

---

## ✅ CHECKLIST FINALE

Avant de dire "ça ne marche pas", vérifier :

- [ ] Docker Compose démarré (`docker ps` montre mosquitto)
- [ ] ESP8266 flashé avec le bon code
- [ ] ESP8266 connecté WiFi (Serial Monitor montre IP)
- [ ] ESP8266 connecté MQTT (Serial Monitor montre "Connecté")
- [ ] Messages visibles avec `mosquitto_sub`
- [ ] Backend démarré (`npm start`)
- [ ] Backend affiche "Connecté au broker MQTT"
- [ ] Backend affiche logs `📨 [esp8266/...]`
- [ ] Frontend démarré (`npm run dev`)
- [ ] Page ouverte sur http://localhost:5173
- [ ] Console navigateur (F12) montre "WebSocket connecté"
- [ ] Status en haut à droite affiche "Connecté" (vert)

---

## 🆘 SI TOUJOURS RIEN

**Dernière solution** : Redémarrer TOUT dans l'ordre

```bash
# 1. Arrêter tout
docker-compose down
# Ctrl+C dans tous les terminaux

# 2. Redémarrer dans l'ordre
docker-compose up -d

# Terminal 1
cd digital-twin-backend
npm start

# Terminal 2
cd digital-twin-frontend
npm run dev

# 3. Reflasher l'ESP8266
# PlatformIO → Upload

# 4. Ouvrir http://localhost:5173

# 5. Vérifier les logs dans TOUS les terminaux
```

Si après ça, ça ne marche TOUJOURS pas, envoie-moi :
1. Screenshot du Serial Monitor (ESP8266)
2. Logs du backend (terminal)
3. Console navigateur (F12)
