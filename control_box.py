import machine
from machine import Pin, PWM, UART, I2C
import time
import json
import _thread

# == Configuración de pines PWM ==

# CMYK PWM outputs
pwm_c = PWM(Pin(0))  # GP0
pwm_m = PWM(Pin(1))  # GP1
pwm_y = PWM(Pin(2))  # GP2
pwm_k = PWM(Pin(3))  # GP3

# RGB PWM outputs
pwm_r = PWM(Pin(4))  # GP4
pwm_g = PWM(Pin(5))  # GP5
pwm_b = PWM(Pin(6))  # GP6

# Salida PID
pid_pin = PWM(Pin(7))  # GP7

# LED indicador
led = Pin("LED", Pin.OUT)

# Configurar frecuencia para todos los PWM (1 kHz)
pwm_frequency = 1000
for pwm_pin in [pwm_c, pwm_m, pwm_y, pwm_k, pwm_r, pwm_g, pwm_b, pid_pin]:
    pwm_pin.freq(pwm_frequency)

# El PWM en MicroPython para Pico W trabaja con valores de 0 a 65535
PWM_MAX = 65535

# == Configuración del puerto serial ==

uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

# == Configuración del sensor de temperatura MLX90614 ==

# Pines I2C para el sensor MLX90614
i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=100000)

# Dirección I2C del MLX90614 (0x5A)
MLX90614_ADDR = 0x5A

# Registros del MLX90614
MLX90614_TA = 0x06   # Temperatura ambiente
MLX90614_TOBJ1 = 0x07  # Temperatura del objeto

# Semáforo para sincronizar acceso a las variables compartidas
pwm_lock = _thread.allocate_lock()
pid_running = True

# Variables globales para almacenar valores PWM
c_value, m_value, y_value, k_value = 0, 0, 0, 0
r_value, g_value, b_value = 0, 0, 0

class PID:
    def __init__(self, P, I, D):
        self.P = P
        self.I = I
        self.D = D
        self.prev_error = 0
        self.integral = 0

    def compute(self, setpoint, current_value):
        error = setpoint - current_value
        self.integral += error
        derivative = error - self.prev_error
        output = self.P * error + self.I * self.integral + self.D * derivative
        self.prev_error = error
        return output

# Inicialización del controlador PID para temperatura
pid_controller = PID(P=1.0, I=0.1, D=0.01)

def read_mlx90614(register):
    """
    Lee datos del sensor MLX90614
    """
    try:
        data = i2c.readfrom_mem(MLX90614_ADDR, register, 2)
        value = data[0] | (data[1] << 8)
        # Convertir a temperatura en Celsius (según datasheet)
        temp = (value * 0.02) - 273.15
        return temp
    except Exception as e:
        print("Error al leer el sensor:", e)
        return 0

def update_pwm():
    """
    Actualiza las salidas PWM con los valores CMYK y RGB.
    """
    pwm_c.duty_u16(int(c_value / 100 * PWM_MAX))
    pwm_m.duty_u16(int(m_value / 100 * PWM_MAX))
    pwm_y.duty_u16(int(y_value / 100 * PWM_MAX))
    pwm_k.duty_u16(int(k_value / 100 * PWM_MAX))
    pwm_r.duty_u16(int(r_value / 100 * PWM_MAX))
    pwm_g.duty_u16(int(g_value / 100 * PWM_MAX))
    pwm_b.duty_u16(int(b_value / 100 * PWM_MAX))

def read_serial_data():
    """
    Lee los datos CMYK y RGB desde el puerto serial y actualiza las salidas PWM.
    """
    global c_value, m_value, y_value, k_value, r_value, g_value, b_value
    if uart.any():
        data = uart.read()
        try:
            values = json.loads(data)
            c_value = values.get('C', 0)
            m_value = values.get('M', 0)
            y_value = values.get('Y', 0)
            k_value = values.get('K', 0)
            r_value = values.get('R', 0)
            g_value = values.get('G', 0)
            b_value = values.get('B', 0)

            # Actualizar los valores de PWM
            update_pwm()
        except json.JSONDecodeError:
            print("Error al procesar los datos recibidos.")

def update_pid():
    """
    Actualiza la salida del PWM para el control de temperatura usando PID.
    """
    global pid_pin
    target_temp = 13  # Temperatura deseada (por ejemplo, 13°C)
    current_temp = read_mlx90614(MLX90614_TA)
    pid_output = pid_controller.compute(target_temp, current_temp)

    # Ajustar el PWM según la salida PID
    pwm_value = max(0, min(PWM_MAX, int(pid_output)))
    pid_pin.duty_u16(pwm_value)

def blink_led():
    """
    Función para hacer parpadear el LED como indicativo de actividad.
    """
    led.toggle()
    time.sleep(0.5)

def main_loop():
    """
    Bucle principal para la actualización del sistema.
    """
    while True:
        # Leer datos seriales (CMYK y RGB)
        read_serial_data()

        # Actualizar control PID para temperatura
        update_pid()

        # Parpadear el LED indicador
        blink_led()

        # Esperar un poco antes de la siguiente actualización
        time.sleep(0.1)

# Iniciar el bucle principal
main_loop()
