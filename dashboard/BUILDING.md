# The 3D building view

MuseumGuard opens on a see-through 3D museum: 3 floors, 12 rooms, 54 sensors.
Click a room and you get the familiar floating-window dashboard, scoped to that
room. One room — **B1 · Archive & Vault** — is the real hardware rig. The other
11 are simulated, so the dashboard can be shown at building scale.

It is drawn with **CSS 3D transforms and nothing else**: no WebGL, no npm, no
CDN, no build step. The whole view is one 727-line file plus the geometry the
server already sends.

## Getting around

| | |
|---|---|
| **Orbit** | drag anywhere on the stage |
| **Zoom** | mouse wheel |
| **Isolate a floor** | the floor tabs; the other storeys drop to 7 % opacity **and stop taking clicks**, which is how you reach a basement room hidden under the ground floor |
| **Open a room** | click it — or deep-link straight to `#/room/F1_JEWELS` |
| **Peek without opening** | hover for live values per sensor |

Navigation is hash-based, so moving between the building and a room never
reloads the page: the single SSE connection and the login session both survive.

The floor spacing used to be a slider. Every setting below about a third buried
the lower floors and every setting above it scattered them into three unrelated
plans, so it is now fixed at what the middle of that slider gave.

## The rooms

Nine of the twelve are public galleries; the other three are the ones the story
needs. Each carries a different sensor mix, because a jewel vault is not a
loading bay.

| Floor | Room | Sensors |
|---|---|---|
| B1 | **Archive & Vault** — *the live rig* | the real 5, under the `GALLERY`/`BASEMENT` wire zones |
| B1 | Roman Antiquities | TEMP, HUMIDITY, WATER, CASE_TILT |
| B1 | Loading bay | DOOR, MOTION, KEYPAD |
| B1 | Cast Court | MOTION, LIGHT, VIBRATION |
| G | Lobby | TEMP, HUMIDITY, MOTION, SOUND |
| G | Egyptian Wing | TEMP, HUMIDITY, LIGHT, CASE_TILT, MOTION, VIBRATION |
| G | Sculpture Hall | TEMP, HUMIDITY, LIGHT, VIBRATION |
| G | Arms & Armour | TEMP, HUMIDITY, CASE_TILT, MOTION |
| F1 | Paintings Gallery | TEMP, HUMIDITY, LIGHT, UV, CASE_TILT, MOTION |
| F1 | Crown Jewels | CASE_TILT, VIBRATION, SOUND, MOTION, KEYPAD, LIGHT |
| F1 | Textile Gallery | TEMP, HUMIDITY, LIGHT, UV |
| F1 | Asian Ceramics | TEMP, HUMIDITY, CASE_TILT, VIBRATION, SMOKE |

## What you are looking at

**Rooms** are glass boxes coloured by their worst sensor state — green / amber /
red — with a pulsing fill when something is in ALARM. A row of dots along the
south edge carries one dot per sensor in its *own* state, so you can see *which*
sensor is hot before opening anything. The live room wears a blue pip.

**The exhibits** are what make a room legible as a room, and each is drawn as
the thing it claims to be. An exhibit standing on the floor is two crossed
silhouettes on a plinth — cheap (two `<div>`s), and unlike a billboard it still
reads as an object from any orbit angle, because one of the two planes is always
near face-on. The silhouette is a `clip-path` picked by `pose`:

| `pose` | where |
|---|---|
| `statue` | Sculpture Hall, Cast Court, Egyptian Wing |
| `torso` | Roman Antiquities, Sculpture Hall |
| `bust` | Cast Court, Roman Antiquities |
| `vase` | Asian Ceramics |
| `armour` | Arms & Armour |
| `mannequin` | Textile Gallery |

Glass vitrines can hold something — `holds: "crown" | "gem" | "vase" | "bust" |
"blade"` puts a small gilt exhibit on an interior pedestal. Walls carry framed
paintings (gilt frame, canvas inset), carved `relief` panels, hung shields, and
tall fabric `hanging`s. Every room also has a door, on whichever wall faces the
middle of the plate.

**The shell** is deliberately rough massing — enough that the stack reads as one
building rather than three floating floor plans. A glazed facade per storey with
punched windows (the basement gets none; it is below grade), a roof with a
parapet and a skylight, and a classical entrance portico on the west face in
front of the Lobby: a flight of steps, a colonnade, an entablature and a
pediment.

## How it fits together

```
building.py          floors, room geometry, sensor-kind catalog, the exhibits,
                     the shell, and the scripted incidents
  -> config.py       one SensorDef per room sensor (49 synthetic + 5 real)
  -> transports.py   SimulatedSource drives all 54; correlated incidents
  -> storage.py      synthetic readings are buffered + streamed, NEVER persisted
  -> server.py       /api/bootstrap carries the building model; SSE unchanged
  -> index.html      shell: room routing, STATES map, the renderer holder
       building-css3d.js   the view
```

