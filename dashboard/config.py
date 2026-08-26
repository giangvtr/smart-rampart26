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
                 room=None, synthetic=False, kind="analog"):
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
              room=LIVE_ROOM, kind="event"),
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
        ))

SENSORS_BY_KEY = {s.key: s for s in SENSORS}
ZONES = sorted({s.zone for s in SENSORS})


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

# time-scale presets for the per-panel combo box: (label, seconds or None=all)
TIME_SCALES = [
    ("30 s", 30),
    ("2 min", 120),
    ("5 min", 300),
    ("30 min", 1800),
    ("All", None),
]
DEFAULT_TIME_SCALE_INDEX = 1  # "2 min"

UI_REFRESH_MS = 250     # plot repaint cadence
BANNER_FLASH_MS = 500   # alarm banner flash cadence

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
