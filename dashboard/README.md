# MuseumGuard — Dashboard

Monitoring station for the MuseumGuard sensor rig (temp/humidity, light, water
level, motion across a Gallery + Basement zone). Live charts in floating,
snappable windows, colour-coded alarm states, a flashing alarm banner,
login-gated alarm override/disarm, and zero-install local logging.

Runs today against a built-in **simulator** (no hardware needed); swaps to a real
Arduino over USB/Bluetooth by changing one line.

## Status

Working end to end, on simulated data:

- ✅ Web UI (stdlib server + SSE, canvas charts, floating-window workspace).
- ✅ Desktop UI (PySide6 + pyqtgraph docks) — feature-equivalent.
- ✅ Simulator with latching water/motion alarms that honour ARM/DISARM/RESET.
- ✅ SQLite + daily CSV logging, audit trail for logins and overrides.
- ✅ PBKDF2 login gate on the override controls.
- ✅ `HttpIngestSource` (**WiFi / ESP32**) — the default source. ESP32 zone
  nodes POST readings to `/api/ingest`; the pending override rides back on the
  same reply (no inbound connection to the node, so it works behind NAT and in
  Wokwi). Server-side latching, ARM/DISARM gating, and a 6 s heartbeat watchdog
  live in the source. See *Connecting the ESP32 over WiFi* below.
- 🔌 `SerialSource` (USB / Bluetooth-Classic) is written but **not yet run
  against real firmware** — a one-line swap in `make_source()`.
- 🚧 `WebSocketSource` (push WebSocket) and `BleSource` (HM-10 BLE) remain
  deliberate stubs; the WiFi path above uses plain HTTP POST instead.
- 🚧 HMAC frame authentication for the radio link is designed and documented
  below, but **not wired in** — see *Security notes*.

## Two frontends, one engine

Pick whichever you prefer — they share the same engine and the same database:

| | Web (recommended) | Desktop |
|---|---|---|
| Run | `python server.py` → http://127.0.0.1:8000 | `python app.py` |
| UI files | `server.py` + `static/index.html` | `app.py` + `panels.py` |
| Dependencies | **none** (stdlib only) | PySide6 + pyqtgraph |
| Graph controls | wheel-zoom, drag-pan, live/pause, hover readout | pan/zoom via pyqtgraph |
| Panels | floating windows: move, resize, edge-snap, minimise/maximise/close, taskbar, layout remembered | docks: drag/float/resize/close |

Shared by both: `config.py`, `core.py`, `transports.py`, `storage.py`,
`security.py`. Only the presentation layer differs.

## Quick start — web (no dependencies)

```bash
python server.py            # from the dashboard/ folder
# then open http://127.0.0.1:8000
```

Uses only the Python standard library: no Flask/FastAPI, no npm, no CDN. The
charts are drawn on plain `<canvas>` with **no charting library**, so it works
with no internet at the venue. Live data arrives over Server-Sent Events.

Options: `python server.py --port 9000 --host 0.0.0.0`

> The login posts a plaintext password over HTTP, so it binds to `127.0.0.1` by
> default. Don't expose it beyond the demo machine without TLS in front.

## Quick start — desktop

```bash
pip install -r requirements.txt
python app.py          # from the dashboard/ folder
# or, from the repo root:  python -m dashboard.app
```

A window opens streaming simulated data. No Arduino required.

## Demo login

Read-only monitoring needs no login. The **override/disarm controls** are gated:

| Username | Password |
|----------|----------------------|
| `guard`  | `MuseumGuard!2026`   |

The password is **not** stored in source — only a salted PBKDF2-SHA256 hash lives
in `security.py`. To change it, follow the regeneration one-liner in that file and
replace `_SALT_HEX` / `_HASH_HEX`.

## Using the dashboard

**Graph controls (web):** mouse-wheel over a chart to **zoom** the time axis,
**drag** to scroll back through history (the chart shows `⏸ PAUSED`),
**double-click** or the **● Live** button to jump back to now. Hovering shows a
crosshair with the exact value and timestamp. Each window's title bar carries a
time-scale selector (30 s / 2 min / 5 min / 30 min / All).

**Windows (web):** every sensor is a floating window in a desktop-style
workspace.

- **Move** by dragging the title bar; **resize** from any edge or corner.
- **Snap** like Windows: drag to the top edge to maximise, to the left/right
  edge for a half, into a corner for a quarter, to the bottom edge for a bottom
  half. A translucent ghost previews the target before you drop.
- Title-bar buttons **─ ▢ ✕** minimise / maximise / close; double-clicking the
  title bar also toggles maximise. Dragging a maximised window restores it under
  the cursor.
- The **taskbar** along the bottom has a button per sensor, its dot carrying the
  live state colour: click to focus, click again to minimise, click a closed or
  minimised one to bring it back.
- The sidebar **Panels** checkboxes open/close windows too, and **‹** collapses
  the whole sidebar for more chart space.
- **Reset layout** (top bar) restores the default two-column tiling and reopens
  everything. Otherwise the arrangement — positions, sizes, z-order, what's
  closed, sidebar state — is saved to `localStorage` and restored on reload.

**Docks (desktop):** panels are pyqtgraph docks — drag to rearrange, drag edges
to resize, drag out to float, **×** to close, and the **View** menu re-adds
closed ones.

Common to both:

- Warn/alarm zones are shaded on every chart; the panel border and read-out
  recolour with state (green OK, amber warning, red alarm).
- A **banner** across the top names the zones currently in ALARM (it flashes in
  the desktop UI).
