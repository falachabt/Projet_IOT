import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
try:
    from picamera2 import Picamera2
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False
from datetime import datetime
import os
import threading
import traceback

# ─── Roboflow Inference ───────────────────────────────────────
from inference_sdk import InferenceHTTPClient

class FlaconCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Contrôle Qualité Flacon - V5 Roboflow String Parsing")
        self.root.geometry("1200x800")

        self.output_dir = "./output"
        os.makedirs(self.output_dir, exist_ok=True)

        self.camera = None
        self.is_running = False
        self.analyzing = False
        self.current_frame = None
        self.use_webcam = False

        print("[INFO] Initialisation client Roboflow Inference...")
        try:
            self.rf_client = InferenceHTTPClient(
                api_url="https://serverless.roboflow.com",
                api_key="8LX7VmCoSaapXMG92lzA"
            )
            self.workspace_name = "projet-iot-u7nvb"
            self.workflow_id = "find-bottles-and-caps"
            print("[OK] Client Roboflow prêt")
        except Exception as e:
            print(f"[ERREUR] Client Roboflow: {e}")
            messagebox.showerror("Erreur Roboflow", f"Impossible d'initialiser le client:\n{e}")
            self.rf_client = None

        self.create_widgets()
        self.init_camera()
        self.start_video()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.video_label = ttk.Label(left_frame, text="Démarrage de la caméra...", 
                                     background="black", foreground="white")
        self.video_label.pack(fill=tk.BOTH, expand=True)

        right_frame = ttk.Frame(main_frame, padding="10")
        right_frame.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(right_frame, text="Contrôle Qualité Flacon", font=("Arial", 16, "bold")).pack(pady=10)

        self.camera_status_label = ttk.Label(right_frame, text="Caméra: Initialisation...", font=("Arial", 10))
        self.camera_status_label.pack(pady=5)

        self.analyze_button = ttk.Button(right_frame, text="📸 ANALYSER", command=self.trigger_analysis,
                                         style="Accent.TButton")
        self.analyze_button.pack(pady=20, ipadx=30, ipady=10)

        ttk.Separator(right_frame, orient='horizontal').pack(fill='x', pady=10)

        ttk.Label(right_frame, text="Résultats de l'analyse", font=("Arial", 12, "bold")).pack(pady=5)

        self.results_frame = ttk.Frame(right_frame, relief="sunken", borderwidth=2)
        self.results_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.status_label = ttk.Label(self.results_frame, text="--", font=("Arial", 24, "bold"))
        self.status_label.pack(pady=15)

        self.bottle_label = ttk.Label(self.results_frame, text="Bouteille: --", font=("Arial", 11))
        self.bottle_label.pack(pady=5)

        self.cap_label = ttk.Label(self.results_frame, text="Bouchon: --", font=("Arial", 11))
        self.cap_label.pack(pady=5)

        self.confidence_label = ttk.Label(self.results_frame, text="Confiance: --", font=("Arial", 10), foreground="gray")
        self.confidence_label.pack(pady=5)

        self.timestamp_label = ttk.Label(self.results_frame, text="", font=("Arial", 9), foreground="gray")
        self.timestamp_label.pack(pady=5)

        ttk.Separator(right_frame, orient='horizontal').pack(fill='x', pady=10)

        ttk.Label(right_frame, text="Seuil de confiance (%)", font=("Arial", 11, "bold")).pack(pady=5)
        conf_frame = ttk.Frame(right_frame)
        conf_frame.pack(fill='x', pady=3)
        ttk.Label(conf_frame, text="Confiance min:").pack(side=tk.LEFT)
        self.conf_var = tk.IntVar(value=40)
        ttk.Spinbox(conf_frame, from_=10, to=99, textvariable=self.conf_var, width=10).pack(side=tk.RIGHT)

        ttk.Separator(right_frame, orient='horizontal').pack(fill='x', pady=10)
        stats_frame = ttk.Frame(right_frame)
        stats_frame.pack(fill='x', pady=5)

        self.counter_label = ttk.Label(stats_frame, text="Total: 0", font=("Arial", 9))
        self.counter_label.pack(side=tk.LEFT, padx=10)

        self.ok_counter_label = ttk.Label(stats_frame, text="OK: 0", font=("Arial", 9), foreground="green")
        self.ok_counter_label.pack(side=tk.LEFT, padx=10)

        self.nok_counter_label = ttk.Label(stats_frame, text="NOK: 0", font=("Arial", 9), foreground="red")
        self.nok_counter_label.pack(side=tk.LEFT, padx=10)

        self.analysis_count = 0
        self.ok_count = 0
        self.nok_count = 0

        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

    def init_camera(self):
        try:
            if CAMERA_AVAILABLE:
                print("[INFO] Initialisation Picamera2...")
                self.camera = Picamera2()
                config = self.camera.create_preview_configuration(main={"size": (1280, 720)})
                self.camera.configure(config)
                self.camera.start()
                self.use_webcam = False
                self.camera_status_label.config(text="Caméra: Picamera2 ✓", foreground="green")
            else:
                print("[INFO] Utilisation webcam...")
                self.camera = cv2.VideoCapture(0)
                if not self.camera.isOpened():
                    raise Exception("Webcam non détectée")
                self.use_webcam = True
                self.camera_status_label.config(text="Caméra: Webcam ✓", foreground="green")
        except Exception as e:
            print(f"[ERREUR] Caméra: {e}")
            self.camera_status_label.config(text="Caméra: ERREUR ✗", foreground="red")
            messagebox.showerror("Erreur Caméra", str(e))

    def start_video(self):
        self.is_running = True
        self.update_video()

    def update_video(self):
        if not self.is_running:
            return

        try:
            if self.use_webcam:
                ret, frame = self.camera.read()
                if not ret:
                    return
            else:
                frame = self.camera.capture_array("main")
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            self.current_frame = frame.copy()

            if not self.analyzing:
                display_frame = self.resize_frame(frame)
                cv2.putText(display_frame, "Mode: Surveillance - Prêt à analyser", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)

        except Exception as e:
            print(f"[ERREUR vidéo] {e}")

        self.root.after(33, self.update_video)

    def resize_frame(self, frame, max_width=800, max_height=600):
        h, w = frame.shape[:2]
        scale = min(max_width / w, max_height / h)
        return cv2.resize(frame, (int(w * scale), int(h * scale)))

    def trigger_analysis(self):
        if self.current_frame is None:
            messagebox.showwarning("Attention", "Aucune image disponible")
            return
        if self.analyzing:
            messagebox.showinfo("Info", "Analyse en cours...")
            return
        if not self.rf_client:
            messagebox.showerror("Erreur", "Client Roboflow non initialisé")
            return

        self.analyze_button.config(state="disabled", text="⏳ Analyse...")
        self.analyzing = True

        threading.Thread(target=self.perform_analysis, daemon=True).start()

    def perform_analysis(self):
        try:
            frame = self.current_frame.copy()

            print("[DEBUG] Type image envoyée :", type(frame))
            print("[DEBUG] Shape :", frame.shape if isinstance(frame, np.ndarray) else "N/A")

            result = self.rf_client.run_workflow(
                workspace_name=self.workspace_name,
                workflow_id=self.workflow_id,
                images={"image": frame},
                use_cache=True
            )

            # ─── DEBUG COMPLET ───────────────────────────────────────────────
            print("\n" + "="*80)
            print("[DEBUG] Type de result :", type(result))
            print("[DEBUG] Contenu complet de result :")
            print(result)
            print("="*80 + "\n")

            # Préparation des variables de résultat
            bottle_detected = False
            cap_detected = False
            bottle_conf = 0.0
            cap_conf = 0.0
            bottle_boxes = []   # vide car pas de bounding boxes dans ce format
            cap_boxes = []      # vide car pas de bounding boxes dans ce format

            conf_threshold = self.conf_var.get() / 100.0

            # ─── CAS 1 : liste de strings ───────────────────────────────────
            if isinstance(result, list) and all(isinstance(item, str) for item in result):
                print("[DEBUG] Format détecté : liste de STRINGS")
                for item in result:
                    parts = item.strip().split()
                    if len(parts) < 2:
                        continue
                    cls_name = parts[0].lower()
                    try:
                        conf = float(parts[1])
                    except ValueError:
                        continue

                    if conf < conf_threshold:
                        continue

                    if any(k in cls_name for k in ["bottle", "flacon", "flask", "bouteille"]):
                        bottle_detected = True
                        bottle_conf = max(bottle_conf, conf)
                        print(f"   → Bouteille détectée : {conf:.3f}")

                    elif any(k in cls_name for k in ["cap", "bouchon", "lid", "cover", "top", "capsule"]):
                        cap_detected = True
                        cap_conf = max(cap_conf, conf)
                        print(f"   → Bouchon détecté : {conf:.3f}")

            # ─── CAS 2 : une seule string ───────────────────────────────────
            elif isinstance(result, str):
                print("[DEBUG] Format détecté : STRING unique")
                text = result.lower()
                bottle_detected = any(k in text for k in ["bottle", "flacon", "flask", "bouteille"])
                cap_detected = any(k in text for k in ["cap", "bouchon", "lid", "cover", "top", "capsule"])
                # Pas de confiance précise possible ici
                bottle_conf = cap_conf = 0.0 if bottle_detected and cap_detected else 0.0

            # ─── CAS 3 : autre format inattendu ─────────────────────────────
            else:
                print("[WARNING] Format de réponse inattendu :", type(result))
                bottle_detected = cap_detected = False

            is_ok = bottle_detected and cap_detected

            # Affichage résultat texte sur l'image (pas de boxes possibles)
            color_ok = (0, 255, 0) if is_ok else (0, 0, 255)
            status_text = "✓ OK" if is_ok else "✗ REJET"
            cv2.putText(frame, status_text, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 3, color_ok, 6)

            # Message supplémentaire si détections
            if bottle_detected:
                cv2.putText(frame, f"Bouteille {bottle_conf:.2f}", (50, 180),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
            if cap_detected:
                cv2.putText(frame, f"Bouchon {cap_conf:.2f}", (50, 220),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 165, 0), 3)

            # Affichage Tkinter
            display_frame = self.resize_frame(frame)
            frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

            # Sauvegarde
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            status_clean = "OK" if is_ok else "REJET"
            filename = f"{timestamp}_{status_clean}.jpg"
            cv2.imwrite(os.path.join(self.output_dir, filename), frame)

            # Mise à jour UI
            self.root.after(0, self.update_results, status_text, bottle_detected, cap_detected,
                            bottle_conf, cap_conf, timestamp)

            self.analysis_count += 1
            if is_ok:
                self.ok_count += 1
            else:
                self.nok_count += 1
            self.root.after(0, self.update_counters)

            print(f"[OK] Analyse terminée → {status_text} | Bouteille: {bottle_conf:.1%} | Bouchon: {cap_conf:.1%}")

        except Exception as e:
            print(f"[ERREUR Analyse] {e}")
            traceback.print_exc()
            self.root.after(0, messagebox.showerror, "Erreur Analyse", str(e))

        finally:
            self.analyzing = False
            self.root.after(0, lambda: self.analyze_button.config(state="normal", text="📸 ANALYSER"))

    def update_results(self, status, bottle_detected, cap_detected, bottle_conf, cap_conf, timestamp):
        self.status_label.config(text=status, foreground="green" if "OK" in status else "red")

        bottle_text = f"DÉTECTÉE ({bottle_conf:.1%})" if bottle_detected else "ABSENTE"
        self.bottle_label.config(text=f"Bouteille: {bottle_text}", foreground="green" if bottle_detected else "red")

        cap_text = f"DÉTECTÉ ({cap_conf:.1%})" if cap_detected else "ABSENT"
        self.cap_label.config(text=f"Bouchon: {cap_text}", foreground="green" if cap_detected else "red")

        if bottle_detected and cap_detected:
            avg = (bottle_conf + cap_conf) / 2
            self.confidence_label.config(text=f"Conf moyenne: {avg:.1%}")
        else:
            self.confidence_label.config(text="Confiance: --")

        self.timestamp_label.config(text=f"Analysé: {timestamp}")

    def update_counters(self):
        self.counter_label.config(text=f"Total: {self.analysis_count}")
        self.ok_counter_label.config(text=f"OK: {self.ok_count}")
        self.nok_counter_label.config(text=f"NOK: {self.nok_count}")

    def cleanup(self):
        self.is_running = False
        if self.camera:
            if self.use_webcam:
                self.camera.release()
            else:
                self.camera.stop()
        print("[INFO] Application fermée")

    def on_closing(self):
        if messagebox.askokcancel("Quitter", "Vraiment quitter ?"):
            self.cleanup()
            self.root.destroy()

def main():
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')
    app = FlaconCheckerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()