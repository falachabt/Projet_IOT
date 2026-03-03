"""
Interface Tkinter — GUI desktop avec streaming caméra + résultats IA.

Lancement :
    python -m v2.app_tkinter
"""

from __future__ import annotations

import os
import json
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime

import cv2
import numpy as np
from PIL import Image, ImageTk

import paho.mqtt.client as mqtt

from camera import Camera
from config import (
    OUTPUT_DIR,
    MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE, MQTT_USERNAME, MQTT_PASSWORD,
    MQTT_TOPIC_TRIGGER, MQTT_TOPIC_RESULT,
)
from detector import BottleDetector


class BottleCheckerTkApp:
    """Interface graphique Tkinter pour le contrôle qualité bouteille."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Bottle Checker V2 — Tkinter")
        self.root.geometry("1280x780")
        self.root.configure(bg="#1a1d27")

        # État
        self.camera: Camera | None = None
        self.detector: BottleDetector | None = None
        self.is_running = False
        self.current_frame = None
        self.analyzing = False
        self.analysis_count = 0
        self.ok_count = 0
        self.nok_count = 0
        self._mqtt_client: mqtt.Client | None = None

        self._build_ui()
        self._init_backend()
        self._start_mqtt()
        self._start_video_loop()

    # ═════════════════════════════════════════════════════════
    #  CONSTRUCTION UI
    # ═════════════════════════════════════════════════════════
    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Status.TLabel", font=("Segoe UI", 28, "bold"))
        style.configure("Detail.TLabel", font=("Segoe UI", 11))
        style.configure("Big.TButton", font=("Segoe UI", 12, "bold"), padding=12)

        main = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # ── Gauche : vidéo ────────────────────────
        left = ttk.Frame(main)
        main.add(left, weight=3)

        self.video_lbl = ttk.Label(left, text="Démarrage caméra…", background="black")
        self.video_lbl.pack(fill=tk.BOTH, expand=True)

        # ── Droite : contrôles ────────────────────
        right = ttk.Frame(main, padding=12)
        main.add(right, weight=1)

        ttk.Label(right, text="Contrôle Qualité", style="Title.TLabel").pack(pady=(0, 10))

        # Statut gros
        self.status_lbl = ttk.Label(right, text="EN ATTENTE", style="Status.TLabel", foreground="#71717a")
        self.status_lbl.pack(pady=10)

        # Bouton analyser
        self.btn_analyze = ttk.Button(
            right, text="📸  ANALYSER", style="Big.TButton",
            command=self._trigger_analysis,
        )
        self.btn_analyze.pack(fill=tk.X, pady=10)

        ttk.Separator(right, orient="horizontal").pack(fill="x", pady=10)

        # Détails
        detail_frame = ttk.LabelFrame(right, text="Résultats", padding=10)
        detail_frame.pack(fill=tk.X, pady=5)

        self.lbl_bottle = ttk.Label(detail_frame, text="🍾 Bouteille : —", style="Detail.TLabel")
        self.lbl_bottle.pack(anchor="w", pady=3)
        self.lbl_cap = ttk.Label(detail_frame, text="🔴 Bouchon : —", style="Detail.TLabel")
        self.lbl_cap.pack(anchor="w", pady=3)
        self.lbl_label = ttk.Label(detail_frame, text="🏷️ Étiquette : —", style="Detail.TLabel")
        self.lbl_label.pack(anchor="w", pady=3)

        self.lbl_time = ttk.Label(detail_frame, text="", foreground="gray")
        self.lbl_time.pack(anchor="w", pady=(8, 0))

        ttk.Separator(right, orient="horizontal").pack(fill="x", pady=10)

        # Compteurs
        ctr = ttk.Frame(right)
        ctr.pack(fill="x")
        self.lbl_total = ttk.Label(ctr, text="Total : 0")
        self.lbl_total.pack(side="left", padx=8)
        self.lbl_ok = ttk.Label(ctr, text="OK : 0", foreground="green")
        self.lbl_ok.pack(side="left", padx=8)
        self.lbl_nok = ttk.Label(ctr, text="NOK : 0", foreground="red")
        self.lbl_nok.pack(side="left", padx=8)

        ttk.Separator(right, orient="horizontal").pack(fill="x", pady=10)

        # Caméra badge
        self.lbl_camera = ttk.Label(right, text="Caméra : initialisation…", foreground="orange")
        self.lbl_camera.pack(anchor="w")

        # MQTT badge
        self.lbl_mqtt = ttk.Label(right, text="MQTT : connexion…", foreground="orange")
        self.lbl_mqtt.pack(anchor="w")

        # Log
        ttk.Label(right, text="Journal", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(10, 2))
        self.log_txt = scrolledtext.ScrolledText(right, height=8, width=40, state="normal", font=("Consolas", 8))
        self.log_txt.pack(fill=tk.BOTH, expand=True)

    # ═════════════════════════════════════════════════════════
    #  BACKEND
    # ═════════════════════════════════════════════════════════
    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}\n"
        print(line, end="")
        self.log_txt.insert(tk.END, line)
        self.log_txt.see(tk.END)

    def _init_backend(self):
        try:
            self._log("Chargement du modèle YOLO…")
            self.detector = BottleDetector()
            self._log("Modèle chargé ✓")
        except Exception as e:
            self._log(f"ERREUR modèle : {e}")
            messagebox.showerror("Erreur", f"Impossible de charger le modèle :\n{e}")

        try:
            self.camera = Camera()
            self.lbl_camera.config(text=f"Caméra : {self.camera.backend} ✓", foreground="green")
            self._log(f"Caméra ({self.camera.backend}) ✓")
        except Exception as e:
            self.lbl_camera.config(text="Caméra : ERREUR ✗", foreground="red")
            self._log(f"ERREUR caméra : {e}")
            messagebox.showerror("Caméra", str(e))

    # ── Boucle vidéo ─────────────────────────────────────────
    def _start_video_loop(self):
        self.is_running = True
        self._update_video()

    def _update_video(self):
        if not self.is_running:
            return

        if self.camera and not self.analyzing:
            frame = self.camera.read()
            if frame is not None:
                self.current_frame = frame.copy()
                self._display_frame(frame)

        self.root.after(33, self._update_video)

    def _display_frame(self, frame: np.ndarray):
        """Affiche une frame BGR dans le label vidéo."""
        display = self._resize(frame, 800, 600)
        rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
        img = ImageTk.PhotoImage(Image.fromarray(rgb))
        self.video_lbl.imgtk = img  # empêcher le GC
        self.video_lbl.configure(image=img)

    @staticmethod
    def _resize(frame: np.ndarray, max_w: int = 800, max_h: int = 600) -> np.ndarray:
        h, w = frame.shape[:2]
        scale = min(max_w / w, max_h / h, 1.0)
        return cv2.resize(frame, (int(w * scale), int(h * scale)))

    # ── Analyse ──────────────────────────────────────────────
    def _trigger_analysis(self):
        if self.current_frame is None:
            messagebox.showwarning("Attention", "Aucune image disponible")
            return
        if self.analyzing:
            return
        self.analyzing = True
        self.btn_analyze.config(state="disabled", text="⏳ Analyse…")
        self._log("Analyse déclenchée…")
        threading.Thread(target=self._perform_analysis, daemon=True).start()

    def _perform_analysis(self):
        try:
            frame = self.current_frame.copy()
            result, annotated = self.detector.analyze(frame)

            # Afficher l'image annotée
            self.root.after(0, self._display_frame, annotated)

            # Mise à jour UI
            self.root.after(0, self._update_results, result)
            self._mqtt_publish_result(result)

        except Exception as e:
            self._log(f"Erreur analyse : {e}")
            self.root.after(0, messagebox.showerror, "Erreur", str(e))
        finally:
            self.analyzing = False
            self.root.after(0, lambda: self.btn_analyze.config(state="normal", text="📸  ANALYSER"))

    def _update_results(self, result: dict):
        status = result["status"]
        is_ok = status == "OK"

        self.status_lbl.config(
            text=status,
            foreground="#22c55e" if is_ok else "#ef4444",
        )

        def fmt(item: dict) -> tuple[str, str]:
            if item["detected"]:
                return f"DÉTECTÉ ({item['confidence']:.0%})", "green"
            return "ABSENT", "red"

        bt, bc = fmt(result["bottle"])
        self.lbl_bottle.config(text=f"🍾 Bouteille : {bt}", foreground=bc)

        ct, cc = fmt(result["cap"])
        self.lbl_cap.config(text=f"🔴 Bouchon : {ct}", foreground=cc)

        lt, lc = fmt(result["label"])
        self.lbl_label.config(text=f"🏷️ Étiquette : {lt}", foreground=lc)

        self.lbl_time.config(text=f"{result.get('timestamp', '')}  •  {result.get('elapsed_ms', '')} ms")

        # Compteurs
        self.analysis_count += 1
        if is_ok:
            self.ok_count += 1
        else:
            self.nok_count += 1
        self.lbl_total.config(text=f"Total : {self.analysis_count}")
        self.lbl_ok.config(text=f"OK : {self.ok_count}")
        self.lbl_nok.config(text=f"NOK : {self.nok_count}")

        self._log(f"Résultat → {status}")

    # ── MQTT ─────────────────────────────────────────────────
    def _start_mqtt(self):
        """Démarre le client MQTT en background."""
        def on_connect(client, userdata, flags, rc, properties=None):
            if rc == 0:
                client.subscribe(MQTT_TOPIC_TRIGGER)
                self.root.after(0, self.lbl_mqtt.config,
                                {"text": f"MQTT : {MQTT_BROKER} ✓", "foreground": "green"})
                self._log(f"MQTT connecté — écoute '{MQTT_TOPIC_TRIGGER}'")
            else:
                self.root.after(0, self.lbl_mqtt.config,
                                {"text": f"MQTT : erreur (rc={rc})", "foreground": "red"})
                self._log(f"MQTT erreur connexion rc={rc}")

        def on_message(client, userdata, msg):
            payload = msg.payload.decode(errors="ignore")
            # Filtrer : ne déclencher que si objet_detecte est true
            try:
                data = json.loads(payload)
                if not data.get("objet_detecte", False):
                    return
            except (json.JSONDecodeError, AttributeError):
                pass  # payload non-JSON → on laisse passer
            self._log(f"MQTT trigger reçu : {payload}")
            # Déclencher l'analyse depuis le thread principal Tkinter
            self.root.after(0, self._trigger_analysis)

        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.on_connect = on_connect
        client.on_message = on_message
        if MQTT_USERNAME:
            client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
            client.loop_start()
            self._mqtt_client = client
            self._log(f"MQTT connexion à {MQTT_BROKER}:{MQTT_PORT}…")
        except Exception as e:
            self.lbl_mqtt.config(text=f"MQTT : indisponible", foreground="gray")
            self._log(f"MQTT indisponible : {e}")

    def _mqtt_publish_result(self, result: dict):
        """Publie le résultat JSON sur le topic MQTT résultat."""
        if self._mqtt_client:
            try:
                self._mqtt_client.publish(MQTT_TOPIC_RESULT, json.dumps(result))
                self._log(f"MQTT résultat publié → {result['status']}")
            except Exception as e:
                self._log(f"MQTT publish erreur : {e}")

    # ── Fermeture ────────────────────────────────────────────
    def on_closing(self):
        self.is_running = False
        if self._mqtt_client:
            self._mqtt_client.loop_stop()
            self._mqtt_client.disconnect()
        if self.camera:
            self.camera.release()
        self.root.destroy()


# ─────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    app = BottleCheckerTkApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
