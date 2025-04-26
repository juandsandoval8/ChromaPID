```mermaid
flowchart TD
    %% ================= MAESTRO (Raspberry Pi Zero 2W) =================
    subgraph Maestro["Raspberry Pi Zero 2W (Servidor Principal)"]
        A["Cámara Web adaptada a Raspberry (OpenCV)"] --> B["Selección de Color en Node-RED Dashboard"]
        C["Sensor RGB Digital (Util para entender la conversion RGB a CMYK) (!!Opcional)"] --> B
        D["Carga Manual de Imágenes"] --> B
        B --> E["Conversión RGB a CMYK"]
        E --> F["Empaquetado Formato JSON (Colores (CMYK y RGB))"]
        F --> G["Publicación por MQTT"]
    end

    %% ================= ESCLAVO (Raspberry Pi Pico W) =================
    subgraph Esclavo["Raspberry Pi Pico W (Módulo de Control)"]
        G --> H["Recepción de JSON por MQTT (Colores (CMYK y RGB))"]
        H --> I["Control PWM de Salidas"]

        %% PWM
        I --> M["4 Canales PWM CMYK (Bombas de Tinta)"]
        I --> N["3 Canales PWM RGB (LED HUE Casero)"]

        %% Temperatura - Control Independiente
        subgraph Temperatura["Control PID temperatura"]
            J1["Sensor de Temperatura Cian (DS18B20)"] --> P1["PID Control Cian"]
            J2["Sensor de Temperatura Magenta (DS18B20)"] --> P2["PID Control Magenta"]
            J3["Sensor de Temperatura Amarillo (DS18B20)"] --> P3["PID Control Amarillo"]
            J4["Sensor de Temperatura Negro (DS18B20)"] --> P4["PID Control Negro"]

            P1 --> T1["PWM Calefactor Cian (C)"]
            P2 --> T2["PWM Calefactor Magenta (M)"]
            P3 --> T3["PWM Calefactor Amarillo (Y)"]
            P4 --> T4["PWM Calefactor Negro (K)"]
        end

        %% Bombas
        M --> R["Puentes H L298N"]
        R --> S["4 Bombas de Pintura (Cian (C), Magenta (M), Amarillo (Y), Negro (K))"]

        %% Mezclador
        L["Control Manual del Mezclador"] --> Z["Botón Físico de Activación"]
    end

    %% ================= PERIFÉRICOS =================
    subgraph Periféricos["Estructura física"]
        N --> U["LED HUE Casero (Simulación de Color con PWM RGB)"]
        M --> V["Tanques Metálicos de Tinta CMYK (Calefaccionados)"]
        T1 --> V
        T2 --> V
        T3 --> V
        T4 --> V
        S --> Y["Sistema de Mezcla de Pintura"]
        Z --> X["Motor de Mezclado"]
    end

    %% ================= ESTILOS =================
    style Maestro fill:#e6f3ff,stroke:#0066cc,stroke-width:2px
    style Esclavo fill:#ffe6e6,stroke:#cc0000,stroke-width:2px
    style Temperatura fill:#ffe0b3,stroke:#cc6600,stroke-width:2px
    style Periféricos fill:#f0f0f0,stroke:#666,stroke-width:1px
    style G fill:#fff2cc,stroke:#ff9900,stroke-width:1px
    style V fill:#f9f,stroke:#333
    style U fill:#f9f,stroke:#333


```
