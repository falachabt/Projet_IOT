#!/bin/bash

# Script de démarrage sur Raspberry Pi
# À copier sur le Raspberry Pi avec les images Docker

set -e

echo "🚀 Démarrage du Jumeau Numérique IoT sur Raspberry Pi"
echo "======================================================"

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Vérifier Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker n'est pas installé!${NC}"
    echo "Installation de Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo -e "${YELLOW}⚠️  Veuillez vous déconnecter et reconnecter pour que les changements prennent effet${NC}"
    exit 1
fi

# Vérifier Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Installation de Docker Compose...${NC}"
    sudo apt-get update
    sudo apt-get install -y docker-compose
fi

# Charger les images Docker si elles existent
if [ -d "./docker-images" ]; then
    echo -e "\n${BLUE}[1/3] Chargement des images Docker...${NC}"

    if [ -f "./docker-images/mosquitto.tar" ]; then
        echo "  - Chargement mosquitto..."
        docker load -i ./docker-images/mosquitto.tar
    fi

    if [ -f "./docker-images/backend.tar" ]; then
        echo "  - Chargement backend..."
        docker load -i ./docker-images/backend.tar
    fi

    if [ -f "./docker-images/frontend.tar" ]; then
        echo "  - Chargement frontend..."
        docker load -i ./docker-images/frontend.tar
    fi
fi

# Démarrer les services
echo -e "\n${BLUE}[2/3] Démarrage des services Docker...${NC}"
docker-compose up -d

# Attendre que les services démarrent
echo -e "\n${BLUE}[3/3] Vérification des services...${NC}"
sleep 10

# Vérifier l'état
if docker-compose ps | grep -q "Up"; then
    echo -e "\n${GREEN}✅ Jumeau Numérique démarré avec succès!${NC}"
    echo ""
    echo "🌐 Accès aux interfaces:"
    echo "  - Frontend Web:  http://$(hostname -I | awk '{print $1}')"
    echo "  - Backend API:   http://$(hostname -I | awk '{print $1}'):3000"
    echo "  - MQTT Broker:   $(hostname -I | awk '{print $1}'):1883"
    echo ""
    echo "📊 État des services:"
    docker-compose ps
    echo ""
    echo "📝 Commandes utiles:"
    echo "  - Voir les logs:      docker-compose logs -f"
    echo "  - Arrêter:            docker-compose down"
    echo "  - Redémarrer:         docker-compose restart"
    echo ""
else
    echo -e "${RED}❌ Erreur lors du démarrage${NC}"
    echo "Logs:"
    docker-compose logs --tail=50
    exit 1
fi
