"""
Point d'entrée principal — choix du mode de lancement.

Usage :
    python -m . web       → Interface web (Flask)
    python -m . tkinter   → Interface Tkinter
    python -m . mqtt      → Mode MQTT (headless)
    python -m . analyze   → Analyse unique (capture + JSON)
"""

import sys


def main():
    modes = {
        "web": "app_web",
        "tkinter": "app_tkinter",
        "mqtt": "app_mqtt",
    }

    if len(sys.argv) < 2 or sys.argv[1] not in modes and sys.argv[1] != "analyze":
        print(
            "\n"
            "╔══════════════════════════════════════════════════════╗\n"
            "║        Bottle Checker V2 — Contrôle Qualité         ║\n"
            "╠══════════════════════════════════════════════════════╣\n"
            "║                                                      ║\n"
            "║  Usage :                                             ║\n"
            "║    python __main__.py web       Web (Flask)          ║\n"
            "║    python __main__.py tkinter   Tkinter              ║\n"
            "║    python __main__.py mqtt      MQTT (headless)      ║\n"
            "║    python __main__.py analyze   Analyse → JSON       ║\n"
            "║                                                      ║\n"
            "╚══════════════════════════════════════════════════════╝\n"
        )
        sys.exit(0)

    mode = sys.argv[1]

    if mode == "analyze":
        # Mode one-shot : capture une frame, analyse, affiche le JSON
        from camera import Camera
        from detector import BottleDetector

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
