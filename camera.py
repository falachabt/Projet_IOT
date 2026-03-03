"""
Abstraction caméra — supporte Webcam (OpenCV) et PiCamera2.
Utilisation :
    cam = Camera()
    frame = cam.read()       # numpy BGR
    cam.release()
"""

import cv2
import numpy as np

try:
    from picamera2 import Picamera2
    _PICAMERA_AVAILABLE = True
except ImportError:
    _PICAMERA_AVAILABLE = False

from config import CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT


class Camera:
    """Wrapper unifié pour accéder à une caméra (webcam ou PiCamera2)."""

    def __init__(self, force_webcam: bool = False):
        self._cap = None
        self._picam = None
        self._use_picam = False
        self._opened = False

        if _PICAMERA_AVAILABLE and not force_webcam:
            self._init_picamera()
        else:
            self._init_webcam()

    # ── initialisations ──────────────────────────────────────
    def _init_picamera(self):
        try:
            self._picam = Picamera2()
            cfg = self._picam.create_preview_configuration(
                main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT)}
            )
            self._picam.configure(cfg)
            self._picam.start()
            self._use_picam = True
            self._opened = True
            print("[Camera] PiCamera2 initialisée")
        except Exception as e:
            print(f"[Camera] PiCamera2 échoué ({e}), repli webcam")
            self._init_webcam()

    def _init_webcam(self):
        self._cap = cv2.VideoCapture(CAMERA_INDEX)
        if not self._cap.isOpened():
            raise RuntimeError(
                f"Impossible d'ouvrir la webcam (index {CAMERA_INDEX}). "
                "Vérifiez qu'une caméra est branchée."
            )
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        self._use_picam = False
        self._opened = True
        print(f"[Camera] Webcam index {CAMERA_INDEX} initialisée")

    # ── lecture ───────────────────────────────────────────────
    def read(self) -> np.ndarray | None:
        """Renvoie une frame BGR (numpy array) ou None si erreur."""
        if not self._opened:
            return None
        try:
            if self._use_picam:
                frame = self._picam.capture_array("main")
                return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            else:
                ret, frame = self._cap.read()
                return frame if ret else None
        except Exception as e:
            print(f"[Camera] Erreur lecture : {e}")
            return None

    # ── propriétés ───────────────────────────────────────────
    @property
    def is_opened(self) -> bool:
        return self._opened

    @property
    def backend(self) -> str:
        return "picamera2" if self._use_picam else "webcam"

    # ── libération ───────────────────────────────────────────
    def release(self):
        self._opened = False
        if self._use_picam and self._picam:
            try:
                self._picam.stop()
            except Exception:
                pass
        elif self._cap:
            self._cap.release()
        print("[Camera] Ressources libérées")
