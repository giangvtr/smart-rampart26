/* MuseumGuard — 3D building view, Variant B: three.js (WebGL).
 *
 * Same geometry, same data, same interactions as building-css3d.js — the point
 * of having both is that the only variable is the renderer.
 *
 * What WebGL buys over the CSS variant:
 *   - real depth sorting, so near walls actually occlude far ones
 *   - real lighting: glass that catches highlights and darkens at grazing angles
 *   - alarm rooms lit from the inside by a moving point light, which reads as a
 *     room glowing rather than a rectangle changing colour
 *   - a free camera (orbit + dolly) instead of two Euler angles
 *
 * What it costs: ~1.3 MB of vendored three.js, an ES module + import map, and a
 * WebGL context. See BUILDING.md for the measured comparison.
 *
 * three.js is vendored under /static/vendor so the demo still works with no
 * internet. If those files are missing this module simply fails to import and
 * never registers — the shell leaves the "three.js" button disabled and the
 * CSS 3D variant carries the demo.
 */
import * as THREE from "three";
import { OrbitControls } from "/static/vendor/OrbitControls.js";
import { CSS2DRenderer, CSS2DObject } from "/static/vendor/CSS2DRenderer.js";

const WALL_H     = 4;            // metres; the plate is 40 x 26 m
const FLOOR_GAP  = [5.2, 30];    // vertical spacing between storeys, explode 0..1
const ALARM_LIGHTS = 3;          // pool size; lights are not free to add/remove

const S = {
  ready: false,
  host: null, renderer: null, labels: null, scene: null, camera: null, controls: null,
  floors: new Map(),      // floor id -> THREE.Group
  rooms: new Map(),       // room id  -> {group, glass, edges, dots, room, last}
  lights: [],
  ray: new THREE.Raycaster(), pointer: new THREE.Vector2(),
  pickables: [], hover: null,
  explode: 0.26, floor: null,
  gap: FLOOR_GAP[0], gapTarget: FLOOR_GAP[0],
  bytes: 0,
};

// --- scene ----------------------------------------------------------------
function buildScene(host){
  const B = MG.building;
  const W = B.floorW, D = B.floorD;

  S.host = host;
  S.scene = new THREE.Scene();
  S.scene.fog = new THREE.Fog(0x05070a, 90, 260);

  S.camera = new THREE.PerspectiveCamera(42, 1, 0.5, 600);
  S.camera.position.set(33, 27, 39);

  S.renderer = new THREE.WebGLRenderer({antialias: true, alpha: true});
  S.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  S.renderer.toneMapping = THREE.ACESFilmicToneMapping;
  S.renderer.toneMappingExposure = 1.15;
  S.renderer.domElement.style.cssText = "position:absolute; inset:0; display:block";
  host.appendChild(S.renderer.domElement);

  // labels ride in a DOM overlay: crisp text at any zoom, no texture atlas
  S.labels = new CSS2DRenderer();
  S.labels.domElement.style.cssText =
    "position:absolute; inset:0; pointer-events:none; overflow:hidden";
  host.appendChild(S.labels.domElement);

  S.controls = new OrbitControls(S.camera, S.renderer.domElement);
  S.controls.enableDamping = true;
  S.controls.dampingFactor = 0.08;
  S.controls.minDistance = 22;
  S.controls.maxDistance = 190;
  S.controls.maxPolarAngle = Math.PI * 0.495;   // never go under the floor
  S.controls.target.set(0, 3, 0);

  // -- lighting --
  S.scene.add(new THREE.HemisphereLight(0x9fc6ff, 0x0a0e14, 1.15));
  const key = new THREE.DirectionalLight(0xdcecff, 1.5);
  key.position.set(38, 60, 26);
  S.scene.add(key);
  const rim = new THREE.DirectionalLight(0x4f7fff, 0.7);
  rim.position.set(-40, 20, -32);
  S.scene.add(rim);

  // a pool of point lights, re-parented to whichever rooms are in alarm --
  // adding/removing lights recompiles every material, so the count is fixed
  for (let i = 0; i < ALARM_LIGHTS; i++){
    const l = new THREE.PointLight(0xff3b30, 0, 34, 2);
    S.scene.add(l);
    S.lights.push(l);
  }

  // -- floors --
  const topLevel = Math.max(...B.floors.map(f => f.level));
  for (const f of B.floors){
    const g = new THREE.Group();
    S.scene.add(g);
    S.floors.set(f.id, g);
    g.userData.level = f.level;

    const slab = new THREE.Mesh(
      new THREE.BoxGeometry(W, 0.25, D),
      new THREE.MeshStandardMaterial({
        color: 0x141c26, roughness: 0.85, metalness: 0.1,
        transparent: true, opacity: 0.72,
      })
    );
    slab.position.y = -0.13;
    g.add(slab);

    const grid = new THREE.GridHelper(Math.max(W, D), Math.round(Math.max(W, D) / 2),
                                      0x2d4055, 0x1d2a38);
    grid.material.transparent = true; grid.material.opacity = 0.5;
    grid.position.y = 0.02;
    g.add(grid);

    const cap = document.createElement("div");
    cap.style.cssText = "font:11px/1 system-ui,sans-serif; letter-spacing:2.4px;" +
      "text-transform:uppercase; color:#7d8b9a; white-space:nowrap";
    cap.textContent = f.name;
    const capObj = new CSS2DObject(cap);
    capObj.position.set(-W/2 - 13, 0.5, 0);   // clear of the plate at any orbit
    g.add(capObj);

    addShell(g, f, W, D, f.level === topLevel);
    for (const r of MG.rooms.filter(r => r.floor === f.id)) addRoom(g, r, W, D);
  }

  bindPointer();
  S.ready = true;
}

