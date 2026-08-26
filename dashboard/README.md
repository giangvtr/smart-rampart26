# MuseumGuard — Dashboard

Monitoring station for the MuseumGuard sensor rig: four Basement sensors —
**water level, temperature, humidity and fire**. Live charts in a 2x2 of
floating, snappable windows — or a phone-friendly **Simple** board of
colour-coded value boxes — colour-coded alarm states, a flashing alarm banner,
a full-screen fire alert, login-gated alarm override/disarm, and zero-install
local logging.

Talks to the real **ESP32 zone nodes over WiFi** out of the box; `--source sim`
falls back to a built-in simulator with no hardware at all.

A third view is a **see-through 3D museum** — 3 floors, 12 rooms, nine of them
galleries hung with paintings and filled with statues, vitrines and armour —
where you click a room to get its dashboard. Drawn with CSS 3D transforms, so
it downloads nothing. One room is the real rig; the other 11 are **empty unless
you pass `--demo-rooms`**. See **[BUILDING.md](BUILDING.md)**.

## Status

Working end to end, on simulated data:

- ✅ Web UI (stdlib server + SSE, canvas charts, floating-window workspace, plus
  a simple value-box view that works on a phone).
- ✅ Desktop UI (PySide6 + pyqtgraph docks) — feature-equivalent.
- ✅ Simulator with latching water/fire alarms that honour ARM/DISARM/RESET.
- ✅ SQLite + daily CSV logging, audit trail for logins and overrides.
- ✅ Two-tier PBKDF2 login: a `viewer` password gates the dashboard itself, a
  separate `guard` password gates the override/disarm controls.
- ✅ Login attempts are rate-limited per IP (5 fails → 5 min lockout).
- ✅ 3D building view (CSS transforms, no dependencies) with per-room
  drill-down and hash deep links; `--demo-rooms` populates the 11 simulated
  rooms, and it is off by default.
- ✅ `HttpIngestSource` (**WiFi / ESP32**) — the default source. ESP32 zone
  nodes POST readings to `/api/ingest`; the pending override rides back on the
  same reply (no inbound connection to the node, so it works behind NAT and in
  Wokwi). Server-side latching, ARM/DISARM gating, and a 6 s heartbeat watchdog
  live in the source. See *Connecting the ESP32 over WiFi* below.
- ✅ Full-screen **fire alert** on `BASEMENT.FIRE` going ALARM, with an
  acknowledge button that disarms (silences) the node.
- 🔌 `SerialSource` (USB / Bluetooth-Classic) is written but **not yet run
  against real firmware** — select it with `--source serial`.
- 🚧 `WebSocketSource` (push WebSocket) and `BleSource` (HM-10 BLE) remain
  deliberate stubs; the WiFi path above uses plain HTTP POST instead.
- 🚧 HMAC frame authentication for the radio link is designed and documented
  below, but **not wired in** — see *Security notes*.

## Two frontends, one engine

Pick whichever you prefer — they share the same engine and the same database:

| | Web (recommended) | Desktop |
|---|---|---|
| Run | `python server.py` → http://127.0.0.1:8000 | `python app.py` |
| UI files | `server.py` + `static/index.html` (+ `static/login.html`) | `app.py` + `panels.py` |
| Dependencies | **none** (stdlib only) | PySide6 + pyqtgraph |
| Graph controls | wheel-zoom, drag-pan, live/pause, hover readout | pan/zoom via pyqtgraph |
| On a phone | drawer sidebar, Simple boxes, graphs as a scrolling stack | — |
| Panels | floating windows: move, resize, edge-snap, minimise/maximise/close, taskbar, layout remembered | docks: drag/float/resize/close |
| Simple view | value-only boxes, mobile-ready | — |

Shared by both: `config.py`, `core.py`, `transports.py`, `storage.py`,
`security.py`, `anomaly.py`. Only the presentation layer differs.

## Quick start — web (no dependencies)

```bash
python server.py            # from the dashboard/ folder
# then open http://127.0.0.1:8000
```

