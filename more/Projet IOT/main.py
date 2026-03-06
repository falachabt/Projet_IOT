import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from PIL import Image, ImageTk
import cv2
import numpy as np
import threading
import queue
import time
import os
from datetime import datetime
import paho.mqtt.client as mqtt

try:
    from picamera2 import Picamera2
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False

from ultralytics import YOLO

class BottleCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Contrôle Bouteille - YOLO + MQTT Trigger + Réponse")
        self.root.geometry("1200x800")

        # ─── CONFIG MQTT ───────────────────────────────────────────────
        self.MQTT_BROKER = "10.66.108.235"
        self.MQTT_PORT   = 1883
        self.MQTT_TOPIC_TRIGGER    = "esp8266/ultrason/distance"     # topic qui déclenche
        self.MQTT_TOPIC_RESPONSE   = "esp8266/bouteille/etat"        # ← topic de réponse simple (ESP8266)
        self.MQTT_TOPIC_DETAILED   = "raspberry/camera/resultat"     # ← topic détaillé (Backend Jumeau Numérique)

        # ─── CONFIG YOLO ───────────────────────────────────────────────
        self.YOLO_MODEL  = "yolo11n.pt"           # ← À remplacer par ton modèle custom !!!
        self.CONF_THRESH = 0.35

        self.output_dir = "./analyses_bouteilles"
        os.makedirs(self.output_dir, exist_ok=True)

        # Variables état
        self.camera = None
        self.use_picamera = False
        self.is_running = False
        self.current_frame = None
        self.analyzing = False

        # File pour messages MQTT → GUI
        self.mqtt_queue = queue.Queue()

        # Charger YOLO
        print("[INFO] Chargement modèle YOLO...")
        self.model = YOLO(self.YOLO_MODEL)
        print("[OK] Modèle chargé")

        # Interface
        self.create_widgets()

        # Init caméra
        self.init_camera()

        # Vidéo live
        self.start_video_loop()

        # MQTT dans thread séparé
        self.start_mqtt_thread()

        # Vérification file MQTT toutes les 150 ms
        self.root.after(150, self.process_mqtt_queue)

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ─── GAUCHE : Vidéo ───
        left = ttk.Frame(main_frame)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.video_lbl = ttk.Label(left, text="Démarrage caméra...", background="black")
        self.video_lbl.pack(fill=tk.BOTH, expand=True)

        # ─── DROITE : Contrôles & Résultats ───
        right = ttk.Frame(main_frame, padding=10)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        ttk.Label(right, text="Contrôle Bouteille", font=("Arial", 18, "bold")).pack(pady=10)

        self.status_big = ttk.Label(right, text="EN ATTENTE", font=("Arial", 24, "bold"))
        self.status_big.pack(pady=15)

        self.detail_lbl = ttk.Label(right, text="", font=("Arial", 12))
        self.detail_lbl.pack(pady=8)

        self.btn_analyze = ttk.Button(right, text="Analyser manuellement", command=self.trigger_manual_analysis)
        self.btn_analyze.pack(pady=15, ipadx=20, ipady=10)

        ttk.Separator(right, orient='horizontal').pack(fill='x', pady=15)

        self.log_txt = scrolledtext.ScrolledText(right, height=12, width=50, state='normal')
        self.log_txt.pack(fill=tk.X)

        self.mqtt_status = ttk.Label(right, text="MQTT : déconnecté", foreground="orange")
        self.mqtt_status.pack(pady=5)

    def log(self, msg):
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] {msg}")
        self.log_txt.insert(tk.END, f"[{ts}] {msg}\n")
        self.log_txt.see(tk.END)

    def init_camera(self):
        try:
            if CAMERA_AVAILABLE:
                self.log("Initialisation Picamera2...")
                self.camera = Picamera2()
                config = self.camera.create_preview_configuration(main={"size": (1280, 720)})
                self.camera.configure(config)
                self.camera.start()
                self.use_picamera = True
                self.log("Picamera2 OK")
            else:
                self.log("Initialisation Webcam...")
                self.camera = cv2.VideoCapture(0)
                if not self.camera.isOpened():
                    raise Exception("Webcam non détectée")
                self.log("Webcam OK")
        except Exception as e:
            self.log(f"ERREUR caméra : {e}")
            messagebox.showerror("Caméra", str(e))

    def start_video_loop(self):
        self.is_running = True
        self.update_video()

    def update_video(self):
        if not self.is_running:
            return

        try:
            if self.use_picamera:
                frame = self.camera.capture_array("main")
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            else:
                ret, frame = self.camera.read()
                if not ret:
                    return

            self.current_frame = frame.copy()

            if not self.analyzing:
                display = cv2.resize(frame, (800, 600))
                cv2.putText(display, "Surveillance - MQTT trigger", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                img_rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
                imgtk = ImageTk.PhotoImage(Image.fromarray(img_rgb))
                self.video_lbl.imgtk = imgtk
                self.video_lbl.configure(image=imgtk)

        except Exception as e:
            self.log(f"Erreur vidéo : {e}")

        self.root.after(40, self.update_video)

    def mqtt_on_connect(self, client, userdata, flags, rc, props=None):
        if rc == 0:
            self.mqtt_status.config(text="MQTT : connecté ✓", foreground="green")
            client.subscribe(self.MQTT_TOPIC_TRIGGER)
            self.log(f"Abonné à {self.MQTT_TOPIC_TRIGGER}")
        else:
            self.mqtt_status.config(text=f"MQTT : échec (code {rc})", foreground="red")

    def mqtt_on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode('utf-8').strip()
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.log(f"Reçu sur {msg.topic} → {payload}")
            self.mqtt_queue.put(("TRIGGER", payload, ts))
        except Exception as e:
            self.log(f"Erreur décodage MQTT : {e}")

    def start_mqtt_thread(self):
        def mqtt_loop():
            self.mqtt_client = mqtt.Client(protocol=mqtt.MQTTv5)
            self.mqtt_client.on_connect = self.mqtt_on_connect
            self.mqtt_client.on_message = self.mqtt_on_message
            try:
                self.mqtt_client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
                self.mqtt_client.loop_forever()
            except Exception as e:
                self.log(f"Erreur connexion MQTT : {e}")

        t = threading.Thread(target=mqtt_loop, daemon=True)
        t.start()

    def process_mqtt_queue(self):
        try:
            while not self.mqtt_queue.empty():
                typ, payload, ts = self.mqtt_queue.get_nowait()
                if typ == "TRIGGER":
                    self.log(f"→ Déclenchement AUTO suite à MQTT ({payload})")
                    self.trigger_analysis(auto=True, trigger_payload=payload)
        except queue.Empty:
            pass

        self.root.after(150, self.process_mqtt_queue)

    def trigger_manual_analysis(self):
        self.trigger_analysis(auto=False, trigger_payload="manuel")

    def trigger_analysis(self, auto=False, trigger_payload=""):
        if self.current_frame is None:
            messagebox.showwarning("Pas d'image", "Aucune frame disponible")
            return
        if self.analyzing:
            self.log("Analyse déjà en cours → ignorée")
            return

        self.analyzing = True
        prefix = "AUTO" if auto else "MANUEL"
        self.log(f"Analyse {prefix} démarrée...")

        thread = threading.Thread(target=self.perform_analysis, args=(auto, trigger_payload))
        thread.daemon = True
        thread.start()

    def publish_result(self, status, detail="", trigger="", data=None):
        import json
        try:
            # Message simple pour ESP8266
            if status == "OK":
                msg_simple = "OK"
            elif status in ("KO", "ERREUR"):
                msg_simple = "KO"
            else:
                msg_simple = "ERROR"

            self.mqtt_client.publish(
                self.MQTT_TOPIC_RESPONSE,
                payload=msg_simple,
                qos=1,
                retain=False
            )
            self.log(f"→ Publié {self.MQTT_TOPIC_RESPONSE} : {msg_simple}")

            # Message JSON détaillé pour Backend Jumeau Numérique
            if data:
                msg_detailed = json.dumps(data)
                self.mqtt_client.publish(
                    self.MQTT_TOPIC_DETAILED,
                    payload=msg_detailed,
                    qos=1,
                    retain=False
                )
                self.log(f"→ Publié {self.MQTT_TOPIC_DETAILED} (JSON)")

        except Exception as e:
            self.log(f"Erreur publication MQTT : {e}")

    def perform_analysis(self, auto, trigger_payload):
        try:
            frame = self.current_frame.copy()
            results = self.model(frame, conf=self.CONF_THRESH, verbose=False)

            bouteille_trouvee = False
            avec_bouchon = False
            msg_detail = ""
            confiance_max = 0.0

            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls)
                    cls_name = r.names[cls_id].lower()
                    conf = float(box.conf)

                    # Tracker la confiance max
                    if conf > confiance_max:
                        confiance_max = conf

                    if "bouteille" in cls_name or "bottle" in cls_name:
                        bouteille_trouvee = True
                        x1,y1,x2,y2 = map(int, box.xyxy[0])
                        cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)

                        if "bouchon" in cls_name or "cap" in cls_name or "avec" in cls_name or "fermee" in cls_name or "fermée" in cls_name:
                            avec_bouchon = True

            if not bouteille_trouvee:
                etat = "ERREUR"
                detail = "Aucune bouteille détectée"
                color_bgr = (0, 0, 255)   # Rouge
                color_tk = "#FF0000"
            elif bouteille_trouvee and not avec_bouchon:
                etat = "ERREUR"
                detail = "Bouteille SANS bouchon !"
                color_bgr = (0, 165, 255)  # Orange
                color_tk = "#FFA500"
            else:
                etat = "OK"
                detail = "Bouteille avec bouchon → Validé"
                color_bgr = (0, 200, 0)    # Vert
                color_tk = "#00C800"

            # Annoter l'image
            cv2.putText(frame, etat, (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 2.5, color_bgr, 5)
            cv2.putText(frame, detail, (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 1, color_bgr, 2)

            # Afficher résultat
            display = cv2.resize(frame, (800, 600))
            img_rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
            imgtk = ImageTk.PhotoImage(Image.fromarray(img_rgb))
            self.video_lbl.imgtk = imgtk
            self.video_lbl.configure(image=imgtk)

            # Sauvegarde
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{ts}_{etat}.jpg"
            path = os.path.join(self.output_dir, filename)
            cv2.imwrite(path, frame)

            # Mise à jour interface
            self.root.after(0, lambda: self.status_big.config(text=etat, foreground=color_tk))
            self.root.after(0, lambda: self.detail_lbl.config(text=detail))
            self.log(f"Résultat : {etat} - {detail} - Sauvegardé : {filename}")

            # ─── ENVOI MQTT RÉPONSE ───────────────────────────────
            # Préparer données détaillées pour jumeau numérique
            result_data = {
                "timestamp": datetime.now().isoformat(),
                "status": etat,
                "bouteille_detectee": bouteille_trouvee,
                "bouchon_present": avec_bouchon,
                "niveau_liquide": None,  # Peut être ajouté plus tard avec OpenCV
                "confiance": confiance_max,
                "image_path": path,
                "trigger": trigger_payload,
                "detail": detail
            }

            self.publish_result(etat, detail, trigger_payload, result_data)

        except Exception as e:
            self.log(f"Erreur pendant l'analyse : {e}")
            error_data = {
                "timestamp": datetime.now().isoformat(),
                "status": "ERROR",
                "bouteille_detectee": False,
                "bouchon_present": False,
                "niveau_liquide": None,
                "confiance": 0.0,
                "image_path": None,
                "trigger": trigger_payload,
                "detail": str(e)
            }
            self.publish_result("ERROR", str(e), trigger_payload, error_data)
        finally:
            self.analyzing = False

    def on_closing(self):
        self.is_running = False
        if self.camera:
            if self.use_picamera:
                self.camera.stop()
            else:
                self.camera.release()
        if hasattr(self, 'mqtt_client'):
            try:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
            except:
                pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = BottleCheckerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()