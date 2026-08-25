// MuseumGuard - ESP32 environmental zone node (WiFi -> HTTP JSON).
//
// Sends sensor readings to the Flask dashboard every 2 seconds, and reads a
// command back FROM THE SAME POST's reply (no inbound connection to the ESP32
// is needed - that is why this works even inside the Wokwi simulator).
//
// Arduino IDE / Wokwi setup:
//   1. ESP32 board package installed (Espressif).
//   2. Libraries: "DHT sensor library" (Adafruit), "LiquidCrystal_I2C".
//   3. Set WIFI_SSID / WIFI_PASS / SERVER below.
//
// Wiring (ESP32 is 3.3V logic):
//   DHT data    -> GPIO4
//   LCD I2C SDA -> GPIO21,  SCL -> GPIO22
//   RGB LED R/G/B -> GPIO25 / GPIO26 / GPIO27  (each via ~220R)
//   Potentiometer wiper -> GPIO34  (ADC1, input-only)

#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include "DHT.h"

// ---- config -----------------------------------------------------------------
const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASS = "";                                       // "" for Wokwi
const char* SERVER    = "http://192.168.95.204:8000/api/ingest";  // server IP + port (dashboard defaults to :8000)
const char* ZONE      = "GAL01";

const unsigned long POST_INTERVAL = 2000;  // 2s heartbeat

// ---- sensors / actuators ----------------------------------------------------
#define DHTPIN  4
#define DHTTYPE DHT22          // DHT22 in Wokwi; use DHT11 for the real sensor
DHT dht(DHTPIN, DHTTYPE);

LiquidCrystal_I2C lcd(0x27, 16, 2);

const int redPin   = 25;
const int greenPin = 26;
const int bluePin  = 27;
const int potPin   = 34;       // ADC1 input-only

// ---- thresholds -------------------------------------------------------------
const float COLD_LIMIT       = 20.0;
const float HOT_LIMIT        = 28.0;
const float HIGH_HUMIDITY    = 60.0;
const int   BAD_AIR_LIMIT    = 40;

struct Color { int r, g, b; };
const Color BLUE   = {0,   0,   255};
const Color GREEN  = {0,   255, 0};
const Color RED    = {255, 0,   0};
const Color CYAN   = {0,   255, 255};   // high humidity
const Color PURPLE = {255, 0,   255};   // bad air

// ---- timing state -----------------------------------------------------------
unsigned long lastLcdSwap  = 0;
const long lcdSwapInterval = 2000;
bool showHumidity = true;

unsigned long lastColorStep  = 0;
const long colorStepInterval = 1000;
int currentColorIndex = 0;

unsigned long lastPost = 0;

// Command received from the dashboard (via the POST reply).
// "AUTO" = normal behaviour, "OFF" = LED forced off (alarm acknowledged).
String ledCommand = "AUTO";

// -----------------------------------------------------------------------------
void setColor(int r, int g, int b) {
  // Common-cathode LED. ESP32 core 3.x: address the PIN in ledcWrite().
  ledcWrite(redPin, r);
  ledcWrite(greenPin, g);
  ledcWrite(bluePin, b);
}

void connectWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  lcd.setCursor(0, 0);
  lcd.print("WiFi connecting ");
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
  }
  lcd.setCursor(0, 0);
  lcd.print("WiFi OK         ");
  Serial.print("connected: ");
  Serial.println(WiFi.localIP());
  delay(500);
}

