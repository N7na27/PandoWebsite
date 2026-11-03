/* LapRotator 3D model on the landing page.
   Default: turns around the scope's axis. Hover (or keyboard focus, or a tap on touch screens): eases to a stop at that angle.
   Posed like the product render: scope running off to the lower left, camera body up front on the right.
   The model (assets/model/laprotator.glb) is exported from LapRotator.blend by tools/model.py.
   Until it loads, or if WebGL is missing, the poster image shows. */
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const box = document.querySelector(".lr-model");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const SPEED = (Math.PI * 2) / 14; // one turn every 14 seconds
const EASE = 7; // how fast it eases to a stop or back up to speed (higher is quicker)
// Which way the scope points: left, a little down, and toward the viewer
const SCOPE_DIR = new THREE.Vector3(-0.89, -0.2, 0.42);
// First angle (and the poster): buttons on top, tipped toward the viewer, "Pando" facing out
const BUTTONS_TOWARD = new THREE.Vector3(0, 1, 0.5);
// Frame the device body; the scope beyond this point (meters, Onshape z) may run out of frame
const BODY_END_Z = 0.07;

// Look of each website material from tools/model.py (base colors come from the model file).
// Materials made in Blender aren't listed here and keep their own values.
const LOOK = {
  housing: { roughness: 0.42, clearcoat: 0.7, clearcoatRoughness: 0.14, envMapIntensity: 0.85 },
  chrome: { metalness: 1, roughness: 0.16 },
  dark: { roughness: 0.5, clearcoat: 0.3, clearcoatRoughness: 0.3 },
  print: { roughness: 0.55 },
};

if (box) {
  // Load only when the section comes close, so the 1.5 MB model never slows the first paint
  const near = new IntersectionObserver((entries) => {
    if (entries.some((e) => e.isIntersecting)) { near.disconnect(); start().catch(() => {}); }
  }, { rootMargin: "400px 0px" });
  near.observe(box);
}

// Photo studios for reflections. Plastic gets a soft grey sweep with softboxes. Chrome gets a dark
// room with bright strips, which gives steel its crisp light and dark bands.
function studio(contrast) {
  const scene = new THREE.Scene();
  const dome = new THREE.SphereGeometry(10, 48, 24);
  const colors = [];
  const pos = dome.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    const y = pos.getY(i) / 10; // -1 floor .. 1 ceiling
    const g = contrast ? (y > 0 ? 0.1 + 0.15 * y : 0.1 + 0.07 * y) : (y > 0 ? 0.5 + 0.25 * y : 0.5 + 0.22 * y);
    colors.push(g, g, g * 1.02);
  }
  dome.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
  scene.add(new THREE.Mesh(dome, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide })));
  const softbox = (w, h, power, x, y, z) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color: new THREE.Color(power, power, power), side: THREE.DoubleSide }));
    m.position.set(x, y, z);
    m.lookAt(0, 0, 0);
    scene.add(m);
  };
  if (contrast) {
    softbox(14, 2.2, 6, 0, 7, 0); // long overhead strip
    softbox(14, 1.2, 3, 0, -1.5, 8); // low front strip
    softbox(2, 9, 4, -8, 1, 2); // left strip
    softbox(8, 5, 1.8, 2, 3, 8); // broad front card, keeps flat faces mid grey
    softbox(14, 1, 2, 0, 3, -8); // back strip
  } else {
    softbox(9, 4, 4, 0, 7, 1); // overhead
    softbox(2, 7, 3, -7, 1.5, 3); // left strip
    softbox(2, 7, 1.6, 7, 0.5, 1); // right strip
    softbox(6, 3, 1.4, 1, 1, 8); // front fill
    softbox(5, 2, 1.2, 0, 2, -8); // back, for rims
  }
  return scene;
}

