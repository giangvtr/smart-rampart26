"""
MuseumGuard dashboard -- web frontend (alternative to the Qt desktop app).

Same features, nicer UI, better graph controls. Uses **only the Python standard
library** on the server side: no Flask, no FastAPI, no npm, no CDN. The browser
page (static/index.html) draws its charts on a plain <canvas> -- no charting
library either, so the demo works with no internet at the venue.

Both frontends share the exact same engine; only the presentation differs:

    config.py / core.py / transports.py / storage.py / security.py   <- shared
        app.py    + panels.py            -> PySide6 desktop UI
        server.py + static/index.html    -> browser UI   (this file)

Run:
    python server.py            # then open http://127.0.0.1:8000
    python server.py --port 9000 --host 0.0.0.0

Transport is chosen exactly like the desktop app -- see make_source() below.

Live data reaches the browser over Server-Sent Events (SSE), a one-way stream
that is a natural fit for telemetry and needs no WebSocket library. Commands go
back over ordinary POSTs.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import queue
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import anomaly
import config
import forecast as forecast_mod
import hvac as hvac_mod
import preservation as preservation_mod
import security
from core import Command
from storage import Storage
from transports import HttpIngestSource, SerialSource, SimulatedSource  # noqa: F401 (alt sources for the swap)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
SESSION_COOKIE = "mg_session"  # gates page/bootstrap/stream access (viewer or guard)


def make_source(name: str = "http"):
    """The single swap-point for how data reaches the dashboard.

    Chosen at launch with --source (default "http"):

      http   HttpIngestSource -- the real ESP32 path: nodes POST readings to
             /api/ingest over WiFi and pick up commands on the same reply.
      sim    SimulatedSource  -- fake data, no hardware (for a quick demo/test).
      serial SerialSource     -- USB / Bluetooth-Classic Arduino (port in config.py).

    BLE stubs live in transports.py.
    """
    if name == "sim":
        return SimulatedSource()
    if name == "serial":
        return SerialSource(port=config.SERIAL_PORT, baud=config.SERIAL_BAUD)
    return HttpIngestSource()


# --------------------------------------------------------------------------
# Hub: owns the source + storage, fans events out to connected browsers
# --------------------------------------------------------------------------
class Hub:
    def __init__(self, source_name: str = "http", forecast_name: str = "sim"):
        self.storage = Storage()
        self.source = make_source(source_name)
        # Learns each stream's normal and flags the windows that break it. It
        # lives here rather than in the browser so every tab sees the same
        # verdicts, and so one opened late still gets what it missed.
        self.detector = anomaly.AnomalyEngine()
        # Live "how long will the collection last at these conditions" metric
        # (PI / TWPI), fed the same temp/humidity readings as the detector.
        self.preservation = preservation_mod.PreservationEngine()
        # Predictive HVAC: turns temp/RH + forecast into a conditioning effort
        # that rides back on the ESP32's POST reply as an LED PWM duty. The
        # forecast source is swappable (sim default = offline-safe).
        self.forecast = forecast_mod.make_forecast(forecast_name)
        self.hvac = hvac_mod.HvacController(
            self.forecast,
            on_state=lambda st: self._broadcast("hvac", {"hvac": st}),
            on_forecast=lambda fo: self._broadcast("forecast", {"forecast": fo}),
        )
        self.connected = False
        self.armed = True
        # New id per process. All server state (buffers, latches, tokens) lives
        # in memory, so a restart wipes it -- the browser compares this against
        # what it booted with to tell "SSE dropped" from "server restarted".
        self.boot_id = secrets.token_hex(8)
        self.tokens: dict[str, dict[str, str]] = {}   # token -> {"user", "role"}
        self._clients: set[queue.Queue] = set()
        self._lock = threading.Lock()
        self._events: list[dict] = []          # recent log lines for new clients

        self.source.reading_received.connect(self._on_reading)
        self.source.connection_changed.connect(self._on_connection)
        self.source.notice.connect(self._on_notice)

    def start(self) -> None:
        self.forecast.start()
        self.hvac.start()
        self.source.start()

    def stop(self) -> None:
        self.source.stop()
        self.hvac.stop()
        self.forecast.stop()
        self.storage.close()

    # -- fan-out ----------------------------------------------------------
    def subscribe(self) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=1000)
        with self._lock:
            self._clients.add(q)
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        with self._lock:
            self._clients.discard(q)

    def _broadcast(self, kind: str, payload: dict) -> None:
        msg = {"type": kind, **payload}
        with self._lock:
            clients = list(self._clients)
        for q in clients:
            try:
                q.put_nowait(msg)
            except queue.Full:
                pass  # a stalled browser must not block the transport

    # -- source callbacks (fire on the transport thread) -------------------
    def _on_reading(self, reading) -> None:
        prev = self.storage.record_reading(reading)
        # feed the climate engines the same sample. Preservation returns a
        # payload when both temp+humidity are known; HVAC just tracks the value
        # and acts on its own ramp thread.
        pres = self.preservation.feed(reading)
        if pres is not None:
            self._broadcast("preservation", {"preservation": pres})
        self.hvac.feed(reading)
        # score before broadcasting, so the reading can carry the expected range
        # this very sample was judged against -- the chart draws them together
        records = self.detector.feed(reading)
        self._broadcast("reading", {
            "key": reading.key, "zone": reading.zone, "sensor": reading.sensor,
            "value": reading.value, "state": reading.state, "ts": reading.ts,
            "band": self.detector.current_band(reading.key),
        })
        for record in records:
            self._broadcast("anomaly", {"anomaly": record})
            # Log it once, when the window closes: while it is open its kind and
            # severity are still being written, and a spike that turns out to be
            # a level shift should not appear in the log twice.
            if not record["open"]:
                self._log(f"ANOMALY [{record['zone']}·{record['label']}] "
                          f"{record['kindLabel']} ({record['severity']}) — "
                          f"{record['message']}")
        if prev is not None:
            unit = config.SENSORS_BY_KEY[reading.key].unit
            self._log(f"[{reading.zone}·{reading.sensor}] {prev} → {reading.state}"
                      f" ({reading.value:g} {unit})")

    def _on_connection(self, connected: bool) -> None:
        self.connected = connected
        self._broadcast("connection", {"connected": connected})

    def _on_notice(self, msg: str) -> None:
        self._log(msg)

    def _log(self, msg: str) -> None:
        entry = {"ts": time.time(), "msg": msg}
        self._events.append(entry)
        del self._events[:-200]
        self._broadcast("log", entry)

    # -- state for a newly connected browser ------------------------------
    def bootstrap(self) -> dict:
        sensors = []
        for s in config.SENSORS:
            buf = self.storage.buffers[s.key]
            times, values = buf.arrays()
            sensors.append({
                "key": s.key, "zone": s.zone, "sensor": s.sensor, "label": s.label,
                "unit": s.unit, "warn": s.warn, "alarm": s.alarm,
                "vmin": s.vmin, "vmax": s.vmax, "latched": s.latched,
                "history": {"t": times, "v": values},
                "state": buf.last_state or config.STATE_DISCONNECTED,
                "value": buf.last_value,
                "detectAnomalies": s.detect_anomalies,
                "band": self.detector.band(s.key),
            })
        return {
            "bootId": self.boot_id,
            "appTitle": config.APP_TITLE,
            "sensors": sensors,
            "colors": config.STATE_COLORS,
            "timeScales": config.TIME_SCALES,
            "defaultScaleIndex": config.DEFAULT_TIME_SCALE_INDEX,
            "connected": self.connected,
            "armed": self.armed,
            "anomalyEnabled": self.detector.enabled,
            "anomalies": self.detector.recent(60),
            "preservation": self.preservation.snapshot(),
            "hvac": self.hvac.state(),
            "forecast": self.forecast.outlook(),
            "events": self._events[-50:],
            "serverTime": time.time(),
        }

    # -- auth + commands ---------------------------------------------------
    def login(self, username: str, password: str, client_ip: str) -> tuple[str | None, str | None]:
        """Returns (token, error). `error` is a user-facing message on failure."""
        wait = security.LOGIN_LIMITER.seconds_locked(client_ip)
        if wait > 0:
            return None, f"Too many attempts. Try again in {int(wait) + 1}s."
        role = security.authenticate(username, password)
        if role is None:
            security.LOGIN_LIMITER.record_failure(client_ip)
            return None, "Invalid credentials"
        security.LOGIN_LIMITER.record_success(client_ip)
        token = secrets.token_urlsafe(24)
        uname = username.strip().lower()
        self.tokens[token] = {"user": uname, "role": role}
        self.storage.record_audit(uname, "LOGIN", f"web:{role}")
        self._log(f"Agent '{uname}' logged in (web, {role}).")
        return token, None

    def role_for(self, token: str) -> str | None:
        entry = self.tokens.get(token)
        return entry["role"] if entry else None

    def logout(self, token: str) -> None:
        entry = self.tokens.pop(token, None)
        if entry:
            self.storage.record_audit(entry["user"], "LOGOUT", "web")
            self._log(f"Agent '{entry['user']}' logged out.")

    def command(self, token: str, zone: str, sensor: str, action: str) -> bool:
        entry = self.tokens.get(token)
        if not entry or entry["role"] != "guard":
            return False
        user = entry["user"]
        # HVAC overrides never reach the alarm/command path -- they steer the
        # controller's mode directly, and its effort rides back on ingest replies.
        if zone == "SYSTEM" and sensor == "HVAC":
            if not self.hvac.set_override(action):
                return False
            self._broadcast("hvac", {"hvac": self.hvac.state()})
            self.storage.record_audit(user, f"HVAC_{action}", "SYSTEM.HVAC")
            self._log(f"AUDIT: {user} set HVAC {action}")
            return True
        self.source.send_command(Command(zone, sensor, action))
        if zone == "SYSTEM" and sensor == "ALL" and action in ("ARM", "DISARM"):
            self.armed = action == "ARM"
            self._broadcast("system", {"armed": self.armed})
        elif action == "RESET":
            # Marks the end of one alarm *episode*. The browser needs this as an
            # explicit event: a latched sensor whose raw value is still over the
            # threshold re-latches on the very next reading, so the UI never
            # observes a non-ALARM sample it could infer the boundary from.
            self._broadcast("reset", {"key": f"{zone}.{sensor}"})
        self.storage.record_audit(user, action, f"{zone}.{sensor}")
        self._log(f"AUDIT: {user} issued {action} {zone}.{sensor}")
        return True

    def ingest(self, payload: dict) -> str:
        """Feed one ESP32 POST body into the HTTP source (if that transport is
        active) and return the command string to hand back on the reply."""
        fn = getattr(self.source, "ingest", None)
        if fn is None:
            # Some other transport is active (sim/serial); accept but no-op.
            return "AUTO"
        return fn(payload)


HUB: Hub | None = None


# --------------------------------------------------------------------------
# HTTP handler
# --------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "MuseumGuard"

    def log_message(self, fmt, *args):  # quieter console
        pass

    # -- helpers ----------------------------------------------------------
    def _send_json(self, obj, status: int = 200) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except ValueError:
            return {}

    def _token(self) -> str:
        return (self.headers.get("X-Auth-Token") or "").strip()

    def _cookie_token(self) -> str:
        raw = self.headers.get("Cookie") or ""
        for part in raw.split(";"):
            part = part.strip()
            if part.startswith(f"{SESSION_COOKIE}="):
                return part[len(SESSION_COOKIE) + 1:]
        return ""

    def _has_page_access(self) -> bool:
        # The cookie carries whichever role last logged in (viewer or guard,
        # guard being the stronger one) -- either is enough to view the page.
        return security.role_satisfies(HUB.role_for(self._cookie_token()), "viewer")

    def _client_ip(self) -> str:
        return self.client_address[0]

    # -- routes -----------------------------------------------------------
    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            if not self._has_page_access():
                return self._serve_static("login.html")
            return self._serve_static("index.html")
        if path == "/login.html":
            return self._serve_static("login.html")
        if path == "/api/bootstrap":
            if not self._has_page_access():
                return self._send_json({"error": "login required"}, 401)
            return self._send_json(HUB.bootstrap())
        if path == "/api/stream":
            if not self._has_page_access():
                return self._send_json({"error": "login required"}, 401)
            return self._serve_stream()
        if path.startswith("/static/"):
            return self._serve_static(path[len("/static/"):])
        self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        data = self._read_json()
        if path == "/api/login":
            token, error = HUB.login(str(data.get("username", "")),
                                     str(data.get("password", "")), self._client_ip())
            if token:
                resp = {"ok": True, "token": token, "user": HUB.tokens[token]["user"],
                        "role": HUB.tokens[token]["role"]}
                # The dashboard-access cookie is only set for the initial gate-page
                # login (static/login.html); the in-page "Agent login" modal that
                # elevates to `guard` for overrides uses the X-Auth-Token header
                # instead, so it doesn't clobber (or get killed by logging out of)
                # the viewer session. No `Secure` attribute yet -- this is plain
                # HTTP until TLS is added; see security.py.
                if data.get("cookie"):
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    cookie = f"{SESSION_COOKIE}={token}; Path=/; HttpOnly; SameSite=Lax"
                    self.send_header("Set-Cookie", cookie)
                    body = json.dumps(resp).encode("utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                return self._send_json(resp)
            status = 429 if "Too many attempts" in (error or "") else 401
            return self._send_json({"ok": False, "error": error}, status)
        if path == "/api/logout":
            HUB.logout(self._token())
            return self._send_json({"ok": True})
        if path == "/api/command":
            ok = HUB.command(self._token(), str(data.get("zone", "")),
                             str(data.get("sensor", "")), str(data.get("action", "")))
            if ok:
                return self._send_json({"ok": True})
            return self._send_json({"ok": False, "error": "Guard login required"}, 403)
        if path == "/api/ingest":
            # ESP32 zone node -> readings in; pending command rides back on the
            # reply (no inbound connection to the node is ever opened). No login:
            # the nodes are unauthenticated devices on the LAN, like a sensor bus.
            # Deliberately NOT behind the viewer cookie gate -- that gate is for
            # browsers, and the firmware carries no session.
            if not data or "zone" not in data:
                return self._send_json({"error": "expected JSON with a 'zone'"}, 400)
            cmd = HUB.ingest(data)
            # The HVAC effort/mode is a *persistent* level, not a one-shot queued
            # command, so it rides back on every reply alongside the alarm cmd.
            zone = config.canonical_zone(data.get("zone", ""))
            hstate = HUB.hvac.state()
            return self._send_json({
                "ok": True, "cmd": cmd,
                "hvac": HUB.hvac.level_for(zone), "hvacMode": hstate["mode"],
            })
        self._send_json({"error": "not found"}, 404)

    # -- static files -----------------------------------------------------
    def _serve_static(self, rel: str) -> None:
        # constrain to STATIC_DIR (no path traversal)
        full = os.path.normpath(os.path.join(STATIC_DIR, rel))
        if not full.startswith(STATIC_DIR) or not os.path.isfile(full):
            return self._send_json({"error": "not found"}, 404)
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        with open(full, "rb") as fh:
            body = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    # -- SSE stream -------------------------------------------------------
    def _serve_stream(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        q = HUB.subscribe()
        try:
            while True:
                try:
                    msg = q.get(timeout=15.0)
                    payload = f"data: {json.dumps(msg)}\n\n"
                except queue.Empty:
                    payload = ": keepalive\n\n"   # keeps proxies/browsers happy
                self.wfile.write(payload.encode("utf-8"))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass  # browser navigated away
        finally:
            HUB.unsubscribe(q)


def main() -> int:
    global HUB
    parser = argparse.ArgumentParser(description="MuseumGuard web dashboard")
    # localhost by default: the login posts a plaintext password over HTTP, so
    # do not expose this beyond the demo machine without TLS in front of it.
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--source", choices=["http", "sim", "serial"], default="http",
                        help="data source: http=ESP32 WiFi (default), "
                             "sim=fake data no hardware, serial=USB/Bluetooth Arduino")
    parser.add_argument("--forecast", choices=["sim", "http", "off"], default="sim",
                        help="HVAC weather feedforward: sim=synthetic outlook "
                             "(default, offline), http=Open-Meteo (needs internet), "
                             "off=purely reactive")
    args = parser.parse_args()

    HUB = Hub(args.source, args.forecast)
    HUB.start()
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    httpd.daemon_threads = True
    print(f"{config.APP_NAME} web dashboard -> http://{args.host}:{args.port}"
          f"  [source: {args.source}, forecast: {args.forecast}]")
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        httpd.server_close()
        HUB.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
