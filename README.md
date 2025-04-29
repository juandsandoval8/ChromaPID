# Proyecto Sistema de Control de Colores y Temperatura con Raspberry Pi

## Descripción

Este proyecto tiene como objetivo desarrollar un sistema de control automatizado de colores y temperatura utilizando tecnologías como Raspberry Pi, MQTT, control PWM, y sensores de temperatura. El sistema es capaz de gestionar un proceso de mezcla de tintas CMYK (Cian, Magenta, Amarillo, Negro) con control preciso tanto de los colores como de la temperatura de los tanques de tinta.

### Funcionalidades principales:
1. **Selección y Conversión de Color**: 
   - Utiliza una cámara adaptada a Raspberry Pi para capturar colores en tiempo real.
   - Se realiza la conversión de colores RGB a CMYK para simular el proceso de mezcla de tinta.
   - La conversión de color es visible en un Dashboard de Node-RED.
   
2. **Control PWM para Bombas de Tinta**:
   - El sistema controla las bombas de tinta para cada uno de los colores CMYK a través de señales PWM, permitiendo la dosificación precisa de cada tinta.
   
3. **Control de Temperatura con PID**:
   - El sistema incluye un control PID independiente para regular la temperatura de cada tanque de tinta (Cian, Magenta, Amarillo, Negro) utilizando sensores DS18B20.
   - Cada tanque tiene su propio calefactor controlado por PWM, lo que asegura una temperatura constante y precisa para cada color.
   
4. **Comunicación entre Raspberry Pi (Maestro) y Raspberry Pi Pico W (Esclavo)**:
   - La comunicación entre las dos placas se realiza mediante MQTT, donde los datos de color y temperatura se envían y reciben en formato JSON.
   - El Raspberry Pi Zero 2W actúa como el servidor principal, gestionando la selección de color y la conversión RGB a CMYK, mientras que el Raspberry Pi Pico W es el controlador que maneja las bombas de tinta y los calefactores.

## Componentes

### Hardware
- **Raspberry Pi Zero 2W**: Encargada de la selección de color, conversión RGB a CMYK, y la gestión de comunicación MQTT.
- **Raspberry Pi Pico W**: Controlador que maneja los PWM para las bombas de tinta y los calefactores.
- **Cámara Web**: Utilizada para capturar imágenes y realizar la detección de colores.
- **Sensores de Temperatura DS18B20**: Cuatro sensores para medir la temperatura en cada tanque de tinta (Cian, Magenta, Amarillo, Negro).
- **Bombas de Tinta CMYK**: Cuatro bombas controladas por PWM para la dosificación precisa de las tintas.
- **Puentes H L298N**: Utilizados para el control de las bombas de tinta.
- **LEDs RGB**: Simulan los colores resultantes de la mezcla de tintas.
- **Calefactores**: Controlados por PWM para mantener la temperatura de los tanques de tinta.

### Software
- **MQTT**: Utilizado para la comunicación entre el Raspberry Pi Zero 2W y el Raspberry Pi Pico W.
- **Node-RED**: Herramienta utilizada para el Dashboard donde se visualizan y controlan los colores.
- **Python**: Lenguaje utilizado para el control de las bombas de tinta, calefactores y la comunicación MQTT.
- **PID Control**: Algoritmo utilizado para controlar la temperatura de los tanques de tinta.

## Arquitectura del Sistema

### 1. **Raspberry Pi Zero 2W (Servidor Principal)**
- **Cámara Web adaptada a Raspberry Pi**: Utiliza OpenCV para detectar colores en imágenes en tiempo real.
- **Node-RED Dashboard**: Interfaz gráfica para la selección de colores y monitoreo del sistema.
- **Conversión de RGB a CMYK**: Se lleva a cabo la conversión de color desde el espacio RGB al modelo de color CMYK.
- **Comunicación MQTT**: Publica los datos de color y temperatura en formato JSON.

### 2. **Raspberry Pi Pico W (Módulo de Control)**
- **Recepción de datos por MQTT**: Recibe los valores de color (CMYK y RGB) y temperatura en formato JSON.
- **Control PWM**: Controla las bombas de tinta y los calefactores de cada tanque.
- **Control de temperatura con PID**: Mantiene la temperatura constante en los tanques de tinta mediante calefactores controlados por señales PWM.
  
### 3. **Sistema de Periféricos**
- **Tanques Metálicos de Tinta CMYK**: Los cuatro tanques de tinta están calefaccionados y controlados mediante señales PWM.
- **Sistema de Mezcla de Pintura**: Los colores se combinan de acuerdo con los valores de CMYK recibidos.
- **Motor de Mezclado**: Controla la mezcla de la pintura, activado manualmente.

## Instalación

### Requisitos
- **Hardware**:
  - Raspberry Pi Zero 2W
  - Raspberry Pi Pico W
  - Cámara web
  - Sensores DS18B20
  - Bombas de tinta y puentes H L298N
  - Calefactores y componentes electrónicos adicionales
  
- **Software**:
  - Python 3
  - Node-RED
  - MQTT Broker (Ej. Mosquitto)
  - Bibliotecas Python: `umqtt.simple`, `DS18X20`, `machine`, entre otras.

### Pasos de Instalación
1. **Configuración de la Raspberry Pi Zero 2W**:
   - Instalar Raspberry Pi OS y configurar la conexión Wi-Fi.
   - Instalar Node-RED y configurar el Dashboard para la selección de colores.

2. **Configuración del Raspberry Pi Pico W**:
   - Programar el Pico W con MicroPython para manejar los controles PWM.
   - Configurar la comunicación MQTT para recibir los datos de color y temperatura.

3. **Conexión de Hardware**:
   - Conectar los sensores DS18B20 a los pines GPIO de la Raspberry Pi Pico W.
   - Conectar las bombas de tinta y los calefactores a los puentes H L298N.
   - Asegurarse de que los LEDs RGB y los calefactores estén correctamente conectados.

4. **Pruebas**:
   - Realizar pruebas de comunicación entre las dos Raspberry Pi utilizando MQTT.
   - Verificar la correcta conversión de colores y el funcionamiento del control PID de temperatura.


# El grupo G10 de digitales les desea todos sus visitante "kisses and hugs".
