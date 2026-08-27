// Smart Rampart - MINIMAL test: WiFi + water sensor + dashboard POST + DISARM.
//
// Purpose: prove the full round trip, INCLUDING the command that rides back on
// the POST reply. The node reads the analog water-level sensor every 3s, POSTs
// it to the dashboard, and turns ON the onboard LED as a local ALARM when the
// level is high. Clicking DISARM (or "Reset BASEMENT - Water level") on the
// dashboard queues a command that comes back on the next POST reply and
// silences the LED. No DHT, no RGB LED, no potentiometer.
//
// Setup:
//   1. ESP32 board package installed (Espressif).
//   2. Set WIFI_SSID / WIFI_PASS / SERVER below.
//
// Wiring (all 3.3V logic):
//   Water sensor signal (S) -> GPIO34   (ADC1, input-only)
//   Potentiometer wiper     -> GPIO35   (ADC1, input-only) = fire index
//   DHT data                -> GPIO4
//   Water sensor / DHT VCC -> 3V3,  GND -> GND
//   IMPORTANT: GPIO34/35 have NO internal pull resistor. If a pin is left
//   unconnected, add a 10k resistor from that pin -> GND so it reads a
//   stable 0 instead of floating noise.
//   Water alarm indicator: onboard LED on GPIO2. Fire alarm shows as a
//   center-screen popup on the dashboard (no node LED needed).
//
// Test without a real sensor: briefly jumper 3V3 -> GPIO34 to force a high
// reading (ALARM). The onboard LED turns on; click DISARM on the dashboard and
// it should go out on the next POST (within ~3s).

#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>   // needed when SERVER is an https:// URL (tunnel)
#include "DHT.h"                // Adafruit "DHT sensor library" + "Adafruit Unified Sensor"

// ---- config -----------------------------------------------------------------
const char* WIFI_SSID = "Hotspot";
const char* WIFI_PASS = "hahahaha";
const char* SERVER    = "http://192.168.1.204:8000/api/ingest";  // laptop LAN IP (same router as the ESP32); server must run with --host 0.0.0.0
const char* ZONE      = "BASE01";        // maps to BASEMENT on the dashboard

const int waterPin  = 34;                // ADC1 input-only: water level sensor
const int firePin   = 35;                // ADC1 input-only: potentiometer = fire index
const int ALARM_LED = 2;                 // onboard LED = local WATER alarm indicator

#define DHTPIN  15
#define DHTTYPE DHT11                     // DHT22; use DHT11 if that is your sensor
DHT dht(DHTPIN, DHTTYPE);

const int WATER_ALARM_LEVEL = 3000;             // averaged ADC above this = WATER ALARM
const int WATER_WARN_LEVEL  = 2000;             // averaged ADC above this = WATER WARN

// Fire is reported as a 0..100 index (pot mapped). The dashboard alarms above
// 70 (see BASEMENT.FIRE in config.py); we mirror that here just for serial.
const int FIRE_ALARM_INDEX = 70;

const unsigned long POST_INTERVAL = 3000;  // sample + POST every 3s
unsigned long lastPost = 0;

// Local alarm state. The LED turns on while water is above ALARM_LEVEL, unless
// the dashboard has silenced it (DISARM / RESET / OFF on the POST reply). The
// silence holds until the water drops back below the threshold, so a fresh
// flood re-triggers the alarm.
bool alarmSilenced = false;

// -----------------------------------------------------------------------------
void connectWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("WiFi connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("connected, IP: ");
  Serial.println(WiFi.localIP());
}

// Robust ADC read. The ESP32 has ONE ADC behind a mux, so the first sample
// after switching channels carries charge from the previous pin -- we discard a
// few settling reads, then take the MEDIAN of many samples. A median ignores
// the occasional full-scale spike that an average would smear into the result.
int readStable(int pin) {
  // Let the ADC mux settle on this channel.
  for (int i = 0; i < 4; i++) { analogRead(pin); delayMicroseconds(300); }

  const int N = 21;
  int s[N];
  for (int i = 0; i < N; i++) {
    s[i] = analogRead(pin);
    delayMicroseconds(300);
  }
  // insertion sort (N is tiny) then return the middle element
  for (int i = 1; i < N; i++) {
    int v = s[i], j = i - 1;
    while (j >= 0 && s[j] > v) { s[j + 1] = s[j]; j--; }
    s[j + 1] = v;
  }
  return s[N / 2];
}

