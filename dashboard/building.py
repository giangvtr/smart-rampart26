"""
The museum building: floors, rooms, room geometry and the sensor-kind catalog.

Pure data with **no imports from `config`** -- the dependency runs one way,
`config` imports this and turns `ROOMS` into `SensorDef`s. Keeping it inert
means both the 3D renderers and the simulator read the same numbers, and a room
can be moved or re-equipped without touching any logic.

Scenario
--------
The physical hackathon rig is five sensors in ONE basement room (`B1_ARCHIVE`,
`live=True`). Every other room is simulated so the dashboard can be shown at
building scale. Simulated rooms are deliberately given *different* sensor mixes
-- a plant room is not a jewel vault -- and the kinds are taken from
BRAINSTORM.md so the demo argues the motivation doc rather than decorating it.

Geometry
--------
Each floor is a `FLOOR_W x FLOOR_D` metre plate; rooms are axis-aligned
rectangles `(x, y, w, h)` in metres from the floor's top-left corner. Rooms do
not overlap and leave a 1 m margin, so a renderer can draw them naively.
"""
from __future__ import annotations

# floor plate size in metres
FLOOR_W = 40.0
FLOOR_D = 26.0

# wall height in metres (renderers extrude rooms by this)
WALL_H = 4.0

# level is the storey index used for stacking: basement below ground.
FLOORS = [
    {"id": "B1", "name": "Basement",     "level": -1},
    {"id": "G",  "name": "Ground floor", "level": 0},
    {"id": "F1", "name": "First floor",  "level": 1},
]

FLOORS_BY_ID = {f["id"]: f for f in FLOORS}


# --------------------------------------------------------------------------
# Sensor kinds
# --------------------------------------------------------------------------
# One entry per kind of sensor that can be fitted to a room. The five kinds the
# real rig uses (TEMP, HUMIDITY, LIGHT, MOTION, WATER) carry exactly the
# thresholds already in config.SENSORS, so a simulated room behaves like the
# real one; the rest are new kinds drawn from BRAINSTORM.md.
#
#   warn/alarm : (low, high) bounds, None on a side means "no bound there"
#   latched    : an alarm holds until an explicit RESET (mirrors the firmware)
#   kind       : "analog" wanders around a baseline, "event" blips discretely
SENSOR_TYPES: dict[str, dict] = {
    "TEMP": dict(
        label="Temperature", unit="°C", warn=(18, 24), alarm=(15, 28),
        vmin=10, vmax=32, latched=False, period_s=2.0, kind="analog"),
    "HUMIDITY": dict(
        label="Humidity", unit="%RH", warn=(45, 55), alarm=(35, 65),
        vmin=20, vmax=80, latched=False, period_s=2.0, kind="analog"),
    "LIGHT": dict(
        label="Light", unit="adc", warn=(None, 700), alarm=(None, 900),
        vmin=0, vmax=1023, latched=False, period_s=1.0, kind="analog"),
    "UV": dict(
        label="UV exposure", unit="idx", warn=(None, 2), alarm=(None, 4),
        vmin=0, vmax=10, latched=False, period_s=3.0, kind="analog"),
    "MOTION": dict(
        label="Motion", unit="bool", warn=None, alarm=(None, 0.5),
        vmin=0, vmax=1, latched=True, period_s=0.5, kind="event"),
    "WATER": dict(
        label="Water level", unit="adc", warn=(None, 100), alarm=(None, 300),
        vmin=0, vmax=600, latched=True, period_s=2.0, kind="analog"),
    "SMOKE": dict(
        label="Smoke", unit="ppm", warn=(None, 120), alarm=(None, 300),
        vmin=0, vmax=600, latched=True, period_s=1.5, kind="analog"),
    "CASE_TILT": dict(
        label="Case tilt", unit="°", warn=(None, 2), alarm=(None, 5),
        vmin=0, vmax=15, latched=True, period_s=0.5, kind="event"),
    "VIBRATION": dict(
        label="Vibration", unit="mg", warn=(None, 150), alarm=(None, 400),
        vmin=0, vmax=1000, latched=False, period_s=0.5, kind="analog"),
    "SOUND": dict(
        label="Sound level", unit="dB", warn=(None, 70), alarm=(None, 85),
        vmin=30, vmax=110, latched=False, period_s=0.5, kind="analog"),
    "DOOR": dict(
        label="Door contact", unit="bool", warn=None, alarm=(None, 0.5),
        vmin=0, vmax=1, latched=True, period_s=0.5, kind="event"),
    "KEYPAD": dict(
        label="Keypad fails", unit="fails", warn=(None, 2), alarm=(None, 4),
        vmin=0, vmax=6, latched=True, period_s=1.0, kind="event"),
}


