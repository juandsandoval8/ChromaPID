import time
import board
import busio
import adafruit_tcs34725
import paho.mqtt.client as mqtt
import json

# === Configura MQTT ===
MQTT_BROKER = "192.168.x"  # Cambia si usas otro servidor MQTT
MQTT_PORT = 1883
MQTT_TOPIC_PUB = "sensor/color/rgb"
MQTT_TOPIC_SUB = "sensor/color/echo"

# === Configura el sensor TCS34725 ===
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_tcs34725.TCS34725(i2c)
sensor.integration_time = 100
sensor.gain = 4

# === Configura MQTT ===
def on_connect(client, userdata, flags, rc):
    print("Conectado al broker MQTT con código:", rc)
    client.subscribe(MQTT_TOPIC_SUB)

def on_message(client, userdata, msg):
    print(f"[MQTT recibido] {msg.topic}: {msg.payload.decode()}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

# === Bucle principal ===
try:
    while True:
        r, g, b, _ = sensor.color_raw
        rgb = {"r": r, "g": g, "b": b}
        json_data = json.dumps(rgb)
        
        print(f"[Sensor RGB] {rgb}")
        client.publish(MQTT_TOPIC_PUB, json_data)

        time.sleep(2)

except KeyboardInterrupt:
    print("Terminando programa.")
    client.loop_stop()
    client.disconnect()