async function start() {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;

  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(studio(false), 0.02).texture;
  const chromeEnv = pmrem.fromScene(studio(true), 0.01).texture;
  const key = new THREE.DirectionalLight(0xffffff, 1.6);
  key.position.set(-2, 4, 3);
  scene.add(key);

  const camera = new THREE.PerspectiveCamera(24, 1, 0.01, 50);

  const gltf = await new GLTFLoader().loadAsync("assets/model/laprotator.glb");
  const model = gltf.scene;
  const swapped = {};
  model.traverse((o) => {
    if (!o.isMesh) return;
    const old = o.material;
    if (!(old.name in LOOK)) return; // a material made in Blender: keep it as exported
    if (!swapped[old.name]) {
      swapped[old.name] = new THREE.MeshPhysicalMaterial({ name: old.name, color: old.color, metalness: 0, ...LOOK[old.name] });
      if (old.name === "chrome") swapped[old.name].envMap = chromeEnv;
    }
    o.material = swapped[old.name];
  });

  // Center along the scope, keep the scope's axis (x = 0, y = 0) as the spin axis
  const bounds = new THREE.Box3().setFromObject(model);
  const length = bounds.max.z - bounds.min.z;
  model.position.z = -(bounds.min.z + bounds.max.z) / 2;
  const spin = new THREE.Group(); // turns around its own z axis = the scope
  spin.add(model);
  spin.scale.setScalar(1 / length);
  const tilt = new THREE.Group(); // points the scope across the frame
  tilt.add(spin);
  tilt.lookAt(SCOPE_DIR);
  scene.add(tilt);

  // Points on the device body (not the far scope), used to frame it so nothing clips at any angle
  const samples = [];
  model.updateMatrixWorld(true);
  model.traverse((o) => {
    if (!o.isMesh) return;
    const p = o.geometry.attributes.position;
    for (let i = 0; i < p.count; i += 30) {
      const v = new THREE.Vector3().fromBufferAttribute(p, i).applyMatrix4(o.matrixWorld);
      if (v.z - model.position.z < BODY_END_Z) samples.push(v);
    }
  });
  const sweep = [];
  for (let a = 0; a < 24; a++) {
    spin.rotation.z = (a / 24) * Math.PI * 2;
    tilt.updateMatrixWorld(true);
    for (const s of samples) sweep.push(s.clone().applyMatrix4(spin.matrixWorld));
  }

  // Starting angle: turn until the buttons (the camera's -y side) face BUTTONS_TOWARD
  let startAngle = 0, best = -Infinity;
  const want = BUTTONS_TOWARD.clone().normalize(), dir = new THREE.Vector3();
  for (let a = 0; a < 360; a++) {
    spin.rotation.z = THREE.MathUtils.degToRad(a);
    tilt.updateMatrixWorld(true);
    dir.set(0, -1, 0).transformDirection(spin.matrixWorld);
    if (dir.dot(want) > best) { best = dir.dot(want); startAngle = spin.rotation.z; }
  }

  function fit() {
    // The box is the frame; the canvas also reaches left past it (CSS --lr-bleed) so the scope can trail off
    const w = box.clientWidth, h = box.clientHeight;
    if (!w || !h) return;
    const bleed = Math.max(0, Math.round(box.getBoundingClientRect().left - renderer.domElement.getBoundingClientRect().left));
    renderer.setSize(w + bleed, h, false);
    camera.aspect = w / h;
    // Find the camera distance and offset that fill the box with the turning body.
    // Perspective makes near parts look bigger, so measure, adjust and measure again.
    const tan = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
    const margin = bleed ? 1.08 : 1.3; // on phones (no bleed) leave room for more of the scope
    let cx = 0, cy = 0, d = 4;
    for (let i = 0; i < 8; i++) {
      let uLo = Infinity, uHi = -Infinity, vLo = Infinity, vHi = -Infinity;
      for (const p of sweep) {
        const k = 1 / (d - p.z);
        const u = (p.x - cx) * k, v = (p.y - cy) * k;
        if (u < uLo) uLo = u; if (u > uHi) uHi = u;
        if (v < vLo) vLo = v; if (v > vHi) vHi = v;
      }
      cx += ((uLo + uHi) / 2) * d;
      cy += ((vLo + vHi) / 2) * d;
      d *= Math.max((uHi - uLo) / 2 / (tan * camera.aspect), (vHi - vLo) / 2 / tan) * margin;
    }
    camera.position.set(cx, cy, d);
    camera.lookAt(cx, cy, 0);
    camera.setViewOffset(w, h, -bleed, 0, w + bleed, h);
    draw();
  }

  function draw() { renderer.render(scene, camera); }

  // Motion: speed eases toward the target, so a hover glides to a stop at the angle it is on
  let angle = startAngle;
  let speed = reduceMotion ? 0 : SPEED;
  let held = false; // hover, keyboard focus or a tap
  let onScreen = true;
  let last = 0, frame = 0;
  spin.rotation.z = angle;

  function tick(t) {
    frame = 0;
    const dt = last ? Math.min((t - last) / 1000, 0.1) : 0;
    last = t;
    const target = held || reduceMotion ? 0 : SPEED;
    speed += (target - speed) * (1 - Math.exp(-EASE * dt));
    if (Math.abs(speed) < 0.0005 && target === 0) speed = 0;
    angle += speed * dt;
    spin.rotation.z = angle;
    draw();
    if (speed !== 0 || target !== 0) loop();
  }
  function loop() {
    if (!frame && onScreen && !document.hidden) frame = requestAnimationFrame(tick);
  }
  function hold(on) {
    held = on;
    last = 0;
    loop();
  }

  box.addEventListener("pointerenter", (e) => { if (e.pointerType === "mouse") hold(true); });
  box.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse") hold(false); });
  box.addEventListener("pointerup", (e) => { if (e.pointerType !== "mouse") hold(!held); });
  box.addEventListener("focus", () => { if (box.matches(":focus-visible")) hold(true); });
  box.addEventListener("blur", () => { if (held && !box.matches(":hover")) hold(false); });

  new IntersectionObserver((entries) => {
    onScreen = entries[entries.length - 1].isIntersecting;
    last = 0;
    loop();
  }).observe(box);
  document.addEventListener("visibilitychange", () => { last = 0; loop(); });
  new ResizeObserver(fit).observe(box);

  box.appendChild(renderer.domElement);
  fit();
  box.classList.add("is-live");
  loop();
}