**All geometry lives in `building.py`.** The renderer owns no dimensions of its
own beyond how many pixels a metre is worth on screen, so a room can be moved,
re-equipped or re-furnished without opening any JavaScript. Adding an exhibit
type is one entry in `POSES` and one line in `furnish()`.

Two things are building-wide and outlive any one room, so they are seeded once
at boot rather than inside `build()`: the `STATES` map behind the banner and the
room colours, and the `ANOMS` list behind the anomaly pane. `openRoom()` replays
both onto the charts it has just built.

The renderer talks to the page through one small object and nothing else:

```js
MG.register({ name, label, bytes,
              mount(stageEl), unmount(), update(), setFloor(floorId|null) });

MG.rooms          // [{id, name, floor, x, y, w, h, keys, fixtures, live, ...}]
MG.building       // {floors, floorW, floorD, wallH, shell, liveRoom}
MG.roomState(id)  // worst state across the room's sensors
MG.stateOf(key)   // one sensor's state
MG.sensorsIn(id)  // live values, for the tooltip
MG.color(state)   // the shared state palette
MG.openRoom(id)   // drill into the dashboard
```

`update()` runs once per animation frame while the building is on screen;
everything else is driven from the bar. The renderer never touches the
dashboard, and the dashboard never reaches into the scene — swapping in a
different implementation (a canvas wireframe, a WebGL one) is one file and no
changes anywhere else.

## Why CSS 3D and not WebGL

Measured on this machine, 12 rooms / 54 sensors / 133 exhibits, Chrome:

| | |
|---|---|
| Bytes downloaded | **0** |
| Scene | 1105 DOM elements (98 of them exhibit silhouettes) |
| `update()` | **0.009 ms** |
| `update()` + a full camera re-apply | **0.076 ms** — 0.5 % of a 60 fps frame |

**Read those honestly.** `update()` only mutates styles; the projection and
compositing happen off the main thread, so this is the cost of *telling the
browser what changed*, not the cost of drawing the building. The real ceiling
here is compositor work on ~1100 transformed planes, which these numbers do not
capture.

That ceiling is still a long way off at this scale, and CSS 3D buys things a
WebGL renderer would have to reimplement: rooms are `<div>`s, so hit-testing,
hover, tooltips and crisp text at any zoom are the browser's job. A WebGL
version was built and measured against this one; it looked better — real depth
sorting, glass that catches a highlight, alarm rooms lit from the inside — but
it cost 1.27 MB of vendored library to do it, and at this scale that is paying
for polish, not for capability. It has been removed. If this ever grows to 30+
rooms, or wants imported floor plans, shadows or bloom, that is the point to
bring it back.

## Known limits, stated plainly

- **No true depth sorting.** CSS composites transformed planes per stacking
  context, so at some orbit angles a far wall paints over a near one. With
  translucent glass that mostly reads as "you can see through the building",
  which is the intended effect — but it is a happy accident, not occlusion.
- **No lighting or shadows.** Rooms are flat fills; an alarm can only pulse its
  colour, not glow.
- **Rooms on lower floors sit behind the ones above them** in the default view,
  which is what the floor tabs are for — dimmed floors are click-through
  precisely so the basement stays reachable.
- **Room labels on the lower storeys are dimmed** by the translucent slabs above
  them. Hovering names the room regardless, and isolating a floor clears it.

## Notes on the simulation

- **Only `B1_ARCHIVE` is real.** Its five sensors still report under the
  `GALLERY` / `BASEMENT` wire zones, so the Arduino protocol never learned about
  rooms and the firmware is unaffected. `room` is a display grouping only.
- **Simulated rooms are never written to disk.** `record_reading` commits and
  fsyncs per reading; 49 extra sensors would mean ~60 fsyncs/sec of fiction and
  a polluted evidence log. Verified: `museumguard.sqlite` and
  `logs/readings-*.csv` contain `GALLERY` and `BASEMENT` rows only.
- **Scripted incidents** (`building.INCIDENTS`) fire every 20–40 s in a random
  room and drive several sensors bad *together* — a disturbed case tilts AND
  vibrates AND makes noise. That is the corroboration argument from
  `BRAINSTORM.md` made visible; independent random walks would just look like
  noise. They clear after ~15 s, and simulated latching alarms auto-release so a
  long demo does not accumulate stuck-red rooms. The **real** rig still latches
  until an operator RESETs it.
- **Anomaly detection covers the analog streams only**, simulated ones included.
  An on/off sensor has no normal spread for `anomaly.py` to learn from, so
  DOOR / MOTION / CASE_TILT / KEYPAD are excluded and left to their alarm
  latches.
- The desktop UI (`app.py`) deliberately stays on the 5 real sensors — 54 docks
  would be unusable.