- **Status tiles** give a one-glance value + state per sensor.
- **Controls**: log in, then **ARM/DISARM** the security system or **Reset** a
  latched water/motion alarm. `DISARM` is the "someone's cleaning, don't fire the
  water alarm" switch. Every override is written to the audit log.
- **Event log** shows state transitions, commands, and connection changes.
- A **CONNECTED / DISCONNECTED** indicator; a dropped link marks sensors
  DISCONNECTED instead of showing stale data as if live.

## Connecting the ESP32 over WiFi (default)

`make_source()` returns `HttpIngestSource()` out of the box, so the server is
ready for the ESP32 nodes with no change:

1. Run `python server.py --host 0.0.0.0` so the nodes (on the same WiFi) can
   reach the laptop. Note the laptop's LAN IP.
2. Point each node's `SERVER` at `http://<laptop-ip>:8000/api/ingest`
   (see `esp32_node/esp32_node.ino` and `WINDOWS/main.py`).
3. Each node POSTs one JSON blob per cycle; the server **fans it out** into the
   per-sensor model using `ZONE_ALIASES` + `FIELD_TO_SENSOR` in `config.py`:

   ```json
   {"zone": "GAL01", "temp": 21.4, "humidity": 50, "light": 300, "state": "OK"}
   ```

   `GAL01`→`GALLERY`, `temp`→`TEMP`, etc. Unmapped fields (e.g. `air`) are
   ignored. The reply carries the pending command: `{"ok": true, "cmd": "RESET"}`
   (one of `AUTO`/`OFF`/`ARM`/`DISARM`/`RESET`), which the firmware acts on.

To demo without hardware, set `make_source()` back to `SimulatedSource()`.

## Connecting a real Arduino (USB or Bluetooth)

1. Set `SERIAL_PORT` / `SERIAL_BAUD` in `config.py` (on Windows a paired HC-05/06
   Bluetooth module appears as an outgoing **COM port**, so the same code path
   handles USB *and* Bluetooth-Classic — only the port name differs).
2. In `make_source()` — in `server.py` for the web UI, or `app.py` for the
   desktop UI — comment the `SimulatedSource()` line and uncomment the
   `SerialSource(...)` line.
3. Firmware should emit one line per reading:
   `ZONE,SENSOR,VALUE,STATE,TIMESTAMP\n`
   e.g. `BASEMENT,WATER,340,ALARM,00:14:02`. The dashboard sends commands back as
   `CMD,ZONE,SENSOR,ACTION\n` (e.g. `CMD,BASEMENT,WATER,RESET`, `CMD,SYSTEM,ALL,DISARM`).

Nothing else in the app changes — the UI, storage and plots only ever see the
canonical `Reading`/`Command` model.

## Architecture (why it's transport-agnostic)

Input is split into three swappable concerns, so *how* data arrives is a late
decision that never touches the UI:

- **`core.py`** — the canonical `Reading`/`Command` model + the `Source` and
  `Codec` interfaces (with `LineCodec` CSV and `JsonCodec`). The whole app imports
  only from here. Deliberately has **no GUI-framework dependency** (its `Event` is
  a plain observer, not a Qt signal) so both frontends share it.
- **`transports.py`** — adapters: `SimulatedSource`, `SerialSource` (USB +
  Bluetooth-Classic). `WebSocketSource` (WiFi/ESP) and `BleSource` (HM-10 BLE) are
  ready stubs — adding a transport is one small adapter, no UI changes.
- **`config.py`** — sensors, thresholds, colours, timing, ports.
- **`storage.py`** — SQLite + daily CSV logging + in-memory plot buffers.
- **`security.py`** — PBKDF2 login (+ documented link-auth upgrade path).
- **`server.py` + `static/index.html`** — the web UI (stdlib HTTP + SSE; canvas
  charts and the window manager both live in `index.html`, no build step).
- **`panels.py` + `app.py`** — the desktop UI (pyqtgraph widgets, main window).

## Local data logging (no Postgres)

Everything is logged locally, zero install:

- **`museumguard.sqlite`** — tables `readings`, `events` (state transitions),
  `audit` (logins + overrides).
- **`logs/readings-YYYY-MM-DD.csv`** — a daily CSV mirror of every reading,
  opens directly in Excel/pandas.

Both are runtime artifacts and are git-ignored.

## Security notes — is the Arduino ↔ laptop link safe?

**Short answer: the login here protects the dashboard UI, not the radio link.**

- The Arduino Uno has **no built-in radio**. Bluetooth means bolting on an
  **HC-05/06 (Classic SPP)** or **HM-10 (BLE)** — both are **weak at the RF
  layer**. Classic legacy pairing and BLE "Just Works" can be sniffed/spoofed.
  Changing the default PIN (not `1234`/`0000`), disabling discoverability, and
  MAC-binding to the laptop raises the bar but is **not** real security.
- **Most secure option for the demo: stay wired (USB serial).** A physical link
  removes the RF attack surface entirely.
- **If Bluetooth is required, secure it at the application layer** — treat the link
  as an untrusted pipe and authenticate every frame:

  ```
  frame = payload || counter || HMAC-SHA256(shared_key, payload || counter)
  ```

  - HMAC gives integrity + authenticity so a `DISARM`/`RESET` command **cannot be
    forged**; the monotonic `counter` blocks **replay** of a captured command.
  - Sensor telemetry isn't confidential, so authenticity beats encryption. Add an
    AEAD (ChaCha20-Poly1305 / ASCON) later only if confidentiality is needed.
  - Drop-in point: verify the HMAC in `core.LineCodec.decode_reading` (reject on
    mismatch) and append it in `encode_command`. **Not wired in this POC** — this
    is the documented next step.

The MVP login is a single shared credential — a POC gate, explicitly not a
hardened multi-user auth system.