Uses only the Python standard library: no Flask/FastAPI, no npm, no CDN. The
charts are drawn on plain `<canvas>` with **no charting library**, so it works
with no internet at the venue. Live data arrives over Server-Sent Events.

The 3D building view keeps that promise too: it is CSS transforms and a single
864-line script, so it downloads nothing either. It is driven by one finger
and a pinch on a phone as well as by a mouse.

Options: `python server.py --port 9000 --host 0.0.0.0 --source sim --demo-rooms`

`--source` picks where readings come from — `http` (default: real ESP32 over
WiFi), `sim` (fake data, no hardware), or `serial` (USB/Bluetooth Arduino, port
in `config.py`). Nothing in the code needs editing to switch.

`--demo-rooms` populates the 11 **simulated** museum rooms behind the 3D view.
It is **off by default**: without it the dashboard has exactly the four real
basement sensors and every reading on screen is a real measurement. See
*The 3D building view* below.

You'll land on a sign-in page first — that's the `viewer` gate (see *Demo
login* below). Signing in sets a cookie; the dashboard itself opens after.

> The login posts a plaintext password over HTTP, so it binds to `127.0.0.1` by
> default. Don't expose it beyond the demo machine without TLS in front
> (deferred — see *Security notes*).

## Quick start — desktop

```bash
pip install -r requirements.txt
python app.py          # from the dashboard/ folder
# or, from the repo root:  python -m dashboard.app
```

A window opens streaming simulated data (the desktop app always uses the
simulator — `make_source()`'s default). No Arduino required. The desktop UI
has no sign-in page of its own — it opens straight into monitoring, and the
`guard` login gates the override controls (see below).

## Demo login

Two separate credentials, both gating different things:

| Username | Password          | Gates |
|----------|-------------------|-------|
| `viewer` | `N1KOM%YLHfN953J` | Loading the web dashboard at all (the sign-in page at `/`) |
| `guard`  | `eBDTCBxO5D#edpT` | The **override/disarm controls** (web + desktop), via the in-page "Agent login" |

Both frontends enforce the same rule: a `viewer` login can watch but not act —
only `guard` unlocks ARM/DISARM/Reset. The desktop app has no viewer gate on
the window itself, so `viewer` is effectively web-only there.

Neither password is stored in source — only salted PBKDF2-SHA256 hashes live in
`security.py` (`_ACCOUNTS`). To rotate one, run the regeneration one-liner at
the top of that file and replace the matching `salt` / `hash` entry.

Login attempts (either account) are rate-limited per source IP: 5 failures
locks that IP out for 5 minutes (`security.RateLimiter`).

## Using the dashboard

**Graph controls (web):** mouse-wheel over a chart to **zoom** the time axis,
**drag** to scroll back through history (the chart shows `⏸ PAUSED`),
**double-click** or the **● Live** button to jump back to now. Hovering shows a
crosshair with the exact value and timestamp. Each window's title bar carries a
time-scale selector (30 s / 2 min / 5 min / 30 min / All).

**Three views (web):** the **Building / Graphs / Simple** switch in the top bar.

- **Graphs** — the floating-window workspace, a 2x2 for the four-sensor live
  rig. This is the landing view.
- **Simple** — one box per sensor showing just its current value, filled with
  that sensor's state colour (green OK, amber warning, red alarm, grey
  disconnected; alarming boxes pulse). Handy for a wall display or a quick
  glance, and it's what phones land on.
- **Building** — the 3D museum. Click a room to open its dashboard in whichever
  of Graphs/Simple you last used.

Graphs and Simple always show **one room** — the live rig unless you picked
another in the building view; the subtitle names it, and the URL carries it
(`#/room/B1_ARCHIVE`) so a room is linkable. The choice of view is remembered.

The alarm banner follows where you are: building-wide in the building view,
scoped to the open room once you are inside one. The full-screen **fire alert**
is the exception — it is building-wide always, so it reaches you even while you
are looking at a room three floors up.

