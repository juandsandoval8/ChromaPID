import network
import time
import json
import _thread
from machine import Pin, PWM
from umqtt.simple import MQTTClient
from onewire import OneWire
from ds18x20 import DS18X20

# == Configuración WiFi y MQTT ==
WIFI_SSID = "TU_RED_WIFI"
WIFI_PASSWORD = "TU_CONTRASENA"
MQTT_BROKER = "192.168.1.x"  # IP del broker MQTT
MQTT_TOPIC = "color/detection"
CLIENT_ID = "PicoW_ColorReceiver"

# == Configuración PWM para CMYK y RGB ==
PWM_FREQUENCY = 1000
PWM_MAX = 65535

# == Pines PWM para CMYK y RGB ==
pwm_c = PWM(Pin(0))
pwm_m = PWM(Pin(1))
pwm_y = PWM(Pin(2))
pwm_k = PWM(Pin(3))
pwm_r = PWM(Pin(4))
pwm_g = PWM(Pin(5))
pwm_b = PWM(Pin(6))

for pwm in [pwm_c, pwm_m, pwm_y, pwm_k, pwm_r, pwm_g, pwm_b]:
    pwm.freq(PWM_FREQUENCY)

# == Variables de color ==
c_value, m_value, y_value, k_value = 0, 0, 0, 0
r_value, g_value, b_value = 0, 0, 0

# == LED indicador ==
led = Pin("LED", Pin.OUT)

# == Sensores de Temperatura DS18B20 ==
ds_c = DS18X20(OneWire(Pin(10)))
ds_m = DS18X20(OneWire(Pin(11)))
ds_y = DS18X20(OneWire(Pin(12)))
ds_k = DS18X20(OneWire(Pin(13)))

roms_c = ds_c.scan()
roms_m = ds_m.scan()
roms_y = ds_y.scan()
roms_k = ds_k.scan()

# == Setpoints de Temperatura ==
TEMP_CYAN_SETPOINT = 40.0   # ºC
TEMP_MAGENTA_SETPOINT = 40.0
TEMP_YELLOW_SETPOINT = 40.0
TEMP_BLACK_SETPOINT = 40.0

# == Pines de calentamiento como salidas digitales ==
heat_c_pin = Pin(20, Pin.OUT)
heat_m_pin = Pin(21, Pin.OUT)
heat_y_pin = Pin(22, Pin.OUT)
heat_k_pin = Pin(26, Pin.OUT)

# Apagamos todo al inicio
heat_c_pin.value(0)
heat_m_pin.value(0)
heat_y_pin.value(0)
heat_k_pin.value(0)

# == Ciclo base para control ON/OFF (segundos) ==
CYCLE_TIME = 10  # Cada 10 segundos revisa y ajusta

# == Parámetros PID ==
Kp = 50
Ki = 0.5
Kd = 1

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

# == Control PID con salida ON/OFF (Modulación por Tiempo) ==
def control_temp(ds_sensor, roms, setpoint, heater_pin):
    last_time = time.time()
    integral = 0
    last_error = 0

    while True:
        ds_sensor.convert_temp()
        time.sleep_ms(750)
        temp = ds_sensor.read_temp(roms[0])
        
        # Cálculo del error
        error = setpoint - temp
        current_time = time.time()
        dt = current_time - last_time

        # Cálculo PID
        integral += error * dt
        derivative = (error - last_error) / dt if dt > 0 else 0
        pid_output = Kp * error + Ki * integral + Kd * derivative
        pid_output = max(0, min(100, pid_output))  # Limitar entre 0% y 100%

        # Calcular tiempos ON/OFF
        on_time = CYCLE_TIME * (pid_output / 100)
        off_time = CYCLE_TIME - on_time

        # Encender resistencia
        heater_pin.on()
        time.sleep(on_time)

        # Apagar resistencia
        heater_pin.off()
        time.sleep(off_time)

        # Actualizar variables para próxima iteración
        last_time = current_time
        last_error = error

# == Función Principal ==
def main():
    connect_wifi()
    client = MQTTClient(CLIENT_ID, MQTT_BROKER)
    client.set_callback(sub_cb)
    client.connect()
    client.subscribe(MQTT_TOPIC)
    print(f"[INFO] Suscrito a {MQTT_TOPIC}")

    # Lanzar controladores de temperatura en hilos separados
    _thread.start_new_thread(control_temp, (ds_c, roms_c, TEMP_CYAN_SETPOINT, heat_c_pin))
    _thread.start_new_thread(control_temp, (ds_m, roms_m, TEMP_MAGENTA_SETPOINT, heat_m_pin))
    _thread.start_new_thread(control_temp, (ds_y, roms_y, TEMP_YELLOW_SETPOINT, heat_y_pin))
    _thread.start_new_thread(control_temp, (ds_k, roms_k, TEMP_BLACK_SETPOINT, heat_k_pin))

    # Bucle principal de MQTT
    while True:
        client.check_msg()
        led.toggle()
        time.sleep(0.5)

# == Iniciar ejecución ==
main()
