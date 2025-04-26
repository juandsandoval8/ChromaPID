import network
import time
import json
import _thread
from machine import Pin, PWM
from umqtt.simple import MQTTClient
from onewire import OneWire
from ds18x20 import DS18X20

# == Conexión WiFi ==
WIFI_SSID = "tu_ssid"
WIFI_PASSWORD = "tu_password"

# == Configuración MQTT ==
MQTT_BROKER = "192.168.1.x"  # IP del broker MQTT
MQTT_TOPIC = "color/detection"
CLIENT_ID = "PicoW_ColorReceiver"

# PWM Configuration igual que antes...
# pwm_c, pwm_m, pwm_y, pwm_k, pwm_r, pwm_g, pwm_b, pid_pin
# pwm_frequency = 1000, PWM_MAX = 65535

# LED indicador
led = Pin("LED", Pin.OUT)

# Variables PWM
c_value, m_value, y_value, k_value = 0, 0, 0, 0
r_value, g_value, b_value = 0, 0, 0

def connect_wifi():
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("[INFO] Conectando a WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        while not wlan.isconnected():
            time.sleep(0.5)
    print("[INFO] Conexión WiFi establecida:", wlan.ifconfig())

def update_pwm():
    pwm_c.duty_u16(int(c_value / 100 * PWM_MAX))
    pwm_m.duty_u16(int(m_value / 100 * PWM_MAX))
    pwm_y.duty_u16(int(y_value / 100 * PWM_MAX))
    pwm_k.duty_u16(int(k_value / 100 * PWM_MAX))
    pwm_r.duty_u16(int(r_value / 255 * PWM_MAX))
    pwm_g.duty_u16(int(g_value / 255 * PWM_MAX))
    pwm_b.duty_u16(int(b_value / 255 * PWM_MAX))

def sub_cb(topic, msg):
    global c_value, m_value, y_value, k_value, r_value, g_value, b_value
    print(f"[INFO] Mensaje recibido en {topic}: {msg}")
    try:
        values = json.loads(msg)
        c_value = values.get('c', 0)
        m_value = values.get('m', 0)
        y_value = values.get('y', 0)
        k_value = values.get('k', 0)
        r_value = values.get('r', 0)
        g_value = values.get('g', 0)
        b_value = values.get('b', 0)
        update_pwm()
    except Exception as e:
        print(f"[ERROR] Fallo en el parseo del mensaje MQTT: {e}")

def main():
    connect_wifi()
    client = MQTTClient(CLIENT_ID, MQTT_BROKER)
    client.set_callback(sub_cb)
    client.connect()
    client.subscribe(MQTT_TOPIC)
    print(f"[INFO] Suscrito a {MQTT_TOPIC}")

    while True:
        client.check_msg()
        led.toggle()
        time.sleep(0.5)

# Ejecutar el programa
main()
