# MuseumGuard — End-to-End Test Runbook

Environmental & security monitoring: **ESP32 zone nodes (WiFi)** POST sensor
readings to a **dashboard server on the laptop**; the dashboard shows live
per-zone status and sends override/ARM/DISARM commands back on the POST reply.

> **Goal of this doc:** get from cold laptop to a working end-to-end demo as fast
> as possible tomorrow morning. Follow it top to bottom.

---

## 0. What talks to what

```
  ESP32 (Gallery)  ──POST readings──▶  ┐
  Pico W (Basement water) ─POST──────▶ │  Laptop: dashboard/server.py  ──▶ browser
                    ◀──cmd on reply───  ┘        (http://<laptop-ip>:8000)
```

- Nodes are HTTP **clients**; the laptop is the **server**. Commands ride back on
  each node's POST reply (no inbound connection to the node — works behind NAT).
- Everything is on **one WiFi network**. Use a **phone/laptop hotspot**, not
  venue/guest WiFi (guest networks often block device-to-device traffic).

---

## 1. Before anything else — sanity check (2 min, no hardware)

Prove the software works with the built-in simulator first. If this fails, fix
it before touching hardware.

```bash
cd dashboard
python server.py            # binds 127.0.0.1:8000
```

Temporarily use the simulator so you see data with no ESP32:
in `dashboard/server.py`, in `make_source()`, make it:

```python
# return HttpIngestSource()   # ← the real ESP32 path (put this back in step 4)
return SimulatedSource()      # ← fake data, no hardware
```

Open <http://127.0.0.1:8000>. You should see live charts moving, status tiles,
and an event log. Log in (below), hit **ARM/DISARM/Reset** — the banner and log
react. **Once this works, put `make_source()` back to `HttpIngestSource()`.**

**Demo login** (read-only monitoring needs no login; controls do):

| Username | Password           |
|----------|--------------------|
| `guard`  | `MuseumGuard!2026` |

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

### 3a. ESP32 (Gallery — temp/humidity, `esp32_node/esp32_node.ino`)

Arduino IDE **or** Wokwi.

1. Board package: **esp32 by Espressif** installed.
2. Libraries: **DHT sensor library** (Adafruit), **LiquidCrystal_I2C**.
3. Edit the top of `esp32_node.ino`:
   ```cpp
   const char* WIFI_SSID = "YourHotspotName";
   const char* WIFI_PASS = "YourHotspotPass";
   const char* SERVER    = "http://LAPTOP_IP:8000/api/ingest";   // ← your IP
   const char* ZONE      = "GAL01";                              // GAL01 → GALLERY
   ```
   - For **Wokwi**: keep `WIFI_SSID = "Wokwi-GUEST"`, `WIFI_PASS = ""`, and
     `SERVER` must be a **public URL** (Wokwi cloud can't reach a LAN IP) — run
     `ngrok http 8000` and use the `https://…ngrok…/api/ingest` URL. (HTTPS on
     ESP32 also needs `WiFiClientSecure` + `setInsecure()` — ask if needed.)
   - Real hardware on the hotspot: use `LAPTOP_IP` directly, plain HTTP.
4. Upload. Open **Serial Monitor @ 115200** — you should see
   `connected: <node-ip>` then `POST {...} -> 200`.

### 3b. Pico W (Basement water — `WINDOWS/main.py`, MicroPython)

1. MicroPython flashed on the Pico W; open **Thonny**.
2. Edit the top of `main.py`:
   ```python
   WIFI_SSID = "YourHotspotName"
   WIFI_PASS = "YourHotspotPass"
   SERVER = "http://LAPTOP_IP:8000/api/ingest"
   ZONE = "GAL01"        # ← change to "BASE01" so it maps to BASEMENT
   ```
   > Note: as shipped `ZONE = "GAL01"`. For the basement water node set it to
   > `"BASE01"` (→ BASEMENT.WATER on the dashboard).
3. Save as `main.py` **onto the Pico**. Reset — the onboard LED settles solid
   once WiFi connects; Thonny's shell prints `sent {...} -> 200`.

---

## 4. Bring it together (the actual end-to-end test)

1. Server running from step 2 (`--host 0.0.0.0`, `make_source()` =
   `HttpIngestSource()`).
2. Power the ESP32 and Pico on the same hotspot.
3. Open `http://LAPTOP_IP:8000` on the laptop (and/or a phone).

Within ~2 s each node's zone tile should go live. Then walk the checklist.

### Acceptance checklist (from the spec §10)

- [ ] **Live values** — Gallery temp/humidity update on the dashboard within ~2 s.
- [ ] **Light warning** — cover the LDR → LIGHT tile goes amber/red. *(needs LDR
      in firmware — see Known gaps.)*
- [ ] **Water flood** — wet the basement sensor → WATER tile red and **latches**
      (stays red after drying) until an agent Resets it.
- [ ] **Motion** — ARMED + wave at PIR → MOTION alarm + banner; DISARMED → no
      alarm. *(needs PIR in firmware — see Known gaps.)*
- [ ] **Login gate** — logged out, the ARM/Reset controls are disabled/refused.
- [ ] **Override round-trip** — log in, hit **Reset** on a latched alarm →
      clears on the dashboard **and** the node's LED/buzzer within ~2 s.
- [ ] **Disconnect** — power off a node → its zone shows **DISCONNECTED** within
      ~6 s; the other zone keeps updating.
- [ ] **Resilience** — unplug one sensor → the node's other readings keep flowing.

### Verify the command path by hand

1. Log in (`guard` / `MuseumGuard!2026`).
2. Trip a latching alarm (wet the water sensor).
3. Click **Reset** on that tile.
4. Watch the node's **Serial Monitor**: the next `POST … -> 200` reply contains
   `"cmd":"RESET"`, and the node acts on it (LED off). End-to-end confirmed.

---

## 5. Known gaps to decide on in the morning

- **Firmware sensor coverage:** `esp32_node.ino` currently sends **temp +
  humidity** only (plus `air` from a pot, which the server ignores). **LDR light
  and PIR motion are not in the firmware yet.** The server already accepts
  `light`/`motion` fields — the moment the firmware sends them, the tiles light
  up. Decide: add LDR + PIR (recommended: PIR via **hardware interrupt**, see the
  chat discussion) before or after the first successful temp/humidity run.
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
| Controls do nothing | not logged in | log in with the demo creds |
| Zone name wrong on dashboard | node `ZONE` id | `GAL01`→GALLERY, `BASE01`→BASEMENT (see `dashboard/config.py` `ZONE_ALIASES`) |

---

## Quick reference

```bash
# run the dashboard (from repo root)
cd dashboard && python server.py --host 0.0.0.0      # http://LAPTOP_IP:8000

# no-hardware demo: set make_source() -> SimulatedSource() in server.py
# find laptop IP (Windows):  ipconfig   (look for the hotspot adapter IPv4)
```

- Dashboard code + deeper docs: [`dashboard/README.md`](dashboard/README.md)
- ESP32 firmware: [`esp32_node/esp32_node.ino`](esp32_node/esp32_node.ino)
- Pico water node: [`WINDOWS/main.py`](WINDOWS/main.py)
- Login: `guard` / `MuseumGuard!2026`
