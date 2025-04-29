#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// LCD 20x4 con dirección I2C típica 0x27
LiquidCrystal_I2C lcd(0x27, 20, 4);

// Pines para sensores ultrasónicos
const int trigPins[4] = {14, 26, 33, 4};
const int echoPins[4] = {27, 25, 32, 2};
long durations[4];
float distances[4];

// Altura máxima del tanque en cm (ajustable)
const float maxLevelCM = 50.0;

void setup() {
  Serial.begin(115200);
  lcd.init();
  lcd.backlight();

  // Inicializar pines
  for (int i = 0; i < 4; i++) {
    pinMode(trigPins[i], OUTPUT);
    pinMode(echoPins[i], INPUT);
  }

  lcd.setCursor(0, 0);
  lcd.print("Sistema de Niveles");
  delay(2000);
  lcd.clear();
}

float getDistance(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 30000); // timeout 30ms
  float distance = duration * 0.034 / 2.0; // cm

  if (duration == 0) return -1; // error en lectura
  return distance;
}

void loop() {
  for (int i = 0; i < 4; i++) {
    distances[i] = getDistance(trigPins[i], echoPins[i]);
  }

  lcd.clear();
  for (int i = 0; i < 4; i++) {
    lcd.setCursor(0, i);
    lcd.print("Tq");
    lcd.print(i + 1);
    lcd.print(": ");

    if (distances[i] < 0 || distances[i] > maxLevelCM) {
      lcd.print("Error     ");
    } else {
      float nivel = maxLevelCM - distances[i]; // nivel desde el fondo
      lcd.print(nivel, 1);
      lcd.print("cm      ");
    }
  }

  delay(1000);
}
