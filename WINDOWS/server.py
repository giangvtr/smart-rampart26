# MuseumGuard - Flask server + live web dashboard, with command round-trip.
#
# Run:
#   pip install flask
#   python server.py
# Open http://<this-PC-IP>:5000/ in a browser (or on any device on the same WiFi).
#
# Data flow (no inbound connection to the ESP32 is ever needed):
#   node   --POST /api/ingest--> server        (readings in)
#   server --reply {"cmd": ...}--> node         (command out, on the SAME reply)
#   browser--POST /api/command--> server        (button queues the command; login-gated)
#
# Because the command rides back on the node's own POST reply, the server never
# has to connect TO the node - which is why this also works from the Wokwi sim.
#
# What the server layer adds on top of the raw ingest (v0.5 spec):
#   * Shared-credential login gate (FR-DASH-3): read-only monitoring is open,
#     but Acknowledge / Override / ARM / DISARM require a session login.
#   * Per-zone command queue: AUTO / OFF (env ack), ARM / DISARM (motion),
#     RESET (clear a latched water/motion alarm)  -- FR-DASH-4, FR-MOT-2, FR-WTR-3.
#   * Latched-alarm memory for water + motion (FR-WTR-3, FR-MOT-3/4): once an
#     alarm fires it stays latched on the dashboard until an agent RESETs it,
#     even if the sensor value later returns to normal.
#   * Disconnect detection (FR-NET-4 / FR-DASH-6): a zone with no heartbeat for
#     >6s is shown as "disconnected" instead of stale-as-live; other zones keep
#     updating independently.
#   * In-memory audit log (FR-DASH-5): every override/arm/disarm is timestamped.

import os
import time
from functools import wraps
from flask import Flask, request, jsonify, render_template, session

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "museumguard-demo-secret")

# ---- config -----------------------------------------------------------------
# Single shared agent credential for the MVP (FR-DASH-3). Override via env vars.
AGENT_USER = os.environ.get("MG_USER", "agent")
AGENT_PASS = os.environ.get("MG_PASS", "guard")

STALE_AFTER_S = 6          # FR-NET-4: 3 missed 2s cycles => disconnected
LOG_MAX = 200              # cap the in-memory event log

# ---- in-memory state --------------------------------------------------------
readings = {}   # zone -> latest reading dict (+ ts)
commands = {}   # zone -> pending command str: AUTO | OFF | ARM | DISARM | RESET
latched = {}    # zone -> True while a latched (water/motion) alarm is standing
event_log = []  # list of {ts, zone, kind, detail} newest-first


def log_event(zone, kind, detail=""):
    event_log.insert(0, {
        "ts": time.time(),
        "zone": zone,
        "kind": kind,
        "detail": detail,
    })
    del event_log[LOG_MAX:]


def zone_is_latching(reading):
    """Water and motion alarms latch; plain environmental ones self-clear."""
    if reading.get("level") is not None or reading.get("water") is not None:
        return True
    if reading.get("motion") is not None or reading.get("armed") is not None:
        return True
    return False


# -----------------------------------------------------------------------------
#  Ingest: readings in, pending command out on the same reply.
# -----------------------------------------------------------------------------
@app.route("/api/ingest", methods=["POST"])
def ingest():
    data = request.get_json(silent=True)
    if not data or "zone" not in data:
        return jsonify({"error": "expected JSON with a 'zone' field"}), 400

    zone = str(data["zone"])
    first_seen = zone not in readings
    prev_state = (readings.get(zone) or {}).get("state")

    reading = {
        "zone": zone,
        # environmental fields
        "temp": data.get("temp"),
        "humidity": data.get("humidity"),
        "air": data.get("air"),
        "light": data.get("light"),
        # water-node fields
        "raw": data.get("raw"),
        "voltage": data.get("voltage"),
        "level": data.get("level"),
        "water": data.get("water"),
        # motion / security fields
        "motion": data.get("motion"),
        "armed": data.get("armed"),
        "state": data.get("state"),
        "ts": time.time(),
    }
    readings[zone] = reading

    if first_seen:
        log_event(zone, "online", "node came online")

    # Latch a standing alarm from a latching sensor so the dashboard keeps it
    # visible until an agent RESETs it (FR-WTR-3 / FR-MOT-3).
    state = str(reading.get("state") or "").upper()
    if zone_is_latching(reading) and state == "ALARM":
        if not latched.get(zone):
            latched[zone] = True
            log_event(zone, "alarm", "latched alarm raised")

    # Log environmental state transitions too (start + clear), FR-SYS-2.
    if not zone_is_latching(reading) and state and state != str(prev_state or "").upper():
        log_event(zone, "state", f"{prev_state or '-'} -> {state}")

    return jsonify({"ok": True, "cmd": commands.get(zone, "AUTO")}), 200


# -----------------------------------------------------------------------------
#  Command: dashboard button -> queues the pending command (LOGIN REQUIRED).
# -----------------------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if not session.get("agent"):
            return jsonify({"error": "login required"}), 401
        return view(*a, **kw)
    return wrapped


@app.route("/api/command", methods=["POST"])
@login_required
def set_command():
    data = request.get_json(silent=True) or {}
    zone = str(data.get("zone", ""))
    cmd = str(data.get("cmd", "")).upper()
    if not zone or cmd not in ("AUTO", "OFF", "ARM", "DISARM", "RESET"):
        return jsonify({"error": "need zone and cmd in {AUTO,OFF,ARM,DISARM,RESET}"}), 400

    commands[zone] = cmd
    # RESET clears any standing latched alarm on the server side immediately so
    # the dashboard reflects the acknowledge even before the next node poll.
    if cmd == "RESET":
        latched.pop(zone, None)

    log_event(zone, "override", f"{session.get('agent')} sent {cmd}")
    return jsonify({"ok": True, "zone": zone, "cmd": cmd}), 200


# ---- auth -------------------------------------------------------------------
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    if data.get("user") == AGENT_USER and data.get("pass") == AGENT_PASS:
        session["agent"] = AGENT_USER
        return jsonify({"ok": True, "agent": AGENT_USER}), 200
    return jsonify({"error": "invalid credentials"}), 401


@app.route("/api/logout", methods=["POST"])
def logout():
    session.pop("agent", None)
    return jsonify({"ok": True}), 200


@app.route("/api/me")
def me():
    return jsonify({"agent": session.get("agent")}), 200


# ---- read-only monitoring (no login) ----------------------------------------
@app.route("/api/readings")
def api_readings():
    now = time.time()
    out = []
    for r in readings.values():
        item = dict(r)
        item["age_s"] = round(now - r["ts"], 1)
        item["disconnected"] = item["age_s"] > STALE_AFTER_S
        item["cmd"] = commands.get(r["zone"], "AUTO")
        item["latched"] = bool(latched.get(r["zone"]))
        out.append(item)
    out.sort(key=lambda x: x["zone"])
    return jsonify(out)


@app.route("/api/log")
def api_log():
    return jsonify([
        {**e, "ts_str": time.strftime("%H:%M:%S", time.localtime(e["ts"]))}
        for e in event_log
    ])


@app.route("/")
def index():
    return render_template("dashboard.html")




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
