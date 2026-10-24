// Smart Rampart - ESP32 Node
//
// Setup:
//   1. ESP32 board package installed (Espressif).
//   2. Set WIFI_SSID / WIFI_PASS / SERVER below.
//
// Wiring (all 3.3V logic):
//   Water sensor signal (S) -> GPIO34   (ADC1, input-only)
//   Fire sensor            -> GPIO35   (ADC1, input-only) = fire index
//   DHT data                -> GPIO15
//   Water sensor / DHT VCC -> 3V3,  GND -> GND
//   IMPORTANT: GPIO34/35 have NO internal pull resistor. If a pin is left
//   unconnected, add a 10k resistor from that pin -> GND so it reads a
//   stable 0 instead of floating noise.
//   Alarm indicator: onboard LED on GPIO2, shared by WATER and FIRE alarms.
//   Fire gets the full-screen popup on the dashboard, the node
//   LED/buzzer and the dashboard popup are not exclusive, both fire.
//   Buzzer (water + fire alarm) -> GPIO25   (active buzzer; digitalWrite HIGH/LOW)
//   HVAC effort indicator    -> GPIO26   (PWM LED; duty = HVAC effort 0..255
//                                         from the dashboard's predictive
//                                         controller, riding on the POST reply)
//
//
// -----------------------------------------------------------------------------
// Task layout (Arduino-ESP32's built-in FreeRTOS -- no extra framework):
//
//   SensorTask   (core 1, ~100ms) samples the ADC + DHT, writes raw values
//                into SensorState. Never touches Wi-Fi/HTTP, so it can't be
//                stalled by a slow network call.
//   AlarmTask    (core 1, ~100ms) runs the water + fire latch/silence state
//                machines off SensorState + CommandState, and drives
//                ALARM_LED + BUZZER_PIN directly (either channel in ALARM
//                lights both). Publishes the finalized reading into a
//                depth-1 mailbox queue (xQueueOverwrite) for NetworkTask.
//   NetworkTask  (core 0, alongside the Wi-Fi driver's own tasks) POSTs the
//                latest reading every POST_INTERVAL, parses cmd/hvac/hvacMode
//                out of the reply into CommandState. A reading that fails to
//                POST (Wi-Fi drop) goes into a small in-RAM backlog ring
//                instead of being discarded, and drains faster than normal
//                once the link comes back -- no flash/DB involved, this is
//                only meant to ride out a brief outage, not a power loss.
//   ActuatorTask (core 1, ~50ms) drives the HVAC_LED_PIN PWM duty from
//                CommandState, independent of the alarm path's timing.
// -----------------------------------------------------------------------------

#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>   // needed when SERVER is an https:// URL (tunnel)
#include "DHT.h"                // Adafruit "DHT sensor library" + "Adafruit Unified Sensor"

// ---- config -----------------------------------------------------------------
const char* WIFI_SSID = "Hotspot";
const char* WIFI_PASS = "xxxxxxx";
const char* SERVER    = "http://192.168.1.204:8000/api/ingest";  
const char* ZONE      = "BASE01";        // maps to BASEMENT on the dashboard

const int waterPin  = 34;                // ADC1 input-only: water level sensor
const int firePin   = 35;                // ADC1 input-only: potentiometer = fire index
const int ALARM_LED = 2;                 // onboard LED = local WATER alarm indicator
const int BUZZER_PIN = 25;               // active buzzer = local WATER alarm sound
const int HVAC_LED_PIN = 26;             // PWM = HVAC conditioning-effort indicator

#define DHTPIN  15
#define DHTTYPE DHT11                     // DHT22; use DHT11 if that is your sensor
DHT dht(DHTPIN, DHTTYPE);

const int WATER_ALARM_LEVEL = 3000;             // averaged ADC above this = WATER ALARM
const int WATER_WARN_LEVEL  = 2000;             // averaged ADC above this = WATER WARN

