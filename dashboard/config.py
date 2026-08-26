"""
MuseumGuard dashboard — central configuration.

Single source of truth for zones, sensors, thresholds, colors, timing and the
serial defaults. Everything else imports from here so tuning the demo is a
one-file job.
"""
from __future__ import annotations

import building

# --------------------------------------------------------------------------
# Sensor / zone model
# --------------------------------------------------------------------------
# state names (also what the Arduino sends in the STATE field)
STATE_OK = "OK"
STATE_WARN = "WARN"
STATE_ALARM = "ALARM"
STATE_STALE = "STALE"            # last-known value, sensor read failed
STATE_DISCONNECTED = "DISCONNECTED"  # no link to the node at all

# ordering used to pick the "worst" state for summary widgets
STATE_SEVERITY = {
    STATE_DISCONNECTED: 4,
    STATE_ALARM: 3,
    STATE_STALE: 2,
    STATE_WARN: 1,
    STATE_OK: 0,
}

# colors (used for panel borders, status tiles, plot traces)
STATE_COLORS = {
    STATE_OK: "#2e7d32",            # green
    STATE_WARN: "#f9a825",          # amber
    STATE_ALARM: "#c62828",         # red
    STATE_STALE: "#6d4c41",         # brown
    STATE_DISCONNECTED: "#616161",  # grey
}

# A sensor definition. `warn`/`alarm` are (low, high) bounds; a reading outside
# `warn` is a warning, outside `alarm` is an alarm. `None` on a side means "no
# bound on that side" (e.g. water only has an upper danger bound). `latched`
# means an alarm stays until an explicit reset/override (water, motion).
class SensorDef:
    def __init__(self, key, zone, label, unit, warn, alarm,
                 vmin, vmax, latched=False, period_s=2.0,
                 room=None, synthetic=False, kind="analog",
                 detect_anomalies=True):
        self.key = key            # unique id, e.g. "BASEMENT.TEMP"
        self.zone = zone
        self.label = label
        self.unit = unit
        self.warn = warn          # (low, high) or None
        self.alarm = alarm        # (low, high) or None
        self.vmin = vmin          # plot y-axis suggestion
        self.vmax = vmax
        self.latched = latched
        self.period_s = period_s
        # `room` is a DISPLAY grouping for the 3D building view; `zone` stays the
        # wire token the node sends, so adding rooms never touched the protocol.
        self.room = room or zone
        # synthetic = simulated demo room, never written to SQLite/CSV
        self.synthetic = synthetic
        self.kind = kind          # "analog" (wanders) or "event" (blips)
        # Whether anomaly.py should watch this stream. Set False for on/off
        # sensors: a 0/1 signal has no "normal spread" to learn, so every trip
        # would score as an infinite deviation. All four real sensors are
        # continuous; the simulated on/off ones opt out below.
        self.detect_anomalies = detect_anomalies

    @property
    def sensor(self) -> str:
        # the SENSOR token used on the wire, e.g. "TEMP"
        return self.key.split(".", 1)[1]


# One zone: the Basement rig -- the four sensors the ESP32 node actually
# carries (water level, temperature, humidity, fire). The Gallery zone (light
# and motion in the exhibition hall) was dropped: no firmware ever sent it, so
# its tiles only ever showed DISCONNECTED. Adding a second zone back is just
# more entries here plus a ZONE_ALIASES line -- nothing else is zone-aware.
#
# The scenario puts the physical rig in one basement room of the 3D building,
# hence room=LIVE_ROOM on all four. These are the only NON-synthetic sensors;
# the simulated museum rooms are opt-in, see enable_demo_rooms() below.
LIVE_ROOM = "B1_ARCHIVE"

SENSORS = [
    SensorDef("BASEMENT.WATER",   "BASEMENT", "Water level", "adc",
              warn=(None, 100), alarm=(None, 300), vmin=0, vmax=600, latched=True, period_s=2.0,
              room=LIVE_ROOM),
    SensorDef("BASEMENT.TEMP",     "BASEMENT", "Temperature", "°C",
              warn=(18, 26), alarm=(15, 30), vmin=10, vmax=40, period_s=3.0, room=LIVE_ROOM),
    SensorDef("BASEMENT.HUMIDITY", "BASEMENT", "Humidity",    "%RH",
              warn=(40, 60), alarm=(30, 70), vmin=20, vmax=90, period_s=3.0, room=LIVE_ROOM),
    # Fire: potentiometer stand-in (0..100). Upper danger bound only; latched so
    # a detected fire stays in ALARM until an explicit reset/override.
    SensorDef("BASEMENT.FIRE",     "BASEMENT", "Fire",        "idx",
              warn=(None, 50), alarm=(None, 70), vmin=0, vmax=100, latched=True, period_s=3.0,
              room=LIVE_ROOM),
]

