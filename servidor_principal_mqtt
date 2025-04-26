import cv2
import threading
import time
import paho.mqtt.client as mqtt
import json

class MQTTManager:
    def __init__(self, broker="localhost", port=1883, topic="color_data"):
        self.client = mqtt.Client()
        self.broker = broker
        self.port = port
        self.topic = topic
        self.connected = False

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print("[INFO] Conectado al broker MQTT")
        else:
            print(f"[ERROR] Error al conectar al broker MQTT: {rc}")

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        print("[INFO] Desconectado del broker MQTT")

    def connect(self):
        try:
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            time.sleep(2)  # Estabilizar la conexión
            return True
        except Exception as e:
            print(f"[ERROR] Error al conectar: {e}")
            return False

    def send_data(self, data_dict):
        if not self.connected:
            print("[WARN] No hay conexión MQTT.")
            return False
        try:
            json_data = json.dumps(data_dict)
            self.client.publish(self.topic, json_data)
            print(f"[INFO] Datos enviados al broker MQTT: {json_data}")
            return True
        except Exception as e:
            print(f"[ERROR] Error enviando datos por MQTT: {e}")
            return False

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        print("[INFO] Conexión MQTT cerrada.")

class ColorConverter:
    @staticmethod
    def rgb_to_cmyk(r, g, b):
        r_norm, g_norm, b_norm = r/255.0, g/255.0, b/255.0
        k = 1 - max(r_norm, g_norm, b_norm)
        if k == 1:
            return 0, 0, 0, 100
        c = (1 - r_norm - k) / (1 - k)
        m = (1 - g_norm - k) / (1 - k)
        y = (1 - b_norm - k) / (1 - k)
        return int(c*100), int(m*100), int(y*100), int(k*100)

    @staticmethod
    def cmyk_to_rgb(c, m, y, k):
        c, m, y, k = [max(0, min(100, val)) for val in (c, m, y, k)]
        r = 255 * (1 - c/100) * (1 - k/100)
        g = 255 * (1 - m/100) * (1 - k/100)
        b = 255 * (1 - y/100) * (1 - k/100)
        return int(r), int(g), int(b)

class CameraManager:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None
        self.active = False
        self.frame = None
        self.lock = threading.Lock()

    def start_camera(self):
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            print("[ERROR] No se pudo iniciar la cámara.")
            return False
        self.active = True
        threading.Thread(target=self._capture_loop, daemon=True).start()
        print("[INFO] Cámara iniciada.")
        return True

    def _capture_loop(self):
        while self.active:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame.copy()
            time.sleep(0.03)

    def get_frame(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def stop_camera(self):
        self.active = False
        if self.cap:
            self.cap.release()
        print("[INFO] Cámara detenida.")

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
            print("[INFO] Datos de color enviados exitosamente.")

class ColorDetectionThread(threading.Thread):
    def __init__(self, camera_manager, color_detector, x=None, y=None, interval=1.0):
        super().__init__(daemon=True)
        self.camera_manager = camera_manager
        self.color_detector = color_detector
        self.interval = interval
        self.running = False
        self.x = x
        self.y = y

    def run(self):
        self.running = True
        while self.running:
            frame = self.camera_manager.get_frame()
            if frame is not None:
                height, width = frame.shape[:2]
                x = self.x if self.x is not None else width // 2
                y = self.y if self.y is not None else height // 2
                self.color_detector.detect_color(frame, x, y)
            time.sleep(self.interval)

    def stop(self):
        self.running = False

# Uso práctico
if __name__ == "__main__":
    mqtt_mgr = MQTTManager(broker="localhost", port=1883, topic="color_data")
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
