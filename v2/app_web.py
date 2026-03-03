"""
Interface Web — Flask + streaming vidéo temps réel + résultats IA.

Lancement :
    python -m v2.app_web
    → ouvre http://localhost:5000
"""

from __future__ import annotations

import json
import threading
import time

import cv2
from flask import Flask, Response, jsonify, render_template, send_from_directory

from v2.camera import Camera
from v2.config import OUTPUT_DIR, WEB_HOST, WEB_PORT, WEB_DEBUG
from v2.detector import BottleDetector

# ─────────────────────────────────────────────────────────────
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)

# Objets partagés
camera: Camera | None = None
detector: BottleDetector | None = None

# Dernier résultat d'analyse (thread-safe via verrou)
_lock = threading.Lock()
_last_result: dict | None = None
_last_annotated_frame = None  # numpy BGR
_current_frame = None          # frame live courante
_analyzing = False


# ─────────────────────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    """Flux MJPEG temps réel."""
    return Response(
        _generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/analyze", methods=["POST"])
def analyze():
    """Déclenche une analyse sur la frame courante."""
    global _last_result, _last_annotated_frame, _analyzing

    if _analyzing:
        return jsonify({"error": "Analyse déjà en cours"}), 429

    frame = _current_frame
    if frame is None:
        return jsonify({"error": "Pas de frame disponible"}), 503

    _analyzing = True
    try:
        result, annotated = detector.analyze(frame)
        with _lock:
            _last_result = result
            _last_annotated_frame = annotated
        return jsonify(result)
    finally:
        _analyzing = False


@app.route("/last_result")
def last_result():
    """Renvoie le dernier résultat d'analyse."""
    with _lock:
        if _last_result is None:
            return jsonify({"status": "NO_ANALYSIS_YET"})
        return jsonify(_last_result)


@app.route("/output/<path:filename>")
def serve_output(filename):
    return send_from_directory(OUTPUT_DIR, filename)


# ─────────────────────────────────────────────────────────────
#  STREAMING
# ─────────────────────────────────────────────────────────────
def _generate_frames():
    """Génère un flux MJPEG à partir de la caméra."""
    global _current_frame
    while True:
        frame = camera.read()
        if frame is None:
            time.sleep(0.05)
            continue

        _current_frame = frame.copy()

        # Si une analyse a été faite, superposer l'annotation pendant 3 secondes
        display = frame
        with _lock:
            if _last_annotated_frame is not None and _last_result is not None:
                # Afficher l'annotation
                display = _last_annotated_frame.copy()

        _, buf = cv2.imencode(".jpg", display, [cv2.IMWRITE_JPEG_QUALITY, 70])
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n"
        )
        time.sleep(0.033)  # ~30 fps


# ─────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────
def main():
    global camera, detector
    print("=" * 60)
    print("  Bottle Checker V2 — Interface Web")
    print("=" * 60)

    detector = BottleDetector()
    camera = Camera()

    print(f"\n→ Ouvrez http://localhost:{WEB_PORT} dans votre navigateur\n")
    app.run(host=WEB_HOST, port=WEB_PORT, debug=WEB_DEBUG, threaded=True)


if __name__ == "__main__":
    main()