# The four above are the real rig, and by default they are ALL that exists.
LIVE_SENSORS = list(SENSORS)

SENSORS_BY_KEY = {s.key: s for s in SENSORS}
ZONES = sorted({s.zone for s in SENSORS})

# --------------------------------------------------------------------------
# Simulated museum rooms -- opt-in (server.py --demo-rooms)
# --------------------------------------------------------------------------
# The 3D building has 12 rooms; exactly one of them (LIVE_ROOM) is the physical
# rig. The other 11 are fiction, so they are NOT created unless someone asks for
# them: a default run has four sensors and every reading on the dashboard is a
# real measurement. With --demo-rooms the rooms are populated from
# building.ROOMS and the 3D view fills with plausible activity for a demo.
#
# This is a startup switch, not a runtime toggle -- Storage allocates a ring
# buffer per sensor at construction, so it must be decided before the Hub is
# built. server.py calls this from main() before constructing Hub.
DEMO_ROOMS = False


def enable_demo_rooms() -> int:
    """Populate the 11 simulated rooms. Returns how many sensors were added.

    Idempotent: calling it twice is a no-op, so an accidental second call
    cannot double up the sensor list.
    """
    global DEMO_ROOMS
    if DEMO_ROOMS:
        return 0
    DEMO_ROOMS = True

    added = 0
    for room in building.ROOMS:
        for tok in room.sensors:
            t = building.SENSOR_TYPES[tok]
            SENSORS.append(SensorDef(
                f"{room.id}.{tok}", room.id, t["label"], t["unit"],
                warn=t["warn"], alarm=t["alarm"], vmin=t["vmin"], vmax=t["vmax"],
                latched=t["latched"], period_s=t["period_s"],
                room=room.id, synthetic=True, kind=t["kind"],
                # same rule as the real rig: an on/off stream has no spread for
                # anomaly.py to learn from, so only the analog kinds are watched
                detect_anomalies=(t["kind"] == "analog"),
            ))
            added += 1

    SENSORS_BY_KEY.update({s.key: s for s in SENSORS})
    ZONES[:] = sorted({s.zone for s in SENSORS})
    return added


def fmt_value(sdef: "SensorDef", value: float) -> str:
    """A reading, formatted for a human.

    On/off sensors read Yes/No -- "1 bool" makes the reader translate before
    they can act on it. The web UI has the same rule in fmtValue().
    """
    if value is None:
        return "--"
    if sdef.unit == "bool":
        return "Yes" if value >= 0.5 else "No"
    return f"{value:g} {sdef.unit}"


def sensors_in_room(room_id: str) -> list[SensorDef]:
    return [s for s in SENSORS if s.room == room_id]


def sensor_lookup(zone: str, sensor: str) -> SensorDef | None:
    return SENSORS_BY_KEY.get(f"{zone}.{sensor}")


# --------------------------------------------------------------------------
# ESP32 HTTP-ingest mapping (WiFi path)
# --------------------------------------------------------------------------
# The ESP32 firmware posts one JSON blob per node using short zone ids and its
# own field names. HttpIngestSource fans that blob out into canonical per-sensor
# Readings using the two maps below, so the firmware wire format stays simple
# while the dashboard still sees the BASEMENT.TEMP / BASEMENT.WATER model.

# short firmware zone id -> canonical zone (pass-through if already canonical)
ZONE_ALIASES = {
    "BASE01": "BASEMENT",
    "BASEMENT": "BASEMENT",
}

# JSON field in the POST body -> canonical SENSOR token. Fields not listed
# (e.g. "air", "light", "motion", "state", "zone") are ignored by the fan-out,
# so a node may post extra fields without the server caring.
FIELD_TO_SENSOR = {
    "temp": "TEMP",
    "temperature": "TEMP",
    "humidity": "HUMIDITY",
    "water": "WATER",
    "level": "WATER",
    "fire": "FIRE",
    "pot": "FIRE",
}


def canonical_zone(zone: str) -> str:
    z = str(zone).strip().upper()
    return ZONE_ALIASES.get(z, z)


