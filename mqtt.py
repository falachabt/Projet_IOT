# mqtt_ecoute_esp8266.py
import paho.mqtt.client as mqtt
from datetime import datetime
import time

# Configuration
BROKER = "10.66.108.235"
PORT   = 1883
TOPIC  = "esp8266/ultrason/distance"

# Si authentification nécessaire → décommenter et remplir
# USERNAME = "ton_user"
# PASSWORD = "ton_pass"
USERNAME = None
PASSWORD = None

def now():
    """Heure formatée avec millisecondes"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"[{now()}] Connecté au broker {BROKER}:{PORT}")
        client.subscribe(TOPIC)
        print(f"[{now()}] Abonné au topic : {TOPIC}")
    else:
        print(f"[{now()}] Échec connexion - code retour = {rc}")


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode('utf-8').strip()
        
        if payload.upper() in ("OK", "OUI", "GOOD"):
            print(f"[{now()}] {msg.topic:38} → Capteur OK")
        elif payload.upper() in ("KO", "NOK", "ERROR", "FAIL"):
            print(f"[{now()}] {msg.topic:38} → Capteur KO !")
        else:
            # Pour tout autre message inattendu
            print(f"[{now()}] {msg.topic:38} → {payload!r}")
            
    except UnicodeDecodeError:
        print(f"[{now()}] {msg.topic:38} → [données binaires - {len(msg.payload)} octets]")
    except Exception as e:
        print(f"[{now()}] Erreur traitement message : {e}")


# Création du client MQTT
client = mqtt.Client(protocol=mqtt.MQTTv5, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

if USERNAME is not None:
    client.username_pw_set(USERNAME, PASSWORD)

client.on_connect = on_connect
client.on_message = on_message

print(f"Début connexion vers {BROKER}:{PORT} ...")

try:
    client.connect(BROKER, PORT, keepalive=60)
except Exception as e:
    print(f"Erreur connexion : {e}")
    exit(1)

# Lancement de la boucle en arrière-plan
client.loop_start()

try:
    print("Écoute en cours...  (Ctrl+C pour arrêter)")
    while True:
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\nArrêt demandé (Ctrl+C)")
finally:
    client.loop_stop()
    client.disconnect()
    print("Déconnexion terminée.")