# --------------------------------------------------------------------------
# Rooms
# --------------------------------------------------------------------------
class Room:
    """One showroom / service room on one floor.

    `sensors` are SENSOR_TYPES tokens to fit (simulated rooms only). The live
    room instead names the wire `zones` its real hardware already reports under,
    so the Arduino protocol never had to learn about rooms.
    """

    def __init__(self, id, name, floor, x, y, w, h,
                 sensors=(), zones=None, live=False, note="", style="empty"):
        self.id = id
        self.name = name
        self.floor = floor
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.sensors = list(sensors)
        # a simulated room reports under a single zone named after itself
        self.zones = list(zones) if zones else [id]
        self.live = live
        self.note = note
        # what the room is furnished with -- drives `fixtures`, filled in at the
        # bottom of this module once every room exists.
        self.style = style
        self.fixtures: list[dict] = []

    def to_json(self) -> dict:
        return {
            "id": self.id, "name": self.name, "floor": self.floor,
            "x": self.x, "y": self.y, "w": self.w, "h": self.h,
            "zones": self.zones, "live": self.live, "note": self.note,
            "style": self.style, "fixtures": self.fixtures,
        }


ROOMS = [
    # -- B1: the real rig lives here -------------------------------------
    Room("B1_ARCHIVE", "Archive & Vault", "B1", 1, 1, 18, 12,
         zones=["GALLERY", "BASEMENT"], live=True,
         note="Live hardware — the physical MuseumGuard rig", style="archive"),
    Room("B1_ROMAN", "Roman Antiquities", "B1", 21, 1, 18, 12,
         sensors=["TEMP", "HUMIDITY", "WATER", "CASE_TILT"], style="antiquities"),
    Room("B1_LOADING", "Loading bay", "B1", 1, 15, 22, 10,
         sensors=["DOOR", "MOTION", "KEYPAD"], style="loading"),
    Room("B1_CASTS", "Cast Court", "B1", 25, 15, 14, 10,
         sensors=["MOTION", "LIGHT", "VIBRATION"], style="casts"),

    # -- G ----------------------------------------------------------------
    Room("G_LOBBY", "Lobby", "G", 1, 1, 16, 13,
         sensors=["TEMP", "HUMIDITY", "MOTION", "SOUND"], style="lobby"),
    Room("G_EGYPT", "Egyptian Wing", "G", 19, 1, 20, 13,
         sensors=["TEMP", "HUMIDITY", "LIGHT", "CASE_TILT", "MOTION", "VIBRATION"],
         style="egypt"),
    Room("G_SCULPT", "Sculpture Hall", "G", 1, 16, 22, 9,
         sensors=["TEMP", "HUMIDITY", "LIGHT", "VIBRATION"], style="sculpture"),
    Room("G_ARMOURY", "Arms & Armour", "G", 25, 16, 14, 9,
         sensors=["TEMP", "HUMIDITY", "CASE_TILT", "MOTION"], style="armoury"),

    # -- F1 ---------------------------------------------------------------
    Room("F1_PAINT", "Paintings Gallery", "F1", 1, 1, 20, 13,
         sensors=["TEMP", "HUMIDITY", "LIGHT", "UV", "CASE_TILT", "MOTION"],
         style="paintings"),
    Room("F1_JEWELS", "Crown Jewels", "F1", 23, 1, 16, 13,
         sensors=["CASE_TILT", "VIBRATION", "SOUND", "MOTION", "KEYPAD", "LIGHT"],
         note="Highest-value room — tilt/vibration/sound corroborate each other",
         style="vault"),
    Room("F1_TEXTILE", "Textile Gallery", "F1", 1, 16, 18, 9,
         sensors=["TEMP", "HUMIDITY", "LIGHT", "UV"], style="textiles"),
    Room("F1_CERAMICS", "Asian Ceramics", "F1", 21, 16, 18, 9,
         sensors=["TEMP", "HUMIDITY", "CASE_TILT", "VIBRATION", "SMOKE"],
         style="ceramics"),
]