// --- materials ------------------------------------------------------------
// Shared and cached: 106 fixtures across 12 rooms would otherwise compile a
// hundred near-identical shaders on first mount.
const MAT = new Map();
const cached = (key, make) => {
  if (!MAT.has(key)) MAT.set(key, make());
  return MAT.get(key);
};

const solid = (hex, opacity = 0.9) => cached(`s${hex}${opacity}`, () =>
  new THREE.MeshStandardMaterial({
    color: hex, roughness: 0.72, metalness: 0.18,
    transparent: opacity < 1, opacity,
  }));

const vitrine = hex => cached(`v${hex}`, () =>
  new THREE.MeshPhysicalMaterial({
    color: hex, transparent: true, opacity: 0.14,
    roughness: 0.05, metalness: 0, clearcoat: 1,
    side: THREE.DoubleSide, depthWrite: false,
  }));

const flat = (hex, opacity, emissive = 0.5) => cached(`f${hex}${opacity}${emissive}`, () =>
  new THREE.MeshStandardMaterial({
    color: hex, emissive: hex, emissiveIntensity: emissive,
    roughness: 0.5, metalness: 0.1, side: THREE.DoubleSide,
    transparent: opacity < 1, opacity,
  }));

const lineMat = (hex, opacity = 0.55) => cached(`l${hex}${opacity}`, () =>
  new THREE.LineBasicMaterial({color: hex, transparent: true, opacity}));

/** Box + its bright edge outline, positioned by footprint centre. */
function volume(parent, x, y, z, w, h, d, mat, edge){
  const geo = new THREE.BoxGeometry(w, h, d);
  const m = new THREE.Mesh(geo, mat);
  m.position.set(x, y + h / 2, z);
  parent.add(m);
  if (edge){
    const e = new THREE.LineSegments(new THREE.EdgesGeometry(geo), lineMat(edge, 0.45));
    e.position.copy(m.position);
    parent.add(e);
  }
  return m;
}

// --- furniture ------------------------------------------------------------
/* Draws the fixture list building.furnish() emits. Room-local metres are
 * measured from the room's top-left corner; three is centre-origin with Y up,
 * so plan y becomes z and the height axis becomes y. */
