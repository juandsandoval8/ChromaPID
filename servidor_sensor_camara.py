import time
import json
import board
import busio
import adafruit_tcs34725
import paho.mqtt.client as mqtt
import cv2
import numpy as np

# =================== FUNCIONES DE CONVERSIÓN ===================
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

# =================== CONFIGURACIÓN MQTT ===================
MQTT_BROKER = "192.168.1.x"  # Cambia por tu IP
MQTT_PORT = 1883
MQTT_TOPIC_COMANDO = "modo/seleccion"
MQTT_TOPIC_COORDENADAS = "color/coordenadas"
MQTT_TOPIC_DETALLES = "color/detection"

# =================== INICIALIZAR MQTT ===================
client = mqtt.Client()
try:
    client.connect(MQTT_BROKER, MQTT_PORT)
    print(f"[INFO] Conectado al broker MQTT {MQTT_BROKER}")
except Exception as e:
    print(f"[ERROR] No se pudo conectar al broker MQTT: {e}")
    exit(1)

# =================== VARIABLE GLOBAL PARA CLICK ===================
current_mode = "sensor"  # Valores posibles: camara, imagen, sensor
last_image_path = None

# =================== MANEJO DE MENSAJES MQTT ===================
def on_message(client, userdata, msg):
    global current_mode, last_image_path
    try:
        if msg.topic == MQTT_TOPIC_COMANDO:
            data = json.loads(msg.payload.decode())
            new_mode = data.get("modo")
            if new_mode in ["camara", "imagen", "sensor"]:
                current_mode = new_mode
                print(f"[INFO] Modo cambiado a: {current_mode}")
                last_image_path = None  # Limpiar imagen previa si hay

        elif msg.topic == MQTT_TOPIC_COORDENADAS and current_mode in ["camara", "imagen"]:
            data = json.loads(msg.payload.decode())
            x = data.get("x")
            y = data.get("y")
            if x is not None and y is not None:
                print(f"[INFO] Coordenadas recibidas: ({x}, {y})")
                if current_mode == "camara":
                    r, g, b = detect_from_camera(x, y)
                elif current_mode == "imagen" and last_image_path:
                    r, g, b = detect_from_image(last_image_path, x, y)
                else:
                    return
                if r is not None:
                    send_color_data(r, g, b)

    except Exception as e:
        print(f"[ERROR] Error procesando mensaje MQTT: {e}")

client.on_message = on_message
client.subscribe(MQTT_TOPIC_COMANDO)
client.subscribe(MQTT_TOPIC_COORDENADAS)
client.loop_start()

# =================== SENSOR RGB ===================
def leer_sensor_rgb():
    i2c = busio.I2C(board.SCL, board.SDA)
    sensor = adafruit_tcs34725.TCS34725(i2c)
    sensor.integration_time = 100
    sensor.gain = 4
    r, g, b, _ = sensor.color_raw
    print(f"[Sensor RGB] Leído: R={r}, G={g}, B={b}")
    return r, g, b

# =================== DETECCIÓN DESDE CÁMARA ===================
def detect_from_camera(x=320, y=240):
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("[ERROR] No se pudo capturar desde la cámara.")
        return None, None, None
    b, g, r = frame[y, x]
    print(f"[Cámara] Color detectado: R={r}, G={g}, B={b}")
    return int(r), int(g), int(b)

# =================== DETECCIÓN DESDE IMAGEN LOCAL ===================
def detect_from_image(path, x=320, y=240):
    img = cv2.imread(path)
    if img is None:
        print("[ERROR] No se pudo cargar la imagen.")
        return None, None, None
    if y >= img.shape[0] or x >= img.shape[1]:
        print("[ERROR] Coordenadas fuera de rango.")
        return None, None, None
    b, g, r = img[y, x]
    print(f"[Imagen] Color detectado: R={r}, G={g}, B={b}")
    return int(r), int(g), int(b)

# =================== ENVIAR DATOS POR MQTT ===================
def send_color_data(r, g, b):
    c, m, y_c, k = rgb_to_cmyk(r, g, b)
    data = {
        "r": r,
        "g": g,
        "b": b,
        "c": c,
        "m": m,
        "y": y_c,
        "k": k
    }
    client.publish(MQTT_TOPIC_DETALLES, json.dumps(data))
    print(f"[INFO] Datos enviados por MQTT: {data}")

# =================== FUNCIÓN PRINCIPAL ===================
print("[INFO] Esperando comandos desde Node-RED...")

while True:
    if current_mode == "sensor":
        r, g, b = leer_sensor_rgb()
        send_color_data(r, g, b)

    elif current_mode == "camara":
        pass  # Se espera clic desde Node-RED

    elif current_mode == "imagen":
        pass  # Se espera carga de imagen y clic desde Node-RED

    time.sleep(0.5)
