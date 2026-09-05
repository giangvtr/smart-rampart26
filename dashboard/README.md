# Smart Rampart — Dashboard

The monitoring station for the Smart Rampart sensor rig, and the runbook for standing it up.
An **ESP32 node (WiFi)** POSTs sensor readings to this **dashboard server on the laptop**; the
dashboard shows live status and rides override / ARM / DISARM commands back on the POST reply.

Four sensors, all in the **Basement** zone: **water level, temperature, humidity and fire**. On
top of the live view it runs three predictive brains — **HVAC feedforward** (`hvac.py` +
`forecast.py`), a **Preservation Index** (`preservation.py`), and **anomaly detection**
(`anomaly.py`).

> **New here?** For the project story, the hardware, and the big picture, start at the
> [top-level README](../README.md). **This doc** is everything an operator or developer needs to
> *run* the dashboard — from a cold laptop to a working end-to-end demo, then the full reference.

<p align="center">
  <img src="../media/graph.png" alt="Graphs view" width="49%">
  <img src="../media/building.png" alt="3D building view" width="49%">
</p>

---

## Part I — Runbook: cold laptop to working demo

### 0. What talks to what

```
  ESP32 BASE01 (water, fire, temp, humidity) ──POST readings──▶ ┐
  Pico W BASE01 (optional second node) ───────POST────────────▶ │
                                      ◀────cmd on reply─────── ┘
                            Laptop: dashboard/server.py  ──▶ browser
                                    (http://<laptop-ip>:8000)
```

- Nodes are HTTP **clients**; the laptop is the **server**. Commands ride back on each node's
  POST reply (no inbound connection to the node — works behind NAT).
- Everything is on **one WiFi network**. Use a **phone/laptop hotspot**, not venue/guest WiFi
  (guest networks often block device-to-device traffic).

### 1. Sanity check first (2 min, no hardware)

Prove the software works with the built-in simulator before touching hardware. **No code
editing** — just pass `--source sim`:

```bash
cd dashboard
python server.py --source sim        # fake data, no hardware, binds 127.0.0.1:8000
```

Open <http://127.0.0.1:8000>. You'll hit the sign-in page first — log in as `viewer` (creds
below). You should see live charts moving, status tiles, an event log, the HVAC panel and the
preservation index. Log in again as `guard` via **Agent login** in the top bar, hit
**ARM/DISARM/Reset** — the banner and log react. That's the whole UI working. **Stop with
Ctrl+C**, then move to step 2 (drop `--source sim` — the real ESP32 path is the default).

> `--source` picks where data comes from: `http` (default, real ESP32 over WiFi), `sim` (fake
> data), or `serial` (USB/Bluetooth Arduino). Nothing in the code needs changing between them.
>
> There's also a **3D building view** in the top bar (Building / Graphs / Simple). By default
> only the basement room has sensors; add `--demo-rooms` to populate the other 11 with simulated
> activity for a showpiece run. Off by default so every reading on screen is a real one. See
> [`BUILDING.md`](BUILDING.md).

**Demo login** — two tiers:

| Username | Password          | Gates |
|----------|-------------------|-------|
| `viewer` | `N1KOM%YLHfN953J` | Loading the web dashboard at all (sign-in page at `/`) |
| `guard`  | `eBDTCBxO5D#edpT` | The **ARM / DISARM / Reset** controls, via the in-page "Agent login" |

A `viewer` can watch but not act; only `guard` unlocks the overrides. Login is rate-limited per
IP (5 fails → 5 min lockout).

### 2. Start the real server (so nodes can reach it)

```bash
cd dashboard
python server.py --host 0.0.0.0        # 0.0.0.0 = reachable from other devices
```

You need **only the Python standard library** for the web UI — no pip install.

Now find the laptop's IP **on the hotspot network**:

```bash
# Windows PowerShell:
ipconfig                # look for the hotspot adapter's IPv4, e.g. 192.168.137.1
# macOS/Linux:
# ipconfig getifaddr en0   /   hostname -I
```

Write that IP down — call it `LAPTOP_IP`. Confirm from a phone browser on the same hotspot:
open `http://LAPTOP_IP:8000` — the dashboard should load. If it doesn't, it's a
**network/firewall** problem, not a code problem (see Troubleshooting).