function addFixtures(group, room){
  const hw = room.w / 2, hd = room.h / 2, H = WALL_H;

  for (const f of (room.fixtures || [])){
    if (f.t === "painting" || f.t === "window" || f.t === "door"){
      addWallPiece(group, room, f, hw, hd);
      continue;
    }
    const x = f.x - hw, z = f.y - hd;

    if (f.t === "case"){
      volume(group, x, 0, z, f.w, f.h, f.d, vitrine(f.c), f.c);

    } else if (f.t === "column"){
      const col = new THREE.Mesh(
        new THREE.CylinderGeometry(f.w / 2, f.w / 2, f.h, 14),
        solid(f.c, 0.75));
      col.position.set(x, f.h / 2, z);
      group.add(col);

    } else if (f.t === "statue"){
      // plinth, then a rough figure on top: nobody should be able to read the
      // pose, only "there is a statue there"
      const base = f.h * 0.26;
      volume(group, x, 0, z, f.w, base, f.d, solid(f.c, 0.85), f.c);
      const bodyH = (f.h - base) * 0.78;
      const body = new THREE.Mesh(
        new THREE.CylinderGeometry(f.w * 0.16, f.w * 0.34, bodyH, 10),
        solid(f.c, 0.92));
      body.position.set(x, base + bodyH / 2, z);
      group.add(body);
      const head = new THREE.Mesh(
        new THREE.SphereGeometry(f.w * 0.17, 10, 8), solid(f.c, 0.92));
      head.position.set(x, base + bodyH + f.w * 0.14, z);
      group.add(head);

    } else {
      volume(group, x, 0, z, f.w, f.h, f.d, solid(f.c, 0.88), f.c);
    }
  }
}

/** Paintings, windows and doors sit flat against the inside face of a wall. */
function addWallPiece(group, room, f, hw, hd){
  const eps = 0.06;
  let x, z, rotY;
  if (f.wall === "n" || f.wall === "s"){
    x = f.at - hw;
    z = (f.wall === "n" ? -hd + eps : hd - eps);
    rotY = 0;
  } else {
    z = f.at - hd;
    x = (f.wall === "w" ? -hw + eps : hw - eps);
    rotY = Math.PI / 2;
  }
  const y = (f.sill || 0) + f.h / 2;

  if (f.t === "door"){
    const d = new THREE.Mesh(new THREE.PlaneGeometry(f.w, f.h), flat(f.c, 0.30, 0.8));
    d.position.set(x, y, z); d.rotation.y = rotY;
    group.add(d);
    return;
  }

  // frame first, canvas inset in front of it -- two planes read as a hung
  // picture from across the room, which is all the resolution this needs
  const frame = new THREE.Mesh(new THREE.PlaneGeometry(f.w, f.h), flat(f.c, 0.85, 0.45));
  frame.position.set(x, y, z); frame.rotation.y = rotY;
  group.add(frame);

  const nx = f.wall === "n" ? 0 : f.wall === "s" ? 0 : (f.wall === "w" ? 1 : -1);
  const nz = f.wall === "n" ? 1 : f.wall === "s" ? -1 : 0;
  const canvas = new THREE.Mesh(
    new THREE.PlaneGeometry(f.w * 0.82, f.h * 0.82),
    f.t === "window" ? flat("#9fd8ff", 0.35, 0.7) : solid("#241a10", 0.95));
  canvas.position.set(x + nx * 0.03, y, z + nz * 0.03);
  canvas.rotation.y = rotY;
  group.add(canvas);
}

// --- the building shell ---------------------------------------------------
/* Facade, roof and entrance portico. Rough massing on purpose: enough for the
 * stack to read as one building rather than three floating floor plans. */
function addShell(g, floor, W, D, isTop){
  const SH = MG.building.shell;
  if (!SH) return;
  const H = WALL_H;

  // glazed envelope: one box, so it depth-sorts as a single surface
  const geo = new THREE.BoxGeometry(W, H, D);
  const skin = new THREE.Mesh(geo, cached("skin", () =>
    new THREE.MeshPhysicalMaterial({
      color: 0xa8bdd6, transparent: true, opacity: 0.06,
      roughness: 0.1, metalness: 0.1, clearcoat: 1,
      side: THREE.DoubleSide, depthWrite: false,
    })));
  skin.position.y = H / 2;
  g.add(skin);
  const outline = new THREE.LineSegments(new THREE.EdgesGeometry(geo),
                                         lineMat(0xadc7e5, 0.45));
  outline.position.y = H / 2;
  g.add(outline);

  addFacadeWindows(g, W, D, H, SH.window);
  if (isTop) addRoof(g, W, D, H, SH.roof);
  if (SH.entrance && SH.entrance.floor === floor.id) addPortico(g, W, D, H, SH.entrance);
}

