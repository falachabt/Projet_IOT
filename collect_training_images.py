"""
Script pour collecter des images d'entrainement pour YOLO
Appuyez sur ESPACE pour capturer une image
Appuyez sur Q ou ESC pour quitter
"""

import cv2
import os
from datetime import datetime
try:
    from picamera2 import Picamera2
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False
    print("[INFO] Picamera2 non disponible - Mode webcam")

# Configuration
OUTPUT_DIR = "./training_data/images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("""
╔══════════════════════════════════════════════════════════════╗
║       COLLECTE D'IMAGES POUR ENTRAINEMENT YOLO               ║
╚══════════════════════════════════════════════════════════════╝

INSTRUCTIONS:
1. Place ton flacon devant la caméra
2. Varie les angles et conditions:
   - Bouchon FERME (au moins 50 images)
   - Bouchon OUVERT (au moins 50 images)
   - Bouchon ABSENT (au moins 50 images)
   - Différents niveaux de liquide
   - Différentes positions/angles
   - Différents éclairages

3. Appuie sur ESPACE pour capturer
4. Appuie sur Q ou ESC pour terminer

Images sauvegardées dans: {}
""".format(OUTPUT_DIR))

# Initialiser la caméra
if CAMERA_AVAILABLE:
    print("[INFO] Initialisation Picamera2...")
    camera = Picamera2()
    config = camera.create_preview_configuration(main={"size": (1280, 720)})
    camera.configure(config)
    camera.start()
    USE_WEBCAM = False
    print("[OK] Picamera2 initialisée")
else:
    print("[INFO] Utilisation webcam...")
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("[ERREUR] Impossible d'ouvrir la webcam")
        exit(1)
    USE_WEBCAM = True
    print("[OK] Webcam initialisée")

image_count = 0

try:
    while True:
        # Capturer frame
        if USE_WEBCAM:
            ret, frame = camera.read()
            if not ret:
                print("[ERREUR] Échec capture")
                break
        else:
            frame = camera.capture_array("main")
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Afficher info
        display = frame.copy()
        cv2.putText(display, f"Images capturees: {image_count}", (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(display, "ESPACE = capturer | Q/ESC = quitter", (20, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Crosshair au centre pour aider à cadrer
        h, w = display.shape[:2]
        cv2.line(display, (w//2 - 30, h//2), (w//2 + 30, h//2), (0, 255, 0), 2)
        cv2.line(display, (w//2, h//2 - 30), (w//2, h//2 + 30), (0, 255, 0), 2)
        
        cv2.imshow("Collecte Images - Entrainement YOLO", display)
        
        # Gestion clavier
        key = cv2.waitKey(1)
        
        if key == 32:  # ESPACE
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"img_{timestamp}.jpg"
            filepath = os.path.join(OUTPUT_DIR, filename)
            cv2.imwrite(filepath, frame)
            image_count += 1
            print(f"[{image_count}] Image capturée: {filename}")
            
            # Flash visuel
            for _ in range(2):
                white = display.copy()
                white[:] = (255, 255, 255)
                cv2.imshow("Collecte Images - Entrainement YOLO", white)
                cv2.waitKey(50)
                cv2.imshow("Collecte Images - Entrainement YOLO", display)
                cv2.waitKey(50)
        
        elif key == 27 or key == ord('q') or key == ord('Q'):  # ESC ou Q
            break

finally:
    if USE_WEBCAM:
        camera.release()
    else:
        camera.stop()
    cv2.destroyAllWindows()
    
    print(f"\n{'='*60}")
    print(f"COLLECTE TERMINÉE")
    print(f"{'='*60}")
    print(f"Total images capturées: {image_count}")
    print(f"Dossier: {OUTPUT_DIR}")
    print(f"\nPROCHAINE ÉTAPE:")
    print(f"1. Annote les images avec Label Studio ou Roboflow")
    print(f"2. Exporte au format YOLO")
    print(f"3. Lance l'entrainement avec: python train_custom_model.py")
