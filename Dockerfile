# ─────────────────────────────────────────────────────────────
# Bottle Checker — Image multi-arch (amd64 + arm64 + armv7)
# Compatible Raspberry Pi 3 / 4 / 5
# ─────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Évite les prompts interactifs apt
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Dépendances système nécessaires à OpenCV + YOLO
RUN apt-get update && apt-get install -y --no-install-recommends \
    # OpenCV headless
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    # Caméra v4l2 (webcam USB + Pi Camera via libcamera-compat)
    v4l-utils \
    libv4l-dev \
    # Pour paho-mqtt TLS (optionnel mais recommandé)
    libssl-dev \
    # Utilitaires debug
    curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier uniquement requirements d'abord (cache Docker)
COPY requirements.txt .

# Installer les dépendances Python
# On utilise opencv-python-headless (pas de GUI) + on exclut opencv-python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        opencv-python-headless>=4.8 \
        numpy>=1.24 \
        "ultralytics>=8.0" \
        Pillow>=10.0 \
        "paho-mqtt>=2.0" \
        "flask>=3.0"

# Copier le code source
COPY . .

# Créer le dossier de sortie
RUN mkdir -p /app/output

# Exposer le port Flask
EXPOSE 5000

# Le modèle YOLO est téléchargé automatiquement par ultralytics au premier lancement
# (ou peut être monté via volume si déjà téléchargé)

CMD ["python", "__main__.py", "web"]
