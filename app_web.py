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
import paho.mqtt.client as mqtt
from flask import Flask, Response, jsonify, render_template, send_from_directory

from camera import Camera
from config import (
    OUTPUT_DIR, WEB_HOST, WEB_PORT, WEB_DEBUG,
    MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE, MQTT_USERNAME, MQTT_PASSWORD,
    MQTT_TOPIC_TRIGGER, MQTT_TOPIC_RESULT,
)
from detector import BottleDetector

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
_mqtt_connected = False


# ─────────────────────────────────────────────────────────────
#  MQTT TRIGGER
# ─────────────────────────────────────────────────────────────
def _mqtt_on_connect(client, userdata, flags, rc, properties=None):
    global _mqtt_connected
    if rc == 0:
        _mqtt_connected = True
        client.subscribe(MQTT_TOPIC_TRIGGER)
        print(f"[MQTT] Connecté — écoute sur '{MQTT_TOPIC_TRIGGER}'")
    else:
        print(f"[MQTT] Échec connexion (rc={rc})")


def _mqtt_on_message(client, userdata, msg):
    """Déclenche une analyse dès réception d'un message trigger."""
    global _last_result, _last_annotated_frame, _analyzing
    raw = msg.payload.decode(errors='ignore')
    # Filtrer : ne déclencher que si objet_detecte est true
    try:
        data = json.loads(raw)
        if not data.get("objet_detecte", False):
            return
    except (json.JSONDecodeError, AttributeError):
        pass  # payload non-JSON → on laisse passer
    print(f"[MQTT] Trigger reçu : {raw}")

    if _analyzing or _current_frame is None:
        return

    _analyzing = True
    try:
        frame = _current_frame.copy()
        result, annotated = detector.analyze(frame)
        with _lock:
            _last_result = result
            _last_annotated_frame = annotated
        client.publish(MQTT_TOPIC_RESULT, json.dumps(result))
        print(f"[MQTT] Résultat publié → {result['status']}")
    except Exception as e:
        print(f"[MQTT] Erreur analyse : {e}")
    finally:
        _analyzing = False


def _start_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = _mqtt_on_connect
    client.on_message = _mqtt_on_message
    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
        client.loop_start()
        print(f"[MQTT] Connexion à {MQTT_BROKER}:{MQTT_PORT}…")
    except Exception as e:
        print(f"[MQTT] Impossible de se connecter : {e}")


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


@app.route("/mqtt_status")
def mqtt_status():
    """Statut de la connexion MQTT."""
    return jsonify({"connected": _mqtt_connected, "broker": MQTT_BROKER, "topic_trigger": MQTT_TOPIC_TRIGGER})


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

    _start_mqtt()

    print(f"\n→ Ouvrez http://localhost:{WEB_PORT} dans votre navigateur")
    print(f"→ MQTT trigger sur '{MQTT_TOPIC_TRIGGER}' ({MQTT_BROKER}:{MQTT_PORT})\n")
    app.run(host=WEB_HOST, port=WEB_PORT, debug=WEB_DEBUG, threaded=True)


if __name__ == "__main__":
    main()
