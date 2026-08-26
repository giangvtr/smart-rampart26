# The 3D building view

MuseumGuard opens on a see-through 3D museum: 3 floors, 12 rooms, 53 sensors.
Click a room and you get the familiar floating-window dashboard, scoped to that
room. One room — **B1 · Archive & Vault** — is the real hardware rig. The other
11 are simulated, so the dashboard can be shown at building scale.

It is drawn with **CSS 3D transforms and nothing else**: no WebGL, no npm, no
CDN, no build step. The whole view is one 656-line file plus the geometry the
server already sends.

## Getting around

| | |
|---|---|
| **Orbit** | drag anywhere on the stage |
| **Zoom** | mouse wheel |
| **Explode** | the slider pulls the storeys apart; at 0 the building closes into a single glass block |
| **Isolate a floor** | the floor tabs; the other storeys drop to 7 % opacity **and stop taking clicks**, which is how you reach a basement room hidden under the ground floor |
| **Open a room** | click it — or deep-link straight to `#/room/F1_JEWELS` |
| **Peek without opening** | hover for live values per sensor |

Navigation is hash-based, so moving between the building and a room never
reloads the page: the single SSE connection and the login token both survive.

## What you are looking at

**Rooms** are glass boxes coloured by their worst sensor state — green / amber /
red — with a pulsing fill when something is in ALARM. A row of dots along the
south edge carries one dot per sensor in its *own* state, so you can see *which*
sensor is hot before opening anything. The live room wears a blue pip.

**Furniture** is what makes a room legible as a room: gilt-framed paintings on
the gallery walls, statues on plinths in the Sculpture Hall and the Egyptian
Wing, glass vitrines, shelving runs in the Archive, server racks, crates on the
loading bay, tanks in the plant room. Every room also has a door, on whichever
wall faces the middle of the plate.

**The shell** is deliberately rough massing — enough that the stack reads as one
building rather than three floating floor plans. A glazed facade per storey with
punched windows (the basement gets none; it is below grade), a roof with a
parapet and a skylight, and a classical entrance portico on the west face in
front of the Lobby: a flight of steps, a colonnade, an entablature and a
pediment.

Room labels **fade out as the stack closes**. Compressed, you are looking
through 12 rooms at once and every caption collides — and the closed stack is
the "here is the building" shot, which wants no labels anyway. Isolating a floor
brings them straight back.

## How it fits together

```
building.py          floors, room geometry, sensor-kind catalog, furniture,
                     the shell, and the scripted incidents
  -> config.py       one SensorDef per room sensor (48 synthetic + 5 real)
  -> transports.py   SimulatedSource drives all 53; correlated incidents
  -> storage.py      synthetic readings are buffered + streamed, NEVER persisted
  -> server.py       /api/bootstrap carries the building model; SSE unchanged
  -> index.html      shell: room routing, STATES map, the renderer holder
       building-css3d.js   the view
```

**All geometry lives in `building.py`.** The renderer owns no dimensions of its
own beyond how many pixels a metre is worth on screen, so a room can be moved,
re-equipped or re-furnished without opening any JavaScript.

The renderer talks to the page through one small object and nothing else:

```js
MG.register({ name, label, bytes,
              mount(stageEl), unmount(), update(),
              setExplode(0..1), setFloor(floorId|null) });

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

Measured on this machine, 12 rooms / 53 sensors / 106 fixtures, Chrome:

| | |
|---|---|
| Bytes downloaded | **0** |
| Scene | 778 DOM elements |
| `update()` | **0.034 ms** |
| `update()` + a full camera re-apply (i.e. mid-orbit) | **0.103 ms** — 0.6 % of a 60 fps frame |

**Read those honestly.** `update()` only mutates styles; the projection and
compositing happen off the main thread, so this is the cost of *telling the
browser what changed*, not the cost of drawing the building. The real ceiling
here is compositor work on ~780 transformed planes, which these numbers do not
capture.

That ceiling is still a long way off at this scale, and CSS 3D buys things a
WebGL renderer would have to reimplement: rooms are `<div>`s, so hit-testing,
hover, tooltips and crisp text at any zoom are the browser's job. A WebGL
version was built and measured against this one; it looked better — real depth
sorting, glass that catches a highlight, alarm rooms lit from the inside — but
it cost 1.27 MB of vendored library to do it, and at 12 rooms that is paying for
polish, not for capability. It has been removed. If this ever grows to 30+
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

## Notes on the simulation

- **Only `B1_ARCHIVE` is real.** Its five sensors still report under the
  `GALLERY` / `BASEMENT` wire zones, so the Arduino protocol never learned about
  rooms and the firmware is unaffected. `room` is a display grouping only.
- **Simulated rooms are never written to disk.** `record_reading` commits and
  fsyncs per reading; 48 extra sensors would mean ~60 fsyncs/sec of fiction and
  a polluted evidence log. Verified: `museumguard.sqlite` and
  `logs/readings-*.csv` contain `GALLERY` and `BASEMENT` rows only.
- **Scripted incidents** (`building.INCIDENTS`) fire every 20–40 s in a random
  room and drive several sensors bad *together* — a disturbed case tilts AND
  vibrates AND makes noise. That is the corroboration argument from
  `BRAINSTORM.md` made visible; independent random walks would just look like
  noise. They clear after ~15 s, and simulated latching alarms auto-release so a
  long demo does not accumulate stuck-red rooms. The **real** rig still latches
  until an operator RESETs it.
- The desktop UI (`app.py`) deliberately stays on the 5 real sensors — 53 docks
  would be unusable.
