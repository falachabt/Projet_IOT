"""
Mode MQTT — attend un signal de déclenchement, analyse, renvoie le résultat.

Architecture :
  1. Se connecte au broker MQTT
  2. S'abonne au topic « trigger » (ex: iot/bottle/trigger)
  3. Quand un message arrive → capture + analyse
  4. Publie le résultat JSON sur le topic « result » (ex: iot/bottle/result)

Lancement :
    python -m v2.app_mqtt
    python -m v2.app_mqtt --broker 192.168.1.100 --port 1883
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
import threading
import time
from datetime import datetime

import paho.mqtt.client as mqtt

from v2.camera import Camera
from v2.config import (
    MQTT_BROKER,
    MQTT_KEEPALIVE,
    MQTT_PASSWORD,
    MQTT_PORT,
    MQTT_TOPIC_RESULT,
    MQTT_TOPIC_TRIGGER,
    MQTT_USERNAME,
)
from v2.detector import BottleDetector


def now_str() -> str:
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


class MqttBottleChecker:
    """Service MQTT : écoute un trigger, analyse, publie le résultat."""

    def __init__(
        self,
        broker: str = MQTT_BROKER,
        port: int = MQTT_PORT,
        topic_trigger: str = MQTT_TOPIC_TRIGGER,
        topic_result: str = MQTT_TOPIC_RESULT,
    ):
        self.broker = broker
        self.port = port
        self.topic_trigger = topic_trigger
        self.topic_result = topic_result

        self._analyzing = False
        self._running = True

        # Initialisation composants
        print(f"[{now_str()}] Chargement du détecteur…")
        self.detector = BottleDetector()

        print(f"[{now_str()}] Initialisation caméra…")
        self.camera = Camera()

        # Garder une frame live en arrière-plan
        self._current_frame = None
        self._frame_thread = threading.Thread(target=self._frame_loop, daemon=True)
        self._frame_thread.start()

        # Client MQTT
        self.client = mqtt.Client(
            protocol=mqtt.MQTTv5,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
        if MQTT_USERNAME:
            self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    # ── Boucle de capture continue ───────────────────────────
    def _frame_loop(self):
        """Capture des frames en continu pour être prêt dès le trigger."""
        while self._running:
            frame = self.camera.read()
            if frame is not None:
                self._current_frame = frame
            time.sleep(0.05)  # ~20 fps

    # ── Callbacks MQTT ───────────────────────────────────────
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print(f"[{now_str()}] ✓ Connecté au broker {self.broker}:{self.port}")
            client.subscribe(self.topic_trigger, qos=1)
            print(f"[{now_str()}] ✓ Abonné à : {self.topic_trigger}")
            print(f"[{now_str()}] ⏳ En attente de trigger…\n")
        else:
            print(f"[{now_str()}] ✗ Connexion échouée (code {rc})")

    def _on_message(self, client, userdata, msg):
        payload = msg.payload.decode("utf-8", errors="replace").strip()
        print(f"[{now_str()}] 📩 Reçu sur {msg.topic} → {payload!r}")

        if self._analyzing:
            print(f"[{now_str()}] ⚠ Analyse déjà en cours, message ignoré")
            return

        # Lancer l'analyse dans un thread pour ne pas bloquer la boucle MQTT
        threading.Thread(
            target=self._handle_trigger, args=(payload,), daemon=True
        ).start()

    def _handle_trigger(self, trigger_payload: str):
        self._analyzing = True
        try:
            frame = self._current_frame
            if frame is None:
                err = {"error": "Pas de frame disponible", "trigger": trigger_payload}
                self._publish(err)
                return

            print(f"[{now_str()}] 🔍 Analyse en cours…")
            result, _ = self.detector.analyze(frame.copy(), save=True)

            # Ajouter le payload de déclenchement
            result["trigger"] = trigger_payload

            self._publish(result)
            ok_str = "✓" if result["status"] == "OK" else "✗"
            print(f"[{now_str()}] {ok_str} Résultat : {result['status']}")

        except Exception as e:
            err = {"error": str(e), "trigger": trigger_payload}
            self._publish(err)
            print(f"[{now_str()}] ✗ Erreur analyse : {e}")
        finally:
            self._analyzing = False
            print(f"[{now_str()}] ⏳ En attente de trigger…\n")

    def _publish(self, data: dict):
        payload = json.dumps(data, ensure_ascii=False)
        self.client.publish(self.topic_result, payload=payload, qos=1, retain=False)
        print(f"[{now_str()}] 📤 Publié sur {self.topic_result}")

    # ── Lancement ────────────────────────────────────────────
    def run(self):
        """Connecte et lance la boucle MQTT (bloquant)."""
        print(f"\n{'='*60}")
        print("  Bottle Checker V2 — Mode MQTT")
        print(f"{'='*60}")
        print(f"  Broker   : {self.broker}:{self.port}")
        print(f"  Trigger  : {self.topic_trigger}")
        print(f"  Résultat : {self.topic_result}")
        print(f"{'='*60}\n")

        try:
            self.client.connect(self.broker, self.port, MQTT_KEEPALIVE)
        except Exception as e:
            print(f"[{now_str()}] ✗ Impossible de se connecter : {e}")
            sys.exit(1)

        # Ctrl+C propre
        def _sigint(sig, frame):
            print(f"\n[{now_str()}] Arrêt demandé (Ctrl+C)")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, _sigint)

        self.client.loop_forever()

    def stop(self):
        self._running = False
        self.client.loop_stop()
        self.client.disconnect()
        self.camera.release()
        print(f"[{now_str()}] Ressources libérées, au revoir.")


# ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Bottle Checker V2 — Mode MQTT")
    parser.add_argument("--broker", default=MQTT_BROKER, help="Adresse du broker MQTT")
    parser.add_argument("--port", type=int, default=MQTT_PORT, help="Port MQTT")
    parser.add_argument("--topic-trigger", default=MQTT_TOPIC_TRIGGER, help="Topic de déclenchement")
    parser.add_argument("--topic-result", default=MQTT_TOPIC_RESULT, help="Topic de résultat")
    args = parser.parse_args()

    checker = MqttBottleChecker(
        broker=args.broker,
        port=args.port,
        topic_trigger=args.topic_trigger,
        topic_result=args.topic_result,
    )
    checker.run()


if __name__ == "__main__":
    main()
