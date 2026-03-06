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
from ultralytics import YOLO
from datetime import datetime
import os
import threading

class FlackonCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Contrôle Qualité Flacon - V2")
        self.root.geometry("1200x800")
        
        # Configuration
        self.MIN_FILL_PERCENT = 80
        self.MAX_FILL_PERCENT = 105
        self.BOTTLE_HEIGHT_PX = 800
        self.CAP_HEIGHT_PX = 100
        self.output_dir = "./output"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Variables
        self.camera = None
        self.is_running = False
        self.analyzing = False
        self.current_frame = None
        self.use_webcam = False
        
        # Charger le modèle YOLO
        print("[INFO] Chargement du modèle YOLO...")
        self.model = YOLO("yolo11n.pt")
        print("[OK] Modèle chargé")
        
        # Créer l'interface
        self.create_widgets()
        
        # Initialiser la caméra
        self.init_camera()
        
        # Démarrer l'affichage vidéo
        self.start_video()
        
    def create_widgets(self):
        """Créer tous les widgets de l'interface"""
        
        # Frame principale divisée en 2 colonnes
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # === COLONNE GAUCHE : Vidéo ===
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Label pour la vidéo
        self.video_label = ttk.Label(left_frame, text="Démarrage de la caméra...", 
                                     background="black", foreground="white")
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        # === COLONNE DROITE : Contrôles et Résultats ===
        right_frame = ttk.Frame(main_frame, padding="10")
        right_frame.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Titre
        title_label = ttk.Label(right_frame, text="Contrôle Qualité", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Statut caméra
        self.camera_status_label = ttk.Label(right_frame, text="Caméra: Initialisation...", 
                                            font=("Arial", 10))
        self.camera_status_label.pack(pady=5)
        
        # Bouton principal d'analyse
        self.analyze_button = ttk.Button(right_frame, text="📸 ANALYSER", 
                                        command=self.trigger_analysis,
                                        style="Accent.TButton")
        self.analyze_button.pack(pady=20, ipadx=30, ipady=10)
        
        # Séparateur
        ttk.Separator(right_frame, orient='horizontal').pack(fill='x', pady=10)
        
        # Zone de résultats
        results_label = ttk.Label(right_frame, text="Résultats de l'analyse", 
                                 font=("Arial", 12, "bold"))
        results_label.pack(pady=5)
        
        # Frame pour les résultats
        self.results_frame = ttk.Frame(right_frame, relief="sunken", borderwidth=2)
        self.results_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Statut global
        self.status_label = ttk.Label(self.results_frame, text="--", 
                                     font=("Arial", 24, "bold"))
        self.status_label.pack(pady=15)
        
        # Détails
        self.fill_label = ttk.Label(self.results_frame, text="Niveau: --", 
                                   font=("Arial", 11))
        self.fill_label.pack(pady=5)
        
        self.cap_label = ttk.Label(self.results_frame, text="Bouchon: --", 
                                  font=("Arial", 11))
        self.cap_label.pack(pady=5)
        
        self.timestamp_label = ttk.Label(self.results_frame, text="", 
                                        font=("Arial", 9), foreground="gray")
        self.timestamp_label.pack(pady=5)
        
        # Séparateur
        ttk.Separator(right_frame, orient='horizontal').pack(fill='x', pady=10)
        
        # Paramètres
        params_label = ttk.Label(right_frame, text="Paramètres", 
                                font=("Arial", 11, "bold"))
        params_label.pack(pady=5)
        
        # Niveau min
        min_frame = ttk.Frame(right_frame)
        min_frame.pack(fill='x', pady=3)
        ttk.Label(min_frame, text="Niveau min (%):").pack(side=tk.LEFT)
        self.min_fill_var = tk.IntVar(value=self.MIN_FILL_PERCENT)
        min_spin = ttk.Spinbox(min_frame, from_=0, to=100, textvariable=self.min_fill_var, 
                              width=10, command=self.update_params)
        min_spin.pack(side=tk.RIGHT)
        
        # Niveau max
        max_frame = ttk.Frame(right_frame)
        max_frame.pack(fill='x', pady=3)
        ttk.Label(max_frame, text="Niveau max (%):").pack(side=tk.LEFT)
        self.max_fill_var = tk.IntVar(value=self.MAX_FILL_PERCENT)
        max_spin = ttk.Spinbox(max_frame, from_=0, to=150, textvariable=self.max_fill_var, 
                              width=10, command=self.update_params)
        max_spin.pack(side=tk.RIGHT)
        
        # Compteur d'analyses
        ttk.Separator(right_frame, orient='horizontal').pack(fill='x', pady=10)
        self.counter_label = ttk.Label(right_frame, text="Analyses effectuées: 0", 
                                      font=("Arial", 9))
        self.counter_label.pack(pady=5)
        self.analysis_count = 0
        
        # Configurer les poids pour redimensionnement
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
    def init_camera(self):
        """Initialiser la caméra"""
        try:
            if CAMERA_AVAILABLE:
                print("[INFO] Initialisation Picamera2...")
                self.camera = Picamera2()
                config = self.camera.create_preview_configuration(main={"size": (1280, 720)})
                self.camera.configure(config)
                self.camera.start()
                self.use_webcam = False
                print("[OK] Picamera2 initialisée")
                self.camera_status_label.config(text="Caméra: Picamera2 ✓", foreground="green")
            else:
                print("[INFO] Utilisation de la webcam...")
                self.camera = cv2.VideoCapture(0)
                if not self.camera.isOpened():
                    raise Exception("Impossible d'ouvrir la webcam")
                self.use_webcam = True
                print("[OK] Webcam initialisée")
                self.camera_status_label.config(text="Caméra: Webcam ✓", foreground="green")
        except Exception as e:
            print(f"[ERREUR] Initialisation caméra: {e}")
            self.camera_status_label.config(text="Caméra: ERREUR ✗", foreground="red")
            messagebox.showerror("Erreur Caméra", f"Impossible d'initialiser la caméra:\n{e}")
            
    def start_video(self):
        """Démarrer l'affichage vidéo en temps réel"""
        self.is_running = True
        self.update_video()
        
    def update_video(self):
        """Mettre à jour l'affichage vidéo"""
        if not self.is_running:
            return
            
        try:
            # Capturer une frame
            if self.use_webcam:
                ret, frame = self.camera.read()
                if not ret:
                    print("[ERREUR] Échec capture webcam")
                    return
            else:
                frame = self.camera.capture_array("main")
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            self.current_frame = frame.copy()
            
            # Si analyse en cours, ne pas afficher la frame normale
            if not self.analyzing:
                # Redimensionner pour affichage
                display_frame = self.resize_frame(frame)
                
                # Ajouter un texte indicatif
                cv2.putText(display_frame, "Mode: Surveillance", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Convertir pour Tkinter
                frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
            
        except Exception as e:
            print(f"[ERREUR] Mise à jour vidéo: {e}")
        
        # Rappeler cette fonction après 30ms
        self.root.after(30, self.update_video)
        
    def resize_frame(self, frame, max_width=800, max_height=600):
        """Redimensionner une frame pour l'affichage"""
        height, width = frame.shape[:2]
        scale = min(max_width/width, max_height/height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        return cv2.resize(frame, (new_width, new_height))
        
    def trigger_analysis(self):
        """Déclencher l'analyse de la frame actuelle"""
        if self.current_frame is None:
            messagebox.showwarning("Attention", "Aucune image disponible pour l'analyse")
            return
            
        if self.analyzing:
            messagebox.showinfo("Info", "Une analyse est déjà en cours")
            return
        
        # Désactiver le bouton pendant l'analyse
        self.analyze_button.config(state="disabled", text="⏳ Analyse en cours...")
        
        # Lancer l'analyse dans un thread séparé
        thread = threading.Thread(target=self.perform_analysis)
        thread.daemon = True
        thread.start()
        
    def perform_analysis(self):
        """Effectuer l'analyse de la bouteille"""
        self.analyzing = True
        
        try:
            frame = self.current_frame.copy()
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # --- ETAPE 1 : Détection bouteille avec YOLO ---
            results = self.model(frame_rgb, conf=0.4)
            
            cap_detected = False
            cap_ok = False
            bottle_found = False
            
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cls = int(box.cls)
                    conf = float(box.conf)
                    class_name = self.model.names[cls]
                    
                    # Chercher spécifiquement une bouteille
                    if class_name == 'bottle':
                        bottle_found = True
                        bottle_height = y2 - y1
                        bottle_width = x2 - x1
                        
                        # Rectangle autour de la bouteille
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 2)
                        cv2.putText(frame, f"Bouteille {conf:.2f}", (x1, y1-10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
                        
                        # --- ANALYSE DE LA ZONE DU BOUCHON (20% supérieur de la bouteille) ---
                        cap_zone_height = int(bottle_height * 0.2)
                        cap_y1 = max(0, y1)
                        cap_y2 = min(frame.shape[0], y1 + cap_zone_height)
                        cap_x1 = max(0, x1)
                        cap_x2 = min(frame.shape[1], x2)
                        
                        # Extraire la zone du bouchon
                        cap_zone = frame[cap_y1:cap_y2, cap_x1:cap_x2]
                        
                        if cap_zone.size > 0:
                            # Convertir en niveaux de gris
                            cap_gray = cv2.cvtColor(cap_zone, cv2.COLOR_BGR2GRAY)
                            
                            # Détection de contours dans la zone du bouchon
                            cap_blur = cv2.GaussianBlur(cap_gray, (5, 5), 0)
                            _, cap_thresh = cv2.threshold(cap_blur, 80, 255, cv2.THRESH_BINARY)
                            
                            # Trouver les contours
                            cap_contours, _ = cv2.findContours(cap_thresh, cv2.RETR_EXTERNAL, 
                                                               cv2.CHAIN_APPROX_SIMPLE)
                            
                            # Analyse des contours pour détecter un bouchon
                            significant_contours = [c for c in cap_contours 
                                                   if cv2.contourArea(c) > 100]
                            
                            # Calculer la variance de couleur (bouchon = plus uniforme)
                            color_variance = np.var(cap_gray)
                            
                            # Calculer la densité de pixels blancs (bouchon fermé = plus dense)
                            white_ratio = np.sum(cap_thresh > 200) / cap_thresh.size
                            
                            # Critères pour détecter un bouchon fermé
                            has_circular_shape = len(significant_contours) >= 1
                            uniform_color = color_variance < 1500  # Couleur uniforme
                            good_density = 0.3 < white_ratio < 0.8  # Densité raisonnable
                            
                            cap_detected = has_circular_shape and (uniform_color or good_density)
                            cap_ok = cap_detected
                            
                            # Rectangle zone d'analyse du bouchon
                            rect_color = (0, 255, 0) if cap_ok else (0, 0, 255)
                            cv2.rectangle(frame, (cap_x1, cap_y1), (cap_x2, cap_y2), rect_color, 2)
                            
                            # Afficher les métriques de détection
                            debug_text = f"Var:{color_variance:.0f} Den:{white_ratio:.2f}"
                            cv2.putText(frame, debug_text, (cap_x1, cap_y1-30), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, rect_color, 1)
                            cv2.putText(frame, "Zone bouchon", (cap_x1, cap_y1-15), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, rect_color, 2)
                        
                        break  # Prendre seulement la première bouteille trouvée
            
            # Si pas de bouteille trouvée, analyse impossible
            if not bottle_found:
                status = "✗ REJET"
                color = (0, 0, 255)
                fill_percent = 0
                fill_ok = False
                cap_ok = False
                
                cv2.putText(frame, "Aucune bouteille detectee", (50, 80), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
            else:
                # --- ETAPE 2 : Détection niveau de liquide ---
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blur = cv2.GaussianBlur(gray, (5,5), 0)
                _, thresh = cv2.threshold(blur, 100, 255, cv2.THRESH_BINARY_INV)
                
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                fill_level_px = 0
                if contours:
                    largest = max(contours, key=cv2.contourArea)
                    if cv2.contourArea(largest) > 5000:
                        x, y, w, h = cv2.boundingRect(largest)
                        fill_level_px = y + h // 2
                
                fill_percent = ((self.BOTTLE_HEIGHT_PX - fill_level_px) / self.BOTTLE_HEIGHT_PX) * 100
                fill_ok = self.MIN_FILL_PERCENT <= fill_percent <= self.MAX_FILL_PERCENT
                
                # Résultat global
                status = "✓ OK" if fill_ok and cap_ok and bottle_found else "✗ REJET"
                color = (0, 255, 0) if fill_ok and cap_ok and bottle_found else (0, 0, 255)
                
                # Ajouter les résultats sur l'image
                cv2.putText(frame, status, (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 2.5, color, 5)
                cv2.putText(frame, f"Niveau: {fill_percent:.1f}%", (20, 140), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                bouchon_status = "FERME" if cap_ok else "OUVERT/ABSENT"
                bouchon_color = (0, 255, 0) if cap_ok else (0, 0, 255)
                cv2.putText(frame, f"Bouchon: {bouchon_status}", (20, 180), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, bouchon_color, 2)
            
            # Afficher l'image analysée
            display_frame = self.resize_frame(frame)
            frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
            
            # Sauvegarder l'image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{status.replace(' ', '_').replace('✓', 'OK').replace('✗', 'REJET')}.jpg"
            filepath = os.path.join(self.output_dir, filename)
            cv2.imwrite(filepath, frame)
            
            # Mettre à jour l'interface
            self.root.after(0, self.update_results, status, fill_percent, cap_ok, timestamp)
            
            # Incrémenter le compteur
            self.analysis_count += 1
            self.root.after(0, self.counter_label.config, {"text": f"Analyses effectuées: {self.analysis_count}"})
            
            print(f"[OK] Analyse terminée: {status} - Image: {filename}")
            
        except Exception as e:
            print(f"[ERREUR] Analyse: {e}")
            self.root.after(0, messagebox.showerror, "Erreur", f"Erreur lors de l'analyse:\n{e}")
        
        finally:
            self.analyzing = False
            self.root.after(0, self.analyze_button.config, {"state": "normal", "text": "📸 ANALYSER"})
            
    def update_results(self, status, fill_percent, cap_ok, timestamp):
        """Mettre à jour l'affichage des résultats"""
        # Statut avec couleur
        if "OK" in status:
            self.status_label.config(text=status, foreground="green")
        else:
            self.status_label.config(text=status, foreground="red")
        
        # Détails
        fill_color = "green" if self.MIN_FILL_PERCENT <= fill_percent <= self.MAX_FILL_PERCENT else "orange"
        self.fill_label.config(text=f"Niveau: {fill_percent:.1f}%", foreground=fill_color)
        
        cap_color = "green" if cap_ok else "red"
        cap_text = "OK" if cap_ok else "MANQUANT"
        self.cap_label.config(text=f"Bouchon: {cap_text}", foreground=cap_color)
        
        self.timestamp_label.config(text=f"Analysé le: {timestamp}")
        
    def update_params(self):
        """Mettre à jour les paramètres"""
        self.MIN_FILL_PERCENT = self.min_fill_var.get()
        self.MAX_FILL_PERCENT = self.max_fill_var.get()
        print(f"[CONFIG] Paramètres mis à jour: {self.MIN_FILL_PERCENT}% - {self.MAX_FILL_PERCENT}%")
        
    def cleanup(self):
        """Nettoyer les ressources"""
        self.is_running = False
        if self.camera:
            if self.use_webcam:
                self.camera.release()
            else:
                self.camera.stop()
        print("[INFO] Application arrêtée")
        
    def on_closing(self):
        """Gérer la fermeture de l'application"""
        if messagebox.askokcancel("Quitter", "Voulez-vous vraiment quitter?"):
            self.cleanup()
            self.root.destroy()

def main():
    root = tk.Tk()
    
    # Thème
    style = ttk.Style()
    style.theme_use('clam')
    
    app = FlackonCheckerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
