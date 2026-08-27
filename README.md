# Smart Rampart — End-to-End Test Runbook

Environmental & security monitoring: an **ESP32 node (WiFi)** POSTs sensor
readings to a **dashboard server on the laptop**; the dashboard shows live
status and sends override/ARM/DISARM commands back on the POST reply.

Four sensors, all in the **Basement** zone: **water level, temperature,
humidity and fire**.

> **Goal of this doc:** get from cold laptop to a working end-to-end demo as fast
> as possible tomorrow morning. Follow it top to bottom.

---

## 0. What talks to what

```
  ESP32 BASE01 (water, fire, temp, humidity) ──POST readings──▶ ┐
  Pico W BASE01 (water, optional second node) ─POST──────────▶ │
                                      ◀────cmd on reply─────── ┘
                            Laptop: dashboard/server.py  ──▶ browser
                                    (http://<laptop-ip>:8000)
```

- Nodes are HTTP **clients**; the laptop is the **server**. Commands ride back on
  each node's POST reply (no inbound connection to the node — works behind NAT).
- Everything is on **one WiFi network**. Use a **phone/laptop hotspot**, not
  venue/guest WiFi (guest networks often block device-to-device traffic).

---

## 1. Before anything else — sanity check (2 min, no hardware)

Prove the software works with the built-in simulator first. If this fails, fix
it before touching hardware. **No code editing** — just pass `--source sim`:

```bash
cd dashboard
python server.py --source sim        # fake data, no hardware, binds 127.0.0.1:8000
```

Open <http://127.0.0.1:8000>. You'll hit the sign-in page first — log in as
`viewer` (below). You should then see live charts moving, status tiles, and an
event log. Log in again as `guard` via **Agent login** in the top bar, hit
**ARM/DISARM/Reset** — the banner and log react. That's the whole UI working. **Stop it with Ctrl+C**, then move to step 2
(drop `--source sim` — the real ESP32 path is the default).

> `--source` picks where data comes from: `http` (default, real ESP32 over
> WiFi), `sim` (fake data), or `serial` (USB/Bluetooth Arduino). Nothing in the
> code needs changing between them.
>
> There is also a **3D building view** in the top bar (Building / Graphs /
> Simple). By default only the basement room has sensors in it; add
> `--demo-rooms` to populate the other 11 with simulated activity for a
> showpiece run. Off by default so every reading on screen is a real one.
> See [`dashboard/BUILDING.md`](dashboard/BUILDING.md).

**Demo login** — two tiers (see [`dashboard/README.md`](dashboard/README.md)):

| Username | Password          | Gates |
|----------|-------------------|-------|
| `viewer` | `N1KOM%YLHfN953J` | Loading the web dashboard at all (sign-in page at `/`) |
| `guard`  | `eBDTCBxO5D#edpT` | The **ARM / DISARM / Reset** controls, via the in-page "Agent login" |

You sign in as `viewer` to see the page; a `viewer` can watch but not act. Only
`guard` unlocks the overrides. Login is rate-limited per IP (5 fails → 5 min).

---

## 2. Start the real server (so nodes can reach it)

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

Write that IP down — call it `LAPTOP_IP`. Confirm the server is reachable:
from a phone browser on the same hotspot, open `http://LAPTOP_IP:8000` — the
dashboard should load. If it doesn't, it's a **network/firewall** problem, not a
code problem (see Troubleshooting).

> Windows may pop a **firewall prompt** the first time — allow Python on
> **Private** networks. If you missed it: allow `python.exe` through Windows
> Defender Firewall for the hotspot (Private) profile.

---

## 3. Flash / port the nodes

### 3a. ESP32 (Basement — water + fire + temp/humidity, `esp32_node/esp32_node.ino`)