> Windows may pop a **firewall prompt** the first time — allow Python on **Private** networks.
> If you missed it: allow `python.exe` through Windows Defender Firewall for the Private profile.

### 3. Flash / port the nodes

**3a. ESP32 (Basement — water + fire + temp/humidity, `esp32_node/esp32_node.ino`)**

Arduino IDE **or** Wokwi. This is the node tested end to end. It POSTs `water`, `fire`, `temp`,
`humidity` as `BASE01` → BASEMENT. See `esp32_node/libraries.txt` and `esp32_node/diagram.json`
(Wokwi wiring); `esp32_node/test_sensor_wifi.ino` is the bare WiFi smoke test.

1. Board package: **esp32 by Espressif** installed.
2. Libraries: **DHT sensor library** + **Adafruit Unified Sensor**.
3. Edit the top of `esp32_node.ino`:
   ```cpp
   const char* WIFI_SSID = "YourHotspotName";
   const char* WIFI_PASS = "YourHotspotPass";
   const char* SERVER    = "http://LAPTOP_IP:8000/api/ingest";   // ← your IP
   const char* ZONE      = "BASE01";                             // BASE01 → BASEMENT
   ```
   - For **Wokwi**: keep `WIFI_SSID = "Wokwi-GUEST"`, `WIFI_PASS = ""`, and `SERVER` must be a
     **public URL** (Wokwi cloud can't reach a LAN IP) — run `ngrok http 8000` and use the
     `https://…ngrok…/api/ingest` URL. (HTTPS on ESP32 also needs `WiFiClientSecure` +
     `setInsecure()` — ask if needed.)
   - Real hardware on the hotspot: use `LAPTOP_IP` directly, plain HTTP.
4. **Wiring / pin map** (ESP32 DevKit v4, all 3.3 V logic — the pin numbers are the `const int`
   / `#define` values at the top of `esp32_node.ino`, so match your breadboard to these):

   | Component | Wire from | ESP32 pin | Notes |
   |---|---|---|---|
   | Water-level sensor | signal (S) | **GPIO34** | ADC1, input-only. `VCC`→`3V3`, `GND`→`GND` |
   | Potentiometer (fire index) | wiper | **GPIO35** | ADC1, input-only. Outer legs → `3V3` and `GND` |
   | DHT11/22 temp+humidity | data | **GPIO15** | `DHTPIN` in code. `VCC`→`3V3`, `GND`→`GND`. Add a 10 kΩ data→VCC pull-up if your module has no built-in one |
   | Water alarm indicator | — | **GPIO2** | Onboard LED; lights on local WATER alarm. No wiring needed |

   - **GPIO34/35 have no internal pull resistor.** If a sensor pin is ever left unconnected, tie
     it to `GND` through a 10 kΩ resistor or the ADC reads floating noise.
   - Fire has no node LED — the fire alarm is a full-screen popup on the dashboard.
   - **Pin discrepancy to know about:** the code compiles with `#define DHTPIN 15`, but the header
     comment and the Wokwi `diagram.json` in this repo wire the DHT to **GPIO4** (and the pot to
     D34). The `#define` wins at runtime — so either wire the DHT to **GPIO15**, or change
     `DHTPIN` to `4` to match a GPIO4 wiring. Just make the pin and the `#define` agree.
5. Upload. Open **Serial Monitor @ 115200** — you should see `connected: <node-ip>` then
   `POST {...} -> 200` and the `reply:` line.

   > **No sensor to hand?** Briefly jumper `3V3 → GPIO34` to force a high water reading (ALARM):
   > the onboard LED turns on, and clicking DISARM on the dashboard should turn it off within ~3 s.
   > Turn the potentiometer past ~70 % to raise the fire index and trigger the fire popup.

**3b. Pico W (Basement water — `WINDOWS/main.py`, MicroPython)**

1. MicroPython flashed on the Pico W; open **Thonny**.
2. Edit the top of `main.py`:
   ```python
   WIFI_SSID = "YourHotspotName"
   WIFI_PASS = "YourHotspotPass"
   SERVER = "http://LAPTOP_IP:8000/api/ingest"
   ZONE = "BASE01"       # BASE01 → BASEMENT (the only zone there is)
   ```
   > The Pico is **optional** — the ESP32 in 3a already covers basement water. Only run both if
   > you want a second physical node.
3. Save as `main.py` **onto the Pico**. Reset — the onboard LED settles solid once WiFi connects;
   Thonny's shell prints `sent {...} -> 200`.

**3c. Arduino Uno — room access control (`arduino_node/password_servo_merge.ino`)**

This node is **standalone** — it does *not* talk to the dashboard. A 4×4 keypad takes a PIN; a
correct code drives a servo to unlock a door and blinks a green LED, a wrong code blinks red. It
runs on its own USB power. Flash it from the Arduino IDE.

1. Libraries (Arduino IDE → *Library Manager*): **LiquidCrystal_I2C**, **Servo** (built-in),
   **OnewireKeypad**. `Wire` is built in.
2. **Wiring / pin map** (Arduino Uno, 5 V logic):

   | Component | Wire from | Uno pin | Notes |
   |---|---|---|---|
   | 16×2 LCD (I²C backpack) | SDA | **A4** | I²C data (Uno's fixed SDA). Address `0x27` in code |
   | 16×2 LCD (I²C backpack) | SCL | **A5** | I²C clock (Uno's fixed SCL). `VCC`→`5V`, `GND`→`GND` |
   | SG90 servo (door lock) | signal | **D3** | `VCC`→`5V`, `GND`→`GND`. 0° = locked, 90° = open |
   | RGB LED | red leg | **D2** | Through a 220 Ω resistor. Blinks on wrong PIN |
   | RGB LED | green leg | **D4** | Through a 220 Ω resistor. Blinks on correct PIN |
   | RGB LED | blue leg | **D5** | Through a 220 Ω resistor. Unused (kept LOW) |
   | 4×4 matrix keypad | single-wire out | **A1** | Read as an analog ladder by `OnewireKeypad` (a resistor network on the keypad turns 8 lines into one analog pin) |

   Common RGB-LED leg goes to `GND` (common-cathode). The keypad's common line ties to the
   analog reference the `OnewireKeypad` constructor expects (`4700`, `1000` in code) — keep the
   keypad's onboard resistor ladder intact.
3. The default PIN is `456` (`const String correctCode = "456"` — change it there). Enter it on
   the keypad; the LCD masks digits with `*`, then shows **ACCESS GRANTED** / **WRONG PASSWORD!**.
4. Upload, open the LCD — it should show `Enter password:`. Type `456#` and the servo should sweep
   to 90° for ~3 s, green LED blinking, then relock.

### 4. The end-to-end test

1. Server running from step 2 (`--host 0.0.0.0`, default `--source http`).
2. Power the ESP32 (and Pico) on the same hotspot.
3. Open `http://LAPTOP_IP:8000` on the laptop (and/or a phone).

Within ~2 s the four Basement tiles go live. Then walk the checklist.

**Acceptance checklist**

- [ ] **Live values** — temp/humidity update within ~2 s.
- [ ] **Water flood** — wet the sensor → WATER tile red and **latches** (stays red after drying)
      until a guard Resets it.
- [ ] **Fire alert** — turn the pot past ~70 → full-screen 🔥 popup; **Acknowledge & DISARM**
      clears it and silences the node.
- [ ] **Login gate** — as `viewer` only, the ARM/Reset controls are refused; they unlock after
      the in-page `guard` login.
- [ ] **Override round-trip** — log in, hit **Reset** on a latched alarm → clears on the
      dashboard **and** the node's LED/buzzer within ~2 s.
- [ ] **Disconnect** — power off the node → all four tiles show **DISCONNECTED** within ~6 s and
      the header flips; power back on and both recover on the next POST.
- [ ] **Resilience** — unplug one sensor → the node's other readings keep flowing.

**Verify the command path by hand**

1. Log in as `guard` (`eBDTCBxO5D#edpT`) via **Agent login**.
2. Trip a latching alarm (wet the water sensor).
3. Click **Reset** on that tile.
4. Watch the node's **Serial Monitor**: the next `POST … -> 200` reply carries `"cmd":"RESET"`,
   and the node acts on it (LED off). End-to-end confirmed.

### 5. Known gaps

- **Firmware sensor coverage:** `esp32_node.ino` sends water, fire (pot), temp and humidity for
  `BASE01` — exactly the four the dashboard shows, so no dead tiles. The old Gallery zone (LDR
  light + PIR motion) is **gone**: no firmware ever sent it. To bring it back, add the
  `SensorDef`s and a `ZONE_ALIASES` entry in `config.py` plus the two `FIELD_TO_SENSOR` lines —
  nothing else in the dashboard is zone-aware.
- **Fire is a potentiometer stand-in**, not a real flame/smoke sensor: a 0..100 index, warn at
  50, alarm (latched) at 70. Swap the sensor and the thresholds in `BASEMENT.FIRE` together.
- **Wokwi vs. real WiFi:** cloud Wokwi can't reach `LAPTOP_IP` — needs the ngrok tunnel from 3a.
  Real hardware on the hotspot does not.

### 6. Troubleshooting (fast)

| Symptom | Most likely cause | Fix |
|---|---|---|
| Node Serial shows WiFi connecting forever | wrong SSID/pass; password on an open AP | fix creds; for open/Wokwi AP leave pass `""` |
| `POST … -> -1` or connection refused | wrong `LAPTOP_IP`/port, or server not on `0.0.0.0` | re-check IP with `ipconfig`; start with `--host 0.0.0.0` |
| Node connects but tile never appears | firewall blocking, or guest-WiFi client isolation | allow `python.exe` on Private; use a **hotspot**, not guest WiFi |
| Phone can't open `http://LAPTOP_IP:8000` | same as above | firewall / wrong network |
| Tile shows but stuck / stale | node stopped POSTing | check Serial; tile flips to DISCONNECTED after 6 s |
| Can't get past the sign-in page | wrong tier | that page wants `viewer`; `guard` works there too |
| Controls do nothing | logged in as `viewer` only | use **Agent login** with the `guard` creds |
| Locked out after retries | per-IP rate limit (5 fails) | wait 5 min, or restart the server |
| Node POSTs 200 but no tile | node `ZONE` id is not `BASE01` | only `BASE01`/`BASEMENT` map to a zone (see `config.py` `ZONE_ALIASES`); anything else is dropped |

### Quick reference

```bash
# run the dashboard (from the dashboard/ folder)
python server.py --host 0.0.0.0      # http://LAPTOP_IP:8000

# no-hardware demo: add --source sim
# find laptop IP (Windows):  ipconfig   (look for the hotspot adapter IPv4)
```

- ESP32 firmware: [`../esp32_node/esp32_node.ino`](../esp32_node/esp32_node.ino)
- Pico water node: `WINDOWS/main.py`
- Login: `viewer` / `N1KOM%YLHfN953J` (page), `guard` / `eBDTCBxO5D#edpT` (controls)

---

## Part II — Dashboard reference

### Status

Working end to end (on hardware for the four basement sensors; on simulated data for everything else):

- Web UI (stdlib server + SSE, canvas charts, floating-window workspace, plus a simple
  value-box view that works on a phone).
- Desktop UI (PySide6 + pyqtgraph docks) — feature-equivalent.
- Simulator with latching water/fire alarms that honour ARM/DISARM/RESET.
- SQLite + daily CSV logging, audit trail for logins and overrides.
- Two-tier PBKDF2 login: a `viewer` password gates the dashboard itself, a separate `guard`
  password gates the override/disarm controls. Per-IP rate limit (5 fails → 5 min lockout).
- 3D building view (CSS transforms, no dependencies) with per-room drill-down and hash deep
  links; `--demo-rooms` populates the 11 simulated rooms, off by default.
- **Predictive HVAC** (`hvac.py`): a single conditioning effort + mode driven by the live
  temp/RH stream and a weather-forecast outlook, ramped gradually, carried to the ESP32 as an
  LED-PWM duty on the POST reply.
- **Weather feedforward** (`forecast.py`): optional Open-Meteo pull (no API key) with an offline
  simulated fallback, for pre-emptive conditioning ahead of an outdoor front.
- **Preservation Index / TWPI** (`preservation.py`): live "years of life at these conditions"
  from an offline Arrhenius model.
- `HttpIngestSource` (**WiFi / ESP32**) — the default source. Server-side latching, ARM/DISARM
  gating, and a 6 s heartbeat watchdog live in the source.
- Full-screen **fire alert** on `BASEMENT.FIRE` ALARM, with an acknowledge button that disarms
  (silences) the node.
- `SerialSource` (USB / Bluetooth-Classic) is written but **not yet run against real firmware** —
  select it with `--source serial`. `WebSocketSource` and `BleSource` remain deliberate stubs.
- HMAC frame authentication for the radio link is designed and documented below, but **not wired
  in** — see *Security notes*.

### Two frontends, one engine

Pick whichever you prefer — they share the same engine and database:

| | Web (recommended) | Desktop |
|---|---|---|
| Run | `python server.py` → http://127.0.0.1:8000 | `python app.py` |
| UI files | `server.py` + `static/index.html` (+ `static/login.html`) | `app.py` + `panels.py` |
| Dependencies | **none** (stdlib only) | PySide6 + pyqtgraph |
| Graph controls | wheel-zoom, drag-pan, live/pause, hover readout | pan/zoom via pyqtgraph |
| On a phone | drawer sidebar, Simple boxes, graphs as a scrolling stack | — |
| Panels | floating windows: move, resize, edge-snap, minimise/maximise/close, taskbar, layout remembered | docks: drag/float/resize/close |

Shared by both: `config.py`, `core.py`, `transports.py`, `storage.py`, `security.py`,
`anomaly.py`, `hvac.py`, `forecast.py`, `preservation.py`. Only the presentation layer differs.

### Quick start — web (no dependencies)

```bash
python server.py            # from the dashboard/ folder
# then open http://127.0.0.1:8000
```

Uses only the Python standard library: no Flask/FastAPI, no npm, no CDN. Charts are drawn on
plain `<canvas>` with **no charting library**, so it works with no internet at the venue. Live
data arrives over Server-Sent Events. The 3D building view is CSS transforms and a single script,
so it downloads nothing either.

Options: `python server.py --port 9000 --host 0.0.0.0 --source sim --demo-rooms`

`--source` picks where readings come from — `http` (default: real ESP32 over WiFi), `sim` (fake
data), or `serial` (USB/Bluetooth Arduino, port in `config.py`). `--demo-rooms` populates the 11
**simulated** museum rooms behind the 3D view; off by default.

You'll land on a sign-in page first — the `viewer` gate. Signing in sets a cookie; the dashboard
opens after.

> The login posts a plaintext password over HTTP, so it binds to `127.0.0.1` by default. Don't
> expose it beyond the demo machine without TLS in front (deferred — see *Security notes*).

### Quick start — desktop

```bash
pip install -r requirements.txt
python app.py          # from the dashboard/ folder
# or, from the repo root:  python -m dashboard.app
```

A window opens streaming simulated data (the desktop app always uses the simulator). No Arduino
required. The desktop UI has no sign-in page of its own — it opens straight into monitoring, and
the `guard` login gates the override controls.

### Demo login

| Username | Password          | Gates |
|----------|-------------------|-------|
| `viewer` | `N1KOM%YLHfN953J` | Loading the web dashboard at all (the sign-in page at `/`) |
| `guard`  | `eBDTCBxO5D#edpT` | The **override/disarm controls** (web + desktop), via the in-page "Agent login" |

Both frontends enforce the same rule: a `viewer` login can watch but not act — only `guard`
unlocks ARM/DISARM/Reset. Neither password is stored in source — only salted PBKDF2-SHA256 hashes
live in `security.py` (`_ACCOUNTS`). To rotate one, run the regeneration one-liner at the top of
that file and replace the matching `salt`/`hash`. Attempts are rate-limited per source IP: 5
failures locks that IP out for 5 minutes (`security.RateLimiter`).

### Using the dashboard

**Graph controls (web):** mouse-wheel over a chart to **zoom** the time axis, **drag** to scroll
back through history (`⏸ PAUSED`), **double-click** or **● Live** to jump back to now. Hovering
shows a crosshair with the exact value and timestamp. Each window's title bar carries a
time-scale selector (30 s / 2 min / 5 min / 30 min / All).

**Three views (web):** the **Building / Graphs / Simple** switch in the top bar.

- **Graphs** — the floating-window workspace, a 2×2 for the four-sensor live rig. The landing view.
- **Simple** — one box per sensor showing just its current value, filled with that sensor's state
  colour (green OK, amber warning, red alarm, grey disconnected; alarming boxes pulse). Good for
  a wall display; it's what phones land on.
- **Building** — the 3D museum. Click a room to open its dashboard.

Graphs and Simple always show **one room** — the live rig unless you picked another in the
building view. The URL carries it (`#/room/B1_ARCHIVE`), so a room is linkable, and the choice of
view is remembered. The alarm banner, event log and anomaly pane follow where you are; the
full-screen **fire alert** is building-wide always.

**Side panels (web).** Beyond the charts, the sidebar carries the live brains:

- **HVAC control** — the current mode (Heat / Cool / Dehumidify / Humidify / Idle) and effort %,
  with the reason line ("Pre-emptive dehumidify — warm front approaching in 3 h") and Auto / Off /
  manual override buttons.
- **Preservation** — the effective **TWPI** in years with a GOOD/… badge, and the instantaneous
  PI at the current temp/RH.

**On a phone** (≤ 760 px), the sidebar becomes a ☰ drawer, the Simple boxes reflow to two
columns, and Simple is the default view. **Graphs** works too — panels become one scrolling
column, each chart keeping a readable width and scrolling left/right inside its own panel; a
panel follows the live edge until you swipe back.

**Windows (web):** every sensor is a floating window, laid out by default as a **2×2 filling the
workspace**. Move by dragging the title bar; resize from any edge/corner; **snap** like Windows
(top = maximise, sides = halves, corners = quarters). Title-bar **─ ▢ ✕** minimise / maximise /
close; the **taskbar** has a state-coloured button per sensor; **Reset layout** restores the
default 2×2. Otherwise the arrangement is saved to `localStorage`.

**Docks (desktop):** panels are pyqtgraph docks — drag to rearrange, drag edges to resize, drag
out to float, **×** to close; the **View** menu re-adds closed ones.

Common to both: warn/alarm zones shaded on every chart; panel border and read-out recolour with
state; a **banner** naming zones in ALARM (fire additionally raises a full-screen alert); **status
tiles**; **Controls** (log in, then ARM/DISARM or Reset — every override is audit-logged); an
**event log**; and a **CONNECTED / DISCONNECTED** indicator.

### Connecting the ESP32 over WiFi (default)

`server.py` runs `--source http` out of the box:

1. Run `python server.py --host 0.0.0.0` so the nodes (same WiFi) can reach the laptop.
2. Point each node's `SERVER` at `http://<laptop-ip>:8000/api/ingest`.
3. Each node POSTs one JSON blob per cycle; the server **fans it out** into the per-sensor model
   using `ZONE_ALIASES` + `FIELD_TO_SENSOR` in `config.py`:

   ```json
   {"zone": "BASE01", "water": 120, "fire": 12, "temp": 21.4, "humidity": 50, "state": "OK"}
   ```

   `BASE01`→`BASEMENT`, `temp`→`TEMP`, `pot`/`fire`→`FIRE`, `water`/`level`→`WATER`. Unmapped
   fields are ignored. The reply carries the pending command: `{"ok": true, "cmd": "RESET"}` (one
   of `AUTO`/`OFF`/`ARM`/`DISARM`/`RESET`, plus the HVAC effort duty), which the firmware acts on.

`/api/ingest` is **not** behind the `viewer` cookie gate — that gate is for browsers, and the
firmware carries no session. Nodes are treated as unauthenticated devices on the LAN; see
*Security notes* below. To demo without hardware, add `--source sim`.

### Connecting a real Arduino (USB or Bluetooth)

0. `pip install -r requirements.txt` — pulls in `pyserial`.
1. Set `SERIAL_PORT` / `SERIAL_BAUD` in `config.py` (a paired HC-05/06 appears as a COM port, so
   the same path handles USB *and* Bluetooth-Classic).
2. Start with `python server.py --source serial`. (Desktop UI: swap the `SimulatedSource()` line
   in `app.py`'s `make_source()` for `SerialSource(...)`.)
3. Firmware emits one line per reading: `ZONE,SENSOR,VALUE,STATE,TIMESTAMP\n` (e.g.
   `BASEMENT,WATER,340,ALARM,00:14:02`). Commands come back as `CMD,ZONE,SENSOR,ACTION\n`.

### Architecture (why it's transport-agnostic)

Input is split into swappable concerns, so *how* data arrives never touches the UI:

- **`core.py`** — the canonical `Reading`/`Command` model + the `Source` and `Codec` interfaces
  (`LineCodec` CSV, `JsonCodec`). No GUI-framework dependency, so both frontends share it.
- **`transports.py`** — adapters: `HttpIngestSource` (WiFi/ESP32, default), `SimulatedSource`,
  `SerialSource`. `WebSocketSource` and `BleSource` are ready stubs.
- **`config.py`** — sensors, thresholds, colours, timing, ports, the `ZONE_ALIASES` /
  `FIELD_TO_SENSOR` maps, and the HVAC/preservation tuning constants.
- **`hvac.py`** — predictive conditioning controller (effort + mode, gradual ramp), fed the same
  Readings from `Hub._on_reading`; setpoints reuse the TEMP/HUMIDITY *warn* bands.
- **`forecast.py`** — the `ForecastSource` interface: `SimulatedForecast` (offline default) and
  `HttpForecast` (Open-Meteo, no key, falls back to sim on any failure).
- **`preservation.py`** — the offline Arrhenius PI / TWPI engine, fed the same Readings.
- **`storage.py`** — SQLite + daily CSV logging + in-memory plot buffers.
- **`security.py`** — PBKDF2 login, roles, per-IP rate limiting.
- **`anomaly.py`** — the shared anomaly-detection engine.
- **`server.py` + `static/index.html`** — the web UI (stdlib HTTP + SSE; charts and window
  manager in `index.html`, no build step). `static/login.html` is the sign-in page.
- **`building.py` + `static/js/building-css3d.js`** — the 3D building view; all geometry is data
  in `building.py`. See [BUILDING.md](BUILDING.md).
- **`panels.py` + `app.py`** — the desktop UI.

### Local data logging (no Postgres)

- **`museumguard.sqlite`** — tables `readings`, `events` (state transitions), `audit` (logins +
  overrides).
- **`logs/readings-YYYY-MM-DD.csv`** — a daily CSV mirror of every reading (opens in Excel/pandas).

Both are runtime artifacts and git-ignored.

### Security notes — web dashboard login

- Two tiers: `viewer` (page access) and `guard` (overrides); `guard` is a strict superset,
  enforced in `security.role_satisfies`.
- Passwords are salted PBKDF2-SHA256 (200k iterations), compared with `hmac.compare_digest`; a
  wrong/unknown username still burns a PBKDF2 round so it isn't measurably faster.
- Login is rate-limited per client IP: 5 failures in a 5-minute window locks that IP out for 5
  minutes. This blocks *online* guessing; the iteration count is what defends offline.
- **Not yet done: TLS.** The login still posts the password in the clear over plain HTTP. Held
  off until the Raspberry Pi deployment shape is settled; until then, keep this off open/shared
  networks.
- Session tokens (`Hub.tokens`) are in-memory only and die with the process — by design.

### Security notes — is the Arduino ↔ laptop link safe?

**Short answer: the login here protects the dashboard UI, not the radio link.**

- The Arduino Uno has **no built-in radio**. Bluetooth means bolting on an **HC-05/06 (Classic
  SPP)** or **HM-10 (BLE)** — both **weak at the RF layer** (legacy pairing / "Just Works" can be
  sniffed/spoofed). Changing the PIN, disabling discoverability and MAC-binding raises the bar but
  is **not** real security.
- **Most secure for the demo: stay wired (USB serial)** — no RF attack surface.
- **If Bluetooth is required, secure it at the application layer** — treat the link as untrusted
  and authenticate every frame:

  ```
  frame = payload || counter || HMAC-SHA256(shared_key, payload || counter)
  ```

  - HMAC gives integrity + authenticity so a `DISARM`/`RESET` **cannot be forged**; the monotonic
    `counter` blocks **replay**. Sensor telemetry isn't confidential, so authenticity beats
    encryption. Drop-in point: verify the HMAC in `core.LineCodec.decode_reading` and append it in
    `encode_command`. **Not wired in this POC** — the documented next step.

The MVP login is a single shared credential per tier — a POC gate, explicitly not a hardened
multi-user auth system.
