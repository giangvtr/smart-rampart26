#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include "DHT.h"

// Configurare Senzor DHT
#define DHTPIN 4
#define DHTTYPE DHT11 // Schimbă în DHT22 dacă folosești acel model
DHT dht(DHTPIN, DHTTYPE);

// Configurare LCD I2C
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Configurare Pini LED RGB
const int pinRosu = 3;
const int pinVerde = 5;
const int pinAlbastru = 6;

// Configurare Potențiometru
const int pinPot = A0;

// Praguri stabilite
const float PRAG_RECE = 20.0;
const float PRAG_CALD = 28.0;
const float PRAG_UMIDITATE_MARE = 60.0;
const int PRAG_AER_PROST = 40;

// Structură pentru a stoca o culoare RGB
struct Culoare {
  int r;
  int g;
  int b;
};

// Definiții culori
const Culoare ALBASTRU = {0, 0, 255};
const Culoare VERDE    = {0, 255, 0};
const Culoare ROSU     = {255, 0, 0};
const Culoare CYAN     = {0, 255, 255}; // Umiditate mare
const Culoare MOV      = {255, 255, 0} // Aer prost

// Variabile pentru alternarea textului pe LCD (2 secunde)
unsigned long timpPrecedentLCD = 0;
const long intervalLCD = 2000;
bool afiseazaUmiditate = true;

// Variabile pentru alternarea culorilor pe RGB (1 secundă)
unsigned long timpPrecedentRGB = 0;
const long intervalRGB = 1000; 
int indexCuloareCurenta = 0;

void setup() {
  lcd.init();
  lcd.backlight();
  
  dht.begin();
  
  pinMode(pinRosu, OUTPUT);
  pinMode(pinVerde, OUTPUT);
  pinMode(pinAlbastru, OUTPUT);
}

void loop() {
  unsigned long timpCurent = millis();

  // 1. Citire date de la senzori
  float umiditate = dht.readHumidity();
  float temperatura = dht.readTemperature();
  int valoarePot = analogRead(pinPot);
  int calitateAer = map(valoarePot, 0, 1023, 0, 100);

  // Verificare eroare senzor
  if (isnan(umiditate) || isnan(temperatura)) {
    lcd.setCursor(0, 0);
    lcd.print("Eroare senzor!  ");
    afiseazaCuloare(0, 0, 0);
    delay(1000);
    return;
  }

  // 2. Afișare permanentă Temperatură pe Linia 1
  lcd.setCursor(0, 0);
  lcd.print("Temp: ");
  lcd.print(temperatura, 1);
  lcd.print((char)223);
  lcd.print("C    ");

  // 3. Logică de alternare pentru Linia 2 (LCD)
  if (timpCurent - timpPrecedentLCD >= intervalLCD) {
    timpPrecedentLCD = timpCurent;
    afiseazaUmiditate = !afiseazaUmiditate;
    lcd.setCursor(0, 1);
    lcd.print("                "); // Șterge linia
  }

  lcd.setCursor(0, 1);
  if (afiseazaUmiditate) {
    lcd.print("Umid: ");
    lcd.print(umiditate, 1);
    lcd.print("%     ");
  } else {
    lcd.print("Aer:  ");
    lcd.print(calitateAer);
    lcd.print("%      ");
  }

  // 4. Logică pentru selectarea culorilor active (RGB)
  Culoare culoriActive[3]; // Maxim 3 culori pot fi active simultan
  int numarCulori = 0;

  // Pasul A: Adaugă culoarea de bază pentru temperatură (este mereu activă)
  if (temperatura < PRAG_RECE) {
    culoriActive[numarCulori++] = ALBASTRU;
  } 
  else if (temperatura >= PRAG_RECE && temperatura <= PRAG_CALD) {
    culoriActive[numarCulori++] = VERDE;
  } 
  else {
    culoriActive[numarCulori++] = ROSU;
  }

  // Pasul B: Verifică dacă umiditatea este prea mare (>60%) -> adaugă Cyan
  if (umiditate > PRAG_UMIDITATE_MARE) {
    culoriActive[numarCulori++] = CYAN;
  }

  // Pasul C: Verifică dacă aerul este prost (<40%) -> adaugă Mov
  if (calitateAer < PRAG_AER_PROST) {
    culoriActive[numarCulori++] = MOV;
  }

  // 5. Logică de ciclare a culorilor RGB (la fiecare 1 secundă)
  if (timpCurent - timpPrecedentRGB >= intervalRGB) {
    timpPrecedentRGB = timpCurent;
    indexCuloareCurenta++;
    if (indexCuloareCurenta >= numarCulori) {
      indexCuloareCurenta = 0; // Resetează ciclul
    }
  }

  // Trimite valorile către pinii LED-ului RGB
  Culoare c = culoriActive[indexCuloareCurenta];
  afiseazaCuloare(c.r, c.g, c.b);

  delay(50); // Mică pauză pentru stabilitate
}

void afiseazaCuloare(int r, int g, int b) {
  analogWrite(pinRosu, r);
  analogWrite(pinVerde, g);
  analogWrite(pinAlbastru, b);
}