function addFacadeWindows(g, W, D, H, win){
  const mat = flat("#9fd8ff", 0.30, 0.75);
  const geo = new THREE.PlaneGeometry(win.w, win.h);
  const runs = [
    {len: W, rotY: 0,             fix: -D / 2 - 0.05, axis: "x"},
    {len: W, rotY: Math.PI,       fix:  D / 2 + 0.05, axis: "x"},
    {len: D, rotY: Math.PI / 2,   fix: -W / 2 - 0.05, axis: "z"},
    {len: D, rotY: -Math.PI / 2,  fix:  W / 2 + 0.05, axis: "z"},
  ];
  for (const r of runs){
    const n = Math.max(1, Math.floor((r.len - 2) / win.gap));
    for (let i = 0; i < n; i++){
      const at = 1 + (r.len - 2) * (i + 0.5) / n - r.len / 2;
      const m = new THREE.Mesh(geo, mat);
      m.rotation.y = r.rotY;
      if (r.axis === "x") m.position.set(at, win.sill + win.h / 2, r.fix);
      else                m.position.set(r.fix, win.sill + win.h / 2, at);
      g.add(m);
    }
  }
}

function addRoof(g, W, D, H, roof){
  volume(g, 0, H, 0, W, 0.3, D, solid("#222e3c", 0.8), 0xadc7e5);

  const sky = new THREE.Mesh(
    new THREE.PlaneGeometry(roof.skylight[0], roof.skylight[1]),
    flat("#9fd8ff", 0.4, 0.9));
  sky.rotation.x = -Math.PI / 2;
  sky.position.y = H + 0.35;
  g.add(sky);

  // parapet: a hollow rim, drawn as its outline only
  const p = new THREE.BoxGeometry(W, roof.parapet, D);
  const rim = new THREE.LineSegments(new THREE.EdgesGeometry(p), lineMat(0xadc7e5, 0.5));
  rim.position.y = H + roof.parapet / 2;
  g.add(rim);
}

function addPortico(g, W, D, H, e){
  const x0 = -W / 2;                       // the west face
  const cz = e.at - D / 2;

  for (let i = 0; i < e.steps; i++){
    const out = e.depth + (i + 1) * e.run;
    const pad = (i + 1) * e.run * 0.6;
    volume(g, x0 - out / 2, -(i + 1) * e.rise, cz,
           out, e.rise, e.width + pad * 2, solid("#8f9bab", 0.8), 0xadc7e5);
  }

  for (let i = 0; i < e.columns; i++){
    const col = new THREE.Mesh(
      new THREE.CylinderGeometry(e.column_r, e.column_r, H, 16),
      solid("#aab4bf", 0.85));
    col.position.set(x0 - e.depth * 0.68,
                     H / 2,
                     cz - e.width / 2 + e.width * (i + 0.5) / e.columns);
    g.add(col);
  }

  volume(g, x0 - e.depth / 2, H, cz, e.depth, 0.9, e.width + 0.8,
         solid("#aab4bf", 0.85), 0xadc7e5);

  // pediment: an extruded triangle standing on the entablature, facing out
  const half = (e.width + 0.8) / 2;
  const tri = new THREE.Shape();
  tri.moveTo(-half, 0); tri.lineTo(half, 0); tri.lineTo(0, e.pediment); tri.closePath();
  const ped = new THREE.Mesh(
    new THREE.ExtrudeGeometry(tri, {depth: 0.7, bevelEnabled: false}),
    solid("#b9c6d6", 0.85));
  ped.rotation.y = Math.PI / 2;            // local x -> world z, so it faces -x
  ped.position.set(x0 - e.depth, H + 0.9, cz);
  g.add(ped);
}

