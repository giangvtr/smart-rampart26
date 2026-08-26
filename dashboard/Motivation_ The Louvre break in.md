# Brainstorm

**Motivation:** The Louvre break in

**Museum / archive / cultural heritage storage**

* **Tilt sensor on display cases** — real museums do use case-tamper sensors; this is a legitimate, not-stretched use of exactly the sensor you have.

* **DHT11 climate monitoring** — archives and museums are extremely strict about temperature/humidity for preservation (paper, textiles, paintings degrade outside narrow bands)  
* **Fire detection with false-positive suppression matters enormously here** — unlike most buildings, you generally *can't* use water-based suppression near artifacts, so early, reliable, low-false-positive detection is disproportionately valuable — a good talking point for why your corroboration logic matters.  
* **Keypad access control** for restricted collections/archive rooms.  
- 3 fails: send notif to security \+ 30s lock / need security overwrite  
- 5 fails: buzzer (need to make sure it not going forever) \+flashing light on \+ call police  
* Water leak/flooding for underground archives  
* Breakin:  
- Sound sensor \+ vibration: glass breaking  
- Motion sensor for the display case from inside. It has low detection range, could has false detection  
- 

# Composant list

[https://www.bitmi.ro/electronica/kit-arduino-uno-r3-ch340-10171.html](https://www.bitmi.ro/electronica/kit-arduino-uno-r3-ch340-10171.html)

1x Arduino Uno R3 ATMega328P-AU CH340G compatible development board, available individually  [**HERE**](https://www.bitmi.ro/placa-de-dezvoltare-compatibila-arduino-uno-r3-atmega328p-10358.html)  
1x USB cable  
1x 65-pin breadboard wire set, available individually  [**HERE**](https://www.bitmi.ro/electronica/set-de-65-fire-dupont-tata-tata-9-16-cm-10638.html)  
10x 0.25W 100R metal film resistor, available individually  [**HERE**](https://www.bitmi.ro/set-rezistori-20-de-valori-400-bucati-10-10m-1-4w-11255.html)  
10x 0.25W 220R metal film resistor  
10x 0.25W 560R metal film resistor  
10x 0.25W 1K metal film resistor  
10x 0.25W 4.7K metal film  
resistor 10x 0.25W 10K metal film  
resistor 10x 0.25W 47K  
metal film resistor 10x 0.25W 100K  
metal film resistor 10x 0.25W 10M  
5x 5mm red LED, available individually  [**HERE**](https://www.bitmi.ro/set-200-led-uri-de-diferite-culori-3-mm-5-mm-10508.html)  
5x 5mm yellow LED  
5x 5mm green LED  
5x 5mm  
blue LED 5x 5mm white LED  
2x 1N4007 diode  
2x 5516 LDR photoresistor  
1x NTC-MF52-103/3435 10K 3435±1 thermistor  
1x 5mm 4-pin RGB LED 2x  
PN2222A

NPN transistor  1x Shield with mini breadboard for prototyping, compatible with Arduino UNO R3, available individually [**HERE**](https://www.bitmi.ro/shield-cu-mini-breadboard-pentru-prototipuri-compatibil-arduino-uno-r3-10387.html) 1x ULN2003 stepper motor driver, available individually [**HERE**](https://www.bitmi.ro/electronica/modul-driver-uln2003-pentru-motoarele-pas-cu-pas-10642.html) 1x 28BYJ-48 5V Stepper Motor, available individually  [**HERE**](https://www.bitmi.ro/motor-pas-cu-pas-28byj-48-5v-dc-10643.html) 1x SG90 servomotor, 180 degrees, 9g, available individually [**HERE**](https://www.bitmi.ro/servomotor-sg90-180-grade-9g-10496.html) 1x  2-axis XY joystick module, available individually [**HERE**](https://www.bitmi.ro/modul-joystick-cu-2-axe-x-y-10454.html)  
1x Integrated circuit  74HC595N  
1x L293D Integrated Circuit  
1x SW-520D Tilt Sensor  
1x 10K B10K Potentiometer  
1x  LCD1602 Display with I2C/IIC Module, available individually [**HERE**](https://www.bitmi.ro/ecran-lcd1602-cu-modul-i2c-iic-10487.html)  
5x Mini Breadboard Button  
1x 5V Active Buzzer, available individually [**HERE**](https://www.bitmi.ro/modul-buzzer-activ-compatibil-arduino-10397.html)  
1x Passive Buzzer, available individually [**HERE**](https://www.bitmi.ro/modul-buzzer-pasiv-ky-006-10678.html)   
1x 0.56 inch 1x 7-segment LED Display (Common Cathode), available individually [**HERE**](https://www.bitmi.ro/display-led-1-digit-7-segmente-catod-comun-10636.html)  
1x 0.56 inch 4x 7-segment LED Display (Common Cathode), available individually [**HERE**](https://www.bitmi.ro/display-led-4-7-segmente-0-56-catod-comun-10649.html)  
1x 5V 5-pin Relay 10A 250VAC JQC-3FF  
1x  3.3V / 5V Power Supply Module for Breadboard MB102, available individually [**HERE**](https://www.bitmi.ro/modul-sursa-de-alimentare-pentru-breadboard-mb102-10534.html)  
1x  9V Battery Connector with 5.5 x 2.1 mm Jack, available individually [**HERE**](https://www.bitmi.ro/conector-baterie-9v-10513.html)  
1x DHT11 Temperature and Humidity Sensor Arduino compatible, available individually  [**HERE**](https://www.bitmi.ro/modul-senzor-de-temperatura-si-umiditate-dht11-compatibil-arduino-10393.html)  
1x  VS1838B IR receiver module, available individually [**HERE**](https://www.bitmi.ro/modul-receptor-ir-vs1838b-10408.html)  
1x Water level sensor, Arduino compatible, available individually [**HERE**](https://www.bitmi.ro/senzor-masurare-nivel-apa-compatibil-arduino-10635.html)  
1x  Ultrasonic sensor HC-SR04, available individually [**HERE**](https://www.bitmi.ro/senzor-ultrasonic-hc-sr04-10406.html)  
1x Microphone sound sensor with LM393  
1x  Breadboard 830 points MB-102, available individually [**HERE**](https://www.bitmi.ro/breadboard-830-puncte-mb-102-10500.html)  
1x IR remote control  
1x  4x4 matrix keyboard Keypad, available individually [**HERE**](https://www.bitmi.ro/tastatura-matriceala-4x4-keypad-10518.html)  
1x Set of 10 Dupont wires 20cm male-female for breadboard, available individually [**HERE**](https://www.bitmi.ro/40-x-fire-dupont-tata-tata-20cm-10511.html)  
1x DC 3V motor, available individually [**HERE**](https://www.bitmi.ro/motor-dc-3v-6v-pentru-proiecte-electronice-10651.html)  
1x 3-blade propeller

Extras:

1. Tilt sensor  
2. MQ4 gas sensor  
3. Air quality sensor  
4. **Motion detection sensor: security enhancement**  
5. Fire detection sensor  
6. Antenna/Bluetooth  
7. Raspeberry Pico

Components we are using:

- Sensors:  
  - Temperature Sensor  
  - Water Sensor  
- General Components:  
  - Breadboard  
  - Arduino  
- Output:  
- 

# Specification

- What are the features, how to implements, the thresholds, time frame, where to put each of them in a real museum, to measure what   
- Finite state machine/ decision graph  
- External interface graphe: which sensors need. Example

#### **![][image1]**

- Functional requiREMENTS: EXAMPLES:  
+ **FR-W1 (GPS Polling):** The watch shall sample GPS coordinates as a periodic task with period T \= 5 seconds.

+ **FR-W2 (GPS Coordinate Sampling)** : The watch shall poll the GPS sensor every 5 seconds and record the sample as valid if gps-\>location.isValid() returns true; if the signal is invalid, the coordinate shall be recorded as (0.0, 0.0) and the session shall continue uninterrupted to ensure data log continuity.

- air quality and air humidity : next to painting or statue to supervise environment, use lcd display to see temperature and humidity   
- DHT11 module: use as-is, digital pin, 5V  
- Water  level : in basement to protect artifacts from flooding or water damages. Varying from 0 \- 600 ish. Work with 5V, no special library. Analog pin	1\`\`\`\`\`\`\`\`   
- Fire detection : this one could be used in basement or exhibition   
- The light sensor is next to painting or statue to prevent color damages   
- Motion sensor: detecting intruders, connect to sound alarm

# Specification v1

# **MuseumGuard — Environmental & Security Monitoring System**

### **Requirements & Specification Document (MVP, 10-hour hackathon build, 5-person team)**

**Version:** 0.1 (Draft) **Author:** Product/Technical Specification **Date:** 2026-08-25

Modification: The smoke detector and fire detector is not available

---

## **1\. Executive Summary**

MuseumGuard is a low-cost, sensor-based monitoring system built on an **Arduino** (or **Raspberry Pi Pico**) that protects museum artifacts and spaces by continuously watching the environmental and security conditions that most commonly cause damage or loss: unstable temperature/humidity, excess light exposure, water intrusion, fire, and unauthorized intrusion after hours.

The microcontroller is connected to a windows machine via a serial port to send data. The windows collect and display on a monitor (for a security agent), with some button to overwrite (like turn off alarm by login in etc)

Each sensor node reports readings to a local display and/or serial log; when a reading crosses a defined safety threshold, the system raises a visible/audible alert so staff can react before damage occurs. The MVP targets a **single exhibit room \+ a basement storage area**, using off-the-shelf, beginner-friendly sensors.

**Core value proposition:** cheap, non-invasive, real-time protection for irreplaceable artifacts, using parts a museum could realistically deploy at scale for a few dollars per sensor node.

---

## **2\. Project Scope**

### **2.1 In-Scope (MVP, buildable in 10h)**

* One **microcontroller node per zone** (Arduino Uno/Nano or Raspberry Pi Pico), each handling 1–3 sensors.  
* **Temperature & humidity monitoring** near a painting/statue, shown live on an LCD.  
* **Light exposure monitoring** near a painting/statue (LDR/photoresistor), with threshold alert.  
* **Water level monitoring** in the basement (analog sensor), with threshold alert.  
* **Motion detection** (PIR) for after-hours intrusion, triggering a buzzer/sound alarm.  
* Simple **local alerting**: LED \+ buzzer \+ LCD message per triggered condition.  
* Basic **serial/console data log** (timestamp, sensor, value) for demo purposes.  
* One combined **demo panel on a laptop.**

### **2.2 Out-of-Scope (explicitly excluded from MVP)**

* Cloud dashboard, mobile app, or remote notifications (SMS/email/push).  
* Persistent database or long-term data storage/analytics.  
* Multi-room mesh networking or wireless sensor communication (LoRa/WiFi mesh).  
* User authentication, access control, or camera/video surveillance.  
* Battery-power optimization / long-term deployment hardening.  
* Calibration to museum-grade lux/RH accuracy standards (conservation-lab precision).  
* GPS/asset-tracking features (not relevant to a fixed-installation museum use case; mentioned only as a reference pattern for periodic-sampling FRs, see §4).

---

## **3\. User Personas & Use Cases**

| Persona | Description | Primary Needs |
| ----- | ----- | ----- |
| **Curator / Conservator** | Responsible for artifact condition | See current temp/humidity/light near sensitive pieces; get warned before damage thresholds are crossed |
| **Facilities / Security Staff** | Monitors the building day-to-day | Get an immediate, unmistakable alert for fire, flooding, or intrusion |
| **Night Security Guard** | On-site during closed hours | Wants motion detection armed only when museum is closed, with a loud local alarm |
| **Museum Visitor (indirect)** | Benefits from protected artifacts | Never directly interacts with the system, but relies on it not damaging the experience (no false alarms during opening hours) |

**Primary workflows:**

1. Staff walks by the LCD display near an artifact and reads current temp/humidity/light at a glance.  
2. If any value drifts out of the safe range, the LED/buzzer alerts staff on the spot.  
3. If water is detected in the basement, an alarm fires immediately and stays active until reset.  
4. If flame/fire is detected anywhere, the loudest/highest-priority alarm fires immediately.  
5. After closing hours, motion in a gallery triggers a security alarm; during open hours the motion sensor is ignored (or logs only, no alarm).

---

## **4\. Functional Requirements**

Format follows `FR-<Zone/Module>-<Number>`.

### **4.1 Environmental Monitoring (Exhibition Hall — near painting/statue)**

* **FR-ENV-1 (Sampling Rate):** The node shall sample temperature and humidity from the DHT11 every **2 seconds** (DHT11's practical minimum reliable interval).  
* **FR-ENV-2 (Display):** The node shall show current temperature (°C) and humidity (%RH) on a 16x2 LCD, refreshed each sampling cycle.  
* **FR-ENV-3 (Temperature Threshold):** If temperature is outside **18–24 °C**, the node shall trigger a warning LED (yellow) and log the excursion; if outside **15–28 °C**, it shall trigger the alarm LED (red) \+ buzzer.  
* **FR-ENV-4 (Humidity Threshold):** If relative humidity is outside **45–55% RH**, the node shall trigger a warning LED; if outside **35–65% RH**, it shall trigger alarm LED \+ buzzer (mold/warping risk).  
* **FR-ENV-5 (Light Exposure):** The node shall sample the LDR every **1 second** and convert to a relative light-level scale (0–1023 raw ADC, or calibrated lux if time allows). If light level exceeds a **configurable "sensitive-artifact" ceiling** (e.g., raw ADC \> 700, ≈ equivalent of \>150–200 lux for light-sensitive works), it shall trigger a warning LED. Sustained exposure above ceiling for **\>30 seconds** shall trigger the alarm.  
* **FR-ENV-6 (Data Continuity):** If a DHT11 read fails (`NaN`/timeout), the node shall log the last valid reading with a "STALE" flag and continue the loop without halting — same continuity principle as periodic GPS sampling in reference pattern FR-W2 (invalid sample ≠ system halt).

### **4.2 Water Level Monitoring (Basement)**

* **FR-WTR-1 (Sampling):** The node shall poll the analog water-level sensor on **A1** every **2 seconds**.  
* **FR-WTR-2 (Thresholds):** Raw analog range is **0–600**.  
  * 0–100: Dry (OK, green).  
  * 101–300: Damp/Warning (yellow LED, no alarm — logged only).  
  * 301–600: Flood risk (red LED \+ buzzer, alarm latched until manually reset).  
* **FR-WTR-3 (Latching Alarm):** Once the flood threshold is crossed, the alarm shall remain active even if the level later drops, until a physical reset button/switch is pressed (prevents missed events from evaporation/drainage).

### **4.3 Motion / Intrusion Detection (Exhibition Hall)**

* **FR-MOT-1 (Arming Schedule):** The PIR sensor shall only trigger the alarm when the system is in **ARMED (closed-hours)** state; during **OPEN (visiting-hours)** state, motion is ignored or logged silently (no alarm), to avoid false alarms from visitors.  
* **FR-MOT-2 (State Toggle):** The system shall support a manual arm/disarm switch or button (MVP: a physical toggle switch or a serial command) simulating "museum closes/opens."  
* **FR-MOT-3 (Detection):** On PIR digital HIGH while ARMED, the node shall immediately sound the buzzer continuously and light the red LED until manually reset/disarmed.  
* **FR-MOT-4 (Debounce):** The node shall ignore repeated PIR triggers within the same alarm episode (avoid buzzer chatter) — alarm is a single latched event until reset.

### **4.4 System-Wide / Cross-Cutting**

* **FR-SYS-1 (Periodic Task Pattern):** All sensors shall be sampled as independent periodic tasks (non-blocking `millis()`\-based timing, not `delay()`), each with its own period **T**, so one slow sensor never blocks another — mirrors the periodic-polling pattern in reference requirement FR-W1.  
* **FR-SYS-2 (Logging):** Every threshold crossing (start and clear) shall be printed to Serial Monitor as `[timestamp][zone][sensor][value][state]` for demo/debug purposes.  
* **FR-SYS-3 (Startup Self-Check):** On boot, the node shall flash all LEDs once and print sensor init status to Serial, to confirm wiring before a live demo.

---

## **5\. Finite State Machine (per zone controller)**

               ┌─────────────┐  
                │    INIT     │  (boot, sensor self-check)  
                └──────┬──────┘  
                       │ init OK  
                       ▼  
                ┌─────────────┐  
        ┌──────▶│  MONITORING │◀───────────┐  
        │       └──────┬──────┘            │  
        │              │ reading crosses    │ manual RESET  
        │              │ warning threshold  │ pressed  
        │              ▼                    │  
        │       ┌─────────────┐             │  
        │       │   WARNING   │             │  
        │       │ (yellow LED)│             │  
        │       └──────┬──────┘             │  
        │              │ crosses alarm       │  
        │              │ threshold           │  
        │              ▼                    │  
        │       ┌─────────────┐             │  
        └───────│    ALARM    │─────────────┘  
   value back    │ (red LED \+ │  
   in safe range │  buzzer,   │  
   (WARNING/     │  latched)  │  
   non-latched   └─────────────┘  
   sensors only)

Additional **security sub-state** (independent of environmental FSM, gates FR-MOT-\*):

\[DISARMED\] \--(closing time / toggle)--\> \[ARMED\] \--(motion detected)--\> \[INTRUSION\_ALARM\]  
    ▲                                                                          │  
    └───────────────────── (opening time / toggle / manual reset) ────────────┘

**Notes:**

* Environmental sensors (temp/humidity/light) use **WARNING → ALARM → back to MONITORING** (self-clearing, since drift is gradual and reversible).  
* Water and Fire use a **latched ALARM** (does not self-clear — requires physical reset) because these are one-shot critical events.  
* Motion alarm is latched and gated by the ARMED/DISARMED state.

---

## **6\. External Interface Graph (Sensors ↔ Microcontroller)**

| Sensor | Signal Type | MCU Pin (example) | Voltage | Library / Notes |
| ----- | ----- | ----- | ----- | ----- |
| DHT11 (temp/humidity) | Digital (1-wire) | D2 | 5V | `DHT.h` library, use as-is |
| LDR (photoresistor) light sensor | Analog | A0 | 5V (via voltage-divider w/ resistor) | No library, raw ADC read |
| Water level sensor | Analog | A1 | 5V | No library, raw ADC read, range 0–600 |
| PIR motion sensor | Digital | D4 | 5V | No library, `digitalRead()`, needs \~30–60s warm-up on boot |
| 16x2 LCD | Digital (parallel or I2C) | D7–D12 or I2C (A4/A5) | 5V | `LiquidCrystal.h` or `LiquidCrystal_I2C.h` |
| Buzzer (active) | Digital out | D5 | 5V | `digitalRead`/`tone()` optional |
| LEDs (green/yellow/red) x per zone | Digital out | D6, D8, D9 (example) | 5V (via resistor) | — |
| Reset/Arm-Disarm button | Digital in (pull-up) | D10 | 5V | `INPUT_PULLUP` |

**External interface graph (data flow):**

\[DHT11\] ─┐  
\[LDR\]    ├──▶ Sensor Read Layer ──▶ Threshold Engine ──▶ FSM ──▶ Actuator Layer ──▶ \[LEDs\]  
\[Water\]  │        (per FR-\*.1)      (per FR-\*.3/.4)                              ├──▶ \[Buzzer\]  
\[Flame\]  │                                                                       └──▶ \[LCD\]  
\[PIR\]    ┘                                                        │  
                                                                   └──▶ Serial Log (FR-SYS-2)

---

## **7\. Non-Functional Requirements**

* **Performance:** Sensor loop shall complete a full cycle (all zones) in **\< 1 second** for non-fire sensors; fire polling shall react in **≤ 500 ms** end-to-end (sensor read → alarm actuation).  
* **Reliability:** A single failed/disconnected sensor shall not crash or freeze the whole loop (isolate reads in try/guard logic, per FR-ENV-6 pattern).  
* **Usability:** Alert states must be understandable without documentation — color-coded LEDs (green/yellow/red) \+ distinct buzzer pattern for fire vs. flood vs. intrusion if time allows (stretch goal).  
* **Power:** All sensors run on 5V, compatible with a single USB-powered Arduino/Pico per zone (no separate power supply needed for MVP).  
* **Safety/Privacy:** No cameras, no personal data collected — motion sensor only produces a binary trigger, not identity information.  
* **Scalability (documented, not built):** Architecture should allow adding more zones by duplicating the node pattern (1 MCU per room/zone), or later evolving to a wireless mesh — explicitly Out-of-Scope for MVP but noted for judges.

---

## **8\. Technical Constraints & Assumptions**

* **Microcontroller:** Arduino Uno/Nano **or** Raspberry Pi Pico (team choice; sensor pin-outs above are Arduino-style, Pico uses GPIO numbers instead of D-pins — adjust accordingly).  
* **Assumption:** Demo is a **tabletop mock-up** (small model room/basement), not an actual museum installation — thresholds are illustrative, not conservation-lab-certified.  
* **Assumption:** "Open/closed hours" for the security FSM is simulated via a manual switch or serial command, not a real clock/RTC (RTC integration is a stretch goal if time allows).  
* **Assumption:** Each zone (Gallery, Basement) gets its own MCU \+ breadboard for parallel building by sub-teams; no inter-MCU communication required for MVP (each zone is self-contained and demoed independently).  
* **Dependencies:** DHT sensor library, (optional) LiquidCrystal\_I2C library — install before hackathon starts to save setup time.

---

## **9\. Acceptance Criteria (Definition of Done for the 10h Demo)**

1. ✅ LCD near the mock painting displays live, updating temperature and humidity values.  
2. ✅ Covering the LDR (simulating a spotlight/flash) triggers the light-warning LED within 1–2 seconds.  
3. ✅ Pouring/dripping water onto the basement sensor triggers the flood alarm (red LED \+ buzzer) and it **stays on** until reset is pressed.  
4. ✅ A lighter or match held near the flame sensor (from a safe distance) triggers the fire alarm instantly, overriding any other message on shared LCD.  
5. ✅ With the system ARMED, waving a hand in front of the PIR triggers the intrusion buzzer; with the system DISARMED, the same motion produces no alarm (only a log line).  
6. ✅ Serial Monitor shows a readable log of every threshold crossing with timestamp, sensor, and value.  
7. ✅ No single disconnected/faulty sensor freezes the other sensors' readings (demonstrate by unplugging one sensor mid-demo).  
8. ✅ All 5 sensor types (temp/humidity, light, water, flame, motion) are wired, working, and demoable within the mock museum layout at the end of 10 hours.

---

## **10\. Suggested 10-Hour / 5-Person Build Plan**

| Time | Task | Owner(s) |
| ----- | ----- | ----- |
| 0:00–0:30 | Kickoff, assign zones, confirm parts inventory, install libraries | All |
| 0:30–2:00 | Wire \+ code DHT11 \+ LCD (Zone: Gallery-Env) | Person A |
| 0:30–2:00 | Wire \+ code LDR light sensor \+ thresholds | Person B |
| 0:30–2:00 | Wire \+ code Water sensor \+ latched alarm (Zone: Basement) | Person C |
| 0:30–2:00 | Wire \+ code Flame sensor \+ highest-priority alarm | Person D |
| 0:30–2:00 | Wire \+ code PIR \+ arm/disarm switch | Person E |
| 2:00–4:00 | Individual unit testing per sensor against thresholds | All (pairs) |
| 4:00–5:30 | Integrate FSM logic (non-blocking `millis()` loop, shared LED/buzzer priority: fire \> flood \> intrusion \> env) | 2 people |
| 5:30–6:30 | Build mock museum layout (cardboard room \+ basement box) and mount sensors | 2 people |
| 6:30–7:30 | Serial logging \+ polish LCD messages | 1 person |
| 7:30–9:00 | Full integration test, run through all 8 acceptance criteria | All |
| 9:00–10:00 | Buffer, bug fixes, prepare demo script/pitch | All |

---

*End of document.*

# Spec v2

# **MuseumGuard — Environmental & Security Monitoring System**

### **Requirements & Specification Document (MVP, 10-hour hackathon build, 5-person team)**

**Version:** 0.2 **Author:** Product/Technical Specification **Date:** 2026-08-25

**Changes from v0.1:**

* **Removed:** smoke detector and flame/fire detector — hardware not available for this build.  
* **Added:** microcontroller now streams sensor data to a **Windows machine over serial (USB)**; a **desktop dashboard app** displays live status to a security agent and lets them **overwrite/acknowledge alarms** (login-gated).

---

## **1\. Executive Summary**

MuseumGuard is a low-cost, sensor-based monitoring system built on an **Arduino** (or **Raspberry Pi Pico**) that protects museum artifacts and spaces by continuously watching the conditions that most commonly cause damage or loss: unstable temperature/humidity, excess light exposure, water intrusion, and unauthorized intrusion after hours.

The microcontroller is connected to a **Windows machine via USB serial**. It streams structured sensor readings and alarm events over that serial link. The Windows machine runs a **dashboard application** that a security agent watches on a monitor: it shows live values per zone, flags any active alarm, and lets the agent **acknowledge/override (silence) an alarm**, gated behind a simple **login**, so there's an auditable "who cleared this" step instead of anyone being able to walk up and disable the alarm at the sensor node itself.

Each sensor node also keeps **local** alerting (LED \+ buzzer \+ LCD) so an alert is visible even if the dashboard isn't being watched at that instant. The MVP targets a **single exhibit room \+ a basement storage area**.

**Core value proposition:** cheap, non-invasive, real-time protection for irreplaceable artifacts, with a proper human-in-the-loop monitoring station instead of just blinking lights in an empty room.

---

## **2\. Project Scope**

### **2.1 In-Scope (MVP, buildable in 10h)**

* One **microcontroller node per zone** (Arduino Uno/Nano or Raspberry Pi Pico), each handling 1–3 sensors.  
* **Temperature & humidity monitoring** near a painting/statue, shown live on an LCD.  
* **Light exposure monitoring** near a painting/statue (LDR/photoresistor), with threshold alert.  
* **Water level monitoring** in the basement (analog sensor), with threshold alert.  
* **Motion detection** (PIR) for after-hours intrusion, triggering a buzzer/sound alarm.  
* Simple **local alerting**: LED \+ buzzer \+ LCD message per triggered condition.  
* **Serial link (USB) from MCU → Windows PC**, streaming structured readings \+ alarm events.  
* **Windows dashboard app** (see §6) showing live per-zone status to a security agent.  
* **Agent login \+ override/acknowledge control** to silence/clear an active alarm from the dashboard.  
* Basic **log** (timestamp, sensor, value, event) visible both on Serial Monitor and in the dashboard.  
* One combined **demo panel or small mock room layout** showing sensor placement.

### **2.2 Out-of-Scope (explicitly excluded from MVP)**

* **Fire / smoke detection** — hardware not available for this build; explicitly removed from scope (see §9 for how the architecture would extend to it later).  
* Cloud dashboard, mobile app, or remote (off-site) notifications (SMS/email/push).  
* Persistent database or long-term data storage/analytics (dashboard is live/session-only for MVP).  
* Multi-room mesh networking or wireless sensor communication (LoRa/WiFi mesh).  
* Real user-account system / multi-user role management — MVP login is a single shared agent credential, not a full auth system.  
* Camera/video surveillance.  
* Battery-power optimization / long-term deployment hardening.  
* Calibration to museum-grade lux/RH accuracy standards (conservation-lab precision).  
* GPS/asset-tracking features (not relevant to a fixed-installation museum use case; mentioned only as a reference pattern for periodic-sampling FRs, see §5).

---

## **3\. User Personas & Use Cases**

| Persona | Description | Primary Needs |
| ----- | ----- | ----- |
| **Curator / Conservator** | Responsible for artifact condition | See current temp/humidity/light near sensitive pieces; get warned before damage thresholds are crossed |
| **Security Agent (dashboard operator)** | Sits at the Windows monitor, watches the dashboard | See all zones at a glance; get an unmistakable visual/audio alert; log in to acknowledge/clear an alarm once handled |
| **Night Security Guard (on-site, roaming)** | Physically walks the building during closed hours | Wants motion detection armed only when museum is closed, with a loud local alarm at the sensor node itself |
| **Museum Visitor (indirect)** | Benefits from protected artifacts | Never directly interacts with the system, but relies on it not damaging the experience (no false alarms during opening hours) |

**Primary workflows:**

1. Agent sits at the Windows PC; the dashboard shows live temp/humidity/light/water/motion status per zone, color-coded (green/yellow/red).  
2. If any value drifts out of range, both the **local node** (LED/buzzer/LCD) and the **dashboard** raise the alert simultaneously.  
3. If water is detected in the basement, an alarm fires immediately (local \+ dashboard) and stays active until someone clears it.  
4. After closing hours, motion in a gallery triggers a security alarm (local buzzer \+ dashboard alert); during open hours the motion sensor is ignored (or logs only, no alarm).  
5. The agent investigates, then **logs in on the dashboard** and clicks "Acknowledge / Override" to silence the alarm — this sends a command back over serial to reset the node's latched alarm state, and the action is timestamped in the dashboard log.

---

## **4\. Functional Requirements**

Format follows `FR-<Zone/Module>-<Number>`.

### **4.1 Environmental Monitoring (Exhibition Hall — near painting/statue)**

* **FR-ENV-1 (Sampling Rate):** The node shall sample temperature and humidity from the DHT11 every **2 seconds**.  
* **FR-ENV-2 (Display):** The node shall show current temperature (°C) and humidity (%RH) on a 16x2 LCD, refreshed each sampling cycle.  
* **FR-ENV-3 (Temperature Threshold):** If temperature is outside **18–24 °C**, the node shall trigger a warning LED (yellow) and log the excursion; if outside **15–28 °C**, it shall trigger the alarm LED (red) \+ buzzer.  
* **FR-ENV-4 (Humidity Threshold):** If relative humidity is outside **45–55% RH**, the node shall trigger a warning LED; if outside **35–65% RH**, it shall trigger alarm LED \+ buzzer (mold/warping risk).  
* **FR-ENV-5 (Light Exposure):** The node shall sample the LDR every **1 second**. If light level exceeds a configurable ceiling (e.g., raw ADC \> 700), it shall trigger a warning LED. Sustained exposure above ceiling for **\>30 seconds** shall trigger the alarm.  
* **FR-ENV-6 (Data Continuity):** If a DHT11 read fails (`NaN`/timeout), the node shall log the last valid reading with a "STALE" flag and continue the loop without halting.

### **4.2 Water Level Monitoring (Basement)**

* **FR-WTR-1 (Sampling):** The node shall poll the analog water-level sensor on **A1** every **2 seconds**.  
* **FR-WTR-2 (Thresholds):** Raw analog range is **0–600**.  
  * 0–100: Dry (OK, green).  
  * 101–300: Damp/Warning (yellow LED, no alarm — logged only).  
  * 301–600: Flood risk (red LED \+ buzzer, alarm latched until cleared).  
* **FR-WTR-3 (Latching Alarm):** Once the flood threshold is crossed, the alarm shall remain active — including on the dashboard — even if the level later drops, until cleared **either** by the physical reset button at the node **or** by an agent override command from the dashboard (§4.4).

### **4.3 Motion / Intrusion Detection (Exhibition Hall)**

* **FR-MOT-1 (Arming Schedule):** The PIR sensor shall only trigger the alarm when the system is in **ARMED (closed-hours)** state; during **OPEN (visiting-hours)** state, motion is ignored or logged silently (no alarm).  
* **FR-MOT-2 (State Toggle):** The system shall support a manual arm/disarm switch or button, or an equivalent command sent from the dashboard, simulating "museum closes/opens."  
* **FR-MOT-3 (Detection):** On PIR digital HIGH while ARMED, the node shall immediately sound the buzzer continuously and light the red LED, and report the event over serial, until cleared.  
* **FR-MOT-4 (Debounce):** The node shall ignore repeated PIR triggers within the same alarm episode — alarm is a single latched event until reset/override.

### **4.4 Serial Link & Windows Dashboard**

* **FR-DASH-1 (Data Streaming):** Each MCU node shall transmit one line per sampling cycle over USB serial (baud **9600**, or **115200** if stable) in a simple delimited format, e.g.: `ZONE,SENSOR,VALUE,STATE,TIMESTAMP\n` Example: `GALLERY,TEMP,21.4,OK,00:12:35` / `BASEMENT,WATER,340,ALARM,00:14:02`  
* **FR-DASH-2 (Dashboard Display):** The Windows dashboard app shall read the serial port and render a live per-zone panel: current value, status color (green/yellow/red), and a running event log.  
* **FR-DASH-3 (Alarm Visibility):** Any `ALARM` state received shall be shown prominently (flashing panel and/or on-screen sound) until acknowledged.  
* **FR-DASH-4 (Agent Login):** The dashboard shall require a simple login (single shared username/password is acceptable for MVP) before the "Acknowledge / Override" control becomes usable — read-only monitoring shall **not** require login.  
* **FR-DASH-5 (Override Command):** Once logged in, the agent can click "Acknowledge" on an active alarm; the dashboard sends a command line back over serial (e.g., `CMD,BASEMENT,WATER,RESET\n`), and the corresponding node shall clear its latched alarm state on receipt.  
* **FR-DASH-6 (Audit Log):** Every acknowledge/override action shall be recorded in the dashboard's session log with a timestamp (and agent identity, if multiple accounts are added later) — no persistence to disk required for MVP, in-memory/session log is sufficient.  
* **FR-DASH-7 (Connection Resilience):** If the serial connection drops, the dashboard shall show a clear "disconnected" state per zone rather than freezing or showing stale data as if it were live.

### **4.5 System-Wide / Cross-Cutting**

* **FR-SYS-1 (Periodic Task Pattern):** All sensors shall be sampled as independent periodic tasks (non-blocking `millis()`\-based timing, not `delay()`), each with its own period **T**.  
* **FR-SYS-2 (Local Logging):** Every threshold crossing (start and clear) shall be printed to Serial as `[timestamp][zone][sensor][value][state]`, which doubles as the feed the dashboard parses.  
* **FR-SYS-3 (Startup Self-Check):** On boot, the node shall flash all LEDs once and print sensor init status to Serial, to confirm wiring before a live demo.

---

## **5\. Finite State Machine (per zone controller)**

               ┌─────────────┐  
                │    INIT     │  (boot, sensor self-check)  
                └──────┬──────┘  
                       │ init OK  
                       ▼  
                ┌─────────────┐  
        ┌──────▶│  MONITORING │◀───────────┐  
        │       └──────┬──────┘            │  
        │              │ reading crosses    │ manual RESET (node button)  
        │              │ warning threshold  │  OR dashboard override (FR-DASH-5)  
        │              ▼                    │  
        │       ┌─────────────┐             │  
        │       │   WARNING   │             │  
        │       │ (yellow LED)│             │  
        │       └──────┬──────┘             │  
        │              │ crosses alarm       │  
        │              │ threshold           │  
        │              ▼                    │  
        │       ┌─────────────┐             │  
        └───────│    ALARM    │─────────────┘  
   value back    │ (red LED \+ │  
   in safe range │  buzzer,   │  
   (WARNING/     │  latched)  │  
   non-latched   └─────────────┘  
   sensors only)

Security sub-state (independent of environmental FSM, gates FR-MOT-\*):

\[DISARMED\] \--(closing time / toggle)--\> \[ARMED\] \--(motion detected)--\> \[INTRUSION\_ALARM\]  
    ▲                                                                          │  
    └── (opening time / toggle / node reset / dashboard override) ────────────┘

**Notes:**

* Environmental sensors (temp/humidity/light) use **WARNING → ALARM → back to MONITORING** (self-clearing, since drift is gradual and reversible).  
* Water and Motion/Intrusion use a **latched ALARM** — requires either the physical node reset **or** an agent's dashboard override to clear.  
* With fire/smoke detection removed, there is **no single "highest priority" alarm class** anymore — all zone alarms (env/water/motion) are treated as equal priority on the dashboard for MVP (a stretch goal would be to re-introduce severity ranking, see §9).

---

## **6\. External Interface Graph (Sensors ↔ Microcontroller ↔ Windows Dashboard)**

| Sensor | Signal Type | MCU Pin (example) | Voltage | Library / Notes |
| ----- | ----- | ----- | ----- | ----- |
| DHT11 (temp/humidity) | Digital (1-wire) | D2 | 5V | `DHT.h` library, use as-is |
| LDR (photoresistor) light sensor | Analog | A0 | 5V (via voltage-divider w/ resistor) | No library, raw ADC read |
| Water level sensor | Analog | A1 | 5V | No library, raw ADC read, range 0–600 |
| PIR motion sensor | Digital | D4 | 5V | No library, `digitalRead()`, needs \~30–60s warm-up on boot |
| 16x2 LCD | Digital (parallel or I2C) | D7–D12 or I2C (A4/A5) | 5V | `LiquidCrystal.h` or `LiquidCrystal_I2C.h` |
| Buzzer (active) | Digital out | D5 | 5V | `digitalRead`/`tone()` optional |
| LEDs (green/yellow/red) x per zone | Digital out | D6, D8, D9 (example) | 5V (via resistor) | — |
| Reset/Arm-Disarm button | Digital in (pull-up) | D10 | 5V | `INPUT_PULLUP` |
| **USB Serial → Windows PC** | UART over USB | Onboard USB | — | 9600/115200 baud, `pyserial` (Python) or `System.IO.Ports` (C\#/.NET) on the Windows side |

**Data flow (updated):**

\[DHT11\] ─┐  
\[LDR\]    ├──▶ Sensor Read Layer ──▶ Threshold Engine ──▶ FSM ──▶ Actuator Layer ──▶ \[LEDs\]  
\[Water\]  │        (per FR-\*.1)      (per FR-\*.3/.4)                              ├──▶ \[Buzzer\]  
\[PIR\]    ┘                                                                       ├──▶ \[LCD\]  
                                                                                  └──▶ \[USB Serial TX\]  
                                                                                            │  
                                                                                            ▼  
                                                                      ┌───────────────────────────┐  
                                                                      │   Windows Dashboard App    │  
                                                                      │  \- Parses serial lines      │  
                                                                      │  \- Renders per-zone panel   │  
                                                                      │  \- Agent login gate          │  
                                                                      │  \- Sends CMD,...,RESET back  │──▶ \[USB Serial RX on MCU\]  
                                                                      │    over serial on override   │  
                                                                      └───────────────────────────┘

---

## **7\. Non-Functional Requirements**

* **Performance:** Sensor loop shall complete a full cycle (all zones) in **\< 1 second**. Dashboard shall reflect a new sensor reading within **≤ 1 second** of it being sent over serial.  
* **Reliability:** A single failed/disconnected sensor shall not crash or freeze the whole loop (isolate reads in guard logic, per FR-ENV-6). A dropped serial connection shall not crash the dashboard (FR-DASH-7).  
* **Usability:** Alert states must be understandable without documentation — color-coded LEDs/panels (green/yellow/red); the dashboard's "Acknowledge" action must be impossible to trigger accidentally (require login \+ explicit click, not a single misclick).  
* **Power:** All sensors run on 5V, compatible with a single USB-powered Arduino/Pico per zone; the same USB cable also carries the serial data link to the Windows PC.  
* **Security/Privacy:** No cameras, no personal data collected. The login for the dashboard is a basic MVP gate (single shared credential), not a hardened auth system — explicitly noted as a limitation, not a real security control.  
* **Scalability (documented, not built):** Architecture should allow adding more zones (duplicate node pattern) and more serial ports/dashboard panels, or later a proper multi-user login and persistent alarm history — explicitly Out-of-Scope for MVP but noted for judges.

---

## **8\. Technical Constraints & Assumptions**

* **Microcontroller:** Arduino Uno/Nano **or** Raspberry Pi Pico (Pico uses GPIO numbers instead of D-pins — adjust pin table accordingly). Either works fine over USB serial to Windows.  
* **Windows Dashboard:** Any stack the team is fastest in — e.g., a simple Python (`pyserial` \+ `tkinter`/`PyQt`) app, or a C\#/.NET WinForms app using `System.IO.Ports`. No external dependencies beyond serial \+ basic GUI framework, to keep setup time low.  
* **Assumption:** Hardware fire/smoke sensor is **not available** for this build — explicitly out of scope for v0.2. The architecture (FSM \+ serial protocol) is designed so a flame sensor could be re-added later as another `ZONE,SENSOR,VALUE,STATE` line without redesigning the dashboard.  
* **Assumption:** Demo is a **tabletop mock-up** (small model room/basement) next to the laptop running the dashboard, not an actual museum installation — thresholds are illustrative, not conservation-lab-certified.  
* **Assumption:** "Open/closed hours" for the security FSM is simulated via a manual switch, or a button/toggle on the dashboard sending an ARM/DISARM command over serial.  
* **Assumption:** Each zone (Gallery, Basement) gets its own MCU \+ breadboard; both MCUs connect to the **same Windows laptop** via two USB ports (two COM ports), read by the same dashboard app.  
* **Dependencies:** DHT sensor library, (optional) LiquidCrystal\_I2C library on the Arduino side; `pyserial` or `System.IO.Ports` on the Windows side — install before hackathon starts to save setup time.

---

## **9\. Sensor Placement in a Real Museum (target deployment map)**

| Zone | Sensors Present | Why There |
| ----- | ----- | ----- |
| **Exhibition Hall — next to painting/statue** | DHT11 (temp/humidity), LDR (light) | Direct environmental risk to the artifact itself; local LCD readout for staff, plus streamed to dashboard |
| **Exhibition Hall — room-wide** | PIR motion | Detect intruders after closing; mounted at entrance/corner with wide field of view |
| **Basement / Storage** | Water level sensor | Flooding/pipe-burst risk to stored artifacts; mount near floor level or in a sump area |
| **Security office / front desk** | Windows PC running the dashboard | Central point where an agent watches all zones and can override/clear alarms |
| *(Future, not in MVP)* | Flame/smoke sensor — basement and exhibition hall | Fire risk near storage and lighting rigs; the serial protocol already reserves room for a `FIRE` sensor line so this can be bolted on later without redesign |

---

## **10\. Acceptance Criteria (Definition of Done for the 10h Demo)**

1. ✅ LCD near the mock painting displays live, updating temperature and humidity values.  
2. ✅ Covering the LDR (simulating a spotlight/flash) triggers the light-warning LED within 1–2 seconds, and the dashboard panel turns yellow/red to match.  
3. ✅ Pouring/dripping water onto the basement sensor triggers the flood alarm (red LED \+ buzzer at the node, red panel \+ alert on the dashboard) and it **stays on** until cleared.  
4. ✅ With the system ARMED, waving a hand in front of the PIR triggers the intrusion buzzer and a dashboard alert; with the system DISARMED, the same motion produces no alarm (only a log line).  
5. ✅ The dashboard shows live per-zone values updating in near real time as sensors change.  
6. ✅ Without logging in, the "Acknowledge/Override" control is disabled or hidden on the dashboard.  
7. ✅ After logging in, clicking "Acknowledge" on an active alarm clears it both on the dashboard **and** at the physical node (LED/buzzer turn off).  
8. ✅ Unplugging one MCU's USB cable mid-demo shows that zone as "disconnected" on the dashboard, without freezing or crashing the rest of the app.  
9. ✅ No single disconnected/faulty sensor freezes the other sensors' readings on that node.  
10. ✅ All 4 sensor types (temp/humidity, light, water, motion) plus the dashboard \+ override flow are wired, working, and demoable within the mock museum layout at the end of 10 hours.

---

## **11\. Suggested 10-Hour / 5-Person Build Plan**

| Time | Task | Owner(s) |
| ----- | ----- | ----- |
| 0:00–0:30 | Kickoff, assign zones, confirm parts inventory, install libraries (Arduino \+ Windows-side serial lib) | All |
| 0:30–2:00 | Wire \+ code DHT11 \+ LCD (Zone: Gallery-Env) | Person A |
| 0:30–2:00 | Wire \+ code LDR light sensor \+ thresholds | Person B |
| 0:30–2:00 | Wire \+ code Water sensor \+ latched alarm (Zone: Basement) | Person C |
| 0:30–2:00 | Wire \+ code PIR \+ arm/disarm switch | Person D |
| 0:30–2:30 | Build skeleton Windows dashboard app: open serial port, parse `ZONE,SENSOR,VALUE,STATE,TIMESTAMP` lines, render placeholder panel | Person E |
| 2:00–4:00 | Individual unit testing per sensor against thresholds | Persons A–D |
| 2:30–4:30 | Dashboard: live per-zone panel with color states \+ event log | Person E |
| 4:00–5:30 | Integrate FSM logic (non-blocking `millis()` loop, define `CMD,...,RESET` serial protocol both directions) | 2 people |
| 4:30–6:00 | Dashboard: login gate \+ "Acknowledge/Override" button wired to send `CMD` back over serial | Person E \+ 1 helper |
| 5:30–6:30 | Build mock museum layout (cardboard room \+ basement box) and mount sensors near the demo laptop | 2 people |
| 6:30–7:30 | Wire up second MCU's COM port in dashboard (2-zone support), polish LCD \+ dashboard messages | 1–2 people |
| 7:30–9:00 | Full integration test, run through all 10 acceptance criteria (incl. unplug test) | All |
| 9:00–10:00 | Buffer, bug fixes, prepare demo script/pitch | All |

---

*End of document — v0.2.*

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAloAAAFJCAYAAABD8YNCAABNEElEQVR4Xu3dCbxW0/oH8JMoEg2GruR/i8hRXRVFpChxSzJUhnM7Shm7RGUsFQ0Xp6MuMg8JScl0OGZKGTNGuMTBFUJKFHLT+p9n7WmtZ+/9jnu/77vf/ft+PrvOWXu/+33PO+z9e9dae60SAQAAAAChKOEFAAAAABAMBC0AAACAkCBoAQAAAIQEQQsAAAAgJAhaAAAAACFB0AIAAAAICYIWAAAAQEgQtAAAAABCgqAFAAAAEBIELQAAAICQIGgBAAAAhARBCwAAACAkCFoAAAAAIUHQAgAAAAgJghYAAABASBC0AAAAAEKCoAUAAAAQEgQtAAAAgJAgaAEAAACEBEELAAAAICQIWgAAAAAhQdACAAAACAmCFgAAAEBIELQAAAAAQoKgBQAAABASBC0AAACAkCBoAQAAAIQEQQsAAAAgJAhaAAAAACFB0AIAAAAICYIWZKykpETMmjULS0wWer2ffvpp/jYAAIAEELQgYzjxxsfq1avxegMAZABBCzKGE298IGgBAGQGQQsyhhNvfCBoAQBkBkELMoYTb3wgaAEAZAZBCzKGE298IGgBAGQGQQsyhhNvfCBowdixY7HEbIFgIGhBxnDijQ8ELahTp45o3749lpgs9HpDMBC0IGM48cYHghbQiffee+/lxVCkELSCg6AFGcOJNz4QtABBK14QtIKDoAUZy82Jt7r2fkpF5QpeHqQaUdmuMD8KNRWlvCgvELQAQSteELSCU5hnF4iEnJx4q8pEWW0IKimv5msCVKBBa0WlKC0pjMeFoAUIWvGCoBWcwjiKQyTl4sRbXV4ia3VKSspEeFELQSsZBC1A0IoXBK3gFMZRHCIp7BOvFbCsIKTXatWIknaVtf+aakNJWZVRTtu6y4392U2QWohRg1a1KFPCDQU9+16rylw1a2qzJu2vtMK4Z9qHtc74O/jv1u2M+7P2S/dn/M3CFbSs27nXGY8/zOZVBC1A0IoXBK3gIGhBxsI98erhSgsZpDZoeAYLGUC8+jXpAYrQPs2920HLCXeWajs8UdDS7lMJcUSteVPDkxWK7P2Yv9Nt3bV1yuPUwpRRbu9DeD/+sCBoAYJWvCBoBSfcozMUtVBPvEoYMehByQkZOndQMlFtFA9gdlizgopXzZlwfq9izZcewct6zHooMh67/bco23ndH9VqqdtJ5uPn96c//vAgaAGCVrwgaAUn3KMzFLUwT7y89kZSgk0gQcuWOGjZUgpaRhjKJmjZkgUtG4IWhA9BK14QtIIT7tEZilqYJ17vUFGt1S651wv/QKU1w5ns4OQEFdlHql2lslGN1nSoRaIkTYepBC3r/pQGQSc0qY/ZVcMnPB9/WBC0IJCgZb6PjT6LxuL6QuVDfr7Mzwq9363bUbn2uVDJ40F6F9K4m/MV5v6y5XnsSgc9j2q3Cu0YEgwEreCEe3SGohbeiZd1dFc4B0C+jdWXinWGt8uNA5JzgFObIv07w2s1ZzxoicSd4VMJWtY6vS9aCp3hfR9/OBC0IMigpVI/N6lSg5brC0iWQg9afl8S06DWhCNoFb5wj85Q1HDijQ8ELQgraMlaXb/QoDSZe9ZoyfVm7ZhXE7xSo2XcptoIKbS9Tzixglal/J+2VUKXErSsx2PjAar2b+WPzdi3XpNnXGlsLDwweq+jQZyt8jL7cVTb+/ZqDUgfglZwELQgYzjxxgeCFoQVtEqVIJN20JK3dwcUGwtadmAxH4dXTZodhswQpQ25kmrQ0v5OVsuuBbIa+/ERPVD5r3PVaNHjNX+X63xCZDoQtIKDoAUZw4k3PhC0IMig5dTI6DUwoQctpdbL3R/TYDXRe3YzSDFoufat9udUgxarBdP6bCZY5w5avNYt+1otBK3gIGhBxnDijQ8ELQgyaGl8wlSidZkGLbUGyxWGTK7HIIxtpZSCltnvki32fSsBivah1Tyxv9dvnSto+Txn2UDQCg6CFmQMJ974QNCCKAQtNdhYtULZBy3lYpM0gpZXs6TEgpZTx2assx5vonUIWtGCoAUZw4k3PhC0INyg5YQLtRnM+D31oOWSadBSm+ISNR2aP1u/G+HGazy+6nCbDhG0ChqCFmQMJ974QNCCIIOWZ5OayQgwtK427MjtEwct+8o8j9CUcdBqp1zF5woxerhSH6sWbtSrDrX7oU7uTlBSryzk4ch3nXwcVF6KoBUBCFqQMZx44wNBCwIJWhAZCFrBQdCCjOHEGx8IWvG0adMmUVlp1MYgaMULglZwELQgYzjxxgeCVvwsWbJE7LXXXvJ1Jwha8YKgFRwELcgYTrzxgaAVD5s3bxY33nij2G677ey+QQha8YSgFRwELcgYHYCnTp0ay2XixImusmJfELSK39/+9jex5ZZbaiFrm222kesQtOIFQSs4CFqQsZYtW8ZyoRNPo0aNXOVBLS1atHCVFcqCoFWc1q1bJ8466yyx1VZbaSGLlr/+9a9yGwSteEHQCg6CFkAG2rZtK8rKnMu8g9S9e3cxYMAAsXbtWr4KIHAUnq6++mpx3nnnia5du4qdd97ZDllbbLGF/T5H0IoXBK3gIGgBZOD++++3+64ErXfv3rL5hk54ixYt4qsBQnX44YeLjh07yvd3vXr1xOjRo2U5gla8IGgFJ5wzBUAMHHnkkbwoEP369ZMnOTrQ0fLHH3/wTQBCMXPmTPneW7x4sQz71JR4zTXXyHUIWvGCoBUcBC2ALOyxxx68KGsnn3yy1keGmm/ohEdXgwGEid7PVrB/8MEH5ftv4cKF8ncErXhB0AoOghZAFuhgNGXKFF6claFDh7o6JFsLNSsChGHBggVi/vz5Wtlhhx0mPvroI/kzgla8IGgFB0ELIAsTJkwQ9evXF19//TVflbEzzzzTbjqk2qwuXbrITsrdunUTPXr0ECtXruQ3AcgKjQDfunVrXiw+/fRTeUUisYLWxo0bscRgQdAKDoIWQJZuvfXWQDvGU+dj2t/s2bPFAw88YDfdQLUoS/I8uybYLVjG31JWxctz76WXXpLvt+uuu46vsg0ZMkTstNNOYu7cubLmC0s8FghG4qMWAKSEapyCcvHFF4vjjz/e/j2sTvfRg6AVBqop7dmzJy/WUBCjkAUA6Ut81AKAlDzxxBOy83AQqDlSHUOLTnKPPvqoskVcGeGkVOmzZq8pN35Wg5b8mbYr10MN/U7by3UslDn94cpc6wy1+6qotB+DHpRqlNuX1G7pUMsN6mMyfi4pKRW0j8p2ar+8Mns/9t9TW1apBUr1Ns72oqrM2U+5+mh0tH7p0qW8WHPCCSfwIgBIEYIWQEBo7KEgTJ48Wfu9f//+4qCDDtLK4skIJGqQqFxhrvEIWhRcrPVa0FJ+lsGtwoxTyv5kSPEJWup+1Z+tx2D+5oSb2n05gazavD8naMmQZW4rA6AdiswARr/L0GTelxWgzMen/g1GGDPCVqnP36+iPlhjx47lxZpLL71UfPbZZ7wYAFKEoAUQkPPPP1/2Y/nll1/4qqwNHjxYtG/fnhfHDG86rLbDgxa0zFoctQ6H12hZnGDD9y18g5YaWHhTpXr/xn6N2iY3qxZLCXoKvh8elPRAadVmOQvtU60Z80Id2/3WWXr16iWbFgEgc4k/ZQCQsjVr1sg5EC+66CK+Kmvvv/++PCnedNNNfFWM8DDkF7SoJqdGC1S5CFpGc6TTdJdS0CrXa8jsJs0SY9ob6/ElDFqej1Nh1YApf/f69evlnJrDhg1TNtRZg5cuWbKErwKANHgdAQAgQ5WVlUlrCTJ19tln2xP8xhMPQz5BS6npUZsIEwctdyDyDjBW05/5m29Qc4Ke3qRoccKTrHlSmgGdQGXWStXuh/533a/9dyr9svzIsOVsd84554imTZuK77//XttM1bBhQ3v6HQDInNcRAACyQPMgPvvss7w4EOPHjxcbNmzgxTHBw0zioGXXGtX+njxometkbZJRo+QXtNTO8HafLrLCCNlW7ZFWu2Xv13r8ei2V1VRI+7A7+9fuw+pzpW7j7gxv/p3mwvcpF+Vv2X///UXfvn3N37w99NBDYt68ebwYADKAoAUQgu7du/MiiBg1gDn0psN8kSHK8/ElR8Hrvffe48W2zZs3i7322osXA0CGELQAQkAns1mzZvFiKFis6XBFpU+gyk/QspoQJbPWK5PHsXz5cjFp0iRerKFx3Gi2AwAIBoIWQAi++OKLUOZBDIPV3AbF7fbbb1eaLr3R3IaojQUIVuJPHQBkzJoHsdAhaBW/1atXix133FGMGDGCr9JQEHv55Zd5MQBkAUELICQ0Ue9uu+3Gi03Ugdnp3EyNQuq4R2rvG7W8tMLdAdyi9tnx2xcfLVztMK117Iaictppp4nmzZuLn3/+ma+y/fe//xUXXHABLwaALCFoAYSsX79+vEi4rqCrDUDqFW725fxV7NJ9pe+Qb9BKsC9jmhcdarSKnzp3pheaQDhZsyIAZAafLICQ0QnMPQ+iHrS0S/Ht2qsaWa4PMVCTNGj57csel8mszbIgaGUqs6v+cu2yyy4Tt938Ai+2Uc1r69atRVmZMYwEAAQLQQsgZIMGDRIdOnRgpXrQotDkHrNJuGqnUglavvuyKM2HBEErE3xMr8L05ptvKkHb24UXXigaNGggmw4BIHiFf6QAKAKjRo1i8yDyE7UyCbGgCYGVATaVwSYpRKkDUmqTINu399kXazq0g5o5angUyL/ZrJWT4YEN8KnSBvG0p7nRh2fQR2I3ah/VEGqoUcrp+VMGCPUcy0qdZ1B5jXweq5z8ucpZZz0e47E596WFJSUs+5WXdDlb/v/PVubvngOwCnHooYfyIgAIEIIWQA6450HkQYsFA+XkL0cvt9aVl3kHg3I9XPnti48WbtBHKS9k9Pj1v98JMtpYU0KdKkedT9A/aNG+nWfQub1ac+g05bpfP4MZsszn1ni+y+wAZNyXGZ7MxyoDlhmCrO1pjfEamn30zJBMf4O6DaHtrMeqvt5b1v7ctPtw2qtvjdaMGTPEq6++yosBIEBeRwoACME111wjT4TZyc+AmYVCD0NCDxCyxsgJI2q0SB60POY6lGHGXW7wCVrKY1DxqX7UuQe1wUeV26sBSg3D9Hi094CyL/U+dt99d/HHH38Iv6BFY71tvfXWvBgAAuZxpACAsLRt25YXpQlBy4kMapOetRghhfdfS950qDQH2otam+Ts2+ATtJTQo+KTQhu3N/anBTMWtJzH6gQt9+O0HqsTqOgqwvnz55u39Q5aJ598MqbaAcgBjyMFAITpkksu4UWQIlfQ8uwjJVzDYjhhRg9aTm2ST3BysUKLz/YZ1WilH7S8ghOh+6CxsKhzu0MPWlTLRbVdgwcPVrYBgLB4HCkAIExUi/DOO+/w4qxNnTpVvPDCC7y4qLibBPU+Vk5tkhrCqObLCjM1Wqdwfns1IBnbuedAtPbj3aRo9tGy7tsMTon7aKUXtIy/07mNDHHm31RS0lLez3XXXaeFOzXkjRkzRjRs2FCsXLnSLgOA8HgdKQAgRMOHD5c1CkGjyYLr1asnVq1axVcVDR60tKvsWJOdNqK+EkzUpjc9zBjBy1qc+6HO9E65RQYezyv5MrjqMI2gRYywZe5LeQzd9tnJKVfuwygz+3HV/nz99dfb6wAgXAhaAHkwceLEUOZBpKvI1DAABq/mvGLz6aefirFjx/JiDV2QsXTpUl4MACHCERkgDxLPg5idPffckxfFXhyC1sCBA3mRpqamRtZ4AkBuIWgB5MmcOXPE22+/zYuzdvvtt4u33nqLF0MRu/fee5PWZJ5wwgli77335sUAELLEn0wAiCQ66S5atIgXQxE655xzRNOmTcX333/PV9latmwphgwZwosBIAcQtADyyHd4ggxUV1ldoqvFzu16iD59+mjroThRqL711lt5sWb77bcX33zzDS8GgBxA0ALIo+CClj5W0pNPPilPwI899piyDRSjvn378iLNiy++KG644QZeDAA5gqAFkIg2fID6cfG5hF/dXglR6nyF2lhN2mX+HvdD4zZZl/LbYyU52xnhSnkschtjUM6XXnpJ29bZ3hmawFkXjUmlwbF8+XL9veJh2rRpSbcBgHDhEwjgxxps0uQMaJn6xMEUbPTJjikoOcHMLq+9rRPAlME2ax+DVutlD5hpUAfi1ObFM8db6t9xe9c4TsQah8ngN/gmFLJ+/fqJTp068WIbDfdQt25dMW7cOL4KAHIIR1eAVFkhJ9VpVkylbCBNrxG7+dx89v5r70sdUJNzHodX0KoRY1qXiFtuucXe3hrw0w6HrByiga4spaD8zDPP8FU2Gu5hn3324cUAkGMIWgBJqCOJy1CT8sTBBt58JxctaKnNkNbiBC0e6OwpXNTtPIOWsV2rVq3sW9L+5D2aTYcWBK3oWL16tdhxxx3FiBEj+CoNvT+qqhKkdADICQQtAB88jNjNe2nWaGl9uBg1aHliQYsHosRBy9gvTTJMJ+YNGzboNVoIWpFEAeruu+/mxZqRI0cW9VRMAFHic3QHAK15zezfZIUa/4mDnVBlBS+rP5cVZKy+W0Tto6XPuWfWmHkELTvKUf8tr/5eSh8t2v6KpT+IBg0aiAnn9Nb7aCFoRdLxxx/PizQLFy6UYQwACgM+jQAJOFcLUqCpVmqN0rnqUG8aVJsX9U7yzjZqmOK1YWrzohbaZBkFNCdo6duXiD0nGPPcIWhF02WXXSY++eQTXqw58MADxZFHHsmLASBPELQAYmL69OkybEE0HX744eKggw7ixZo6deqI8ePH82IAyCMcdQFipHXr1rwIImDmzJkyJC9evJiv0rRv354XAUCeIWgBxAgNCxDGRNYQroYNG4rRo0fzYs0999wjHn/8cV4MAHmGoAVQoAYNGiQ6dOjAi7NGNSM0LQtEw4IFC8T8+fN5scaaWBoACg+CFkCBeu+990LpU9WjR4+k8+NBYdi0aVPS5t7nn39evk+STSwNAPkR/FEcAAIzatQo8fPPP/PirDzxxBPyxIxmpsJHY6DR0ByJdOnSRfTp04cXA0CBQNACKHAUij766CNenJUlS5aEUlsGwenWrZvo2bMnL9bQ+2LixIm8GAAKCI60AAWubdu2oqzMmZcwKCeffDIvggJCQXjpUmPcMz/HHnssLwKAAoOgBVDg7r//fnnSffbZZ/mqrLz77rvahNNQOD799FMxduxYXqyZPXs2aiUBIgCfUoAIoJG+u3fvzouztvvuu/MiKAADBw7kRZp169aJXXbZRZx++ul8FQAUGAQtgIgYPnx44MFozJgxYqeddhK//vorXwV5sH79etGiRQsxbNgwvspGNZtUk0VjogFA4UPQAoiIL774QmyxxRa8OCs//PCD2GabbdChukBY42F9//33fJVtv/32E0cddRQvBoAChaAFECEUiFauXMmLs3L55ZeLrbfemhdDHqQyHhZtQ2OsAUA0IGgBRAydaF9//XVenBWacJo6YEP+TJkyJWmA6t+/Py8CgAKHoAUQMV27dhX9+vXjxVlDx+r8Wb58edIrCO+8886k2wBA4cGnFiBirJHdH3zwQb4qK7TPd955hxdDDlBw7tSpEy+2rV27VjRr1kyceeaZfBUAFDgELYAICmMeRGu8rsWLF/NVEKIdd9xRjBgxghdr6HWhGi0AiJ5gj9QAkDNhzINIY3Vhwuncat68edLX8eijj+ZFABARCFoAEbVmzRpx4YUX8uKsVFdXB15TBv5oYu+7776bF2smTZokPvjgA14MABGBIypAhLVr1y7weRCp6XDu3Lm8GAJ22WWXJR0XjcbLonGzAldVVhuoy0Q1LweAwCFoAURYWPMgdujQgRdBgN588035ulVUVPBVNhr5nbZ55pln+KrsIWgB5AyCFkDEhTEPYioDZ0IaZLApMZbyanH44YeLgw46SK6yy0tK7c2ry0tEo62t8hJRY5bXVJSK6trFuY1am1mTQnmp/lho37S/dpXmfdSIynbOPqwgVlb7e1lVtfyf1pVWWI8IAJJB0AIoAjQPYpA+++wzeUK95ppr+CrIAIUrS8OGDcXo0aOFWFEpSpVwRSHHCjBX9CwR0+66y15j3V4GLbvU+F3egsJTbVhS1hj7ct2HSanRUoOWXstlBKuyKiNoqeHKKgeA5BC0AIoAzYM4efJkXpwVCgM777yz+O233/gqSIsToAhNDP7HH3/YYUdlBapWTfRDsxq01Lok63cZlpRaKrvWyeM+JL+gZddsGahmjfbDgxX/HQD8IWgBFIl69eoFOg8iTWxMcyDSXIiQDSdoLViwQMyfP98o9ghBFKjo+aagxMuJX9CiQKTXaJk87kMtTxy0jGZEBC2A7CBoARSJ//u//wt85HBMOB0MCkqbNm0SrVu3dgpdzXo1YvdRxqj/QzqmF7SMGi2PQOW6D5Nf0ErQdIigBZAZBC2AIhLGPIjUT4v6bEHmXrq6t9Osp/TXImpHdfr/+eeflzVU2jZJgpbBGAPNWpSttPuwyqxO72rQUsvdneHNXzx+BwB/CFoARcSaBzFomHA6O926dRM9e/bkxZoffvhBnHPOObwYACIu+CMyAOTVoEGDeFHWKLxhwunM0fO3dOlSXqyhK0d/+eUXXgwAEYegBVCEaKJidf68ZcuWiSOOOELZIj00UjyFhWQTTi9fvlw88MAD4pRTTpHjRP3lL3+xm6223HJLseuuu8oxpE444QRZSzZx4kQ5aOd1110n7rjjDjFr1ixx1113yf9vvPFGMWPGDHHllVeK8847T5x66qniuOOOE/vss4/8+6z91qlTR17Jd/bZZ8vtn3zySfHll1/yh5Y3AwcO5EUu7du3F8cffzwvBoAigKAFUIQaN25sz4P4+++/iz333DPrqVwOOeQQOSWM6o033hA33XSTOO2008RWW21lh58+ffqIc889V0yfPl089NBDYtWqVdrtgkBDJCxZskTMmTNHTJkyRQ7aqgY7aqobM2ZMXqcTuvfee5M25U6YMEGGxY8//pivAoAikPgIAACRRB3Y6QT/4YcfyrBBP2tXvGWAJkCm5i3qrE01Ub169ZL7pVBHoWb27NnirbfeksEun6iv06JFi2T4o3BJIaZ58+aySZVqznJl/fr1okWLFmLYsGF8lYaew6uuuooXA0CRQNACKFLWPIjUZEf/b7/99nyTpGhOPpr8mG7frFkzMXjw4IJqlsvEtGnT5LRFNKFz7969xcyZMwMdf8xCz1myaYxuvvlmsXDhQl6cgHrNYQJV+pWNAJA/CFoARYICBPVjOvroo8UBBxwg9t9/f7HNNtvYTWnUtJcqaoqjfkN0u9LS0qR9s6Lo119/FUOHDhVNmzaVfyeFLyoLSt++fXmR5rvvvhNNmjThxQkYQy8k5TdIKQDkRQqfWgCIgjVr1oh//OMfon79+na44sv//vc/fjMN1YJRQGjVqpW46KKLZB+sOHj00UdFeXm5HJz1jDPOEC+//DLfJC0UVN977z1erKFQvNtuu/HiBBC0AKIohU8tAEQNXdVHwYr6J6lBizf70e80pyE1L06aNEl888032vq4eu211+TzRRcRXH/99Xx1QjRgbKdOnXixpm3btomvRqxSRmhfUSkqV9APetCS0+7Yg58ao7hLStCyBiO12AOcKiPDW6PHG/cBmaBQTe+XqVOnYonJkuyLlApBC6BIUS0NNU2pQYs6x1u+/fZbWdauXbukfYni6OuvvxaXXnqp2HbbbWU/rlTcfvvt8jl95pln7DKqRbztttvs38eNGyfq1q0rVqzwTzYUiNy9rBLXaNmjyacQtKwpe9z3AZmwghbEA73eCFoAINHE0GrQsgbNpKYtamKk8aogsZ9++kk+VxRI582bx1draHyvESNGaGXU0b5hw4Zi7dq18nd6HWjssMSc6XSsCan9gpb6+kopBC2rBkzfP2QKQSteELQAQEPjSNEVh3QioKEZ2rRpIwPBtddeyzcFH1T7R9Pj0HP4/vvv89U2GkZCHSiW0JAX1IRLQ2MQGsg1VUbNkxWGPJoOa9fZjYdp1Gip3IEO0oWgFS8IWgDgMn/+fDk8Q4cOHfgqSNMNN9wgr+akccRSQc2GdBKmsEVDStBwDrS88sor4qOPPvK8QEFvOqyxQ5Az2bRRI6WW2yd6s8+VJEOXWl7i0XRoBDgErcwhaMULghYAaGiEeDoJXHDBBXwVZIj6V9FwEDTyezJ0kYFVa2QFLvX3//znP/wmkrqNzdWJ3dymvFoJZ3pwsmrFqGarWqnRssKZdXvIHIJWvCBoAYDtxx9/FI0aNZLzD0Lw6ORKA7omQnMwqqGJFqoR22OPPVIKalAoakR1lRFTq6qqxKZNm+w1CFrxgqAFAHJEd5rAmc9NCMGjwVxpjsVjjz2Wr5I6duxoBywaRoP6bEH0qLWE1utJTcHUHG/VWkI8IGgBgDzx09x+kBvLli0Tf/3rX3mxtMsuu4h69erJKw9pAm5InWz2LK/U+5CtqPRp8nSu1CyrqjbHBTP6spVVOdvY440Rsw8bLfzqTqPcGl+sxrnPdsr9mwsN8ougFR8IWhBZ+gExRbUHVOdQW/tzurfPSmqdh3Pd+4WGEzjmmGN4MYSMwtYpp5zCi+XUR1ROQ21Aeqz+ZfZxQQYjs6O/dhWmGqCMn5MFLeuCAF6uDgRrXbVJn3SvGi3qb0dX8qLpMF4QtCCy0g5aasdgkcHts+I9ppGLOsJ3DowcOVLssMMOvBhy5K677pIn3AULFsjfae5Er6sKITVq0NFrmpyFApU+Sj5JVqPljCOmLnIPSi2XOlq+GrT+/ve/i5oa54tW/oKWUtMmFyuEGryeL/44tYsiShIdQ83nTBkuxGG+Np7rkqh9vlOZlcB5H+QfghZEljwgVjhXUjkfeH6ANcKLfnBwmg2MA656GzWMlYrKCutAWqYdnPWDukO9b3UqFFmmnATUx8MP2PS3JBrTyL4yrCTzy+wffPBBeXt0fM8vGm+Lmgshc+vWrROrV69mn0l9SAuV0cSYRtAyr9j0DxXE+kwbzYeJhsDIS9BSh+4w0fOgPkZ5nOJXlNbeTj228mMePS/ef6f5/Ldzj8WmXtmaNgQtgNwxvmGaochsInB/WzW/VdHvCWq01AOyOmaQ9Y3M+sCqt/c7kKoHKv7t2uKMbyR/c26j1Gj5Bi1lgEltDKQ00bx8NCEy5BddjUavBfhbtWqVePfdd8WTTz4p/vWvf8maWOpT2Lp1a9mXjU7adGWfZ40WDw5E/QwRe35IFrTMgJUotOmcoTL8jg8k50ErQVDkxzSv58sus58nh3q81JnPWbk7GJXVbl9Gx2kELU85fGcAJCZrm5QPnFcwsWuNkgQttXZJrSnSv93qIc7vg+zsQw1A7qZD1+MjqQQtKzyajzETv/32m5g8eTIvhjyiib2LFU1LRIOt0sCr06dPl2O1lZeXy2mKqOla/dzRrAQ9evQQJ510khg1apS4+uqr5VyQNML+Dz/8wHet0YOWSakp1sIV1c5YnyMtDDifL6r5ljVa1i3Uz6z92dSbFfX+Yfw+DbkOWolCn8o7aNVoX1xTP+444ZTvk54jeSy1nkOtts04Vtr3oNaomYHReq2cY6LBuRhBPz7TdvbrS/tI6fEHJ69Bi6p66eoaLPFZnn76af42yJhf0HL6EBgHODscJQpa/OBs4kHL+KDTPpzRt71ZzYXOVUi8Rkt9LOkFLWW9eXBP13XXXSebW4LDm2s9TjzC+ru912kDaiqLdohWTpr8+fcMri7+j7PG81s/nYz191nqtRvpocfw8ccf8+LIeOedd8QTTzwh7rzzTnHuueeKgQMHim7dusnxv9TnmWYc2HfffWW/JZqEm96LNBMBDeq6fv16vtvc8KipCVOug1aq71evoEWfK/UzoYZKWvw+aernxDhmOuX0sxO0PGoea18P4z69v6CmF7T0sCzXedbAhSfvQYteKJqoFkvxL/RaBxu0PE7i5byPhfIhThS0fD54/D6s/VHfsFQOzM43SfWAwT/4yje+BEGL/j6vQyU/2KTigAMO4EVZ8jhYurD+HWawsU8AnkFHf23U9bxviHqQlScDz8eS6HF6BChzaACtTL6PePjKXosWLcTll1/OiwsC1YB+/vnnchogmlJo/Pjx4rTTThP77befHH+NxoeyTrw0ofaBBx4ojjvuODn4Ko0Z9dhjj4k33nhDXuFakEIOWt98840MonT8q6ysFEOHDs1v0NJq+Zx13l9CfLomqPtI8nlSj6N0vJJr7aDl8bmzj4n8WCm0pkN+7PMMWubnVUXdLcJ8vbmCCFoQD6EELbszPKsaVg4ARk0H1W45tRn0obZrQJQPu3XgsA4K7qAllH4b3rz2I6lBzzyBW4/RCRNGc4Z10FEfY1DToVDorVu3Li/OUqIAY1IOkJ58gpb7IGywDtTuNcLcl9fBNMnjNF8ji+xLpwX0JLfPwiOPPCJfz++++46vCgSd7N9++21xxx13iClTpshO+AcffLDYfffdRYMGDZz3U+1Cg6b26dNHDBs2TFx//fXygoklS5aITz/9lO+26NFsCYsWLRLz5s2TzwX1a6TBZrt27Wr3D7MWeh5btmwpv8hQEB07dqz497//LYd0WL58uT1kR65rtBJ9VtTPV0bvbZ/PrRagrM+Q2SIg1yYJWsbv4QStXEPQgpyh1zrIoJU35kk8qqhZp0uXLrw4S6kEkCT9O3wO2F5licqJFa7djybJ49RCtHWQV2tJeY1pcCgIZfMZoeEDXn75ZXk1KU3zM3z4cDnSf/PmzbX5ErfeemvRqlUrGRRGjBgh++rRRNY0OwDVOP35559810Xr66+/ljVNTz31lJg2bZrsO0ZjmFGzJtXU0ZhmapBq0qSJ6N69u+yI/89//lPcfPPN4uGHH5bPOzV9pirXQcvvs0XSCVqeteq+X2rUAGX+3K7U3n9QTYfqo/UMWh5fjL2PDeFB0IKcyeYkUkjkSTzBwSjfkh3wqaZi8ODBvDhL/n2f1GdKre1zHew8TwZUw8cPimbto883dCLXe75GHgd1jXJgtwO1USZPGL4nlWA0btxYNs15WbNmjfjggw/kfIfU/DRmzBjRs2dPsc8++8gAoD7npaWlcl1ZWZkMEPfcc4947rnnZK1KXFB/r88++0y8+uqr4tZbb5W1ePQl49BDD5XP2Y477qg9ZzTEBvUdO+KII+Tngzrh0zhn1O/sq6++Ehs3buR3kbGcBy1iNvW5y5zPV+LPhjBq4tl6uw+sixq0nOOD9fl2gpZgj83Y1v5sV/l3hufrPIOW0MMZPS7fL3shQdCCnKHXOupBywgK/MRfWA4//HBx4oknypHHvVC/mtGjR/PiLCULMIxX/w7zIKqe/GjxOyQmqrXyLid+gZA1F9KWtH/zRGD9bP9vbx0smpaHwhHVMlGNyfHHHy9rn2hSaeuxUu0UhYJOnTrJpr1x48bJJq2XXnpJBosNGzbw3RYlOn/QVYxqkx7NcEA1ddQcqr6+1KRHz6PapHfttdeKF154QYbPZFczBi0vQUviA5bqjyGVzzD//HjVkhn0JkH+edWCFpFBydwvewzO/ZXKcQ3VLzrOujLtSxD/nPr9zbmAoAU5Q6911INWVPTr108+39RJmU48NP6QpXPnzuL8889Xtg5CmkHLolbre9ZoJcL7dlghyn05vSOFx7mCOkbzJkLz97QeX/roCj26Eq+Y/fLLL1pNE4VKtaaJD/dA/QlpImaqaaIhISoqKmRNE72nqabpjz/+4HdR8PIXtCAfELQgZxC0cofGLLJOVNYVYX/729/E5s2bZQijMYqClTzAJOrf4fycKMiw8XjY9lbI8n8EJPnjpG1oXCX9knTj8YfZbEi222472e8nGboK8JJLLuHFBUGtaaKhG6i/GNU00ZWIvKZp2223lTVNtI5qmqh2zqppombSXNc05QqCVrwgaEHOIGjlFjUfbrnllvZJjZqcqMbkyCOPlFeVBSuFAJOsf0fSoGW8h7RgpTQPJA9ZJIXHKcxmBtb0EHaz4Zdffinvl65QS+Shhx4SO+20k7ziLddoHka6cpFqk2bPni0uuOAC2Xmc3lPU6V59v9HStGlT2V+MBmOlqxxpqAfqPE7DRMTxCkYLgla8IGhBztBrTbUq1EQQ9eWQQw6RYYVGtt5rr73kSYY61zZq1Eg2dagnm1QXOklRXxw6OdGgjnTVE10qTicqet6oTw5djk/3T/2wjj76aNmHh05iQ4YMkTUCZ511lhxNm66eoloEfh/02Ghb+hkKy+mnny6beb38/vvvYuLEidpVcOkcuAnVDlEt0f333y9rmqj2qH///rI2iWqV1PeJWtNEj4u2pdvQbWkfdOyGzCFoxQuCFuQMvdZ0NQ+dMKK+0DdzupqLxsiZOXOmHA377rvvFnPnzpXjIVVXV8vau8WLF8u+KDRYI83VRiN/U/8Uqr2gMXXWrl0r+6zQfHdBoiZCOlFal/XTJf0Usuh+CYU1KCzUN4mudONo6AEK8laAp6ZgujpORf2U3nrrLVnTRP2XqKaJ+jNZNU08/NN9qTVN1E+K3rdU00TvTwgXgla8xChoGVdbuJol6OonVzOC2qnW+yolbT/qFVSupgXl9nxdwts5tMEpzUW9PDXRpe5a84o5cJu7j4l7Lqow0ONG02FuUPOS9V6hsEVXsqnDPtx+++1y3CYoHPRaUedu1X//+1/7NVRfz8MOO0yGJApLVAOqHhuoZpRqWylkUbMefSGgZj4KYdTsR81/kF8IWvESm6AlR5D1CRpaJ1qzn4jrSqYEfUsSddB1j1hu/O4aeyRB/xTXZbBC7y8ir7ySnXf531Ztz5COoBUfVANCzzUNukgnVj+0DWovCgMNGEqTJluoRvLZZ58V//jHP2RtlFojRTVaNPFyWCPIQ/gQtOIlJkFLH+HZNViZNX5PuTkQohY6EgQtz1ok/bJwfRtjX677l/jl5Moav6BlhkPjb6p277s2WGmPE0ErFi666CLZXJkM9fkK/upDSBcNREp98vxQ0zT10aPPj9VHi2qtqGkQoglBK17iEbSUuY68QotkN+PxK5e8g5ZXmcTCTCqhTfINQd6PWQ1QVnjkI5bTNgha4IdGCqfXhGpTIH8oMLVp04YXu9AUOTRljlWzlZNjJ4QCQSteYhC0eC2WEXZclFotnXcfLXdYMfAgk0rQMvpgeQUgg1cfLbXmy/n7rJo7s8ar9n4QtCCZ4447zp7sFnJLHksqPb74peDzzz+X0/FA9CBoxUvRBy2jic0dVDxrrUqMWi29+c47HHmhUMNDTCpByzv8OLxqtFRqkKRtrfuhvyPVoOXdnBksBK3CRHPC0US5NAgm5A4N6rnzzjuLn376ia+CImcFrVmzZmGJyVLEQcs72FDtlRqmrDBmBxOt+dBnH4xVK8Ul66PlFc64dIKW7Jcla+eMv0ELWkpnfF1uJtlE0CpcNPUJTUJMoQvCRyOf0yjwNLchTS0TJu++pNmqFtV0DPU9puRGsuOyIZVtcotOuvXq1cMSo6V4g5bvlXw12sFHv8qQd4hPHrQSNf35XXVI/MIZl1bQotDUzumrpQUtvw73K2huN1YWAgStwvX555/LDtc0QCWEi0ZGp07tw4cPF6+//rocHJSuLgxL8EHL5zhSkJzuFABREeg7Nuyg5b6C0GGEqxdliPIKGVa/qORBq1puxxfeJ0yWKwc8+dg8Fq+apfSCFgUa9wzp2l7V8bt87jMMdF+Jgtavv/6acX8VCA69TjfeeCMvhgDQc0uD3HI0yOiUKVN4cSB4rbrz2Vcn31bLnS9/1nHQKqdjpXrs4l8e1WOLdkyqfQzVdjcOfsGRQe6nwrq9/sVVfRxquXVcplYJZ//W32Z+aabFOn6rxz7fYzpAfgWaisIOWlBY6LX2C1rXX3+9HK06Cu+HmqrqgGsICktFRYV8HWiqnnXr1vHVkIGXX35Z7LfffnKMMz/0nKcyoXS6eI22hcKLGVPkl0H7qyGFFvN/5wue+YVR/q7UaClBy+iCYQYkNh6hGrz8vrjKi5HMEKYOX8NbILyu6qbt+Zdbg/I3m4/VVQ5QYAJ9ZyJoxYtX0KKpQ2666Sb7W2avXr209YUm7ImFCwV11KZ5HHfbbTe+CtJEUzbRezvZmGUXX3yx3O7BBx/kq7Jiv19lbY5ai1WthaVknODlHbR4/1P1s6LWYvl9hvRuHkp/Vta1Qb0frUbL2UT+7gqXyjA/AIUs0FSEoBUvVtCief1atGhhhytaaABG3/5BZud+ua19gE7eBEKDuFoHbvr2rtJ+r92/vS/lm7Z6xar6zdxY4nPApgm06W8eO3YsXwU+aF7LQYMGyect3RHcaaLnDz/8kBdnzPrM6DVUxLza2BXAzLXm+98KOcmClqvflrlf+kSpwco/aHk0F9LnkS7wcYqdcqEHLXV/nkHLojQfAhSiQN+ZCFrxQq/1mDFjXCHLWo466ihx1llnacsdd9xhN0M49IOn821WbTJwhrggvkFL+5ar3F49+fDmEfMkce655/ouI0eOTLqcd955SZfzzz/fdxk1alTSZfTo0QkXej2SLTRBMV0ZR9O+0O+YKy8xmjic3s9UO7to0SK+OikaZqN9+/aBjW2WWY2W9xXSiYIW316r0UopaGVXo5Vy0LKwAAdQKHzesZlB0IoXeq3POOMM0aRJE1fIomX//fcXPXr0kGM6WcsVV1zhDlp0wkjlm/kKZxgPv6BF/2sXA5gHdePbvM+3fPMk0bVrV8+FauaSLQcccEDCpUuXLgmXzp07J1zouUy2UJ8hv4Wm5/FaGjVqJHbaaScxadIk/tTE3ltvvSWGDRsm38sPPPAAX52WPffcU04cHQQn1CTuo2WTnwH9IiC7dld+7vQQlFIfrRSDVjZ9tLyDFv/ypHf0ByhEgb4zEbTihV5rq4/Whg0bZKdrCl3169e3w5Znkwn7xu18s2Y8AljioGWceLSgxdgnGHM7v5NEHFEgpOeFAsHvv//OV8cCBU4KRfQ80CTQQaLPSpyOj7zpECCuAv3UI2jFixq0LBS4pk2bZoctmg7GhQUtv9omvp3dNEI/aUHL+pabbOgOhx2wELQ01DRGtTjbbLONOOWUU0RVVSQGV8rKDz/8IG655RbRu3dv0apVKzFhwgTx2Wef8c0CMWfOHNmZPg4QtAAMgaYiBK148QpaFqrdaty4sff7wStAqduxJkIrBNHPVjkFJPsgbnaGdf1sbqc2XZilTlOJ0sEXHLfffrvsx0XPJdVSzps3T/zyyy98s0ijMHXkkUfKv5EGGR06dCjfJBR0fzT8SbFD0AIweJwFM4egFS+JglY4nBotyC2av4/CFo1+Tq879e3q27evbF4r9LG5vvzyS3mhAPWlo8dO/dnowgT6+bHHHuOb58SZZ54p7/+5557jqwCgyASaihC04gVBK56o3x0NxFleXi7fA7SUlpaKK6+8Ujz++OOipiZ/DbF0BSXNQTZ37lx51Wvz5s3tcEVXhqqd2q2rZdu0aSPuvfdeOUxJLg0YMEAO6gsAxS3QVISgFS8IWrBy5UrxyCOPyH5NNKGyFbw6dOgggwQNJTFz5kzx9ttvi1WrVvGbZ2zjxo3iiy++kLVs1Cfwn//8p92J3VoGDx4srrnmGt8hGWjAUXX7XXbZRfYxzBUKdnQl7tdff81XAUARCTQVUdBq2bIllhgtuQ1aUAieeOIJOWkyzeeXjNWsSLVgzz//vOwMftlll4kRI0aIsrIyceihh8rhLWgC7D322EO+pyiwUad0qiWjwEZDbBx77LFyCiFq8qN5GxcsWCBeeuklORNBpl599VUtaFlLnTp15IC7K1bkpoMRDa9Bfx8AFKdAgxYAFKc///xTBiWrjxYt3377Ld9MQ4OwUoiiWq9CRAOJqgGrXr169s+tW7cWM2bMyMkwFy+88IIMd6effjpfBQBFAEELAHxt3rxZLF68WDRt2lQGkC222EKGAgpQiYwfP15uf+edd/JVBcUKVltttZX8u6hz/88//8w3C938+fPl4wCA4oNPNgC4vPbaa3LKn2bNmrma1urWrSv7PiVC21177bW8uOBQwLL+Luov9eOPP/JNcuaGG24Q06dP58UAEHEIWgDgsmzZMlkrRf2meNCiefv8UB+sKNXMWH/TwoUL+aq8OOecc+TjefLJJ/kqAIio6BwRASAvPvnkE9msZoWSqVOn8k0kGkWe1lNH96igibVp6IdCQldD0uMCgOKAoAUACZ144ony6kDqn0VB6uOPP+abSHSlHo2tFSU0MnwhTjPUq1cvOXwFAEQfghYAeKK5DilYVVdXy3GrGjRo4NksSDVeNCQDXZlYLNasWSOHnMhm+Ihs0WCrNOgqAESb+6gJALF36qmnylCl1vZYI8GraIiHdu3aic6dO2vlxYCa7y666CJenDM0ThgNOZGrORgBIBwIWgDgQoHqoYce0spooFIaUFRFg4nuvffe4quvvtLKiwFdeUk1W/n08MMPu8ItAEQLPsEAYKOpbBKd2NWmtIEDB8owAuGj1+SOO+7gxQAQAf5HVACIFZp0mU7oNMFyMtS0SFcixkXfvn15UU6NHj3a1ZQLANGAoAUAEp3IZ8+ezYtdrEDGmxaLGV0IQOEyn6iP3NZbb82LAaDAIWgBxNwll1ySsLlQddVVV4mZM2fy4liguRtpQNZ8oumBOnbsKNauXctXAUCBSu3oCgBFady4cTJk3XTTTXyVC00Rk2ogg/DQBQlHHHEELwaAAoWjJkCMUXBKpYbqnnvukdteeumlfBXk2Ouvvy623XZbUVZWxlcBQAFC0AKIqUmTJqU88TOFLJqHD4wBWq+++mpenFOPP/64fE3OO+88viqp6qoaXgQAIULQAogZ6mdFJ+mKigq+ymXp0qWiUaNGvDj2Lr/8ctlBPt+mTZsmbr75Zl6cQI0orUDQAsglBC2AmKGQdeWVV/Jil48++kjstttuonfv3nwV1CqUflL0ei5YsIAXi5qKUrmOFiNc1YjKdsbvJe0qhRW3rG3U/nd028pypxzRDCBzCFoAMTJjxgwxefJkXuyycuVKsc8++4gDDzxQXukGbj/99BMvyothw4aJunXrihdffFErLykpE9Xmz6UltcFpBf2k12hRoLK2EbU/WetkSCu31tQoPwNAuhC0AGLgxhtvlDUT48eP56s8UU3Wf/7zH14MPhYvXsyLcuq3336T0yF9//33dlmZR02VHrSqtW2MxQhnFLTUWizargxjpQJkBEELoMjdcsst8iQ6duxYvsrTcccdJ9544w1eDD5okFd6fpcsWcJX5RTNN3nYYYfxYrsJ0Wo+tIPWikpRqoUwB4IWQHC8P2UAUDToJHvRRRfxYk+nnHKKbIaC1G3atEkcfPDBolmzZnxVzjVu3FgMGjSIFxthS/bLctdoedGbFNWmRwBIl/enDAAizxr7KlW0Ld0GMvPxxx/zoryg0evptaxWOrOrfazUJkLnd73TO+8MDwCZwycIoAjdd9998gSZ6thX//rXv2Q/LigO//73v8X111/Pi1PGmw4BIHMIWgBFiELW2WefzYs90QkZtRbFh17TuXPn8uKUIGgBBAdHV4Ai8sgjj6QVmmjbTEYXB3+rV68Wu+66q+y7lW8DBgwQTZs25cUAkEOpH5EBoKA99thjMjgNGTKEr/L07LPPilNPPZUXQwDefPNNcdppp/HinPvzzz9F9+7dxddff81XAUCOIGgBFIk6deqIwYMH82JPr732mthuu+14MQRo4sSJvCgvVq1aJa+K3LhxI18FADmAoAUQcc8//7yoX78+L/bVpk0bcdBBB4kNGzbwVRA51SmNb7Vw4X2iTkmJaNzlRL4KAEKGoAUQYTTtCk1ufPzxx/NVntauXSvat28vvv32W74KQvLdd9/xogClFrRooNLy3TBUA0A+4FMHEGHbb7+9OOaYY3ixJ+qc3bNnT/HJJ5/wVRCiFStWiIsvvpgXZ0ydNqe0otIOWjRulkGZPNocaNT5vUSMu+Yato0zrpY1sGm1PSG1M96WPmWPU66O14VBTQHcELQAIurVV18VRx11FC/2RYFshx124MWQAxRCqqpSqnpKQp3g2QhLPGjJ4GNuYwUna1saFZ4ey5iDnW3sAFX7O5+uR4YxuZ2zjX0f5kjz+mCoGEEegEPQAoiYt99+W/zlL38RvXv35qs80XhadPKkqxIhf9atW8eL0uYe38ppOrRrtKrKzBomNfQ4QYucdNJJ8mKIR0e2cmq1rKAlA5R5K+t3Vm6z70tZlOAFAAhaAJFDYzRRE+Bvv/3GV3mikx+NFA/Rl1LQMqnNhzxoOc19DZ3fMwhafE5EAHBD0AKIkOXLl8txkdavX89XeZoyZYq4+eabeTHk0ZIlS3hR6qrUPlO1Vnj10VIZAUsPWkYz4MA5P4p999239r203G4i5IHKbnqUNVfsvkltOZoKARLz+mQCQIGhDtV77rmnOPDAA/kqT3feeaessZgwYQJfBXlGA5nScBzLli3jq1KidmL37gyvdlp3+nBZzXwyLNUGtFJrmy22FAP2aySDlG/Qkrw7w+uPh9d5AQCCFoBJ62eiLC/6NJvkSk1Njdh7773F/vvvL77//nu+2hM97lGjRvFiKBDU9LvHHnvw4rywpm264IIL+CoACACCFgBX+22/kJpD2rZtKzp27Jjy2FdPPfVUQUz/Av7WrFkjrxotFLfddpsMWwAQPHyyADgWtNTmlFK6kqvCudJKXvhudSxWrrYKYmwhmjqlU6dO4osvvuCrPL3//vvyasS+ffvyVQApoffro48+yosBIAsIWgBcwqBVojQjGmMSWX1gaJ3xc/ZjC61evVp07txZTpeTKurD1a1bt5SvRoTC0KVLl4IZRLa8vFxsvfXW4pVXXuGrACBDCFoAXJKgpU55ovbdoo7Ccl3t7dWrs9QBJFPVtWtX0bp165RPwD/+aFxBlmofLigc++23n2jVqpVsTiwEffr0ES1atODFAJAhBC0ALmHQ0munvIJWNmML0UTPPXr0kM2AqTr66KPFTjvtxIshQhYuXChOPLFwJnymCzBSHRAXABJD0ALgsgxamY4ttHHjRtGrVy/RvHlzvspXWVmZbOpZvHgxXwWQlW233Va+vwAgOwhaAFy2QYv6aLHyVMYXOuKII0SzZs3Em2++yVf5kh3yqzOtPwPwR+8ren+NHDmSrwKANCBoAXBZB63MBnGkCZ9ff/11XuyLxj26//77eTFEGF3IcPHFFxdMf6277roLwz4AZAmfIIA8O/bYY+UEv6maMWOGPPlNnz6dr4IiQCPG08jxhYTebwsWLODFAJACBC2APBowYIBo0KCB7AydKjrpXXHFFbwYisgdd9whfvrpJ16cN8OGDRN169YVL774Il8FAEkgaAHkUb169cRzzz3Hi33NmzdPjBkzhhcDhK5///6yD+EHH3zAVwFAAghaAHlAA0Om0/dlyZIl8urCk08+ma+CIldIg4d+9dVXcmDczZs381UA4CP1Iz0ABGLo0KEyZFVVKSOfJvDuu++KnXfeWfTr14+vgiK3du1aGbALyTvvvCMGDRrEiwHAB4IWQI5RyHr44Yd5sa899thDDmJK42xB/Fx77bXigQce4MV5Re/hs88+mxcDgAcELYAcGTFiRFrNhb///rs45JBDxOeff85XQcw8++yzvCjvKACm834GiCt8SgBy4Nxzz5UnpTlz5vBVvvr27Ss7HwMUqssuu0zMnTuXFwOAAkELIGSjRo2SIevuu+/mq3yddNJJctiHl19+ma8CKCj03i7EGjeAQoGgBRAiGuX7tttu48UAGdtqq63SmqYpbH/++afo3r272GuvvfgqABAIWgChGTduHPqwQOCOOuoo0aZNG/Hjjz/yVXnz3XffiX322QcXbAB4wFkAIAQTJkyQIWvmzJl8VcGqTm20CQBPy5cvF8cccwwvBog9BC2AEFDIoquyoqPanhAbIFN16tQRp512Gi8GiDUELYAAXXXVVWk1F5ZWVIqy2u3t21SVyZ9pKa2ocTZUyqvp53aVgtaWlpSKyhXmNisqtd+ry43tS9Rtaln3J/dlbOmUlRslhYr+JuVZkY/ZCoj0N6QbFivbeTzP5nNQqu2vRm5Lz7v8raLU/hl0N954Y1qfAYBih08DQECmTZsmTzBXXnklX+VLDUHy5F1SpoUfGQJkyHK2k4EoSdCSocAKTdrta7Rg4QSrKNRoGc+JVkJh0vwbgghatD9rH9ZzbDOfX4KgldikSZPSusoWoJghaAEEhALQlClTeHFC6smcTvpaUJABqcwzDCQLWqV2YFNuIwNJtV6DY4tm0HJU27V0VvCyf7cCq7ldZYVVO9jf2cZ8PivbqYFWfw4tRiA2bmc/9x41kVYYq7RqFnlwsyi31WoUPfZJZIi2/zYj+PHtrf3ogdCslZPbOH+bEVCdWk3v90f6aF9PPPEELwaIHb+jFgCk6IYbbpAnlXSsWrVKrF+/Xjux6k1VDs8AliRo+YUEh3ViVWrQPO67EKlNn2p4SVSj5TxPetDkIZaHDDVU0WLt3wkwRnhRb2et02sohVYjpuJNu4Ya92su91Xj3bxr1lpy9uO0b28xXn+6D7vmlJUH4fDDDxetWrXixQCxkt7ZAQA0N998szwBjx07lq/ytWHDBnHwwQe7gpZ+wnOozWPEPpELFrSUJkLvk7ebc1KNTtBSqbU37oCg9D1Tgpa6DQ9J/s+BtS/edOgRTGSgKtNeJ4N3jZxaQ+VQaujsxQhKzu/qa6zUVnm9V1yPxXhf0d+uP36PvycLa9asEfvuu698rwPElftTDwApoxMbDUqajr///e+iefPmcqBH10lROXlaTYTGids5+dHP1klTnvzNfRgnWqWPln1iNU6eRqDQa3ScWg6971ZUqLVGWkCofc7otbH+JrVGyz9oVZvPhR8nKCUMWmbtkTvceActm9X0R69n7eNPHHacYKUFaqX5UG7lG7Scmrgwgxb5+OOP5XRSAHGV4FMPAH6oo69eA5GaYcOGiWeeeYYXp8V90owLIwSof7calNSf6TlSm+z8arTU2kK6jYpeX68AxX/WArIZiulxGOXW/s1g5NHs5wrXdh8zd+iu4U2Htfcnt2FNh7Q94YHQuq1xRapHQA0haJFHHnlEPhdjxozhqwCKXvpnCoCYu+++++RJgyaKTsf555+fUTjj4hu0DE7TmR4I7GBjPjfOdqVajZ47PNE2/cXwdqyPkxma7P141E7Z+/LouG69TnZneI+QRezHze7Dr1wGJmWx8O3tMvNntRbM3Rne/IX/XQGiqajovmkIFIA4yf6oDxAj8+bNkyeLESNG8FUJjR8/Xt7urrvu4qvSFvegFRV4ndxo6BM1HALEAd7xACmi5o/hw4fz4qToxDJ16lReDEUOQctf/fr1xSuvvMKLAYoSghZACh577LGMvonfe++94pJLLuHFALHWp08f0aJFC/HJJ5/wVQBFJ/0zB0DM0KCLFLLKy8v5qoQeffTRjMIZQFDeeustcfnll/PivPvll1/E/vvvLzp06MBXARQdnAUAEnj++efFCSecwIuTatKkiTjuuON4MUBefPvtt7yoICxdulSUlZlXcgIUKQQtAB+LFi0SDRo04MVJ0bhBNCL25s2b+SoAYKjWd+TIkbxY+uOPP3gRQOQgaAF4WLJkidhuu+3EMcccw1cl9M0334i2bduKdevW8VUA4GH27NkybE2ePFkr/+mnn8SMGTO0MoAoQtAC8NC4cWPRr18/XpwQ9Tvp2rWrKC11zzkHUAhooN1CVFlpjOSvmj59uqwZBog6BC0ABXUebtasmfjf//7HVyXVqFEj2ecEoFBRUxxN8kxzEBaiLbbYQjbZE2vw1WxnUgDINwQtANOyZcvkHIQ9e/bkq5IaOnSoeO6553gxQMHZYYcdxFNPPcWLC0L//v3lF50PPvhAbLnllnK8rQsvvJBvBhApCFoApv/7v/8TPXr0EBs2bOCrEqKpeHizB0ChKuT+gxs3bhQHHXSQ2Hvvve0arXbt2vHNACIFZweIPRo0sXXr1hk1p9CJ4IYbbuDFAJGwcuVKXpRzH330kbjpppvEiSeeKD9PdKVvnTp17KBFP8+dO5ffDCAyELQg1mpqakSbNm1E586d+aqkKGBhglyIsgEDBqRdgxu0V199VQwZMkRstdVWdrhSFyofNmwYvxlAZCBoQazRUAydOnVKe0BHunoLzYUQdatXrxYDBw7kxXmxdu1a2VGfPlfUP0sNW02bNuWbA0QGzhQQS6tWrRIdO3YUX375JV+VEHV4pyujqPM7QDGwrvIrNFOmTBG77rqrHbYAogrvXtPUqVOxxGQZN26cnNCWmgzTRUM4UHMLxAPV+PD3D5bcLRS2qFmRxqbj68Jann76af42AMgKgpaJvjG1bNkSS0wWer3pEvJ0fPjhh+KII47gxVDEKGjh2BCfhV5rBC0IGoKWiT5gdGkxFL8FCxak9XrT5fBdunTBZeYxZAUtiAcELQgDjiCmdE68EG3pBq1evXrJMbZosmiIFwSteEHQgjDgCGJK58QL0ZZu0GrSpIl48803eTHEAIJWvCBoQRhwBDGlc+KFaEsnaJ1yyili4cKFvBhiAkErXhC0IAw4gphSPfFC9PGgdd9997EthLjkkkvkNnPmzOGrIEYQtOIFQQvCgCOICUErPtSgRVce0qXjHK2naUEg3hC04gVBC8KAI4gJQSs+1KBVWVkpf162bJm9/rrrrhMVFRXKLSCuELTiBUELwoAjiAlBKz7UoFW3bl3584477igefPBB+fP555/PbwIxhaAVLwhaEAYcQUwIWvGhBi36X12GDx/ON4cYQ9CKFwQtCAOOIKaiCVpVZa7wUFJSKipXGKsr2/F1zlJWpexnRaUo9VsXcWrQsiavpZotjPoOXKSCVu1n1utzWl1eImqsX2q3sY4FlrKSMlFNP9QeO/g6jvZlHzPaVTr75evkYu43QuhxI2hB0CJyBAmfdeKNPBm0eOfu6tqDaYkorVAPi3SAdZdJXgdcM8AVAytovfHGG+zE4CwUvM444wyxfv16fnOIkTgELfsY4PW5N8kvaOU8NtXIcmvf2v0oZRTIogJBC8IQkSNI+Io7aBkHRH6g9A5axrZu1aLa4yAeRVbQmjx5shau6tSpI5f69euLJUuW8JtBDBV/0Kpxfk8QtNRacVVNlXNM8QpaVs14VCBoQRii8wkIWXEHrXRqtIxti5kVtDp37myHrHr16okDDzxQzJo1S2zYsIHfBGKq6IPWCqX5L1HQYs2EXjyDVsSOJwhaEIbofAJCVlxBizeFefeV8AxaEfsGmgkraFHzYHV1tdi0aRPfBEAq9qBF62yhBC2/GvLChKAFYYjOJyBkxRW0nBqtmopSz4Mv8QxaEfsGmgkraK1cuZKvAtAUS9CyaUGLPutlzrpQgla0jicIWhCG6HwCQlasQYv49a/wDlp+30D9yqOHT8ED4CdSQYtCjStosc+tGrSo9lrtqJ4oaPkcQ9TbeAYtWUPOuzIULgQtCENUjiChK5oTr0fQspoTeajyDloG7cBqNifyzvRRhaAFqYpW0DKOY07YMi+CUcOUHbRoHQtPCYKW1zHAGM7BOdbwoEW16b4BrUAhaEEYonMECVnRnHi9gpawDor6y50oaPG+Xu5vytGFoAWpilrQsgORtfAvR3bQMpoNtbVe/Tu1JkMzuHmuc44xzuLdN7SQ0eNG0IKgRegIEi6ceOMDQQtSFbmgBVlB0IIw4Ahiwok3PhC0IFUIWvGCoAVhwBHEhBNvfCBoQaoQtOIFQQvCgCOICSfe+EDQglQhaMULghaEAUcQE0688YGgBalC0IoXBC0IA44gJpx44wNBC1KFoBUvCFoQBhxBTDjxxgeCFqQKQSteELQgDDiCmHDijQ8ELUgVgla8IGhBGHAEMeHEGx8IWpAqBK14QdCCMOAIYsKJNz4QtCBVCFrxgqAFYcARxIQTb3wgaEGqELTiBUELwoAjiIk+YPXq1cMSkwVBC1JhBS3+/sFSnAuCFoQBQcs0a9YsLDFbELQgGQpa/H2DpbgXBC0IGoIWAAAAQEgQtAAAAABCgqAFAAAAEBIELQAAAICQIGgBAAAAhARBCwAAACAkCFoAAAAAIUHQAgAAAAgJghYAAABASBC0AAAAAEKCoAUAAAAQEgQtAAAAgJAgaAEAAACEBEELAAAAICQIWgAAAAAhQdACAAAACAmCFgAAAEBIELQAAAAAQoKgBQAAABASBC0AAACAkCBoAQAAAIQEQQsAAAAgJAhaAAAAACFB0AIAAAAICYIWAAAAQEgQtAAAAABCgqAFAAAAEBIELQAAAICQIGgBAAAAhOT/Acx+lreeiEyzAAAAAElFTkSuQmCC>