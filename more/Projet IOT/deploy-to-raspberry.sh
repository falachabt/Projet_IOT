#!/bin/bash

# Script de déploiement sur Raspberry Pi
# Ce script prépare et exporte les images Docker pour le Raspberry Pi

set -e

echo "🚀 Préparation du déploiement pour Raspberry Pi"
echo "================================================"

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Build des images Docker
echo -e "\n${BLUE}[1/4] Build des images Docker...${NC}"
docker-compose build --no-cache

# 2. Export des images
echo -e "\n${BLUE}[2/4] Export des images Docker...${NC}"
mkdir -p ./docker-images

echo "  - Export mosquitto..."
docker pull eclipse-mosquitto:2.0
docker save eclipse-mosquitto:2.0 -o ./docker-images/mosquitto.tar

echo "  - Export backend..."
docker save iot_backend:latest -o ./docker-images/backend.tar

echo "  - Export frontend..."
docker save iot_frontend:latest -o ./docker-images/frontend.tar

# 3. Créer archive complète
echo -e "\n${BLUE}[3/4] Création de l'archive de déploiement...${NC}"
tar -czf iot-jumeau-numerique-raspberry.tar.gz \
    docker-compose.yml \
    mosquitto/ \
    docker-images/ \
    README_DIGITAL_TWIN.md \
    DEMARRAGE_RAPIDE.md

# 4. Nettoyage
echo -e "\n${BLUE}[4/4] Nettoyage...${NC}"
rm -rf ./docker-images

# Afficher informations
echo -e "\n${GREEN}✅ Déploiement préparé avec succès!${NC}"
echo ""
echo "📦 Fichier créé: iot-jumeau-numerique-raspberry.tar.gz"
echo ""
echo "📋 Prochaines étapes:"
echo "  1. Transférer le fichier sur votre Raspberry Pi:"
echo "     ${YELLOW}scp iot-jumeau-numerique-raspberry.tar.gz pi@<IP_RASPBERRY>:~/${NC}"
echo ""
echo "  2. Sur le Raspberry Pi, exécuter:"
echo "     ${YELLOW}tar -xzf iot-jumeau-numerique-raspberry.tar.gz${NC}"
echo "     ${YELLOW}cd iot-jumeau-numerique${NC}"
echo "     ${YELLOW}./start-raspberry.sh${NC}"
echo ""
