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
        self.key = key            # unique id, e.g. "GALLERY.TEMP"
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
        # Whether anomaly.py should watch this stream. Off for on/off sensors:
        # a 0/1 signal has no "normal spread" to learn, so every trip would
        # score as an infinite deviation. Motion is covered by its alarm latch.
        self.detect_anomalies = detect_anomalies

    @property
    def sensor(self) -> str:
        # the SENSOR token used on the wire, e.g. "TEMP"
        return self.key.split(".", 1)[1]


# Two zones from the spec: Gallery (exhibition hall) + Basement. Both are wired
# to the ONE physical rig, which the scenario puts in a single basement room --
# hence room="B1_ARCHIVE" on all five. These are the only non-synthetic sensors.
LIVE_ROOM = "B1_ARCHIVE"

SENSORS = [
    SensorDef("GALLERY.TEMP",     "GALLERY",  "Temperature", "°C",
              warn=(18, 24), alarm=(15, 28), vmin=10, vmax=32, period_s=2.0,
              room=LIVE_ROOM),
    SensorDef("GALLERY.HUMIDITY", "GALLERY",  "Humidity",    "%RH",
              warn=(45, 55), alarm=(35, 65), vmin=20, vmax=80, period_s=2.0,
              room=LIVE_ROOM),
    SensorDef("GALLERY.LIGHT",    "GALLERY",  "Light",       "adc",
              warn=(None, 700), alarm=(None, 900), vmin=0, vmax=1023, period_s=1.0,
              room=LIVE_ROOM),
    SensorDef("GALLERY.MOTION",   "GALLERY",  "Motion",      "bool",
              warn=None, alarm=(None, 0.5), vmin=0, vmax=1, latched=True, period_s=0.5,
              room=LIVE_ROOM, kind="event", detect_anomalies=False),
    SensorDef("BASEMENT.WATER",   "BASEMENT", "Water level", "adc",
              warn=(None, 100), alarm=(None, 300), vmin=0, vmax=600, latched=True, period_s=2.0,
              room=LIVE_ROOM),
]

# The five above are the real rig. Everything below is the simulated museum:
# one zone per room, its sensor mix taken from building.ROOMS. Generated rather
# than written out so re-equipping a room is a one-line edit in building.py.
LIVE_SENSORS = list(SENSORS)

for _room in building.ROOMS:
    for _tok in _room.sensors:
        _t = building.SENSOR_TYPES[_tok]
        SENSORS.append(SensorDef(
            f"{_room.id}.{_tok}", _room.id, _t["label"], _t["unit"],
            warn=_t["warn"], alarm=_t["alarm"], vmin=_t["vmin"], vmax=_t["vmax"],
            latched=_t["latched"], period_s=_t["period_s"],
            room=_room.id, synthetic=True, kind=_t["kind"],
            # same rule as the real rig: an on/off stream has no spread for
            # anomaly.py to learn from, so only the analog kinds are watched
            detect_anomalies=(_t["kind"] == "analog"),
        ))

SENSORS_BY_KEY = {s.key: s for s in SENSORS}
ZONES = sorted({s.zone for s in SENSORS})


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