Arduino IDE **or** Wokwi. This is the node that has actually been tested end to
end ("tested with 3 sensors"): it POSTs `water`, `fire`, `temp`, `humidity` as
`BASE01` → BASEMENT. See `esp32_node/libraries.txt` and `esp32_node/diagram.json`
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
   - For **Wokwi**: keep `WIFI_SSID = "Wokwi-GUEST"`, `WIFI_PASS = ""`, and
     `SERVER` must be a **public URL** (Wokwi cloud can't reach a LAN IP) — run
     `ngrok http 8000` and use the `https://…ngrok…/api/ingest` URL. (HTTPS on
     ESP32 also needs `WiFiClientSecure` + `setInsecure()` — ask if needed.)
   - Real hardware on the hotspot: use `LAPTOP_IP` directly, plain HTTP.
4. Wiring: water sensor → GPIO34, potentiometer (fire index) → GPIO35, DHT →
   GPIO15, onboard LED on GPIO2 is the local water alarm. GPIO34/35 have no
   internal pull — tie an unused one to GND through 10k or it reads noise.
5. Upload. Open **Serial Monitor @ 115200** — you should see
   `connected: <node-ip>` then `POST {...} -> 200` and the `reply:` line.

### 3b. Pico W (Basement water — `WINDOWS/main.py`, MicroPython)

1. MicroPython flashed on the Pico W; open **Thonny**.
2. Edit the top of `main.py`:
   ```python
   WIFI_SSID = "YourHotspotName"
   WIFI_PASS = "YourHotspotPass"
   SERVER = "http://LAPTOP_IP:8000/api/ingest"
   ZONE = "BASE01"       # BASE01 → BASEMENT (the only zone there is)
   ```
   > The Pico is **optional** — the ESP32 in 3a already covers basement water.
   > Only run both if you want a second physical node.
3. Save as `main.py` **onto the Pico**. Reset — the onboard LED settles solid
   once WiFi connects; Thonny's shell prints `sent {...} -> 200`.

---

## 4. Bring it together (the actual end-to-end test)

1. Server running from step 2 (`--host 0.0.0.0`, default `--source http`).
2. Power the ESP32 and Pico on the same hotspot.
3. Open `http://LAPTOP_IP:8000` on the laptop (and/or a phone).

Within ~2 s the four Basement tiles should go live. Then walk the checklist.

### Acceptance checklist (from the spec §10)

- [ ] **Live values** — temp/humidity update on the dashboard within ~2 s.
- [ ] **Water flood** — wet the basement sensor → WATER tile red and **latches**
      (stays red after drying) until an agent Resets it.
- [ ] **Fire alert** — turn the pot past ~70 → a full-screen 🔥 popup appears on
      the dashboard; **Acknowledge & DISARM** clears it and silences the node.
- [ ] **Login gate** — as `viewer` only, the ARM/Reset controls are refused;
      they unlock after the in-page `guard` login.
- [ ] **Override round-trip** — log in, hit **Reset** on a latched alarm →
      clears on the dashboard **and** the node's LED/buzzer within ~2 s.
- [ ] **Disconnect** — power off the node → all four tiles show **DISCONNECTED**
      within ~6 s, and the header flips to DISCONNECTED; power it back on and
      both recover on the next POST.
- [ ] **Resilience** — unplug one sensor → the node's other readings keep flowing.

### Verify the command path by hand

1. Log in as `guard` (`eBDTCBxO5D#edpT`) via **Agent login**.
2. Trip a latching alarm (wet the water sensor).
3. Click **Reset** on that tile.
4. Watch the node's **Serial Monitor**: the next `POST … -> 200` reply contains
   `"cmd":"RESET"`, and the node acts on it (LED off). End-to-end confirmed.

---

## 5. Known gaps to decide on in the morning

- **Firmware sensor coverage:** `esp32_node.ino` sends **water, fire (pot),
  temp and humidity** for `BASE01` — exactly the four the dashboard shows, so
  there are no dead tiles. The old Gallery zone (LDR light + PIR motion) is
  **gone**: no firmware ever sent it. To bring it back, add the `SensorDef`s and
  a `ZONE_ALIASES` entry in `dashboard/config.py` plus the two `FIELD_TO_SENSOR`
  lines — nothing else in the dashboard is zone-aware.
- **Fire is a potentiometer stand-in**, not a real flame/smoke sensor: a 0..100
  index, warn at 50, alarm (latched) at 70. Swap the sensor and the thresholds in
  `BASEMENT.FIRE` together.
- **Wokwi vs. real WiFi:** cloud Wokwi can't reach `LAPTOP_IP` — needs the ngrok
  tunnel from step 3a. Real hardware on the hotspot does not.

---

## 6. Troubleshooting (fast)

| Symptom | Most likely cause | Fix |
|---|---|---|
| Node Serial shows WiFi connecting forever | wrong SSID/pass; using a password on an open AP | fix creds; for open/Wokwi AP leave pass `""` |
| `POST … -> -1` or connection refused | wrong `LAPTOP_IP`/port, or server not on `0.0.0.0` | re-check IP with `ipconfig`; start with `--host 0.0.0.0` |
| Node connects but dashboard tile never appears | firewall blocking, or guest-WiFi client isolation | allow `python.exe` on Private; use a **hotspot**, not guest WiFi |
| Phone can't open `http://LAPTOP_IP:8000` | same as above | firewall / wrong network |
| Tile shows but stuck / stale | node stopped POSTing | check Serial; tile flips to DISCONNECTED after 6 s |
| Can't get past the sign-in page | wrong tier | that page wants `viewer`; `guard` works there too |
| Controls do nothing | logged in as `viewer` only | use **Agent login** with the `guard` creds |
| Locked out after retries | per-IP rate limit (5 fails) | wait 5 min, or restart the server |
| Node POSTs 200 but no tile appears | node `ZONE` id is not `BASE01` | only `BASE01`/`BASEMENT` map to a zone now (see `dashboard/config.py` `ZONE_ALIASES`); anything else is accepted and dropped |

---

## Quick reference

```bash
# run the dashboard (from repo root)
cd dashboard && python server.py --host 0.0.0.0      # http://LAPTOP_IP:8000

# no-hardware demo: add --source sim
# find laptop IP (Windows):  ipconfig   (look for the hotspot adapter IPv4)
```

- Dashboard code + deeper docs: [`dashboard/README.md`](dashboard/README.md)
- ESP32 firmware: [`esp32_node/esp32_node.ino`](esp32_node/esp32_node.ino)
- Pico water node: [`WINDOWS/main.py`](WINDOWS/main.py)
- Login: `viewer` / `N1KOM%YLHfN953J` (page), `guard` / `eBDTCBxO5D#edpT` (controls)