// POST all readings and parse the command that rides back on the reply.
// temp/humidity are NAN when the DHT read failed -- we omit them in that case.
void postReading(int water, float temp, float humidity, int fire, const char* state) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi: DISCONNECTED - skipping POST");
    return;
  }

  HTTPClient http;
  WiFiClientSecure secureClient;
  bool useTls = (strncmp(SERVER, "https:", 6) == 0);
  if (useTls) {
    secureClient.setInsecure();          // tunnel terminates TLS; fine for demo
    http.begin(secureClient, SERVER);
  } else {
    http.begin(SERVER);
  }
  http.addHeader("Content-Type", "application/json");

  char dhtFields[64] = "";
  if (!isnan(temp) && !isnan(humidity)) {
    snprintf(dhtFields, sizeof(dhtFields),
             ",\"temp\":%.1f,\"humidity\":%.1f", temp, humidity);
  }
  char body[192];
  snprintf(body, sizeof(body),
    "{\"zone\":\"%s\",\"water\":%d,\"fire\":%d%s,\"state\":\"%s\"}",
    ZONE, water, fire, dhtFields, state);

  int code = http.POST(body);
  Serial.printf("POST %s -> %d\n", body, code);

  if (code > 0) {
    String reply = http.getString();
    Serial.print("reply: ");
    Serial.println(reply);
    // The dashboard replies with {"ok":true,"cmd":"..."}. Any "silence" command
    // (DISARM / RESET / OFF) clears the local alarm; ARM / AUTO re-enables it.
    if (reply.indexOf("\"cmd\":\"DISARM\"") >= 0 ||
        reply.indexOf("\"cmd\":\"RESET\"")  >= 0 ||
        reply.indexOf("\"cmd\":\"OFF\"")    >= 0) {
      if (!alarmSilenced) Serial.println(">>> command received: alarm SILENCED");
      alarmSilenced = true;
    } else if (reply.indexOf("\"cmd\":\"ARM\"")  >= 0 ||
               reply.indexOf("\"cmd\":\"AUTO\"") >= 0) {
      if (alarmSilenced) Serial.println(">>> command received: alarm RE-ARMED");
      alarmSilenced = false;
    }
  }
  http.end();
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("=== Smart Rampart test: water + DHT + fire + DISARM ===");

  pinMode(ALARM_LED, OUTPUT);
  digitalWrite(ALARM_LED, LOW);

  dht.begin();
  connectWifi();
}

void loop() {
  unsigned long now = millis();

  // Sample + POST every POST_INTERVAL, and drive the alarm LED.
  if (now - lastPost >= POST_INTERVAL) {
    lastPost = now;

    int water = readStable(waterPin);    // median, 0..4095
    int fire  = map(readStable(firePin), 0, 4095, 0, 100);  // pot -> 0..100 fire index
    float temp = dht.readTemperature();  // NAN on a failed read
    float hum  = dht.readHumidity();

    const char* state = (water > ALARM_LEVEL) ? "ALARM"
                      : (water > WARN_LEVEL)  ? "WARN"
                      : "OK";

    // Water back below the threshold clears any prior silence, so the next
    // flood re-triggers the alarm.
    if (water <= ALARM_LEVEL) alarmSilenced = false;

    bool alarmActive = (water > ALARM_LEVEL) && !alarmSilenced;
    digitalWrite(ALARM_LED, alarmActive ? HIGH : LOW);

    Serial.printf("water=%d waterLED=%s | temp=%.1f hum=%.1f | fire=%d%s\n",
                  water, alarmActive ? "ON" : "off",
                  temp, hum, fire, (fire > FIRE_ALARM_INDEX) ? " FIRE!" : "");

    postReading(water, temp, hum, fire, state);
  }

  delay(50);
}