**On a phone** (≤ 760 px), the sidebar becomes a ☰ drawer that slides over the
content instead of eating half the screen (tap the dimmed area to close it), the
Simple boxes reflow to two columns, and Simple is the default view. The choice is
still yours — **Graphs** works on a phone too, it just stops floating:

- The panels become **one column** that scrolls **up and down**, in sensor order.
- Each chart keeps a readable ~700 px width and **scrolls left/right inside its
  own panel** — a full trace squeezed into 340 px is worth nothing. The value
  axis stays pinned to the left edge as you swipe.
- A panel **follows the live edge** until you swipe back in time, then stays
  where you left it; swipe back to the right edge to start following again.
- Move / resize / snap / maximise are off (there is nowhere to float to), but the
  time-scale picker, **● Live**, close, the taskbar and the sidebar toggles all
  work as usual. Rotate to a wide screen and the floating workspace comes back.

**Windows (web):** every sensor is a floating window in a desktop-style
workspace, laid out by default as a **2x2 filling the workspace** — four
sensors, two columns, no scrolling.

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
- **Reset layout** (top bar) restores the default 2x2 and reopens everything.
  Otherwise the arrangement — positions, sizes, z-order, what's closed, sidebar
  state — is saved to `localStorage` and restored on reload. (The saved-layout
  key is versioned; it was bumped when the Gallery sensors were dropped, so an
  old 8-window layout can't strand the four survivors in the bottom half.)
- With a single zone the redundant `BASEMENT ·` prefix is dropped from panel
  titles, status tiles, taskbar and reset buttons. It reappears on its own if a
  second zone is ever added to `config.SENSORS`.

**Docks (desktop):** panels are pyqtgraph docks — drag to rearrange, drag edges
to resize, drag out to float, **×** to close, and the **View** menu re-adds
closed ones.

Common to both:

- Warn/alarm zones are shaded on every chart; the panel border and read-out
  recolour with state (green OK, amber warning, red alarm).
- A **banner** across the top names the zones currently in ALARM (it flashes in
  the desktop UI), and a fire ALARM additionally raises a full-screen alert.
- **Status tiles** give a one-glance value + state per sensor.
- **Controls**: log in, then **ARM/DISARM** the security system or **Reset** a
  latched water/fire alarm. `DISARM` is mirrored to the nodes, which silence
  their local LED/buzzer — the "someone's cleaning, stop the noise" switch. It
  does **not** clear a server-side latch; that needs an explicit Reset. Every
  override is written to the audit log.
- **Event log** shows state transitions, commands, and connection changes.
- A **CONNECTED / DISCONNECTED** indicator; a dropped link marks sensors
  DISCONNECTED instead of showing stale data as if live.

## Connecting the ESP32 over WiFi (default)

`server.py` runs `--source http` out of the box, so it is ready for the ESP32
nodes with no change:

1. Run `python server.py --host 0.0.0.0` so the nodes (on the same WiFi) can
   reach the laptop. Note the laptop's LAN IP.
2. Point each node's `SERVER` at `http://<laptop-ip>:8000/api/ingest`
   (see `esp32_node/esp32_node.ino` and `WINDOWS/main.py`).
3. Each node POSTs one JSON blob per cycle; the server **fans it out** into the
   per-sensor model using `ZONE_ALIASES` + `FIELD_TO_SENSOR` in `config.py`:

   ```json
   {"zone": "BASE01", "water": 120, "fire": 12, "temp": 21.4, "humidity": 50,
    "state": "OK"}
   ```

   `BASE01`→`BASEMENT`, `temp`→`TEMP`, `pot`/`fire`→`FIRE`,
   `water`/`level`→`WATER`, etc. Unmapped fields (e.g. `air`, or a leftover
   `light`/`motion` from older firmware) are ignored. The
   reply carries the pending command: `{"ok": true, "cmd": "RESET"}` (one of
   `AUTO`/`OFF`/`ARM`/`DISARM`/`RESET`), which the firmware acts on.

`/api/ingest` is **not** behind the `viewer` cookie gate — that gate is for
browsers, and the firmware carries no session. The nodes are treated as
unauthenticated devices on the LAN, like a sensor bus; see *Security notes —
is the Arduino ↔ laptop link safe?* for what that does and does not buy you.

To demo without hardware, add `--source sim`.

## Connecting a real Arduino (USB or Bluetooth)

0. `pip install -r requirements.txt` — pulls in `pyserial` (the web UI needs
   nothing else; `PySide6`/`pyqtgraph` in there are for the desktop UI).
1. Set `SERIAL_PORT` / `SERIAL_BAUD` in `config.py` (on Windows a paired HC-05/06
   Bluetooth module appears as an outgoing **COM port**, so the same code path
   handles USB *and* Bluetooth-Classic — only the port name differs).
2. Start the web UI with `python server.py --source serial`. (The desktop UI
   has no flag: swap the `SimulatedSource()` line in `app.py`'s `make_source()`
   for the `SerialSource(...)` one.)
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
- **`transports.py`** — adapters: `HttpIngestSource` (WiFi/ESP32, the default),
  `SimulatedSource`, `SerialSource` (USB + Bluetooth-Classic). `WebSocketSource`
  (push WebSocket) and `BleSource` (HM-10 BLE) are ready stubs — adding a
  transport is one small adapter, no UI changes.
- **`config.py`** — sensors, thresholds, colours, timing, ports, and the
  `ZONE_ALIASES` / `FIELD_TO_SENSOR` maps for the ESP32 wire format.
- **`storage.py`** — SQLite + daily CSV logging + in-memory plot buffers.
- **`security.py`** — PBKDF2 login, roles, per-IP rate limiting (+ documented
  link-auth upgrade path).
- **`anomaly.py`** — the shared anomaly-detection engine; both frontends feed it
  readings and shade the windows it returns.
- **`server.py` + `static/index.html`** — the web UI (stdlib HTTP + SSE; canvas
  charts and the window manager both live in `index.html`, no build step).
  `static/login.html` is the sign-in page.
- **`building.py` + `static/js/building-css3d.js`** — the 3D building view: all
  geometry (floors, rooms, furniture, the shell) is data in `building.py`; the
  renderer only decides how many pixels a metre is worth. See
  [BUILDING.md](BUILDING.md).
- **`panels.py` + `app.py`** — the desktop UI (pyqtgraph widgets, main window).

## Local data logging (no Postgres)

Everything is logged locally, zero install:

- **`museumguard.sqlite`** — tables `readings`, `events` (state transitions),
  `audit` (logins + overrides).
- **`logs/readings-YYYY-MM-DD.csv`** — a daily CSV mirror of every reading,
  opens directly in Excel/pandas.

Both are runtime artifacts and are git-ignored.

## Security notes — web dashboard login

- Two tiers: `viewer` (page access) and `guard` (overrides) — see *Demo login*.
  `guard` is a strict superset of `viewer` (it can view too), enforced in
  `security.role_satisfies`.
- Passwords are salted PBKDF2-SHA256 (200k iterations), compared with
  `hmac.compare_digest`; a wrong/unknown username still burns a PBKDF2 round so
  it isn't measurably faster than a wrong password.
- Login is rate-limited per client IP (`security.RateLimiter`): 5 failures in a
  5-minute window locks that IP out for 5 minutes. This blocks *online*
  guessing; it does nothing for someone who gets the hashes and brute-forces
  offline (that's what the iteration count is for).
- **Not yet done: TLS.** The login still posts the password in the clear over
  plain HTTP — anyone on the same network segment can sniff it. Held off until
  the Raspberry Pi deployment shape (reverse proxy vs. wrapping the socket
  directly) is settled; until then, keep this off open/shared networks.
- Session tokens (`Hub.tokens`) are in-memory only and die with the process —
  by design, so a restart forces re-authentication.

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
