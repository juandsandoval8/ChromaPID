import cv2
import threading
import time
import json
import paho.mqtt.client as mqtt

# Configuración MQTT
MQTT_BROKER = "192.168.1.x"   # <-- Cambia por la IP de tu broker
MQTT_PORT = 1883
MQTT_TOPIC = "color/detection"

class MqttManager:
    def __init__(self, broker, port):
        self.client = mqtt.Client()
        self.broker = broker
        self.port = port

    def connect(self):
        try:
            self.client.connect(self.broker, self.port)
            self.client.loop_start()
            print(f"[INFO] Conectado al broker MQTT {self.broker}:{self.port}")
            return True
        except Exception as e:
            print(f"[ERROR] Error conectando al broker MQTT: {e}")
            return False

    def send_data(self, data_dict):
        try:
            json_data = json.dumps(data_dict)
            self.client.publish(MQTT_TOPIC, json_data)
            print(f"[INFO] Datos publicados en MQTT: {json_data}")
            return True
        except Exception as e:
            print(f"[ERROR] Error enviando datos MQTT: {e}")
            return False

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        print("[INFO] Conexión MQTT cerrada.")

# El resto del código queda igual, solo cambia el gestor de comunicación
# ColorConverter, CameraManager se mantienen igual.

class ColorDetector:
    def __init__(self, mqtt_manager):
        self.mqtt_manager = mqtt_manager

    def detect_color(self, image, x, y):
        if image is None:
            print("[WARN] Imagen no disponible.")
            return
        if not (0 <= x < image.shape[1]) or not (0 <= y < image.shape[0]):
            print("[ERROR] Coordenadas fuera de rango.")
            return
        b, g, r = image[y, x]
        c, m, y_c, k = ColorConverter.rgb_to_cmyk(r, g, b)
        print(f"[INFO] Color detectado RGB({r},{g},{b}) → CMYK({c},{m},{y_c},{k})")
        self.send_color_data(c, m, y_c, k, r, g, b)

    def send_color_data(self, c, m, y, k, r, g, b):
        data = {'c': c, 'm': m, 'y': y, 'k': k, 'r': r, 'g': g, 'b': b}
        success = self.mqtt_manager.send_data(data)
        if success:
            print("[INFO] Datos de color enviados exitosamente por MQTT.")

# Uso práctico
if __name__ == "__main__":
    mqtt_mgr = MqttManager(MQTT_BROKER, MQTT_PORT)
    if mqtt_mgr.connect():
        camera_mgr = CameraManager()
        color_detector = ColorDetector(mqtt_mgr)

        if camera_mgr.start_camera():
            detection_thread = ColorDetectionThread(camera_mgr, color_detector, interval=2.0)
            detection_thread.start()

            try:
                print("[INFO] Sistema corriendo. Presiona Ctrl+C para terminar.")
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("[INFO] Terminando ejecución...")

            detection_thread.stop()
            camera_mgr.stop_camera()
        mqtt_mgr.disconnect()