function addRoom(floorGroup, room, W, D){
  // building coords are top-left origin; three is centre origin, Y up
  const cx = room.x + room.w / 2 - W / 2;
  const cz = room.y + room.h / 2 - D / 2;

  const group = new THREE.Group();
  group.position.set(cx, 0, cz);
  floorGroup.add(group);

  const geo = new THREE.BoxGeometry(room.w, WALL_H, room.h);

  // Glass. depthWrite off so rooms behind stay visible through the ones in
  // front -- that is the whole "see-through building" idea; depth TESTing stays
  // on, so the floor slabs still occlude correctly.
  const glass = new THREE.Mesh(geo, new THREE.MeshPhysicalMaterial({
    color: 0x2e7d32,
    emissive: 0x000000,
    transparent: true, opacity: 0.16,
    roughness: 0.12, metalness: 0.0,
    clearcoat: 1.0, clearcoatRoughness: 0.15,
    side: THREE.DoubleSide, depthWrite: false,
  }));
  glass.position.y = WALL_H / 2;
  glass.userData.roomId = room.id;
  group.add(glass);

  const edges = new THREE.LineSegments(
    new THREE.EdgesGeometry(geo),
    new THREE.LineBasicMaterial({color: 0x2e7d32, transparent: true, opacity: 0.9})
  );
  edges.position.y = WALL_H / 2;
  group.add(edges);

  addFixtures(group, room);

  // one dot per sensor, floating just above the floor
  const dots = new Map();
  room.keys.forEach((k, i) => {
    const cols = Math.min(room.keys.length, 6);
    const dx = ((i % cols + 0.5) / cols - 0.5) * room.w * 0.8;
    // hugged against the south edge so the furniture never swallows them
    const dz = room.h * (0.42 - Math.floor(i / cols) * 0.09);
    const dot = new THREE.Mesh(
      new THREE.SphereGeometry(0.42, 12, 10),
      new THREE.MeshBasicMaterial({color: 0x2e7d32})
    );
    dot.position.set(dx, 0.5, dz);
    group.add(dot);
    dots.set(k, dot);
  });

  const div = document.createElement("div");
  div.style.cssText =
    "font:600 11.5px/1.35 system-ui,sans-serif; color:#e6edf3; white-space:nowrap;" +
    "text-shadow:0 1px 5px #000c; text-align:center";
  div.innerHTML =
    `${room.live ? '<span style="display:inline-block;width:6px;height:6px;border-radius:50%;' +
      'background:#58a6ff;box-shadow:0 0 7px #58a6ff;margin-right:4px"></span>' : ""}${room.name}` +
    `<span style="display:block;font-weight:400;font-size:10px;color:#93a1b0">` +
    `${room.keys.length} sensor${room.keys.length === 1 ? "" : "s"}${room.live ? " · live" : ""}</span>`;
  const label = new CSS2DObject(div);
  label.position.set(0, WALL_H + 1.2, 0);
  group.add(label);

  S.pickables.push(glass);
  S.rooms.set(room.id, {group, glass, edges, dots, room, last: null, label: div});
}

// --- interaction ----------------------------------------------------------
function bindPointer(){
  const dom = S.renderer.domElement;

  dom.addEventListener("pointermove", e => {
    const b = dom.getBoundingClientRect();
    S.pointer.x = ((e.clientX - b.left) / b.width) * 2 - 1;
    S.pointer.y = -((e.clientY - b.top) / b.height) * 2 + 1;
    const hit = pick();
    const id = hit ? hit.object.userData.roomId : null;
    if (id !== S.hover){
      S.hover = id;
      dom.style.cursor = id ? "pointer" : "";
    }
    const tip = document.getElementById("bTip");
    if (!id){ tip.style.display = "none"; return; }
    showTip(MG.rooms.find(r => r.id === id), e, b, tip);
  });

  dom.addEventListener("pointerleave", () => {
    S.hover = null;
    document.getElementById("bTip").style.display = "none";
  });

  // OrbitControls owns the drag; only treat a click that did not orbit as a pick
  let down = null;
  dom.addEventListener("pointerdown", e => { down = {x: e.clientX, y: e.clientY}; });
  dom.addEventListener("pointerup", e => {
    if (!down) return;
    const moved = Math.hypot(e.clientX - down.x, e.clientY - down.y);
    down = null;
    if (moved > 5) return;
    const hit = pick();
    if (hit) MG.openRoom(hit.object.userData.roomId);
  });
}

function pick(){
  S.ray.setFromCamera(S.pointer, S.camera);
  const visible = S.pickables.filter(m => m.parent && m.parent.parent && m.parent.parent.visible);
  const hits = S.ray.intersectObjects(visible, false);
  return hits.length ? hits[0] : null;
}

function showTip(room, e, bounds, tip){
  if (!room) return;
  if (tip._room !== room.id || !tip._at || performance.now() - tip._at > 250){
    tip._room = room.id; tip._at = performance.now();
    const rows = MG.sensorsIn(room.id).map(s =>
      `<div class="r"><span>${s.label}</span>` +
      `<b style="color:${MG.color(s.state)}">${s.value == null ? "--" : s.value} ${s.unit}</b></div>`
    ).join("");
    tip.innerHTML = `<div class="t">${room.name}</div>${rows}` +
      (room.live ? `<div class="live">● live hardware — click to open</div>`
                 : `<div class="live">click to open dashboard</div>`);
  }
  tip.style.display = "block";
  const hb = S.host.getBoundingClientRect();
  let x = e.clientX - hb.left + 16, y = e.clientY - hb.top + 16;
  x = Math.min(x, hb.width  - tip.offsetWidth  - 8);
  y = Math.min(y, hb.height - tip.offsetHeight - 8);
  tip.style.left = x + "px"; tip.style.top = y + "px";
}

