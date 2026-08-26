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

import building
import config
import security
from core import Command
from storage import Storage
from transports import SerialSource, SimulatedSource  # noqa: F401 (SerialSource for the swap)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Windows takes MIME types from the registry, where a stray entry can report
# .js as text/plain -- browsers then refuse to run <script type="module"> at all
# (strict MIME checking), which would silently kill the three.js renderer on
# someone else's laptop. Pin the types that matter.
MIME_OVERRIDES = {
    ".js": "text/javascript",
    ".mjs": "text/javascript",
    ".css": "text/css",
    ".html": "text/html; charset=utf-8",
    ".json": "application/json",
}


def make_source():
    """The single swap-point for how data reaches the dashboard.

    Default: SimulatedSource (no hardware). For the real Arduino over USB or
    Bluetooth-Classic, comment the first line and use the second (set the port
    in config.py). WiFi/BLE stubs live in transports.py.
    """
    return SimulatedSource()
    # return SerialSource(port=config.SERIAL_PORT, baud=config.SERIAL_BAUD)


# --------------------------------------------------------------------------
# Hub: owns the source + storage, fans events out to connected browsers
# --------------------------------------------------------------------------
class Hub:
    def __init__(self):
        self.storage = Storage()
        self.source = make_source()
        self.connected = False
        # New id per process. All server state (buffers, latches, tokens) lives
        # in memory, so a restart wipes it -- the browser compares this against
        # what it booted with to tell "SSE dropped" from "server restarted".
        self.boot_id = secrets.token_hex(8)
        self.tokens: dict[str, str] = {}       # token -> username
        self._clients: set[queue.Queue] = set()
        self._lock = threading.Lock()
        self._events: list[dict] = []          # recent log lines for new clients

        self.source.reading_received.connect(self._on_reading)
        self.source.connection_changed.connect(self._on_connection)
        self.source.notice.connect(self._on_notice)

    def start(self) -> None:
        self.source.start()

    def stop(self) -> None:
        self.source.stop()
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
        self._broadcast("reading", {
            "key": reading.key, "zone": reading.zone, "sensor": reading.sensor,
            "value": reading.value, "state": reading.state, "ts": reading.ts,
        })
        if prev is not None:
            sdef = config.SENSORS_BY_KEY[reading.key]
            # Every transition matters on the real rig. For the 48 simulated
            # sensors only report alarms, or their ordinary OK<->WARN flapping
            # buries the real room's log.
            if not sdef.synthetic or reading.state == config.STATE_ALARM:
                where = sdef.room if sdef.synthetic else reading.zone
                self._log(f"[{where}·{reading.sensor}] {prev} → {reading.state}"
                          f" ({reading.value:g} {sdef.unit})")

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
            # The real rig ships its full hour of history; 48 simulated sensors
            # doing the same would put tens of MB of fiction in this JSON.
            if s.synthetic:
                times = times[-config.BOOTSTRAP_SYNTH_POINTS:]
                values = values[-config.BOOTSTRAP_SYNTH_POINTS:]
            sensors.append({
                "key": s.key, "zone": s.zone, "sensor": s.sensor, "label": s.label,
                "unit": s.unit, "warn": s.warn, "alarm": s.alarm,
                "vmin": s.vmin, "vmax": s.vmax, "latched": s.latched,
                "room": s.room, "synthetic": s.synthetic,
                "history": {"t": times, "v": values},
                "state": buf.last_state or config.STATE_DISCONNECTED,
                "value": buf.last_value,
            })
        return {
            "bootId": self.boot_id,
            "appTitle": config.APP_TITLE,
            "sensors": sensors,
            "building": {
                "floors": building.FLOORS,
                "rooms": [r.to_json() for r in building.ROOMS],
                "floorW": building.FLOOR_W,
                "floorD": building.FLOOR_D,
                "wallH": building.WALL_H,
                "liveRoom": config.LIVE_ROOM,
                "shell": building.SHELL,
            },
            "colors": config.STATE_COLORS,
            "timeScales": config.TIME_SCALES,
            "defaultScaleIndex": config.DEFAULT_TIME_SCALE_INDEX,
            "connected": self.connected,
            "events": self._events[-50:],
            "serverTime": time.time(),
        }

    # -- auth + commands ---------------------------------------------------
    def login(self, username: str, password: str) -> str | None:
        if security.verify_password(username, password):
            token = secrets.token_urlsafe(24)
            self.tokens[token] = username.strip().lower()
            self.storage.record_audit(self.tokens[token], "LOGIN", "web")
            self._log(f"Agent '{self.tokens[token]}' logged in (web).")
            return token
        return None

    def logout(self, token: str) -> None:
        user = self.tokens.pop(token, None)
        if user:
            self.storage.record_audit(user, "LOGOUT", "web")
            self._log(f"Agent '{user}' logged out.")

    def command(self, token: str, zone: str, sensor: str, action: str) -> bool:
        user = self.tokens.get(token)
        if not user:
            return False
        self.source.send_command(Command(zone, sensor, action))
        self.storage.record_audit(user, action, f"{zone}.{sensor}")
        self._log(f"AUDIT: {user} issued {action} {zone}.{sensor}")
        return True


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

    # -- routes -----------------------------------------------------------
    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            return self._serve_static("index.html")
        if path == "/api/bootstrap":
            return self._send_json(HUB.bootstrap())
        if path == "/api/stream":
            return self._serve_stream()
        if path.startswith("/static/"):
            return self._serve_static(path[len("/static/"):])
        self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        data = self._read_json()
        if path == "/api/login":
            token = HUB.login(str(data.get("username", "")), str(data.get("password", "")))
            if token:
                return self._send_json({"ok": True, "token": token,
                                        "user": HUB.tokens[token]})
            return self._send_json({"ok": False, "error": "Invalid credentials"}, 401)
        if path == "/api/logout":
            HUB.logout(self._token())
            return self._send_json({"ok": True})
        if path == "/api/command":
            ok = HUB.command(self._token(), str(data.get("zone", "")),
                             str(data.get("sensor", "")), str(data.get("action", "")))
            if ok:
                return self._send_json({"ok": True})
            return self._send_json({"ok": False, "error": "Login required"}, 403)
        self._send_json({"error": "not found"}, 404)

    # -- static files -----------------------------------------------------
    def _serve_static(self, rel: str) -> None:
        # constrain to STATIC_DIR (no path traversal)
        full = os.path.normpath(os.path.join(STATIC_DIR, rel))
        if not full.startswith(STATIC_DIR) or not os.path.isfile(full):
            return self._send_json({"error": "not found"}, 404)
        ctype = MIME_OVERRIDES.get(os.path.splitext(full)[1].lower())
        if ctype is None:
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
    args = parser.parse_args()

    HUB = Hub()
    HUB.start()
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    httpd.daemon_threads = True
    print(f"{config.APP_NAME} web dashboard -> http://{args.host}:{args.port}")
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
