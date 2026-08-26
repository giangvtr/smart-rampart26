/* MuseumGuard — the 3D building view, drawn with CSS 3D transforms.
 *
 * Zero dependencies. The museum is ordinary DOM inside a `preserve-3d` scene,
 * so the browser does the projection and we get hit-testing, hover and text
 * layout for free — the things a hand-rolled canvas renderer would have to
 * reimplement (picking, depth sorting, billboarded labels).
 *
 * The trade, stated honestly: CSS composites transformed planes per stacking
 * context rather than depth-sorting fragments, so at some angles a far wall can
 * paint over a near one. With translucent glass walls that reads as "see
 * through the building", which is the effect we want anyway — but it is not
 * real occlusion, and there is no lighting or shadowing. At 12 rooms that costs
 * nothing worth having; a WebGL renderer would only start to pay for itself at
 * an order of magnitude more geometry.
 *
 * Everything drawn here — room boxes, furniture, the shell — is geometry from
 * building.py, delivered over /api/bootstrap. This file owns no dimensions of
 * its own beyond how many pixels a metre is worth on screen.
 *
 * Registers itself as `MG.register(...)`; the shell owns the camera-free bar
 * controls (floor filter, readout).
 */
"use strict";

(function(){

// --- tuning ---------------------------------------------------------------
const PX_PER_M   = 13;          // one horizontal metre -> screen px at zoom 1
const VPM        = 9;           // one VERTICAL metre -> px. Lower than
                                // PX_PER_M on purpose: at true scale a 4 m
                                // storey is a sliver next to a 40 m plate.
// How far apart the storeys sit. This was a slider; every value below about a
// third buries the lower floors and every value above it scatters them, so it
// is now simply fixed at what the slider's midpoint used to give.
const FLOOR_GAP  = 173;         // px of translateZ between storeys
const ROOM_Z     = 0.6;         // px a room floats above its floor slab, so
                                // the two are never coplanar for hit-testing
const HOVER_LIFT = 10;          // px a room rises under the cursor
const CLICK_SLOP = 5;           // px of movement still counted as a click

const state = {
  el: null, scene: null, host: null,
  rooms: new Map(),        // room id -> {el, label, dots: Map, room}
  spin: -34, tilt: 58, zoom: 1,
  floor: null,
  hover: null, dirty: true,
};

// --- helpers --------------------------------------------------------------
const el = (cls, parent) => {
  const d = document.createElement("div");
  d.className = cls;
  if (parent) parent.appendChild(d);
  return d;
};

/** #rrggbb -> "r,g,b" so it can drive rgba() alpha ramps in CSS. */
function rgb(hex){
  const h = (hex || "#6e7681").replace("#", "");
  return [0, 2, 4].map(i => parseInt(h.slice(i, i+2), 16)).join(",");
}

/* A vertical plane, positioned by its bottom-left corner in room coordinates.
 *
 * `rotateX(90deg)` about the element's top-left corner sends the element's
 * local +y axis to world +Z, so the plane stands UP out of the floor and its
 * CSS top edge is its base. `axis:"y"` adds a rotateZ so the plane runs along
 * the room's +y instead of +x. Everything vertical in this file — room walls,
 * facade, painting backers, statue silhouettes — is one of these.
 */
function plane(parent, cls, {x = 0, y = 0, z = 0, len, h, axis = "x"}){
  const p = el(cls, parent);
  p.style.width  = (len * PX_PER_M) + "px";
  p.style.height = (h * VPM) + "px";
  p.style.transformOrigin = "0 0";
  p.style.transform =
    `translate3d(${x * PX_PER_M}px, ${y * PX_PER_M}px, ${z * VPM}px) ` +
    (axis === "y" ? "rotateZ(90deg) " : "") + "rotateX(90deg)";
  return p;
}

/* A horizontal slab: ONE div. A plinth is 30-40 cm tall and seen from above --
 * its four sides are three or four extra transformed planes each for almost no
 * pixels, and at ~50 exhibits that is the difference between a smooth scene and
 * a stuttering one. `x,y` is the centre of the footprint. */
function slab(parent, cls, {x, y, z = 0, w, d, colour}){
  const p = el(cls, parent);
  if (colour) p.style.setProperty("--f", rgb(colour));
  p.style.left = ((x - w / 2) * PX_PER_M) + "px";
  p.style.top  = ((y - d / 2) * PX_PER_M) + "px";
  p.style.width  = (w * PX_PER_M) + "px";
  p.style.height = (d * PX_PER_M) + "px";
  p.style.transform = `translateZ(${z * VPM}px)`;
  return p;
}

/* A box: four sides plus a lid. `x,y` is the CENTRE of the footprint, matching
 * the fixture format building.py emits. */
function box(parent, cls, {x, y, z = 0, w, d, h, colour}){
  const g = el(cls + " vol", parent);
  if (colour) g.style.setProperty("--f", rgb(colour));
  const x0 = x - w / 2, y0 = y - d / 2;
  g.style.left = (x0 * PX_PER_M) + "px";
  g.style.top  = (y0 * PX_PER_M) + "px";
  g.style.width  = (w * PX_PER_M) + "px";
  g.style.height = (d * PX_PER_M) + "px";
  g.style.transform = `translateZ(${z * VPM}px)`;

  // the four sides, in the box's own local coordinates
  plane(g, "side", {x: 0, y: 0, len: w, h, axis: "x"});
  plane(g, "side", {x: 0, y: d, len: w, h, axis: "x"});
  plane(g, "side", {x: 0, y: 0, len: d, h, axis: "y"});
  plane(g, "side", {x: w, y: 0, len: d, h, axis: "y"});

  const lid = el("lid", g);
  lid.style.transform = `translateZ(${h * VPM}px)`;
  return g;
}

// --- one-time stylesheet --------------------------------------------------
// Injected rather than living in index.html so this renderer is self-contained:
// deleting this one file removes the 3D view completely.
const CSS = `
#b3d{position:absolute; inset:0; perspective:1700px; perspective-origin:50% 46%}
#b3d .scene{
  position:absolute; left:50%; top:47%; width:0; height:0;
  transform-style:preserve-3d; will-change:transform;
}
#b3d .floor{position:absolute; transform-style:preserve-3d; transition:opacity .25s ease}
#b3d .floor.dim{opacity:.07; pointer-events:none}
#b3d .slab{
  /* decorative only. It is coplanar with every room plate on its floor, and a
     coplanar tie in a preserve-3d context resolves by paint order, not by what
     you think you clicked -- so it must never absorb a pointer. */
  position:absolute; inset:0; transform-style:preserve-3d; pointer-events:none;
  background:
    repeating-linear-gradient(0deg,rgba(88,166,255,.05) 0 1px,transparent 1px 34px),
    repeating-linear-gradient(90deg,rgba(88,166,255,.05) 0 1px,transparent 1px 34px),
    rgba(20,28,38,.42);
  border:1px solid rgba(88,166,255,.17);
  box-shadow:0 0 46px rgba(0,0,0,.55) inset;
}
#b3d .fname{
  position:absolute; white-space:nowrap; font-size:11px; letter-spacing:2.4px;
  text-transform:uppercase; color:#7d8b9a; pointer-events:none;
}

/* ---- the building shell: facade, roof, entrance ---- */
#b3d .shell{position:absolute; inset:0; transform-style:preserve-3d; pointer-events:none}
/* The facade has to say "building" without hiding the rooms it wraps: three
   storeys of it stack into a continuous curtain from most orbit angles, so it
   is drawn as little more than its floor lines and window reveals. */
#b3d .facade{
  position:absolute; transform-style:preserve-3d;
  background:linear-gradient(rgba(150,175,205,.05), rgba(150,175,205,.01));
  border-top:1px solid rgba(173,199,229,.10);
  border-bottom:1px solid rgba(173,199,229,.42);
}
#b3d .facade.below{background:rgba(120,132,148,.05); border-bottom-color:rgba(173,199,229,.16)}
/* NB: "wpane", not "win" -- index.html already owns .win for the floating
   dashboard windows, and its min-width/min-height would inflate every pane. */
#b3d .wpane{
  position:absolute; background:rgba(150,205,255,.10);
  border:1px solid rgba(170,215,255,.34); border-radius:1px;
}
#b3d .roofplate{
  position:absolute; inset:0;
  /* barely there: it sits directly over the top floor's rooms, and at .55 it
     turned the whole storey to mud */
  background:rgba(34,46,60,.14); border:1px solid rgba(173,199,229,.40);
}
#b3d .sky{
  position:absolute; background:rgba(150,205,255,.26);
  border:1px solid rgba(180,220,255,.65);
  box-shadow:0 0 26px rgba(120,190,255,.45) inset;
}
#b3d .parapet{
  position:absolute;
  background:rgba(150,175,205,.12); border-top:1px solid rgba(173,199,229,.5);
}
#b3d .step .lid{background:rgba(174,189,210,.22); border-color:rgba(200,222,245,.60)}
#b3d .step .side{background:rgba(174,189,210,.42)}
/* the porch roof: a big horizontal slab, so it has to stay glassy or it reads
   as a solid lid dropped on the building */
#b3d .arch .lid{background:rgba(195,208,224,.10); border-color:rgba(214,230,250,.85)}
#b3d .arch .side{background:linear-gradient(rgba(195,208,224,.55), rgba(195,208,224,.34))}
#b3d .ped{
  position:absolute;
  background:linear-gradient(rgba(173,199,229,.20), rgba(173,199,229,.52));
  border:1px solid rgba(214,230,250,.90);
  /* on a stood-up plane the element's CSS bottom is world UP, so apex at 100% */
  clip-path:polygon(0 0, 100% 0, 50% 100%);
}

/* ---- a room: floor plate + four upright glass walls ---- */
#b3d .room{position:absolute; transform-style:preserve-3d; cursor:pointer;
  transition:transform .16s ease}
#b3d .plate{
  position:absolute; inset:0;
  background:rgba(var(--c),.12);
  border:1px solid rgba(var(--c),.55);
  box-shadow:inset 0 0 30px rgba(var(--c),.22);
}
#b3d .wall{
  position:absolute; transform-style:preserve-3d;
  background:linear-gradient(rgba(var(--c),.20), rgba(var(--c),.015));
  border-top:1px solid rgba(var(--c),.22);
  border-bottom:1px solid rgba(var(--c),.72);
}
#b3d .room:hover .plate{background:rgba(var(--c),.26); border-color:rgba(var(--c),.95)}
#b3d .room:hover .wall{background:linear-gradient(rgba(var(--c),.34), rgba(var(--c),.05))}

/* Alarm rooms blink so a red room is findable without hunting.
 *
 * It BLINKS rather than throbs, and that is a performance decision. Nothing
 * animates cheaply inside a preserve-3d subtree: Chrome cannot promote an
 * element to its own compositor layer without breaking the 3D depth sort, so
 * even an opacity animation repaints -- measured at 60 -> 25 fps for a single
 * alarming room, and 14 fps with twelve. A "steps(1, end)" timing turns that
 * into two repaints a second instead of sixty, which costs nothing and reads
 * as an alarm just as well. The header banner has always blinked for the same
 * reason; this matches it.
 */
#b3d .glow{
  /* invisible unless the room is alarming -- the keyframes own both levels */
  position:absolute; inset:0; pointer-events:none; opacity:0;
  background:rgba(var(--c),.55);
  box-shadow:inset 0 0 60px rgba(var(--c),.85);
}
#b3d .room.alarm .glow{animation:b3dglow 1.1s steps(1, end) infinite}
#b3d .room.alarm .wall{background:linear-gradient(rgba(var(--c),.46), rgba(var(--c),.08))}
@keyframes b3dglow{ 0%,100%{opacity:.18} 50%{opacity:1} }

/* ---- furniture ---- */
#b3d .vol{position:absolute; transform-style:preserve-3d; pointer-events:none}
#b3d .vol .side{
  position:absolute;
  background:linear-gradient(rgba(var(--f),.42), rgba(var(--f),.16));
  border-top:1px solid rgba(var(--f),.55);
}
#b3d .vol .lid{
  position:absolute; inset:0;
  background:rgba(var(--f),.34); border:1px solid rgba(var(--f),.70);
}
/* a plinth, drawn as its top face only */
#b3d .pplate{
  position:absolute; pointer-events:none;
  background:rgba(var(--f),.52); border:1px solid rgba(var(--f),.85);
}
/* display cases are glass: barely-there fill, bright edges */
#b3d .case .side{background:linear-gradient(rgba(var(--f),.13), rgba(var(--f),.05));
  border-top:1px solid rgba(var(--f),.60); border-bottom:1px solid rgba(var(--f),.60)}
#b3d .case .lid{background:rgba(var(--f),.10); border-color:rgba(var(--f),.75)}
#b3d .plinth .side{background:linear-gradient(rgba(var(--f),.50), rgba(var(--f),.26))}
#b3d .col .lid{border-radius:50%}
#b3d .col .side{background:linear-gradient(rgba(var(--f),.52), rgba(var(--f),.22))}

/* An exhibit: two crossed silhouettes, so it reads as an object from any orbit
   angle. The clip-path comes from POSES, set per element.
   NB: no filter here. drop-shadow would trace the clipped outline nicely, but
   it forces every silhouette onto its own composited layer -- measured at a
   third of the frame budget across ~50 exhibits. A near-opaque fill separates
   them from the glass behind just as well and costs nothing. */
#b3d .fig{
  position:absolute; pointer-events:none;
  background:linear-gradient(rgba(var(--f),.98), rgba(var(--f),.66));
}

/* ---- mounted on a wall ---- */
/* a framed picture: gilt frame, and a canvas inset inside it */
#b3d .art{
  position:absolute; background:rgba(var(--f),.75);
  border:1px solid rgba(var(--f),.95);
  box-shadow:0 0 10px rgba(var(--f),.40);
}
#b3d .art .canvas{
  position:absolute; inset:2px;
  background:linear-gradient(150deg, rgba(58,46,34,.95), rgba(28,22,18,.95));
}
/* a carved relief or a hung shield: stone, no canvas */
#b3d .relief{
  position:absolute; background:linear-gradient(rgba(var(--f),.34), rgba(var(--f),.16));
  border:1px solid rgba(var(--f),.60);
}
/* a textile hanging: soft, no hard frame */
#b3d .hanging{
  position:absolute;
  background:linear-gradient(rgba(var(--f),.16), rgba(var(--f),.48));
  border:1px solid rgba(var(--f),.45); border-bottom-width:2px;
}
#b3d .door{
  position:absolute; background:rgba(var(--f),.14);
  border:1px solid rgba(var(--f),.75); border-top:none;
  box-shadow:0 0 12px rgba(var(--f),.30) inset;
}

/* labels counter-rotate so they always face the viewer */
#b3d .rlabel{
  position:absolute; left:50%; top:50%; white-space:nowrap; pointer-events:none;
  font-size:11.5px; font-weight:600; color:#e6edf3; text-shadow:0 1px 5px #000c;
}
#b3d .rlabel .sub{display:block; font-weight:400; font-size:10px; color:#93a1b0}
#b3d .rlabel .live{
  display:inline-block; width:6px; height:6px; border-radius:50%; margin-right:4px;
  background:#58a6ff; box-shadow:0 0 7px #58a6ff; vertical-align:middle;
}

/* one dot per sensor, so you can see WHICH sensor is hot before opening a room */
#b3d .dot3{
  position:absolute; width:7px; height:7px; border-radius:50%; margin:-3.5px 0 0 -3.5px;
  pointer-events:none; box-shadow:0 0 6px currentColor; background:currentColor;
}
`;

function injectCss(){
  if (document.getElementById("b3d-css")) return;
  const s = document.createElement("style");
  s.id = "b3d-css"; s.textContent = CSS;
  document.head.appendChild(s);
}

// --- build ----------------------------------------------------------------
function buildScene(host){
  injectCss();
  state.host = host;
  state.el = el("", host);
  state.el.id = "b3d";
  state.scene = el("scene", state.el);

  const B = MG.building;
  const W = B.floorW * PX_PER_M, D = B.floorD * PX_PER_M;
  const top = B.floors.reduce((a, f) => f.level > a.level ? f : a, B.floors[0]);

  for (const f of B.floors){
    const floor = el("floor", state.scene);
    floor.dataset.floor = f.id;
    floor.style.width = W + "px"; floor.style.height = D + "px";
    floor.style.left = (-W/2) + "px"; floor.style.top = (-D/2) + "px";

    el("slab", floor);

    // Floor caption, parked off the EAST edge. Below the plate it lands on the
    // next floor down once the stack compresses, and off the west edge it
    // collides with the entrance portico.
    const fname = el("fname", floor);
    fname.textContent = f.name;
    fname.dataset.billboard = "1";
    fname.style.left = W + "px";
    fname.style.top = (D / 2) + "px";

    addShell(floor, f, f.id === top.id);
    for (const r of MG.rooms.filter(r => r.floor === f.id)) addRoom(floor, r);
  }

  bindCamera();
  state.dirty = true;
  applyCamera();
}

/* The outer envelope: a glazed facade per storey, a roof on the top one, and
 * the entrance portico. Deliberately rough — this is massing, not a model. */
function addShell(floorEl, floor, isTop){
  const B = MG.building, SH = B.shell;
  if (!SH) return;
  const W = B.floorW, D = B.floorD, H = B.wallH;
  const g = el("shell", floorEl);

  // four facade walls, with punched windows
  const faces = [
    {x: 0, y: 0, len: W, axis: "x"},
    {x: 0, y: D, len: W, axis: "x"},
    {x: 0, y: 0, len: D, axis: "y"},
    {x: W, y: 0, len: D, axis: "y"},
  ];
  const win = SH.window;
  const below = floor.level < 0;           // a basement has no windows to punch
  for (const face of faces){
    const p = plane(g, "facade" + (below ? " below" : ""),
                    Object.assign({h: H}, face));
    const n = below ? 0 : Math.max(1, Math.floor((face.len - 2) / win.gap));
    for (let i = 0; i < n; i++){
      const at = 1 + (face.len - 2) * (i + 0.5) / n;
      const w = el("wpane", p);
      w.style.left   = ((at - win.w / 2) * PX_PER_M) + "px";
      w.style.top    = (win.sill * VPM) + "px";
      w.style.width  = (win.w * PX_PER_M) + "px";
      w.style.height = (win.h * VPM) + "px";
    }
  }

  if (isTop) addRoof(g, W, D, H, SH.roof);
  if (SH.entrance && SH.entrance.floor === floor.id) addEntrance(g, SH.entrance, H);
}

function addRoof(g, W, D, H, roof){
  const plate = el("roofplate", g);
  plate.style.transform = `translateZ(${H * VPM}px)`;

  const sw = roof.skylight[0], sd = roof.skylight[1];
  const sky = el("sky", g);
  sky.style.left = ((W - sw) / 2 * PX_PER_M) + "px";
  sky.style.top  = ((D - sd) / 2 * PX_PER_M) + "px";
  sky.style.width  = (sw * PX_PER_M) + "px";
  sky.style.height = (sd * PX_PER_M) + "px";
  sky.style.transform = `translateZ(${(H + 0.5) * VPM}px)`;

  const p = roof.parapet;
  plane(g, "parapet", {x: 0, y: 0, z: H, len: W, h: p, axis: "x"});
  plane(g, "parapet", {x: 0, y: D, z: H, len: W, h: p, axis: "x"});
  plane(g, "parapet", {x: 0, y: 0, z: H, len: D, h: p, axis: "y"});
  plane(g, "parapet", {x: W, y: 0, z: H, len: D, h: p, axis: "y"});
}

/* Steps, a colonnade, an entablature and a pediment, projecting from the west
 * face in front of the Lobby. It is what makes the massing say "museum" rather
 * than "office block", so it is the one part of the shell drawn with any care.
 *
 * Everything is laid out in floor coordinates with negative x meaning "outside
 * the building", i.e. the portico hangs off the west edge of the plate. */
function addEntrance(g, e, H){
  const halfW = e.width / 2;

  // the porch floor itself, flush with the storey slab
  box(g, "step", {
    x: -e.depth / 2, y: e.at, z: -0.18,
    w: e.depth, d: e.width, h: 0.18, colour: "#aebdd2",
  });

  // A flight of steps below it. Each step is ONE tread -- spanning the whole
  // porch depth per step, as this first did, turns the flight into a ramp.
  for (let i = 0; i < e.steps; i++){
    const near = e.depth + i * e.run;
    box(g, "step", {
      x: -(near + e.run / 2), y: e.at, z: -(i + 1) * e.rise,
      w: e.run, d: e.width + i * e.run * 0.8, h: e.rise, colour: "#aebdd2",
    });
  }

  // colonnade along the outer edge of the porch
  const r = e.column_r;
  for (let i = 0; i < e.columns; i++){
    box(g, "col", {
      x: -e.depth + r * 1.8,
      y: e.at - halfW * 0.86 + e.width * 0.86 * (i + 0.5) / e.columns,
      w: r * 2, d: r * 2, h: H, colour: "#c3d0e0",
    });
  }

  // entablature spanning the colonnade, then the pediment on its outer face
  const ent = e.entablature || 1.0;
  box(g, "arch", {
    x: -e.depth / 2, y: e.at, z: H,
    w: e.depth, d: e.width + 0.8, h: ent, colour: "#c3d0e0",
  });
  plane(g, "ped", {
    x: -e.depth, y: e.at - halfW - 0.4, z: H + ent,
    len: e.width + 0.8, h: e.pediment, axis: "y",
  });
}

function addRoom(floorEl, room){
  const w = room.w, h = room.h, H = MG.building.wallH;

  const rEl = el("room", floorEl);
  rEl.dataset.room = room.id;
  rEl.style.left = (room.x * PX_PER_M) + "px";
  rEl.style.top  = (room.y * PX_PER_M) + "px";
  rEl.style.width = (w * PX_PER_M) + "px";
  rEl.style.height = (h * PX_PER_M) + "px";
  rEl.style.transform = `translateZ(${ROOM_Z}px)`;

  el("plate", rEl);
  el("glow", rEl);          // the alarm throb; see the note on @keyframes b3dglow

  // four glass walls standing on the plate edges, keyed so wall-mounted
  // fixtures can be dropped straight into the right one
  const walls = {
    n: plane(rEl, "wall", {x: 0, y: 0, len: w, h: H, axis: "x"}),
    s: plane(rEl, "wall", {x: 0, y: h, len: w, h: H, axis: "x"}),
    w: plane(rEl, "wall", {x: 0, y: 0, len: h, h: H, axis: "y"}),
    e: plane(rEl, "wall", {x: w, y: 0, len: h, h: H, axis: "y"}),
  };

  for (const fx of (room.fixtures || [])) addFixture(rEl, walls, fx);

  const label = el("rlabel", rEl);
  label.dataset.billboard = "1";
  label.innerHTML =
    `${room.live ? '<span class="live"></span>' : ""}${room.name}` +
    `<span class="sub">${room.keys.length} sensor${room.keys.length === 1 ? "" : "s"}` +
    `${room.live ? " · live" : ""}</span>`;

  // sensor dots, laid out in a row across the plate
  const dots = new Map();
  room.keys.forEach((key, i) => {
    const d = el("dot3", rEl);
    const cols = Math.min(room.keys.length, 6);
    const cx = (i % cols + 0.5) / cols;
    const cy = 0.86 + Math.floor(i / cols) * 0.09;
    d.style.left = (cx * w * PX_PER_M) + "px";
    d.style.top  = (cy * h * PX_PER_M) + "px";
    dots.set(key, d);
  });

  rEl.addEventListener("pointerenter", () => { state.hover = room.id; showTip(room); });
  rEl.addEventListener("pointermove", moveTip);
  rEl.addEventListener("pointerleave", () => {
    state.hover = null; document.getElementById("bTip").style.display = "none";
  });

  state.rooms.set(room.id, {el: rEl, label, dots, room, last: null});
}

/* The exhibits.
 *
 * A "figure" is two crossed silhouettes standing on a plinth: cheap (two divs)
 * and, unlike a billboard, it still reads as an object from any orbit angle
 * because one of the two planes is always near face-on. The silhouette is a
 * clip-path chosen by `pose`, so a statue looks like a statue and a vase looks
 * like a vase.
 *
 * Remember the plane convention: an upright plane's CSS *top* edge is its base
 * in world space, so every polygon below runs feet-at-0% to head-at-100%. */
const POSES = {
  statue:    "polygon(35% 0, 33% 30%, 38% 48%, 27% 64%, 44% 74%, 40% 80%," +
             " 43% 96%, 50% 100%, 57% 96%, 60% 80%, 56% 74%, 73% 64%, 62% 48%," +
             " 67% 30%, 65% 0)",
  torso:     "polygon(34% 0, 29% 34%, 24% 60%, 31% 82%, 40% 92%," +
             " 60% 92%, 69% 82%, 76% 60%, 71% 34%, 66% 0)",
  bust:      "polygon(18% 0, 22% 30%, 42% 46%, 36% 60%, 37% 80%, 44% 94%," +
             " 56% 94%, 63% 80%, 64% 60%, 58% 46%, 78% 30%, 82% 0)",
  vase:      "polygon(36% 0, 64% 0, 60% 10%, 74% 30%, 78% 52%, 66% 72%, 60% 84%," +
             " 70% 92%, 70% 100%, 30% 100%, 30% 92%, 40% 84%, 34% 72%, 22% 52%," +
             " 26% 30%, 40% 10%)",
  armour:    "polygon(32% 0, 36% 40%, 26% 50%, 22% 68%, 33% 74%, 40% 86%, 44% 90%," +
             " 42% 100%, 58% 100%, 56% 90%, 60% 86%, 67% 74%, 78% 68%, 74% 50%," +
             " 64% 40%, 68% 0)",
  mannequin: "polygon(20% 0, 26% 30%, 34% 52%, 30% 70%, 38% 86%," +
             " 62% 86%, 70% 70%, 66% 52%, 74% 30%, 80% 0)",
  crown:     "polygon(22% 0, 78% 0, 78% 34%, 68% 38%, 72% 100%, 60% 50%," +
             " 50% 96%, 40% 50%, 28% 100%, 32% 38%, 22% 34%)",
  gem:       "polygon(50% 0, 84% 58%, 74% 84%, 26% 84%, 16% 58%)",
};

/** Two crossed silhouettes of height `h` standing at (x, y, z). */
function figure(parent, {x, y, z = 0, w, h, pose, colour}){
  const shape = POSES[pose] || POSES.statue;
  for (const axis of ["x", "y"]){
    const p = plane(parent, "fig", {
      x: axis === "x" ? x - w / 2 : x,
      y: axis === "x" ? y : y - w / 2,
      z, len: w, h, axis,
    });
    p.style.setProperty("--f", rgb(colour));
    p.style.clipPath = shape;
  }
}

/** One piece of furniture, in the format building.furnish() emits. */
function addFixture(rEl, walls, fx){
  switch (fx.t){
    // ---- mounted on a wall ----
    case "painting":
    case "relief":
    case "hanging":
    case "window":
    case "door": {
      const host = walls[fx.wall];
      if (!host) return;
      const cls = fx.t === "door" ? "door"
                : fx.t === "relief" ? "relief"
                : fx.t === "hanging" ? "hanging" : "art";
      const d = el(cls, host);
      d.style.setProperty("--f", rgb(fx.c));
      d.style.left   = ((fx.at - fx.w / 2) * PX_PER_M) + "px";
      d.style.top    = ((fx.sill || 0) * VPM) + "px";
      d.style.width  = (fx.w * PX_PER_M) + "px";
      d.style.height = (fx.h * VPM) + "px";
      if (cls === "art") el("canvas", d);      // the picture inside the frame
      return;
    }

    // ---- a vitrine, optionally with something in it ----
    case "case": {
      box(rEl, "case", {x: fx.x, y: fx.y, w: fx.w, d: fx.d, h: fx.h, colour: fx.c});
      if (!fx.holds) return;
      const base = fx.h * 0.16;
      const inner = Math.min(fx.w, fx.d) * 0.42;
      slab(rEl, "pplate", {x: fx.x, y: fx.y, z: base,
                           w: inner * 1.5, d: inner * 1.5, colour: "#8d9aa8"});
      if (fx.holds === "blade"){                // a sword lies flat, not stands
        box(rEl, "blk", {x: fx.x, y: fx.y, z: base, w: fx.w * 0.7,
                         d: fx.d * 0.12, h: fx.h * 0.08, colour: "#c8d4e2"});
        return;
      }
      figure(rEl, {x: fx.x, y: fx.y, z: base, w: inner,
                   h: fx.h * 0.62, pose: fx.holds, colour: "#e5c76b"});
      return;
    }

    // ---- an exhibit standing on the floor ----
    case "figure": {
      const base = fx.h * 0.17;
      slab(rEl, "pplate", {x: fx.x, y: fx.y, z: base,
                           w: fx.w, d: fx.d, colour: "#8d9aa8"});
      figure(rEl, {x: fx.x, y: fx.y, z: base, w: fx.w * 0.86,
                   h: fx.h - base, pose: fx.pose, colour: fx.c});
      return;
    }

    case "column":
      box(rEl, "col", {x: fx.x, y: fx.y, w: fx.w, d: fx.d, h: fx.h, colour: fx.c});
      return;

    default:
      box(rEl, "blk", {x: fx.x, y: fx.y, w: fx.w, d: fx.d, h: fx.h, colour: fx.c});
  }
}

// --- tooltip --------------------------------------------------------------
function showTip(room){
  const tip = document.getElementById("bTip");
  const rows = MG.sensorsIn(room.id).map(s =>
    `<div class="r"><span>${s.label}</span>` +
    `<b style="color:${MG.color(s.state)}">${MG.fmt(s)}</b></div>`
  ).join("");
  tip.innerHTML = `<div class="t">${room.name}</div>${rows}` +
    (room.live ? `<div class="live">● live hardware — click to open</div>`
               : `<div class="live">click to open dashboard</div>`);
  tip.style.display = "block";
}

function moveTip(e){
  const tip = document.getElementById("bTip");
  const b = state.host.getBoundingClientRect();
  let x = e.clientX - b.left + 16, y = e.clientY - b.top + 16;
  x = Math.min(x, b.width  - tip.offsetWidth  - 8);
  y = Math.min(y, b.height - tip.offsetHeight - 8);
  tip.style.left = x + "px"; tip.style.top = y + "px";
}

// --- camera + picking -----------------------------------------------------
function bindCamera(){
  const host = state.host;
  let drag = null;

  host.addEventListener("pointerdown", e => {
    if (e.button !== 0) return;
    drag = {
      x: e.clientX, y: e.clientY, spin: state.spin, tilt: state.tilt,
      // Remember the room under the cursor NOW. Once we take pointer capture
      // the browser retargets the eventual `click` to the capture element, so
      // a listener on the room div itself never fires with a real mouse --
      // which was exactly the bug this replaces. Drag-vs-click is decided on
      // pointerup instead, by how far the pointer travelled.
      room: e.target.closest ? e.target.closest(".room") : null,
    };
    host.classList.add("dragging");
    // throws for a synthetic pointer event with no live pointer id
    try{ host.setPointerCapture(e.pointerId); }catch(_){}
  });

  host.addEventListener("pointermove", e => {
    if (!drag) return;
    state.spin = drag.spin + (e.clientX - drag.x) * 0.32;
    state.tilt = Math.max(6, Math.min(89, drag.tilt - (e.clientY - drag.y) * 0.28));
    state.dirty = true;
  });

  const end = e => {
    if (!drag) return;
    const d = drag;
    drag = null;
    host.classList.remove("dragging");
    try{ host.releasePointerCapture(e.pointerId); }catch(_){}
    if (e.type !== "pointerup" || !d.room) return;
    if (Math.hypot(e.clientX - d.x, e.clientY - d.y) > CLICK_SLOP) return;   // orbited
    MG.openRoom(d.room.dataset.room);
  };
  host.addEventListener("pointerup", end);
  host.addEventListener("pointercancel", end);

  host.addEventListener("wheel", e => {
    e.preventDefault();
    state.zoom = Math.max(0.35, Math.min(2.6, state.zoom * (e.deltaY > 0 ? 0.9 : 1.1)));
    state.dirty = true;
  }, {passive: false});
}

function applyCamera(){
  const gap = FLOOR_GAP;
  state.scene.style.transform =
    `scale(${state.zoom}) rotateX(${state.tilt}deg) rotateZ(${state.spin}deg)`;

  for (const f of state.el.querySelectorAll(".floor")){
    const level = (MG.building.floors.find(x => x.id === f.dataset.floor) || {}).level || 0;
    // negative Z pushes DOWN the screen after the rotateX, so basements sink
    f.style.transform = `translateZ(${level * gap}px)`;
    f.classList.toggle("dim", state.floor !== null && f.dataset.floor !== state.floor);
  }

  // counter-rotate every label so text faces the viewer rather than lying flat,
  // and float it clear of the roof line
  const counter = `rotateZ(${-state.spin}deg) rotateX(${-state.tilt}deg)`;
  const lift = (MG.building.wallH + 1.4) * VPM;
  for (const l of state.el.querySelectorAll("[data-billboard]")){
    const isRoom = l.classList.contains("rlabel");
    // the trailing translate runs AFTER the counter-rotation, so it moves the
    // text in SCREEN space -- offsetting it before just swings the caption back
    // over the building at most orbit angles
    l.style.transform = `translateZ(${isRoom ? lift : 0}px) ${counter} ` +
      (isRoom ? "translate(-50%,-50%)" : "translate(16px,-50%)");
  }
  state.dirty = false;
}

// --- per-frame ------------------------------------------------------------
function update(){
  if (state.dirty) applyCamera();

  for (const [id, r] of state.rooms){
    const st = MG.roomState(id);
    if (st !== r.last){
      r.last = st;
      r.el.style.setProperty("--c", rgb(MG.color(st)));
      r.el.classList.toggle("alarm", st === "ALARM");
    }
    // sensor dots track their own sensor, not the room's worst. Read STATES
    // directly: rebuilding a room's sensor array per dot per frame would be
    // ~600 array builds a frame for no reason.
    for (const [key, dot] of r.dots){
      const col = MG.color(MG.stateOf(key));
      if (dot._c !== col){ dot._c = col; dot.style.color = col; }
    }
    const lift = `translateZ(${state.hover === id ? HOVER_LIFT : ROOM_Z}px)`;
    if (r._lift !== lift){ r._lift = lift; r.el.style.transform = lift; }
  }
}

// --- lifecycle ------------------------------------------------------------
MG.register({
  name: "css3d",
  label: "CSS 3D",
  bytes: 0,                    // nothing is downloaded to draw this

  mount(host){
    if (!state.el) buildScene(host);
    else { host.appendChild(state.el); state.dirty = true; }
  },
  unmount(){
    if (state.el && state.el.parentNode) state.el.parentNode.removeChild(state.el);
    document.getElementById("bTip").style.display = "none";
  },
  update,
  setFloor(id){ state.floor = id; state.dirty = true; },
});

})();