// ===========================================================================
//  THIS is where data goes out over WiFi, and the command comes back in.
//  The ESP32 opens an HTTP connection, POSTs the JSON body, then reads the
//  server's reply body and looks for a "cmd" field to update ledCommand.
// ===========================================================================
void postReading(float temperature, float humidity, int airQuality, const char* state) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  http.begin(SERVER);
  http.addHeader("Content-Type", "application/json");

  char body[160];
  snprintf(body, sizeof(body),
    "{\"zone\":\"%s\",\"temp\":%.1f,\"humidity\":%.1f,\"air\":%d,\"state\":\"%s\"}",
    ZONE, temperature, humidity, airQuality, state);

  int code = http.POST(body);                 // <-- send over WiFi
  Serial.printf("POST %s -> %d\n", body, code);

  if (code > 0) {
    String reply = http.getString();          // <-- server's response
    Serial.print("reply: ");
    Serial.println(reply);
    // Very small parser: look for "cmd":"..." in the JSON reply.
    // The dashboard replies with one of AUTO / OFF / ARM / DISARM / RESET.
    // For this environmental node, any "silence the alarm" command (OFF /
    // DISARM / RESET) forces the LED off; ARM / AUTO returns to normal.
    if (reply.indexOf("\"cmd\":\"OFF\"") >= 0 ||
        reply.indexOf("\"cmd\":\"DISARM\"") >= 0 ||
        reply.indexOf("\"cmd\":\"RESET\"") >= 0) {
      ledCommand = "OFF";
    } else if (reply.indexOf("\"cmd\":\"AUTO\"") >= 0 ||
               reply.indexOf("\"cmd\":\"ARM\"") >= 0) {
      ledCommand = "AUTO";
    }
  }
  http.end();
}

// -----------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);

  Wire.begin(21, 22);
  lcd.init();
  lcd.backlight();

  dht.begin();

  ledcAttach(redPin, 5000, 8);
  ledcAttach(greenPin, 5000, 8);
  ledcAttach(bluePin, 5000, 8);

  // Startup self-check: flash white once.
  setColor(255, 255, 255);
  delay(300);
  setColor(0, 0, 0);

  connectWifi();
}

void loop() {
  unsigned long now = millis();

  // 1. Read sensors
  float humidity    = dht.readHumidity();
  float temperature = dht.readTemperature();
  int   potValue    = analogRead(potPin);            // ESP32 ADC is 0..4095
  int   airQuality  = map(potValue, 0, 4095, 0, 100);

  // Sensor error -> keep looping, never halt
  if (isnan(humidity) || isnan(temperature)) {
    lcd.setCursor(0, 0);
    lcd.print("Sensor error!   ");
    setColor(0, 0, 0);
    if (now - lastPost >= POST_INTERVAL) {
      lastPost = now;
      postReading(0, 0, airQuality, "STALE");
    }
    delay(200);
    return;
  }

  // 2. Line 1: temperature (always shown)
  lcd.setCursor(0, 0);
  lcd.print("Temp: ");
  lcd.print(temperature, 1);
  lcd.print((char)223);
  lcd.print("C    ");

  // 3. Line 2 alternates humidity / air every 2s
  if (now - lastLcdSwap >= lcdSwapInterval) {
    lastLcdSwap = now;
    showHumidity = !showHumidity;
    lcd.setCursor(0, 1);
    lcd.print("                ");
  }
  lcd.setCursor(0, 1);
  if (showHumidity) {
    lcd.print("Humi: "); lcd.print(humidity, 1); lcd.print("%     ");
  } else {
    lcd.print("Air:  "); lcd.print(airQuality); lcd.print("%      ");
  }

  // 4. Decide which colors are active
  Color activeColors[3];
  int colorCount = 0;
  const char* state = "OK";

  if (temperature < COLD_LIMIT)            activeColors[colorCount++] = BLUE;
  else if (temperature <= HOT_LIMIT)       activeColors[colorCount++] = GREEN;
  else { activeColors[colorCount++] = RED; state = "ALARM"; }

  if (humidity > HIGH_HUMIDITY)   { activeColors[colorCount++] = CYAN;   if (strcmp(state, "OK") == 0) state = "WARN"; }
  if (airQuality < BAD_AIR_LIMIT) { activeColors[colorCount++] = PURPLE; if (strcmp(state, "OK") == 0) state = "WARN"; }

  // 5. Cycle active colors every 1s
  if (now - lastColorStep >= colorStepInterval) {
    lastColorStep = now;
    currentColorIndex = (currentColorIndex + 1) % colorCount;
  }
  if (currentColorIndex >= colorCount) currentColorIndex = 0;

  // 6. Apply the LED - unless the dashboard commanded it OFF (acknowledge).
  if (ledCommand == "OFF") {
    setColor(0, 0, 0);
  } else {
    Color c = activeColors[currentColorIndex];
    setColor(c.r, c.g, c.b);
  }

  // 7. Heartbeat POST every 2s (also brings the command back)
  if (now - lastPost >= POST_INTERVAL) {
    lastPost = now;
    postReading(temperature, humidity, airQuality, state);
  }

  delay(50);
}
