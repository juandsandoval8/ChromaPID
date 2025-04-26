```mermaid
flowchart TD
    %% ================= MAESTRO (Raspberry Pi Zero 2W) =================
    subgraph Maestro["Raspberry Pi Zero 2W (Servidor Principal)"]
        A["Cámara Web (OpenCV)"] --> B[Selección de Color (Node-RED Dashboard)]
        D["Carga Manual de Imágenes"] --> B
        B --> E{{"Conversión RGB → CMYK"}}
        E --> F[Formato JSON]
        F --> G[Publicación MQTT (topic: color/detection)]
    end

    %% ================= ESCLAVO (Raspberry Pi Pico W) =================
    subgraph Esclavo["Raspberry Pi Pico W (Módulo de Control)"]
        G --> H{{"Recepción JSON (via MQTT)"}}
        H --> I[Parseo de Datos]

        %% PWM Outputs
        I --> J[Actualización de PWM]
        J --> J1["4 Canales CMYK (GP0-GP3)"]
        J --> J2["3 Canales RGB (GP4-GP6)"]
        J --> J3["1 Canal PID / Ventilador / Calefactor (GP7)"]

        %% Sensado de Temperatura
        I --> K[Lectura de Temperatura]
        K --> K1["Sensor DS18B20 (OneWire en GP16)"]

        %% Indicadores
        I --> M["LED Onboard Pico W: Indicador de Actividad"]
    end

    %% ================= PERIFÉRICOS =================
    subgraph Periféricos["Periféricos y Estructura Física"]
        J1 --> N["Tanques de Tinta CMYK + Bombas de Pintura"]
        J2 --> P["LED HUE Casero (RGB con PWM)"]
        J3 --> R["Ventilador o Calefactor (Control PID)"]
        K1 --> Q["Lectura de Temperatura en Mezcla"]
    end

    %% ================= COMUNICACIÓN =================
    subgraph Comunicación["Comunicación"]
        G -->|MQTT (Broker local)| H
    end

    %% ================= ESTILOS =================
    style Maestro fill:#e6f3ff,stroke:#0066cc,stroke-width:2px
    style Esclavo fill:#ffe6e6,stroke:#cc0000,stroke-width:2px
    style Periféricos fill:#f0f0f0,stroke:#666,stroke-width:1px
    style Comunicación fill:#fff2cc,stroke:#ff9900,stroke-width:1px
    style P fill:#ffccff,stroke:#990099,stroke-width:2px
    style M fill:#ccffcc,stroke:#009900,stroke-width:2px
```
