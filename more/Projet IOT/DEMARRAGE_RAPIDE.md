# 🚀 Démarrage Rapide - Jumeau Numérique IoT

## Option 1: Avec Docker (Recommandé)

```bash
# 1. Démarrer tous les services
docker-compose up -d

# 2. Vérifier que tout tourne
docker-compose ps

# 3. Ouvrir l'interface web
# http://localhost
```

**C'est tout!** Tous les services sont démarrés:
- ✅ Mosquitto MQTT (port 1883)
- ✅ InfluxDB (port 8086)
- ✅ Backend (port 3000)
- ✅ Frontend (port 80)

## Option 2: Manuel (Développement)

### Étape 1: MQTT Broker
```bash
mosquitto -v
```

### Étape 2: InfluxDB
```bash
docker run -d -p 8086:8086 \
  -e DOCKER_INFLUXDB_INIT_MODE=setup \
  -e DOCKER_INFLUXDB_INIT_USERNAME=admin \
  -e DOCKER_INFLUXDB_INIT_PASSWORD=adminpassword \
  -e DOCKER_INFLUXDB_INIT_ORG=iot-flacons \
  -e DOCKER_INFLUXDB_INIT_BUCKET=iot_flacons \
  -e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=my-super-secret-auth-token \
  influxdb:2.7
```

### Étape 3: Backend
```bash
cd digital-twin-backend
npm install
npm start
```

### Étape 4: Frontend
```bash
cd digital-twin-frontend
npm install
npm run dev
```

### Étape 5: Raspberry Pi
```bash
python main.py
```

### Étape 6: ESP8266
1. Ouvrir `esp8266_controller/esp8266_controller.ino`
2. Modifier WiFi SSID/password (lignes 14-15)
3. Modifier adresse MQTT broker (ligne 18)
4. Flasher sur ESP8266

## 🌐 Accès aux Interfaces

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend Web** | http://localhost:5173 (dev)<br>http://localhost (prod) | - |
| **Backend API** | http://localhost:3000/api/state | - |
| **InfluxDB** | http://localhost:8086 | admin/adminpassword |
| **Grafana** | http://localhost:3001 | admin/admin |

## 🧪 Test Simple

### 1. Vérifier Backend
```bash
curl http://localhost:3000/health
```

Doit retourner:
```json
{
  "status": "OK",
  "mqtt_connected": true,
  "influxdb_connected": true
}
```

### 2. Simuler un Capteur (sans ESP8266)
```bash
# Simuler détection flacon
mosquitto_pub -h localhost -t esp8266/ultrason/distance \
  -m '{"distance": 5.2, "flacon_detecte": true, "timestamp": 123456}'

# Simuler poids
mosquitto_pub -h localhost -t esp8266/poids/valeur \
  -m '{"poids_g": 350, "timestamp": 123456}'

# Simuler résultat caméra
mosquitto_pub -h localhost -t raspberry/camera/resultat \
  -m '{"status": "OK", "bouteille_detectee": true, "bouchon_present": true}'
```

### 3. Vérifier Frontend
Ouvrir http://localhost:5173
- Aller sur "Dashboard" → Voir les données mises à jour
- Aller sur "Vue 3D" → Voir la visualisation 3D

### 4. Contrôler Moteur depuis Frontend
1. Ouvrir Dashboard
2. Carte "Moteurs Convoyeur"
3. Ajuster vitesse avec slider
4. Cliquer "Démarrer"
5. Observer message MQTT publié

### 5. Contrôler LED depuis Frontend
1. Cliquer sur une LED (verte, rouge ou orange)
2. Observer LED s'allumer/éteindre
3. Si ESP8266 connecté, LED physique change aussi

## 📊 Vérifier les Données dans InfluxDB

1. Ouvrir http://localhost:8086
2. Login: admin / adminpassword
3. Aller dans "Data Explorer"
4. Sélectionner bucket `iot_flacons`
5. Sélectionner measurement: `ultrason`, `poids`, `camera`, etc.
6. Cliquer "Submit" pour voir les graphiques

## 🛠️ Commandes Utiles

### Docker
```bash
# Voir logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Redémarrer un service
docker-compose restart backend

# Arrêter tout
docker-compose down

# Supprimer volumes (⚠️ efface données)
docker-compose down -v
```

### MQTT Debug
```bash
# Écouter tous les topics
mosquitto_sub -h localhost -t '#' -v

# Écouter topic spécifique
mosquitto_sub -h localhost -t 'esp8266/#' -v
```

### Backend Debug
```bash
cd digital-twin-backend

# Mode développement avec auto-reload
npm run dev

# Voir logs
tail -f logs/combined.log
```

## ❌ Problèmes Fréquents

### Port 1883 déjà utilisé
```bash
# Windows
netstat -ano | findstr :1883
taskkill /PID <PID> /F

# Linux
sudo lsof -i :1883
sudo kill -9 <PID>
```

### Port 3000 déjà utilisé
Modifier `PORT` dans `digital-twin-backend/.env`

### ESP8266 ne se connecte pas
1. Vérifier SSID/password WiFi
2. Vérifier adresse IP broker MQTT
3. Ouvrir Serial Monitor (115200 baud)
4. Vérifier que broker MQTT accepte connexions anonymes

### Frontend: "CORS error"
Vérifier `WS_CORS_ORIGIN` dans `digital-twin-backend/.env`:
```
WS_CORS_ORIGIN=http://localhost:5173
```

## 📖 Documentation Complète

Voir [README_DIGITAL_TWIN.md](README_DIGITAL_TWIN.md) pour:
- Architecture détaillée
- Configuration MQTT topics
- API REST endpoints
- Dépannage complet
- Sécurité production

## 🎯 Prochaines Étapes

1. ✅ Démarrer système avec Docker
2. ✅ Tester avec données simulées
3. ⬜ Connecter ESP8266 physique
4. ⬜ Connecter Raspberry Pi + caméra
5. ⬜ Câbler capteurs et actionneurs
6. ⬜ Calibrer capteur de poids
7. ⬜ Entraîner modèle YOLO custom
8. ⬜ Tester bout-en-bout avec flacon réel

Bon développement! 🚀