// Fire is reported as a 0..100 index (pot mapped), mirroring the dashboard's
// own BASEMENT.FIRE bounds (config.py) so the node's local alarm agrees with
// the server's. Fire ALARM joins water in driving ALARM_LED + BUZZER_PIN; it
// also still triggers the full-screen popup on the dashboard -- both fire.
const int FIRE_WARN_INDEX  = 50;
const int FIRE_ALARM_INDEX = 70;

const unsigned long SENSOR_PERIOD_MS   = 100;   // SensorTask sample rate
const unsigned long ALARM_PERIOD_MS    = 100;   // AlarmTask evaluation rate
const unsigned long ACTUATOR_PERIOD_MS = 50;    // ActuatorTask PWM/blink rate
const unsigned long POST_INTERVAL_MS   = 3000;  // POST cadence
const unsigned long RETRY_BACKOFF_MS   = 1000;  // retry pace while Wi-Fi/POST is down
const unsigned long DRAIN_PACE_MS      = 300;   // catch-up pace while backlog > 0
const int BACKLOG_CAPACITY             = 20;    // ~1 min of readings at 3s cadence

// -----------------------------------------------------------------------------
// Shared state between tasks. Each struct has its own short-lived mutex --
// critical sections are copy-in/copy-out only, never held across a sensor
// read or an HTTP call.
// -----------------------------------------------------------------------------
struct SensorState {
  int water = 0;
  int fire  = 0;
  float temp = NAN;
  float humidity = NAN;
};
SensorState g_sensor;
SemaphoreHandle_t g_sensorMutex;

struct CommandState {
  char alarm_cmd[12] = "AUTO"; // AUTO / ARM / DISARM / RESET / OFF
  int hvacEffort = 0;          // 0..255 PWM duty from the dashboard's HVAC controller
  char hvacMode[12] = "IDLE";  // IDLE / HEAT / COOL / DEHUMIDIFY / HUMIDIFY
};
CommandState g_command;
SemaphoreHandle_t g_commandMutex;

struct Reading {
  int water = 0;
  int fire  = 0;
  float temp = NAN;
  float humidity = NAN;
  char state[8] = "OK";
};
// AlarmTask -> NetworkTask handoff: a depth-1 mailbox queue (only keep newest value)
QueueHandle_t g_readingMailbox;

// Local alarm state: 
// * LED/buzzer turn on while water or fire is above its ALARM bound
// * If the dashboard has silenced that channel (DISARM / RESET / OFF on the POST reply). Each channel's silence holds
// until ITS OWN reading drops back below the threshold, so a fresh flood or
// flame re-triggers that channel independently of the other. 
// * Only AlarmTask touches these, so no mutex.
bool g_waterSilenced = false;
bool g_fireSilenced  = false;

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

