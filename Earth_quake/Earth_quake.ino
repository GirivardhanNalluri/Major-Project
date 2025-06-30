#include <Wire.h>
#include <LiquidCrystal_I2C.h>
 
// Initialize the LCD with I2C address 0x27, 16 columns, and 2 rows
LiquidCrystal_I2C lcd(0x27, 16, 2);
 
#define buzzer 11 // Pin connected to the buzzer
#define led 13    // Pin connected to the LED
 
// Pins connected to the x, y, and z outputs of the ADXL335 accelerometer
#define x A0
#define y A1
#define z A2 

/* Variables */
int xsample = 0;
int ysample = 0;
int zsample = 0;
long start;
int buz = 0;

/* Macros */
#define samples 50
#define maxVal 20
#define minVal -20
#define buzTime 3000   // 3 seconds

void setup() {
  lcd.init();
  lcd.backlight();
  Serial.begin(9600);
  delay(1000);
 
  Serial.println("System Initialized...");
  lcd.print("  Earth Quake  ");
  lcd.setCursor(0, 1);
  lcd.print("    Detector ");
  delay(2000);
  lcd.clear();
  lcd.print("Calibrating.....");
  lcd.setCursor(0, 1);
  lcd.print("Please wait...");
 
  pinMode(buzzer, OUTPUT);
  pinMode(led, OUTPUT);
  buz = 0;
  digitalWrite(led, buz);
 
  Serial.println("Calibration Started...");
  for (int i = 0; i < samples; i++) {
    xsample += analogRead(x);
    ysample += analogRead(y);
    zsample += analogRead(z);
  }
 
  xsample /= samples;
  ysample /= samples;
  zsample /= samples;
 
  delay(3000);
  lcd.clear();
  lcd.print("   Calibrated");
  delay(1000);
  Serial.println("Calibration Complete!");
  Serial.println("Baseline Values:");
  Serial.print("X Baseline: "); Serial.println(xsample);
  Serial.print("Y Baseline: "); Serial.println(ysample);
  Serial.print("Z Baseline: "); Serial.println(zsample);
 
  lcd.clear();
  lcd.print("  Device Ready");
  delay(1000);
 
  lcd.clear();
  lcd.print("X  Y  Z   Mag");
}

void loop() {
  int value1 = analogRead(x);
  int value2 = analogRead(y);
  int value3 = analogRead(z);
 
  int xValue = xsample - value1;
  int yValue = ysample - value2;
  int zValue = zsample - value3;
 
  int magnitude = sqrt(sq(xValue) + sq(yValue) + sq(zValue));
 
  bool isEarthquake = (xValue < minVal || xValue > maxVal || 
                       yValue < minVal || yValue > maxVal || 
                       zValue < minVal || zValue > maxVal);
 
  if (isEarthquake) {
    if (buz == 0) {
      start = millis();
      buz = 1;
      Serial.println("🚨 Earthquake Detected! Alert Activated.");
      lcd.clear();
      lcd.print("Earthquake !!!");
      digitalWrite(led, HIGH);
      tone(buzzer, 1000);
    }
    
    // Display values including magnitude
    lcd.setCursor(0, 1);
    lcd.print(padValue(xValue));
    lcd.setCursor(4, 1);
    lcd.print(padValue(yValue));
    lcd.setCursor(8, 1);
    lcd.print(padValue(zValue));
    lcd.setCursor(12, 1);
    lcd.print(padValue(magnitude));

    Serial.print("🚨 Earthquake: X: "); Serial.print(xValue);
    Serial.print(" | Y: "); Serial.print(yValue);
    Serial.print(" | Z: "); Serial.print(zValue);
    Serial.print(" | Magnitude: "); Serial.println(magnitude);
 
    if (buz == 1 && millis() >= start + buzTime) {
      noTone(buzzer);
      digitalWrite(led, LOW);
      Serial.println("🔕 Alert Deactivated: Buzzer and LED OFF");
    }
  } else {
    if (buz == 1) {
      buz = 0;
      noTone(buzzer);
      digitalWrite(led, LOW);
      lcd.clear();
      lcd.print("X  Y  Z   Mag");
      Serial.println("✅ Conditions Normal - Display Reset");
    }
    
    // Update display with normal values
    lcd.setCursor(0, 1);
    lcd.print(padValue(xValue));
    lcd.setCursor(4, 1);
    lcd.print(padValue(yValue));
    lcd.setCursor(8, 1);
    lcd.print(padValue(zValue));
    lcd.setCursor(12, 1);
    lcd.print(padValue(magnitude));

    Serial.print("✅ Normal: X: "); Serial.print(xValue);
    Serial.print(" | Y: "); Serial.print(yValue);
    Serial.print(" | Z: "); Serial.print(zValue);
    Serial.print(" | Magnitude: "); Serial.println(magnitude);
  }
 
  delay(150);
}

// Function to pad values for LCD formatting
String padValue(int value) {
  String strValue = String(value);
  while (strValue.length() < 3) {
    strValue = " " + strValue;
  }
  return strValue.substring(0, 3);
}