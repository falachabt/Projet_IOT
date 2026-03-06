# 🍓 Guide de Déploiement sur Raspberry Pi

## 📋 Vue d'ensemble

Ce guide explique comment déployer le jumeau numérique IoT sur votre Raspberry Pi en utilisant Docker.

## 🎯 Prérequis

### Sur votre PC Windows
- Docker installé ✅
- Accès réseau au Raspberry Pi

### Sur le Raspberry Pi
- Raspberry Pi 3/4/5 (recommandé: 4 ou 5)
- Raspberry Pi OS (64-bit recommandé)
- Connexion réseau (WiFi ou Ethernet)
- Au moins 4GB de RAM (8GB recommandé)
- Au moins 16GB d'espace disque disponible

## 🚀 Méthode de Déploiement

### Méthode 1: Export/Import Images Docker (Recommandée pour Raspberry Pi sans internet)

#### Étape 1: Build et Export sur PC Windows

```cmd
# Exécuter le script de build
build-and-export.bat
```

Ce script va:
1. ✅ Builder les images Docker
2. ✅ Exporter les images en fichiers .tar
3. ✅ Créer une archive `iot-jumeau-numerique-raspberry.tar.gz`

**Temps estimé**: 5-10 minutes

#### Étape 2: Transférer sur Raspberry Pi

**Option A: Via SCP (réseau)**
```bash
scp iot-jumeau-numerique-raspberry.tar.gz pi@<IP_RASPBERRY>:~/
```

**Option B: Via clé USB**
1. Copier `iot-jumeau-numerique-raspberry.tar.gz` sur une clé USB
2. Brancher la clé sur le Raspberry Pi
3. Copier le fichier:
```bash
cp /media/pi/USB/iot-jumeau-numerique-raspberry.tar.gz ~/
```

#### Étape 3: Déployer sur Raspberry Pi

```bash
# Se connecter au Raspberry Pi
ssh pi@<IP_RASPBERRY>

# Extraire l'archive
tar -xzf iot-jumeau-numerique-raspberry.tar.gz
cd iot-jumeau-numerique

# Rendre le script exécutable
chmod +x start-raspberry.sh

# Démarrer le système
./start-raspberry.sh
```

Le script va:
1. ✅ Vérifier Docker (installer si nécessaire)
2. ✅ Charger les images Docker
3. ✅ Démarrer tous les services
4. ✅ Afficher les URLs d'accès

**Temps estimé**: 3-5 minutes

### Méthode 2: Build Direct sur Raspberry Pi (Si Raspberry Pi a internet)

#### Étape 1: Cloner le projet

```bash
# Sur le Raspberry Pi
git clone https://github.com/falachabt/Projet_IOT.git
cd Projet_IOT
```

#### Étape 2: Démarrer avec Docker Compose

```bash
# Build et démarrer
docker-compose up -d --build

# Suivre les logs
docker-compose logs -f
```

**⚠️ Attention**: Le build sur Raspberry Pi peut prendre 15-30 minutes!

## 🌐 Accès au Jumeau Numérique

Une fois démarré, accédez au jumeau numérique depuis:

### Depuis le Raspberry Pi lui-même:
```
http://localhost
```

### Depuis un autre ordinateur sur le même réseau:
```
http://<IP_RASPBERRY>
```

Pour trouver l'IP du Raspberry Pi:
```bash
hostname -I
```

### Endpoints disponibles:
| Service | URL | Port |
|---------|-----|------|
| Frontend Web | http://<IP>/ | 80 |
| Backend API | http://<IP>:3000 | 3000 |
| MQTT Broker | mqtt://<IP> | 1883 |

## 🔧 Gestion du Système

### Voir les logs
```bash
# Tous les services
docker-compose logs -f

# Un service spécifique
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mosquitto
```

### Arrêter le système
```bash
docker-compose down
```

### Redémarrer un service
```bash
docker-compose restart backend
```

### Voir l'état des services
```bash
docker-compose ps
```

### Mettre à jour le système
```bash
# Récupérer les dernières modifications
git pull

# Rebuild et redémarrer
docker-compose up -d --build
```

