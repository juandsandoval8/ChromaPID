#include <LiquidCrystal.h>

// LCD: RS, E, D4, D5, D6, D7
LiquidCrystal lcd(14, 15, 16, 17, 18, 19);

// Pines trigger, echo, alarma
const int triggerPins[4] = {2, 4, 6, 8};
const int echoPins[4] = {3, 5, 7, 9};
const int alarmPins[4] = {10, 11, 12, 13};

// Variables de lectura
float distance[4];

// Umbral en cm para considerar “bajo”
const int lowLevelThreshold = 10;

// Intervalo para el parpadeo (ms)
unsigned long blinkInterval = 500;

void setup() {
  lcd.begin(20, 4);

  for (int i = 0; i < 4; i++) {
    pinMode(triggerPins[i], OUTPUT);
    pinMode(echoPins[i], INPUT);
    pinMode(alarmPins[i], OUTPUT);
    digitalWrite(alarmPins[i], LOW);
  }

  lcd.print("Monitoreando tanques");
  delay(2000);
  lcd.clear();
}

void loop() {
  unsigned long currentMillis = millis();

  for (int i = 0; i < 4; i++) {
    // Medir distancia con retardo entre sensores para evitar interferencias
    distance[i] = medirDistancia(triggerPins[i], echoPins[i]);
    delay(50); // Pequeño retardo entre mediciones

    lcd.setCursor(0, i);
    lcd.print("T");
    lcd.print(i + 1);
    lcd.print(": ");

    if (distance[i] > 0 && distance[i] < lowLevelThreshold) {
      digitalWrite(alarmPins[i], HIGH);

      // Parpadeo controlado usando millis()
      if ((currentMillis / blinkInterval) % 2 == 0) {
        lcd.print("BAJO      ");
      } else {
        lcd.print("          ");  // Borrar línea para efecto parpadeo
      }
    } else {
      digitalWrite(alarmPins[i], LOW);
      if (distance[i] <= 0) {
        lcd.print("Error     ");
      } else {
        lcd.print(distance[i]);
        lcd.print("cm        ");
      }
    }
  }

  delay(300); // Retardo entre ciclos de actualización
}

// Función para medir distancia con sensor ultrasónico
float medirDistancia(int trigPin, int echoPin) {
  // Limpiar el trigger
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  // Enviar pulso de trigger
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // Leer pulso de eco con timeout de 30 ms
  long duration = pulseIn(echoPin, HIGH, 30000);

  if (duration == 0) {
    return -1; // Error: no se recibió pulso
  }

  float distance = duration * 0.034 / 2; // Calcular distancia en cm
  return distance;
}
