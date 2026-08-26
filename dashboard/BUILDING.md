# The 3D building view — and whether three.js is worth the rule change

MuseumGuard now opens on a see-through 3D museum: 3 floors, 12 rooms, click a
room to get the familiar floating-window dashboard scoped to it. One room —
**B1 · Archive & Vault** — is the real hardware rig. The other 11 are simulated.

The view is implemented **twice**, behind a live toggle in the building bar, so
the cost of relaxing the project's "stdlib only, no npm, no CDN, works offline"
rule (`README.md`) is something you can see rather than argue about.

Flip between them with the **CSS 3D / three.js** buttons. Same geometry, same
data, same interactions — the renderer is the only variable.

## The numbers

Measured on this machine, 12 rooms / 53 sensors, Chrome, 1568×746.

| | **CSS 3D** (Variant A) | **three.js** (Variant B) |
|---|---|---|
| Bytes downloaded | **0** | **1289 KB** (three 1243, OrbitControls 29, CSS2DRenderer 4, glue 13) |
| Files added to the repo | 1 (`building-css3d.js`) | 4 (`building-three.js` + `static/vendor/*`) |
| Renderer LOC | 346 | 360 |
| Scene cost | 160 DOM elements | 1 WebGL context, 12 meshes + 53 sprites |
| `update()` main-thread cost | 0.017 ms/frame | 1.78 ms/frame |
| Frame budget used @60 fps | ~0 % (compositor does the work) | **~11 %** |
| Works with `file://` / no server | yes | no (ES modules need HTTP) |

**Read the timing honestly.** CSS 3D's `update()` only mutates styles — the
actual projection and compositing happen off the main thread, so 0.017 ms is not
"the cost of drawing the building", it is "the cost of telling the browser what
changed". three.js's 1.78 ms *includes* the draw call submission, so it is close
to the true main-thread cost. **At 12 rooms neither is remotely a bottleneck;
both hold 60 fps.** Performance is not the deciding factor here — capability is.

## What the money actually buys

Things three.js does that the CSS variant **cannot**:

- **Real depth sorting.** CSS composites transformed planes per stacking
  context, so at some orbit angles a far wall paints over a near one. With
  translucent glass this mostly reads as "you can see through the building",
  which is the intended effect — but it is a happy accident, not occlusion.
- **Lighting.** Glass that catches a highlight and darkens at grazing angles.
  The CSS rooms are flat fills; they look like coloured paper, not glass.
- **Alarm rooms lit from inside.** A point light inside an alarming room spills
  red onto the floor slab and the neighbouring rooms. This is the single most
  striking thing in the whole feature and the CSS variant has no equivalent —
  it can only pulse the fill colour.
- **A free camera.** OrbitControls with damping and dolly, versus two Euler
  angles and a scale factor.
- **Headroom.** At 30+ rooms, or if you ever want real geometry (imported floor
  plans, glTF display cases, shadows, bloom), CSS 3D runs out and WebGL does not.

Things the CSS variant does **better**:

- **Nothing to download, nothing to vendor, nothing to break.** It is 346 lines
  of the same kind of code as the rest of the project.
- **Free interaction.** Rooms are `<div>`s: hover, click, tooltips and text
  layout are the browser's job. The three.js version needed a `Raycaster`, a
  drag-vs-click discriminator, and a `CSS2DRenderer` for labels.
- **Crisp text at any zoom without a second renderer.**
- **It keeps the README's strongest claim true.**

## Recommendation

**Keep both; default to CSS 3D.** That is how it currently ships.

For this demo at 12 rooms, the CSS variant is genuinely enough — it is the same
scene, it is legible on a projector, and it costs nothing. Lead with it, because
"a 3D museum with zero dependencies that works with the venue wifi down" is a
stronger story than the extra polish.

Then flip the toggle for ten seconds during the demo. The inside-lit alarm room
is the shot people remember, and having *both* lets you make the engineering
point out loud: this was a deliberate, measured trade, not an npm reflex.

If you would rather not carry 1.27 MB of vendored library in the repo at all,
delete `static/vendor/` and `static/js/building-three.js`. The toggle disables
itself with an explanatory tooltip and nothing else changes — that is the whole
point of the renderer interface.

**On the README wording:** if you keep Variant B, "no CDN, no npm" is still
true (nothing is fetched at runtime, nothing is installed), but "no
dependencies" is not. The accurate phrasing is *"zero dependencies on the
default path; an optional vendored three.js renderer for the 3D view."*

## How it fits together

```
building.py          floors, room geometry, sensor-kind catalog, scripted incidents
  -> config.py       generates one SensorDef per room sensor (48 synthetic + 5 real)
  -> transports.py   SimulatedSource drives all 53; correlated incidents per room
  -> storage.py      synthetic readings are buffered + streamed but NEVER persisted
  -> server.py       /api/bootstrap carries the building model; SSE unchanged
  -> index.html      shell: room routing, STATES map, renderer registry, MG bridge
       building-css3d.js   Variant A
       building-three.js   Variant B
```

Both renderers implement the same tiny interface and talk to the page only
through `window.MG`:

```js
MG.register({ name, label, available, bytes,
              mount(stageEl), unmount(), update(),
              setExplode(0..1), setFloor(floorId|null) });

MG.rooms          // [{id, name, floor, x, y, w, h, keys, live, ...}]
MG.building       // {floors, floorW, floorD, wallH, liveRoom}
MG.roomState(id)  // worst state across the room's sensors
MG.stateOf(key)   // one sensor's state
MG.sensorsIn(id)  // live values for a tooltip
MG.color(state)   // the shared state palette
MG.openRoom(id)   // drill into the dashboard
```

Adding a third renderer (a canvas wireframe, say) means one more file and no
changes anywhere else.

## Notes on the simulation

- **Only `B1_ARCHIVE` is real.** Its five sensors still report under the
  `GALLERY` / `BASEMENT` wire zones, so the Arduino protocol never learned about
  rooms and the firmware you write is unaffected.
- **Simulated rooms are never written to disk.** `record_reading` commits and
  fsyncs per reading; 48 extra sensors would mean ~60 fsyncs/sec of fiction and
  a polluted evidence log. `museumguard.sqlite` and `logs/readings-*.csv` still
  contain `GALLERY` and `BASEMENT` rows only — verified.
- **Scripted incidents** (`building.INCIDENTS`) fire every 20–40 s in a random
  room and drive several sensors bad *together* — a disturbed case tilts AND
  vibrates AND makes noise. That is the corroboration argument from
  `BRAINSTORM.md`, made visible: independent random walks would just look like
  noise. They clear themselves after ~15 s, and simulated latching alarms
  auto-release so a long demo doesn't accumulate stuck-red rooms. The **real**
  rig still latches until an operator RESETs it.
- The desktop UI (`app.py`) deliberately stays on the 5 real sensors.