ROOMS_BY_ID = {r.id: r for r in ROOMS}

# wire zone -> room id. The live room owns two zones, every other room owns one.
ROOM_BY_ZONE = {z: r.id for r in ROOMS for z in r.zones}


def rooms_on(floor_id: str) -> list[Room]:
    return [r for r in ROOMS if r.floor == floor_id]


# --------------------------------------------------------------------------
# Scripted incidents -- what makes the building view worth looking at
# --------------------------------------------------------------------------
# Without these the 3D view is a static grid of green boxes. The simulator runs
# one of these every 20-40 s: several sensors in ONE room go bad *together*,
# which is exactly the corroboration story from BRAINSTORM.md ("sound + vibration",
# "fire detection with false-positive suppression").
#
#   room -> (human label, {sensor token: value to drive toward})
INCIDENTS = {
    "F1_JEWELS": ("Display case disturbed",
                  {"CASE_TILT": 7.0, "VIBRATION": 620.0, "SOUND": 92.0}),
    "G_EGYPT": ("Case tamper in the Egyptian Wing",
                {"CASE_TILT": 6.0, "VIBRATION": 480.0, "MOTION": 1.0}),
    "G_ARMOURY": ("Armour stand disturbed",
                  {"CASE_TILT": 6.5, "MOTION": 1.0}),
    "B1_ROMAN": ("Water ingress in the Roman gallery",
                 {"WATER": 420.0, "HUMIDITY": 72.0}),
    "B1_LOADING": ("Forced entry at the loading bay",
                   {"DOOR": 1.0, "MOTION": 1.0, "KEYPAD": 5.0}),
    "B1_CASTS": ("Impact in the Cast Court",
                 {"VIBRATION": 540.0, "MOTION": 1.0}),
    "F1_TEXTILE": ("Light/UV overexposure on textiles",
                   {"LIGHT": 950.0, "UV": 5.5}),
    "F1_CERAMICS": ("Smoke in the ceramics gallery",
                    {"SMOKE": 380.0, "TEMP": 30.0}),
    "G_SCULPT": ("Structural vibration in the Sculpture Hall",
                 {"VIBRATION": 520.0}),
}

# seconds between incidents, and how long one runs
INCIDENT_GAP_S = (20.0, 40.0)
INCIDENT_HOLD_S = 15.0


# --------------------------------------------------------------------------
# Furnishing -- what makes a room read as a room
# --------------------------------------------------------------------------
# The renderer draws these; it holds no dimensions of its own beyond how many
# pixels a metre is worth on screen. Coordinates are room-local metres.
#
# Volumes give the CENTRE (x, y) of their footprint plus w/d/h. Wall-mounted
# pieces give a wall ("n" = the y=0 edge, "s" = y=h, "w" = x=0, "e" = x=w), a
# distance `at` along it, and a `sill` height.
#
#   figure  an exhibit standing on a plinth. `pose` picks the silhouette:
#           statue / torso / bust / vase / armour / mannequin
#   case    glass vitrine, drawn translucent; `holds` puts an exhibit inside
#   block   solid box (shelving, crates, benches, counters, plinths)
#   column  round structural column, full storey height
#   painting / relief / hanging / door   flat, mounted on a wall
import random

FX_COLORS = {
    "frame":  "#d4af37",   # gilt picture frames
    "stone":  "#b6c0cb",   # marble and plaster
    "bronze": "#b98a4b",
    "glass":  "#8ad3ff",   # vitrine glazing
    "steel":  "#7d8ea0",   # armour, shelving
    "wood":   "#7a5a3a",   # benches, counters
    "crate":  "#8a6c46",
    "fabric": "#a483b8",   # textiles
    "clay":   "#c2764e",   # ceramics
    "gold":   "#e5c76b",   # the jewels
    "door":   "#58a6ff",
}


