# Service d'analyse de flacons avec Roboflow
FROM python:3.11-slim

# Mettre à jour et installer les dépendances système
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de requirements
COPY requirements_docker.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements_docker.txt

# Copier le code de l'application
COPY docker_service.py .

# Créer le dossier pour les images temporaires
RUN mkdir -p /app/temp

# Exposer le port 5000
EXPOSE 5000

# Variables d'environnement
ENV ROBOFLOW_API_KEY=8LX7VmCoSaapXMG92lzA
ENV FLASK_APP=docker_service.py

# Commande de démarrage
CMD ["python", "docker_service.py"]