## 🔌 Connexion du Matériel Physique

### ESP8266 → MQTT Broker

Modifier dans `esp8266_controller.ino`:
```cpp
const char* MQTT_BROKER = "<IP_RASPBERRY>";  // Remplacer par l'IP du Raspberry Pi
const char* WIFI_SSID = "VotreSSID";
const char* WIFI_PASSWORD = "VotreMotDePasse";
```

### Raspberry Pi → Caméra

Le Raspberry Pi peut exécuter `main.py` **en dehors** de Docker pour avoir accès à la caméra:

```bash
# Sur le Raspberry Pi (pas dans Docker)
cd ~/Projet_IOT
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Modifier l'adresse MQTT dans main.py
# MQTT_BROKER = "localhost"  # Car le broker tourne dans Docker

python main.py
```

## 📊 Configuration Réseau

### Ouvrir les ports du firewall (si activé)

```bash
sudo ufw allow 80/tcp      # Frontend
sudo ufw allow 3000/tcp    # Backend
sudo ufw allow 1883/tcp    # MQTT
```

### Configuration IP statique (optionnel mais recommandé)

Éditer `/etc/dhcpcd.conf`:
```bash
sudo nano /etc/dhcpcd.conf
```

Ajouter:
```
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

Redémarrer:
```bash
sudo reboot
```

## 🐛 Dépannage

### Docker n'est pas installé
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Se déconnecter et reconnecter
```

### Erreur "Cannot connect to Docker daemon"
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

### Les services ne démarrent pas
```bash
# Voir les logs détaillés
docker-compose logs

# Vérifier l'espace disque
df -h

# Vérifier la mémoire
free -h
```

### Port déjà utilisé
```bash
# Trouver le processus
sudo lsof -i :80
sudo lsof -i :3000
sudo lsof -i :1883

# Tuer le processus
sudo kill -9 <PID>
```

### Performance lente
```bash
# Augmenter swap (pour Raspberry Pi avec peu de RAM)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Changer CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## 🔄 Démarrage Automatique au Boot

Créer un service systemd:

```bash
sudo nano /etc/systemd/system/iot-jumeau-numerique.service
```

Contenu:
```ini
[Unit]
Description=IoT Jumeau Numérique
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/pi/Projet_IOT
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
User=pi

[Install]
WantedBy=multi-user.target
```

Activer:
```bash
sudo systemctl daemon-reload
sudo systemctl enable iot-jumeau-numerique.service
sudo systemctl start iot-jumeau-numerique.service
```

## 📈 Optimisations pour Raspberry Pi

### Réduire la consommation mémoire

Dans `docker-compose.yml`, limiter la mémoire:
```yaml
services:
  backend:
    mem_limit: 512m
  frontend:
    mem_limit: 256m
```

### Utiliser Docker BuildKit (plus rapide)
```bash
export DOCKER_BUILDKIT=1
docker-compose build
```

### Nettoyer les images inutilisées
```bash
docker system prune -a
```

## 🎯 Checklist de Déploiement

- [ ] Raspberry Pi configuré avec IP statique
- [ ] Docker et Docker Compose installés
- [ ] Archive transférée et extraite
- [ ] Services démarrés avec `start-raspberry.sh`
- [ ] Frontend accessible via navigateur
- [ ] Backend API répond sur `/health`
- [ ] ESP8266 configuré avec bonne IP MQTT
- [ ] Caméra Raspberry Pi fonctionnelle
- [ ] Tests avec flacon réel effectués

## 📞 Support

Pour toute question, consultez:
- [README_DIGITAL_TWIN.md](README_DIGITAL_TWIN.md) - Documentation complète
- [DEMARRAGE_RAPIDE.md](DEMARRAGE_RAPIDE.md) - Guide de démarrage rapide
- Logs Docker: `docker-compose logs -f`

---

**Note**: Ce guide suppose que vous utilisez Raspberry Pi OS. Pour d'autres OS, les commandes peuvent varier légèrement.
