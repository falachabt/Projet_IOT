"""
Point d'entrée principal — choix du mode de lancement.

Usage :
    python -m v2 web       → Interface web (Flask)
    python -m v2 tkinter   → Interface Tkinter
    python -m v2 mqtt      → Mode MQTT (headless)
    python -m v2 analyze   → Analyse unique (capture + JSON)
"""

import sys


def main():
    modes = {
        "web": "v2.app_web",
        "tkinter": "v2.app_tkinter",
        "mqtt": "v2.app_mqtt",
    }

    if len(sys.argv) < 2 or sys.argv[1] not in modes and sys.argv[1] != "analyze":
        print(
            "\n"
            "╔══════════════════════════════════════════════════════╗\n"
            "║        Bottle Checker V2 — Contrôle Qualité         ║\n"
            "╠══════════════════════════════════════════════════════╣\n"
            "║                                                      ║\n"
            "║  Usage :                                             ║\n"
            "║    python -m v2 web       Interface Web (Flask)      ║\n"
            "║    python -m v2 tkinter   Interface Tkinter          ║\n"
            "║    python -m v2 mqtt      Mode MQTT (headless)       ║\n"
            "║    python -m v2 analyze   Analyse unique → JSON      ║\n"
            "║                                                      ║\n"
            "╚══════════════════════════════════════════════════════╝\n"
        )
        sys.exit(0)

    mode = sys.argv[1]

    if mode == "analyze":
        # Mode one-shot : capture une frame, analyse, affiche le JSON
        from v2.camera import Camera
        from v2.detector import BottleDetector

        detector = BottleDetector()
        cam = Camera()
        import time
        time.sleep(0.5)  # laisser la caméra se stabiliser
        frame = cam.read()
        if frame is None:
            print('{"error": "Impossible de capturer une image"}')
            sys.exit(1)
        json_str = detector.analyze_to_json(frame, include_image_base64=False)
        print(json_str)
        cam.release()
    else:
        # Retirer le mode des argv avant de déléguer
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        mod = __import__(modes[mode], fromlist=["main"])
        mod.main()


if __name__ == "__main__":
    main()