// ADC read with median filter (less impacts from spike than normal averaging methods)
int readStable(int pin) {
  // Let the ADC mux settle on this channel.
  for (int i = 0; i < 4; i++) { analogRead(pin); delayMicroseconds(300); }


  // Total reading time per pin: 6,3 ms
  const int N = 21;   // number of reading times (random odd numbers)
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

// JSON field scanners
// Server sends: {"ok": true, "cmd": "RESET", "hvac": 180, "hvacMode": "COOL"}
long parseIntAfter(const String &reply, const char *key) {
  String pattern = String("\"") + key + "\":";
  int idx = reply.indexOf(pattern);
  if (idx < 0) return -1;
  return reply.substring(idx + pattern.length()).toInt();
}

String parseStringAfter(const String &reply, const char *key) {
  String pattern = String("\"") + key + "\":\"";
  int idx = reply.indexOf(pattern);
  if (idx < 0) return String();
  idx += pattern.length();
  int end = reply.indexOf('"', idx);
  if (end < 0) return String();
  return reply.substring(idx, end);
}

// SensorTask - sample the ADC (fire + water level) + DHT
// =============================================================================
void sensorTask(void *pv) {
  float lastTemp = NAN, lastHum = NAN;   // carry the last good DHT read across
                                          // the frequent DHT11 checksum blips
  for (;;) {
    int water = readStable(waterPin);
    int fire  = map(readStable(firePin), 0, 4095, 0, 100);
    float t = dht.readTemperature();
    float h = dht.readHumidity();
    
    if (!isnan(t)) lastTemp = t;
    if (!isnan(h)) lastHum  = h;

    // lock mutex before writing
    if (xSemaphoreTake(g_sensorMutex, portMAX_DELAY) == pdTRUE) {
      g_sensor.water = water;
      g_sensor.fire  = fire;
      g_sensor.temp  = lastTemp;
      g_sensor.humidity = lastHum;
      xSemaphoreGive(g_sensorMutex);
    }

    // wait for next cycle
    vTaskDelay(pdMS_TO_TICKS(SENSOR_PERIOD_MS));
  }
}

// =============================================================================
// AlarmTask - water + fire alarm state machines, sharing one local LED
// and one buzzer (fire still also triggers the dashboard's full-screen popup).

void alarmTask(void *pv) {
  for (;;) {
    // 1. Copies the shared sensor structure into a local variable
    SensorState s;
    xSemaphoreTake(g_sensorMutex, portMAX_DELAY);
    s = g_sensor;
    xSemaphoreGive(g_sensorMutex);

    // 2. Read dashboard commands
    char alarm_cmd[12];
    xSemaphoreTake(g_commandMutex, portMAX_DELAY);
    strncpy(alarm_cmd, g_command.alarm_cmd, sizeof(alarm_cmd));
    xSemaphoreGive(g_commandMutex);
    alarm_cmd[sizeof(alarm_cmd) - 1] = '\0';

    // All share same physical alarm system, but distinct flags for future improvements
    // 3. Silence or re-arm both alarms
    if (strcmp(alarm_cmd, "DISARM") == 0 || strcmp(alarm_cmd, "RESET") == 0 || strcmp(alarm_cmd, "OFF") == 0) {
      if (!g_waterSilenced && !g_fireSilenced) Serial.println(">>> command received: alarm SILENCED");
      g_waterSilenced = true;
      g_fireSilenced  = true;
    } else if (strcmp(alarm_cmd, "ARM") == 0 || strcmp(alarm_cmd, "AUTO") == 0) {
      if (g_waterSilenced || g_fireSilenced) Serial.println(">>> command received: alarm RE-ARMED");
      g_waterSilenced = false;
      g_fireSilenced  = false;
    }

    // 4. Recover alarm after disarm command if needed
    // Each channel's own recovery clears its own silence, so a fresh flood or
    // flame re-triggers that channel independently of the other.
    if (s.water <= WATER_ALARM_LEVEL) g_waterSilenced = false;
    if (s.fire  <= FIRE_ALARM_INDEX)  g_fireSilenced  = false;


    // 5. Decide if to activate alarm
    bool waterAlarmActive = (s.water > WATER_ALARM_LEVEL) && !g_waterSilenced;
    bool fireAlarmActive  = (s.fire  > FIRE_ALARM_INDEX)  && !g_fireSilenced;
    bool alarmActive = waterAlarmActive || fireAlarmActive;

    // 6. Control hardware (LED & BUZZER)
    digitalWrite(ALARM_LED, alarmActive ? HIGH : LOW);
    digitalWrite(BUZZER_PIN, alarmActive ? HIGH : LOW);

    // 7. Update states of each channel
    const char *waterState = (s.water > WATER_ALARM_LEVEL) ? "ALARM"
                            : (s.water > WATER_WARN_LEVEL)  ? "WARN"
                            : "OK";
    const char *fireState  = (s.fire > FIRE_ALARM_INDEX) ? "ALARM"
                            : (s.fire > FIRE_WARN_INDEX)  ? "WARN"
                            : "OK";
    // Combine 2 states into 1 (either ALARM/WARN/OK)
    const char *state = (strcmp(waterState, "ALARM") == 0 || strcmp(fireState, "ALARM") == 0) ? "ALARM"
                       : (strcmp(waterState, "WARN")  == 0 || strcmp(fireState, "WARN")  == 0) ? "WARN"
                       : "OK";

    Serial.printf("water=%d(%s) fire=%d(%s) LED/buzzer=%s | temp=%.1f hum=%.1f\n",
                  s.water, waterState, s.fire, fireState,
                  alarmActive ? "ON" : "off", s.temp, s.humidity);

    // 8. Publish the finalized reading into the mailbox (overwrite last readings)"
    Reading finalized;
    finalized.water = s.water;
    finalized.fire  = s.fire;
    finalized.temp  = s.temp;
    finalized.humidity = s.humidity;
    strncpy(finalized.state, state, sizeof(finalized.state) - 1);
    finalized.state[sizeof(finalized.state) - 1] = '\0';
    xQueueOverwrite(g_readingMailbox, &finalized);

    vTaskDelay(pdMS_TO_TICKS(ALARM_PERIOD_MS));
  }
}

// =============================================================================
// NetworkTask - POST the latest reading, buffer on failure, parse the reply.

// Backlog is a plain ring buffer, local for NetworkTask
Reading g_backlog[BACKLOG_CAPACITY];
int g_backlogHead = 0;
int g_backlogCount = 0;

void backlogPush(const Reading &r) {
  // Check whether the buffer is full
  if (g_backlogCount == BACKLOG_CAPACITY) {
    g_backlogHead = (g_backlogHead + 1) % BACKLOG_CAPACITY;   // drop the oldest
    g_backlogCount--;
  }
  
  g_backlog[(g_backlogHead + g_backlogCount) % BACKLOG_CAPACITY] = r;
  g_backlogCount++;
}

bool backlogPop(Reading &out) {
  if (g_backlogCount == 0) return false;
  out = g_backlog[g_backlogHead];
  g_backlogHead = (g_backlogHead + 1) % BACKLOG_CAPACITY;
  g_backlogCount--;
  return true;
}

// POST one reading and, on success, update CommandState from the reply.
bool attemptPost(const Reading &r) {
  // Check wifi connection
  if (WiFi.status() != WL_CONNECTED) {
    WiFi.reconnect();
    Serial.println("WiFi: DISCONNECTED - buffering reading");
    return false;
  }

  // Configure HTTP and HTTPS
  HTTPClient http;
  WiFiClientSecure secureClient;
  bool useTls = (strncmp(SERVER, "https:", 6) == 0);
  if (useTls) {
    secureClient.setInsecure();          // disable TLS certi
    http.begin(secureClient, SERVER);
  } else {
    http.begin(SERVER);
  }

  // Declare the JSON content type
  http.addHeader("Content-Type", "application/json");

  // Add temperature and humidity only when valid (not NaN)
  char dhtFields[64] = "";
  size_t off = 0;
  if (!isnan(r.temp)) {
    off += snprintf(dhtFields + off, sizeof(dhtFields) - off, ",\"temp\":%.1f", r.temp);
  }
  if (!isnan(r.humidity)) {
    off += snprintf(dhtFields + off, sizeof(dhtFields) - off, ",\"humidity\":%.1f", r.humidity);
  }

  // Construct POST request body
  char body[192];
  snprintf(body, sizeof(body),
    "{\"zone\":\"%s\",\"water\":%d,\"fire\":%d%s,\"state\":\"%s\"}",
    ZONE, r.water, r.fire, dhtFields, r.state);

  // Send POST request
  int code = http.POST(body);
  Serial.printf("POST %s -> %d\n", body, code);
  // Only 2xx means the server actually accepted the reading
  bool ok = (code >= 200 && code < 300);

  // If connected ok, parse server's reply for command updates (cmd, hvac, hvacMode)
  if (ok) {
    String reply = http.getString();
    Serial.print("reply: ");
    Serial.println(reply);

    String alarmCmd = parseStringAfter(reply, "cmd");  // wire field is still "cmd"
    long   hvac     = parseIntAfter(reply, "hvac");
    String mode      = parseStringAfter(reply, "hvacMode");

    xSemaphoreTake(g_commandMutex, portMAX_DELAY);
    if (alarmCmd.length()) strncpy(g_command.alarm_cmd, alarmCmd.c_str(), sizeof(g_command.alarm_cmd) - 1);
    if (hvac >= 0)         g_command.hvacEffort = constrain((int)hvac, 0, 255);
    if (mode.length())     strncpy(g_command.hvacMode, mode.c_str(), sizeof(g_command.hvacMode) - 1);
    xSemaphoreGive(g_commandMutex);
  }

  http.end();
  return ok;
}

void networkTask(void *pv) {
  for (;;) {
    Reading r;
    bool fromBacklog = backlogPop(r);

    if (!fromBacklog) {
      // pdFALSE means AlarmTask hasn't published a first reading yet (e.g. right at boot).
      if (xQueuePeek(g_readingMailbox, &r, 0) != pdTRUE) {
        vTaskDelay(pdMS_TO_TICKS(POST_INTERVAL_MS));
        continue;
      }
    }
    bool ok = attemptPost(r);

    // If sending failed, push the reading back into the backlog and retry after a backoff delay.
    if (!ok) {
      backlogPush(r);                                  
      vTaskDelay(pdMS_TO_TICKS(RETRY_BACKOFF_MS));
      continue;
    }

    // Draining a backlog (just reconnected) to catch up fast; otherwise hold
    // the normal heartbeat cadence.
    vTaskDelay(pdMS_TO_TICKS(g_backlogCount > 0 ? DRAIN_PACE_MS : POST_INTERVAL_MS));
  }
}

// =============================================================================
// ActuatorTask -- HVAC effort/mode indicator

void actuatorTask(void *pv) {
  unsigned long phaseStart = millis();
  for (;;) {
    CommandState cmd;
    xSemaphoreTake(g_commandMutex, portMAX_DELAY);
    cmd = g_command;
    xSemaphoreGive(g_commandMutex);

    bool idle  = (strcmp(cmd.hvacMode, "IDLE") == 0);
    bool blink = (strcmp(cmd.hvacMode, "DEHUMIDIFY") == 0) || (strcmp(cmd.hvacMode, "HUMIDIFY") == 0);

    int duty;
    if (idle) {
      duty = 0;
    } else if (blink) {
      unsigned long phase = (millis() - phaseStart) % 1100;
      bool on = (phase < 150) || (phase >= 300 && phase < 450);
      duty = on ? cmd.hvacEffort : 0;
    } else {
      duty = cmd.hvacEffort;   // steady for HEAT / COOL
    }

    ledcWrite(HVAC_LED_PIN, duty);
    vTaskDelay(pdMS_TO_TICKS(ACTUATOR_PERIOD_MS));
  }
}

// -----------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("=== Smart Rampart: water + DHT + fire + HVAC/buzzer actuators (4 FreeRTOS tasks) ===");

  pinMode(ALARM_LED, OUTPUT);
  digitalWrite(ALARM_LED, LOW);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  ledcAttach(HVAC_LED_PIN, 5000, 8);
  ledcWrite(HVAC_LED_PIN, 0);

  dht.begin();

  g_sensorMutex    = xSemaphoreCreateMutex();
  g_commandMutex   = xSemaphoreCreateMutex();
  g_readingMailbox = xQueueCreate(1, sizeof(Reading));   // depth 1 -- see xQueueOverwrite note above

  connectWifi();

  xTaskCreatePinnedToCore(sensorTask,   "SensorTask",   4096, nullptr, 2, nullptr, 1);  // priority 2, core 1
  xTaskCreatePinnedToCore(alarmTask,    "AlarmTask",    4096, nullptr, 2, nullptr, 1);  // priority 2, core 1
  xTaskCreatePinnedToCore(actuatorTask, "ActuatorTask", 2048, nullptr, 1, nullptr, 1);  // priority 1, core 1
  xTaskCreatePinnedToCore(networkTask,  "NetworkTask",  8192, nullptr, 1, nullptr, 0);  // priority 1, core 0
}

void loop() {
  vTaskDelete(NULL);   // everything happens in the four tasks above
}
