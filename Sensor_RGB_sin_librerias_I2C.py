import smbus
import time
import paho.mqtt.client as mqtt

# Dirección I2C del sensor TCS34725
TCS34725_ADDRESS = 0x29

# Registros del sensor
TCS34725_COMMAND_BIT = 0x80
TCS34725_ENABLE = 0x00
TCS34725_ENABLE_PON = 0x01
TCS34725_ENABLE_AEN = 0x02
TCS34725_ID = 0x12
TCS34725_CDATAL = 0x14
TCS34725_RDATAL = 0x16
TCS34725_GDATAL = 0x18
TCS34725_BDATAL = 0x1A
TCS34725_ATIME = 0x01

# Configuración del MQTT
MQTT_BROKER = "192.168.17"  # Cambia esto a la dirección IP de tu broker MQTT si es diferente
MQTT_PORT = 1883
MQTT_TOPIC_PUBLISH = "sensor/color"
MQTT_TOPIC_SUBSCRIBE = "control/color_request"

# Inicializar el bus I2C
bus = smbus.SMBus(1)  # 1 para la mayoría de las Raspberry Pi, 0 para modelos antiguos

def read_raw_data():
    """Lee los datos crudos de los canales Clear, Red, Green y Blue."""
    data = bus.read_i2c_block_data(TCS34725_ADDRESS, TCS34725_CDATAL | TCS34725_COMMAND_BIT, 8)
    clear = data[1] << 8 | data[0]
    red = data[3] << 8 | data[2]
    green = data[5] << 8 | data[4]
    blue = data[7] << 8 | data[6]
    return clear, red, green, blue

def initialize_sensor():
    """Inicializa el sensor TCS34725."""
    # Verificar el ID del sensor
    chip_id = bus.read_byte_data(TCS34725_ADDRESS, TCS34725_ID | TCS34725_COMMAND_BIT)
    if chip_id != 0x44:
        print("Error: Sensor TCS34725 no encontrado.")
        exit()

    # Habilitar el sensor (PON y AEN)
    bus.write_byte_data(TCS34725_ADDRESS, TCS34725_ENABLE | TCS34725_COMMAND_BIT, TCS34725_ENABLE_PON | TCS34725_ENABLE_AEN)

    # Configurar el tiempo de integración (ATIME), un valor más bajo significa una lectura más rápida
    bus.write_byte_data(TCS34725_ADDRESS, TCS34725_ATIME | TCS34725_COMMAND_BIT, 0xD5) # Ejemplo: 150 ms

def on_connect(client, userdata, flags, rc):
    """Función callback que se ejecuta cuando el cliente MQTT se conecta al broker."""
    if rc == 0:
        print("Conectado al broker MQTT")
        client.subscribe(MQTT_TOPIC_SUBSCRIBE)
    else:
        print(f"Error al conectar al broker MQTT, código: {rc}")

def on_message(client, userdata, msg):
    """Función callback que se ejecuta cuando se recibe un mensaje MQTT."""
    if msg.topic == MQTT_TOPIC_SUBSCRIBE:
        if msg.payload.decode() == "read_color":
            clear, red, green, blue = read_raw_data()
            print(f"Color RAW: C={clear}, R={red}, G={green}, B={blue}")
            # Puedes realizar aquí alguna normalización o cálculo adicional si es necesario
            color_data = {"r": red, "g": green, "b": blue}
            client.publish(MQTT_TOPIC_PUBLISH, str(color_data))
            print(f"Publicado en {MQTT_TOPIC_PUBLISH}: {color_data}")

if __name__ == "__main__":
    initialize_sensor()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("Desconectando...")
        client.disconnect()
