import cv2
import json
import paho.mqtt.client as mqtt
import time

MQTT_BROKER = "192.168.1.x"
MQTT_PORT = 1883
MQTT_TOPIC_DETECCION = "color/detection"
MQTT_TOPIC_COMANDO = "comando/color"

cap = None

def rgb_to_cmyk(r, g, b):
    if r == g == b == 0:
        return 0, 0, 0, 100
    c = 1 - r / 255
    m = 1 - g / 255
    y = 1 - b / 255
    k = min(c, m, y)
    c = round((c - k) / (1 - k) * 100)
    m = round((m - k) / (1 - k) * 100)
    y = round((y - k) / (1 - k) * 100)
    k = round(k * 100)
    return c, m, y, k

def on_message(client, userdata, msg):
    if msg.topic == MQTT_TOPIC_COMANDO:
        try:
            data = json.loads(msg.payload.decode())
            if data.get("accion") == "tomar_foto":
                tomar_foto()
            elif data.get("accion") == "detectar_color" and "x" in data and "y" in data:
                detectar_color(data["x"], data["y"])
        except Exception as e:
            print(f"[ERROR] Error procesando comando: {e}")

def tomar_foto():
    global cap
    if not cap or not cap.isOpened():
        cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite("/tmp/captura.jpg", frame)
        print("[INFO] Foto guardada temporalmente.")

def detectar_color(x, y):
    global cap
    if not cap or not cap.isOpened():
        cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] No se pudo capturar el fotograma.")
        return

    if 0 <= x < frame.shape[1] and 0 <= y < frame.shape[0]:
        b, g, r = frame[y, x]
        r, g, b = int(r), int(g), int(b)
        c, m, y_c, k = rgb_to_cmyk(r, g, b)
        client.publish(MQTT_TOPIC_DETECCION, json.dumps({
            "r": r, "g": g, "b": b,
            "c": c, "m": m, "y": y_c, "k": k
        }))
        print(f"[INFO] Color detectado: RGB({r},{g},{b}) CMYK({c},{m},{y_c},{k})")

# === Configuración MQTT ===
client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT)
client.subscribe(MQTT_TOPIC_COMANDO)
client.loop_start()

print("[INFO] Esperando comandos por MQTT...")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("[INFO] Apagando detector de color.")
    if cap and cap.isOpened():
        cap.release()
    client.loop_stop()
