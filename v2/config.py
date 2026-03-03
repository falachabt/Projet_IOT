"""
Configuration centralisée du projet Bottle Checker V2.
Modifier les valeurs ici pour adapter le système à votre environnement.
"""

import os

# ──────────────────────────────────────────────────────────────
# CHEMINS
# ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ──────────────────────────────────────────────────────────────
# MODÈLE YOLO
# ──────────────────────────────────────────────────────────────
# Le modèle préentraîné YOLO (yolo11n.pt par défaut)
# Les classes "bottle" sont détectées nativement par les modèles COCO
YOLO_MODEL_PATH = os.path.join(BASE_DIR, "..", "yolo11n.pt")
YOLO_CONFIDENCE = 0.40        # Seuil de confiance YOLO pour la détection bouteille
YOLO_BOTTLE_CLASS = "bottle"  # Nom de la classe bouteille dans COCO

# ──────────────────────────────────────────────────────────────
# DÉTECTION BOUCHON (analyse heuristique zone haute de la bouteille)
# ──────────────────────────────────────────────────────────────
CAP_ZONE_RATIO = 0.18          # Ratio haut de la bouteille considéré comme zone bouchon
CAP_EDGE_DENSITY_THRESH = 0.06 # Seuil densité de contours pour détecter un bouchon
CAP_COLOR_VAR_THRESH = 2500    # Seuil de variance couleur (bouchon = plus uniforme)
CAP_MIN_CONTOUR_AREA = 80      # Aire minimale d'un contour significatif dans la zone bouchon

# ──────────────────────────────────────────────────────────────
# DÉTECTION ÉTIQUETTE (analyse heuristique zone corps de la bouteille)
# ──────────────────────────────────────────────────────────────
LABEL_ZONE_TOP_RATIO = 0.25    # Début de la zone étiquette (% depuis le haut de la bouteille)
LABEL_ZONE_BOTTOM_RATIO = 0.85 # Fin de la zone étiquette
LABEL_EDGE_DENSITY_THRESH = 0.04  # Seuil densité d'arêtes pour détecter une étiquette
LABEL_MIN_CONTOUR_AREA = 500   # Aire min d'un contour pour être considéré comme étiquette
LABEL_MIN_RECT_RATIO = 0.25    # Rapport largeur/hauteur min d'un rectangle d'étiquette

# ──────────────────────────────────────────────────────────────
# CAMÉRA
# ──────────────────────────────────────────────────────────────
CAMERA_INDEX = 0               # Index webcam (0 = défaut)
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30

# ──────────────────────────────────────────────────────────────
# MQTT
# ──────────────────────────────────────────────────────────────
MQTT_BROKER = "172.20.10.3"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60
MQTT_USERNAME = None           # Mettre le username si auth requise
MQTT_PASSWORD = None

# Topics
MQTT_TOPIC_TRIGGER = "iot/bottle/trigger"    # Arduino → Rasp : déclenche l'analyse
MQTT_TOPIC_RESULT = "iot/bottle/result"      # Rasp → Arduino : résultat JSON

# ──────────────────────────────────────────────────────────────
# INTERFACE WEB (Flask)
# ──────────────────────────────────────────────────────────────
WEB_HOST = "0.0.0.0"
WEB_PORT = 5000
WEB_DEBUG = False
