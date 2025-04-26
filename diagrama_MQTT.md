```mermaid
flowchart TD
    subgraph Raspberry_Principal [Raspberry Pi Principal (Zero 2 W)]
        A1(Camera Manager: Captura Imagen)
        A2(Color Detector: Detecta Color RGB)
        A3(Color Converter: Convierte a CMYK)
        A4(MQTT Publisher: Publica JSON en Broker)
    end

    subgraph Broker [Broker MQTT (Mosquitto o similar)]
        B1(Topic: color/detection)
    end

    subgraph Raspberry_Pico_W [Raspberry Pi Pico W]
        C1(WiFi Manager: Conexión a Red)
        C2(MQTT Client: Subscripción a Topic)
        C3(Data Handler: Parseo JSON)
        C4(PWM Controller: Actualiza Salidas PWM)
        C5(Temp Sensor: Lee DS18B20)
        C6(LED Manager: Indicador de Estado)
    end

    A1 --> A2
    A2 --> A3
    A3 --> A4
    A4 --> B1
    B1 --> C2
    C2 --> C3
    C3 --> C4
    C5 --> C4
    C2 --> C6
```