// --- per-frame ------------------------------------------------------------
const _c = new THREE.Color();
let _alarmPhase = 0;

function update(){
  if (!S.ready) return;
  resize();

  // ease the floor stack toward the explode target
  S.gapTarget = FLOOR_GAP[0] + (FLOOR_GAP[1] - FLOOR_GAP[0]) * S.explode;
  S.gap += (S.gapTarget - S.gap) * 0.16;
  for (const [id, g] of S.floors){
    g.position.y = g.userData.level * S.gap;
    const show = (S.floor === null || S.floor === id);
    g.visible = show;
    // CSS2DRenderer tests only an object's OWN `visible` flag, never its
    // ancestors' -- so hiding the floor group hides its meshes but leaves the
    // room labels floating in an empty scene. Push the flag down explicitly.
    if (g.userData.shown !== show){
      g.userData.shown = show;
      g.traverse(o => { if (o.isCSS2DObject) o.visible = show; });
    }
  }

  _alarmPhase += 0.09;
  const pulse = 0.5 + 0.5 * Math.sin(_alarmPhase);
  let lightIdx = 0;

  for (const [id, r] of S.rooms){
    const st = MG.roomState(id);
    const col = MG.color(st);

    if (st !== r.last){
      r.last = st;
      _c.set(col);
      r.glass.material.color.copy(_c);
      r.glass.material.emissive.copy(_c);
      r.edges.material.color.copy(_c);
    }

    if (st === "ALARM"){
      r.glass.material.emissiveIntensity = 0.25 + 0.75 * pulse;
      r.glass.material.opacity = 0.20 + 0.22 * pulse;
      // light it from the inside -- this is the effect the CSS variant can't do
      if (lightIdx < S.lights.length && r.group.parent.visible){
        const l = S.lights[lightIdx++];
        r.group.getWorldPosition(l.position);
        l.position.y += WALL_H * 0.55;
        l.intensity = 40 + 70 * pulse;
        l.color.set(col);
      }
    } else {
      r.glass.material.emissiveIntensity = st === "WARN" ? 0.16 : 0.06;
      r.glass.material.opacity = S.hover === id ? 0.30 : 0.16;
    }

    for (const [k, dot] of r.dots){
      const dc = MG.color(MG.stateOf(k));
      if (dot._c !== dc){ dot._c = dc; dot.material.color.set(dc); }
    }
  }
  for (let i = lightIdx; i < S.lights.length; i++) S.lights[i].intensity = 0;

  S.controls.update();
  S.renderer.render(S.scene, S.camera);
  S.labels.render(S.scene, S.camera);
}

function resize(){
  const w = S.host.clientWidth, h = S.host.clientHeight;
  if (!w || !h || (S.renderer._w === w && S.renderer._h === h)) return;
  S.renderer._w = w; S.renderer._h = h;
  S.renderer.setSize(w, h);
  S.labels.setSize(w, h);
  S.camera.aspect = w / h;
  S.camera.updateProjectionMatrix();
}

// --- lifecycle ------------------------------------------------------------
// Report what this variant actually cost to load, so the bar's readout is a
// measurement rather than a number someone typed in.
try{
  for (const e of performance.getEntriesByType("resource")){
    if (/\/static\/(vendor|js\/building-three)/.test(e.name)){
      S.bytes += e.encodedBodySize || e.transferSize || 0;
    }
  }
}catch(_){}

MG.register({
  name: "three",
  label: "three.js",
  available: true,
  get bytes(){ return S.bytes; },

  mount(host){
    if (!S.ready) buildScene(host);
    else { host.appendChild(S.renderer.domElement); host.appendChild(S.labels.domElement); }
    S.renderer._w = S.renderer._h = 0;      // force a resize on the next frame
  },
  unmount(){
    for (const el of [S.renderer && S.renderer.domElement, S.labels && S.labels.domElement]){
      if (el && el.parentNode) el.parentNode.removeChild(el);
    }
    document.getElementById("bTip").style.display = "none";
  },
  update,
  setExplode(t){ S.explode = t; },
  setFloor(id){ S.floor = id; },
});
