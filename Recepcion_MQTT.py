import network
import time
import json
import _thread
from machine import Pin, PWM
from umqtt.simple import MQTTClient
from onewire import OneWire
from ds18x20 import DS18X20

# == Configuración WiFi ==
WIFI_SSID = "tu_ssid"
WIFI_PASSWORD = "tu_password"

# == Configuración MQTT ==
MQTT_BROKER = "192.168.1.17"  # IP del broker MQTT
MQTT_TOPIC = "color/detection"
CLIENT_ID = "PicoW_ColorReceiver"

# == Configuración PWM ==
PWM_FREQUENCY = 1000
PWM_MAX = 65535

# == Pines PWM para CMYK, RGB y Temperatura ==
pwm_c = PWM(Pin(0))
pwm_m = PWM(Pin(1))
pwm_y = PWM(Pin(2))
pwm_k = PWM(Pin(3))
pwm_r = PWM(Pin(4))
pwm_g = PWM(Pin(5))
pwm_b = PWM(Pin(6))
pwm_heat_c = PWM(Pin(20))
pwm_heat_m = PWM(Pin(21))
pwm_heat_y = PWM(Pin(22))
pwm_heat_k = PWM(Pin(26))

# == Configuración de frecuencia para todos los PWM ==
for pwm in [pwm_c, pwm_m, pwm_y, pwm_k, pwm_r, pwm_g, pwm_b, pwm_heat_c, pwm_heat_m, pwm_heat_y, pwm_heat_k]:
    pwm.freq(PWM_FREQUENCY)

# == Variables de color y temperatura ==
c_value, m_value, y_value, k_value = 0, 0, 0, 0
r_value, g_value, b_value = 0, 0, 0
heat_c_value, heat_m_value, heat_y_value, heat_k_value = 0, 0, 0, 0

# == LED indicador ==
led = Pin("LED", Pin.OUT)

# == Sensores de Temperatura DS18B20 (Asumiendo 4 sensores en 4 GPIOs) ==
ds_c = DS18X20(OneWire(Pin(10)))
ds_m = DS18X20(OneWire(Pin(11)))
ds_y = DS18X20(OneWire(Pin(12)))
ds_k = DS18X20(OneWire(Pin(13)))

roms_c = ds_c.scan()
roms_m = ds_m.scan()
roms_y = ds_y.scan()
roms_k = ds_k.scan()

# == Setpoints de Temperatura ==
TEMP_CYAN_SETPOINT = 40.0  # ºC
TEMP_MAGENTA_SETPOINT = 40.0
TEMP_YELLOW_SETPOINT = 40.0
TEMP_BLACK_SETPOINT = 40.0

# == PID básico (Proporcional simple para ejemplo) ==
def pid_control(error):
    kp = 50  # Ganancia proporcional (ajustar)
    output = min(max(kp * error, 0), 100)
    return output

# == Funciones de apoyo ==
def connect_wifi():
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
    pwm_heat_c.duty_u16(int(heat_c_value / 100 * PWM_MAX))
    pwm_heat_m.duty_u16(int(heat_m_value / 100 * PWM_MAX))
    pwm_heat_y.duty_u16(int(heat_y_value / 100 * PWM_MAX))
    pwm_heat_k.duty_u16(int(heat_k_value / 100 * PWM_MAX))

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

# == Controladores PID para cada tanque ==
def control_temp(ds_sensor, roms, setpoint, heat_var_name):
    global heat_c_value, heat_m_value, heat_y_value, heat_k_value
    while True:
        ds_sensor.convert_temp()
        time.sleep_ms(750)
        temp = ds_sensor.read_temp(roms[0])
        error = setpoint - temp
        pwm_output = pid_control(error)
        if heat_var_name == 'c':
            heat_c_value = pwm_output
        elif heat_var_name == 'm':
            heat_m_value = pwm_output
        elif heat_var_name == 'y':
            heat_y_value = pwm_output
        elif heat_var_name == 'k':
            heat_k_value = pwm_output
        update_pwm()
        time.sleep(1)

# == Función Principal ==
def main():
    connect_wifi()
    client = MQTTClient(CLIENT_ID, MQTT_BROKER)
    client.set_callback(sub_cb)
    client.connect()
    client.subscribe(MQTT_TOPIC)
    print(f"[INFO] Suscrito a {MQTT_TOPIC}")

    # Lanzar controladores de temperatura en hilos separados
    _thread.start_new_thread(control_temp, (ds_c, roms_c, TEMP_CYAN_SETPOINT, 'c'))
    _thread.start_new_thread(control_temp, (ds_m, roms_m, TEMP_MAGENTA_SETPOINT, 'm'))
    _thread.start_new_thread(control_temp, (ds_y, roms_y, TEMP_YELLOW_SETPOINT, 'y'))
    _thread.start_new_thread(control_temp, (ds_k, roms_k, TEMP_BLACK_SETPOINT, 'k'))

    # Bucle principal de MQTT
    while True:
        client.check_msg()
        led.toggle()
        time.sleep(0.5)

# == Ejecución ==
main()