# --------------------------------------------------------------------------
# Timing / UI
# --------------------------------------------------------------------------
# how much history to keep in memory per sensor (points). At the fastest 0.5s
# period, 7200 points ~= 1 hour.
RING_BUFFER_POINTS = 7200

# Simulated rooms get a much shorter history: ~50 sensors x 7200 points is a lot
# of RAM for data nobody will scroll back through, and the whole lot has to be
# JSON-encoded on every bootstrap.
SYNTH_RING_POINTS = 900
BOOTSTRAP_SYNTH_POINTS = 300

# time-scale presets for the per-panel time-scale selector: (label, seconds or None=all)
TIME_SCALES = [
    ("30 s", 30),
    ("2 min", 120),
    ("5 min", 300),
    ("30 min", 1800),
    ("All", None),
]
DEFAULT_TIME_SCALE_INDEX = 1  # "2 min"

UI_REFRESH_MS = 250     # plot repaint cadence (desktop UI)
BANNER_FLASH_MS = 500   # alarm banner flash cadence (desktop UI)

# --------------------------------------------------------------------------
# Anomaly detection (see anomaly.py)
# --------------------------------------------------------------------------
# Unlike the warn/alarm bands above, none of this is per-sensor: the detector
# learns each stream's own normal and flags where the *shape* breaks. These are
# the knobs for how twitchy that is. Defaults are tuned for the 0.5-2 s sample
# periods above; raise `level_z` / `delta_z` for fewer, more certain flags.
ANOMALY_ENABLED = True

ANOMALY = {
    # -- learning the baseline --
    # Short on purpose. These streams wander, so a long baseline lags behind
    # where the signal actually is and the lag alone starts scoring as a
    # deviation. Short enough to follow the wander, long enough that a real
    # step still stands out against it.
    "baseline_window_s": 45.0,   # how far back "normal" is learned from
    "min_baseline_points": 15,   # warm-up: nothing is flagged before this
    "min_sigma_frac": 0.004,     # sigma floor as a fraction of the y-range,
                                 # so a quiet stream cannot make every wobble
                                 # look like a 50-sigma event
    # -- point-wise tests --
    "level_z": 4.0,              # robust z on the value that opens a window
    "delta_z": 5.0,              # robust z on the sample-to-sample step:
                                 # above this the onset counts as "abrupt"
    "spike_max_s": 6.0,          # shorter than this -> a spike...
    "shift_min_s": 15.0,         # ...longer, and abrupt -> a level shift
    "close_after_s": 6.0,        # this long back inside normal closes a window
    "max_open_s": 25.0,          # a window cannot outlive this: past it the new
                                 # level is adopted as the baseline. The report
                                 # is about the *change*, so it marks the
                                 # transition, not the whole rest of the run.
    # -- condition tests --
    "flatline_min_s": 45.0,      # near-zero variation this long -> stuck sensor
    "flatline_frac": 0.25,       # "near-zero" = this fraction of the stream's
                                 # own normal per-sample step (NOT of the y-range:
                                 # a wide-range sensor barely moves within its
                                 # range even when perfectly healthy)
    "noise_factor": 4.0,         # recent spread vs baseline -> noise burst
    "noise_min_s": 20.0,
    "drift_window_s": 90.0,      # sustained one-way movement
    "drift_r2": 0.85,            # must fit a straight line this well...
    "drift_k": 4.0,              # ...and travel this many times further than a
                                 # driftless random walk would over the same
                                 # window (see the note in anomaly.py -- R^2 on
                                 # its own calls every wander a trend)
    # -- retention --
    "keep": 200,                 # anomalies kept in memory per process run
}

# --------------------------------------------------------------------------
# Transport defaults (for the real Arduino path — serial / Bluetooth-classic)
# --------------------------------------------------------------------------
SERIAL_PORT = "COM3"    # Bluetooth-Classic (HC-05) shows up as a COM port too
SERIAL_BAUD = 115200

# --------------------------------------------------------------------------
# Local logging (zero-install: SQLite + CSV, no Postgres)
# --------------------------------------------------------------------------
DB_PATH = "museumguard.sqlite"
CSV_DIR = "logs"        # a daily CSV per run day lands here

# --------------------------------------------------------------------------
# App identity
# --------------------------------------------------------------------------
APP_NAME = "MuseumGuard"
APP_TITLE = "MuseumGuard — Environmental & Security Monitoring"