def _wall(rng, room, walls, every, sill, h, kind="painting", colour=None,
          wmin=1.0, wmax=2.1):
    """Evenly space wall-mounted pieces along one or more walls."""
    out = []
    for wall in walls:
        span = room.w if wall in "ns" else room.h
        usable = span - 3.0
        n = max(1, int(usable // every))
        for i in range(n):
            out.append({
                "t": kind,
                "wall": wall,
                "at": round(1.5 + usable * (i + 0.5) / n, 2),
                "w": round(rng.uniform(wmin, wmax), 2),
                "h": round(h * rng.uniform(0.85, 1.2), 2),
                "sill": sill,
                "c": colour or FX_COLORS["frame"],
            })
    return out


def _row(room, n, y, w, d, h, colour, kind="block", inset=2.5, **extra):
    """A row of identical pieces across the room at depth `y`."""
    x0, x1 = inset, room.w - inset
    return [dict({
        "t": kind,
        "x": round(x0 + (x1 - x0) * (i + 0.5) / n, 2),
        "y": round(y, 2),
        "w": w, "d": d, "h": h, "c": colour,
    }, **extra) for i in range(n)]


def _figures(room, n, y, h, pose, colour, inset=2.5, w=1.3):
    return _row(room, n, y, w, w, h, colour, kind="figure", inset=inset, pose=pose)


def _door(room):
    """One door, on whichever wall faces the middle of the floor plate."""
    cx, cy = room.x + room.w / 2, room.y + room.h / 2
    if abs(cy - FLOOR_D / 2) >= abs(cx - FLOOR_W / 2):
        wall = "s" if cy < FLOOR_D / 2 else "n"
        at = room.w / 2
    else:
        wall = "e" if cx < FLOOR_W / 2 else "w"
        at = room.h / 2
    return [{"t": "door", "wall": wall, "at": round(at, 2),
             "w": 1.8, "h": 2.4, "sill": 0.0, "c": FX_COLORS["door"]}]


def furnish(room) -> list[dict]:
    """Deterministic per room -- the same museum every reload."""
    rng = random.Random(room.id)
    D, F = room.h, FX_COLORS
    s = room.style
    f: list[dict] = []

    # ---- galleries ------------------------------------------------------
    if s == "paintings":
        f += _wall(rng, room, "nsew", 3.4, 1.5, 1.5)
        f += _row(room, 2, D * 0.46, 2.4, 1.3, 1.5, F["glass"], "case",
                  holds="bust", inset=6.0)
        f += _row(room, 3, D * 0.78, 2.4, 0.5, 0.45, F["wood"])

    elif s == "egypt":
        f += _wall(rng, room, "ns", 4.6, 1.5, 1.8, kind="relief", colour=F["stone"])
        f += _figures(room, 3, D * 0.28, 2.8, "statue", F["stone"], inset=3.5)
        # a sarcophagus down the middle, then vitrines along the back
        f += [{"t": "block", "x": round(room.w / 2, 2), "y": round(D * 0.54, 2),
               "w": 3.4, "d": 1.3, "h": 0.9, "c": F["bronze"]}]
        f += _row(room, 3, D * 0.80, 2.2, 1.3, 1.6, F["glass"], "case", holds="vase")

    elif s == "sculpture":
        f += _figures(room, 4, D * 0.30, 2.9, "statue", F["stone"], inset=3.0, w=1.5)
        f += _figures(room, 3, D * 0.68, 2.2, "torso", F["stone"], inset=5.0, w=1.4)
        f += [{"t": "column", "x": round(room.w * (0.25 + 0.5 * i), 2),
               "y": round(D * 0.5, 2), "w": 1.0, "d": 1.0, "h": WALL_H,
               "c": F["stone"]} for i in range(2)]

    elif s == "casts":
        # a cast court is wall-to-wall plaster copies, floor to ceiling
        f += _figures(room, 3, D * 0.30, 3.4, "statue", F["stone"], inset=2.5, w=1.6)
        f += _figures(room, 3, D * 0.72, 2.0, "bust", F["stone"], inset=3.0, w=1.1)

    elif s == "antiquities":
        f += _wall(rng, room, "n", 4.2, 1.5, 1.6, kind="relief", colour=F["stone"])
        f += _figures(room, 3, D * 0.28, 2.4, "torso", F["stone"], inset=3.0)
        f += _row(room, 3, D * 0.62, 2.2, 1.3, 1.5, F["glass"], "case", holds="vase")
        f += _figures(room, 2, D * 0.86, 1.9, "bust", F["stone"], inset=5.0, w=1.0)

    elif s == "armoury":
        f += _figures(room, 3, D * 0.30, 2.5, "armour", F["steel"], inset=2.5, w=1.2)
        # low weapon cases, and shields hung on the back wall
        f += _row(room, 2, D * 0.66, 3.2, 1.1, 1.1, F["glass"], "case", holds="blade")
        f += _wall(rng, room, "n", 3.0, 1.9, 1.1, kind="relief", colour=F["steel"],
                   wmin=0.9, wmax=1.3)

    elif s == "vault":
        # small room, high value: cases in a ring around one hero case
        f += _row(room, 3, D * 0.28, 2.0, 1.5, 1.4, F["glass"], "case",
                  holds="gem", inset=2.6)
        f += _row(room, 3, D * 0.80, 2.0, 1.5, 1.4, F["glass"], "case",
                  holds="gem", inset=2.6)
        f += [{"t": "case", "x": round(room.w / 2, 2), "y": round(D / 2, 2),
               "w": 3.0, "d": 3.0, "h": 2.0, "c": F["glass"], "holds": "crown"}]
        f += _wall(rng, room, "n", 5.0, 1.7, 1.2)

    elif s == "textiles":
        # hangings are tall and narrow; mannequins wear the dressed pieces
        f += _wall(rng, room, "nsw", 3.2, 0.9, 2.4, kind="hanging",
                   colour=F["fabric"], wmin=1.2, wmax=1.8)
        f += _figures(room, 3, D * 0.42, 2.0, "mannequin", F["fabric"], inset=3.0, w=1.0)
        f += _row(room, 2, D * 0.78, 3.0, 1.2, 1.1, F["glass"], "case", holds="blade")

    elif s == "ceramics":
        f += _figures(room, 4, D * 0.30, 1.9, "vase", F["clay"], inset=2.5, w=1.0)
        f += _row(room, 3, D * 0.66, 2.2, 1.3, 1.6, F["glass"], "case", holds="vase")
        f += _wall(rng, room, "n", 2.6, 2.0, 0.9, kind="relief", colour=F["clay"],
                   wmin=0.8, wmax=1.1)

    # ---- the two rooms that are not galleries, plus back-of-house -------
    elif s == "lobby":
        f += [{"t": "column", "x": round(room.w * (0.28 + 0.44 * (i % 2)), 2),
               "y": round(D * (0.30 + 0.42 * (i // 2)), 2),
               "w": 1.1, "d": 1.1, "h": WALL_H, "c": F["stone"]} for i in range(4)]
        f += [{"t": "block", "x": round(room.w * 0.5, 2), "y": round(D * 0.18, 2),
               "w": 5.0, "d": 1.4, "h": 1.1, "c": F["wood"]}]      # reception desk
        f += _row(room, 2, D * 0.86, 3.0, 0.6, 0.45, F["wood"], inset=3.5)

    elif s == "archive":
        f += [r for j in range(3)
              for r in _row(room, 2, 2.0 + (D - 4.0) * (j + 0.5) / 3,
                            6.0, 0.9, 2.6, F["steel"])]           # shelving runs
        f += [{"t": "block", "x": round(room.w * 0.5, 2), "y": round(D * 0.5, 2),
               "w": 2.0, "d": 1.0, "h": 0.8, "c": F["wood"]}]     # work table

    elif s == "loading":
        f += [r for j in range(2)
              for r in _row(room, 3, 3.0 + (D - 6.0) * (j + 0.5) / 2,
                            2.2, 2.2, 1.8, F["crate"])]
        # the roller shutter the DOOR sensor watches
        f += [{"t": "door", "wall": "w", "at": round(D / 2, 2),
               "w": 4.5, "h": 3.4, "sill": 0.0, "c": F["door"]}]

    if s != "loading":
        f += _door(room)
    return f


for _r in ROOMS:
    _r.fixtures = furnish(_r)


# --------------------------------------------------------------------------
# The building shell -- the bit that makes it look like a museum
# --------------------------------------------------------------------------
# Renderers extrude this themselves; it is only the massing, deliberately
# rough. Facade windows are generated at `gap` spacing along each outer wall.
SHELL = {
    "window": {"w": 1.8, "h": 2.4, "sill": 1.0, "gap": 4.4},
    # a classical portico projecting from the west face, in front of the Lobby
    "entrance": {
        "floor": "G", "wall": "w", "at": 7.5,
        "width": 12.0, "depth": 5.0, "columns": 6,
        "column_r": 0.45, "steps": 4, "rise": 0.4, "run": 1.0,
        "entablature": 1.2, "pediment": 3.6,
    },
    "roof": {"parapet": 1.2, "skylight": [16.0, 9.0]},
}
