/* LapRotator 3D model on the landing page.
   Default: turns around the scope's axis. Hover (or keyboard focus, or a tap on touch screens): eases to a stop at that angle.
   Drag (or the arrow keys when focused) turns it around the scope by hand; it glides on after a flick.
   Posed like the product render: scope running off to the lower left, camera body up front on the right.
   Looks like the Blender (Cycles) renders: the model file (assets/model/laprotator.glb, exported from
   "LapRotator render (revB).blend" by tools/model.py) brings its materials, Cycles ambient occlusion
   baked per vertex, and the scene's studio: the five area lights, placed as the render camera sees them,
   the near-black world, and AgX "Medium High Contrast". The lights stay fixed to this camera while the
   model turns, like a turntable. Until it loads, or if WebGL is missing, the poster image shows. */
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const box = document.querySelector(".lr-model");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const SPEED = (Math.PI * 2) / 14; // one turn every 14 seconds
const EASE = 7; // how fast it eases to a stop or back up to speed (higher is quicker)
const KEY_STEP = Math.PI / 12; // arrow keys turn it 15 degrees
// Which way the scope points: left, a little down, and toward the viewer
const SCOPE_DIR = new THREE.Vector3(-0.89, -0.2, 0.42);
// First angle (and the poster): buttons on top, tipped toward the viewer, "Pando" facing out
const BUTTONS_TOWARD = new THREE.Vector3(0, 1, 0.5);
// Frame the device body; the scope beyond this point (meters, Onshape z) may run out of frame
const BODY_END_Z = 0.07;
// Radius (meters) of the surface that follows the pointer while dragging, about the housing's
const GRIP_RADIUS = 0.025;
// Blender area-light radiance (power per area) to three.js units, matched against the Cycles hero render
const LIGHT_SCALE = 0.26;
// Blender AgX looks: contrast in AgX log space around 0.4 (OCIO GradingPrimary, log style, pivot -0.2)
const AGX_LOOKS = { "AgX - Base Contrast": 1, "AgX - Medium High Contrast": 1.2 };

if (box) {
  // Load only when the section comes close, so the 1.7 MB model never slows the first paint
  const near = new IntersectionObserver((entries) => {
    if (entries.some((e) => e.isIntersecting)) { near.disconnect(); start().catch(() => {}); }
  }, { rootMargin: "400px 0px" });
  near.observe(box);
}

async function start() {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  const camera = new THREE.PerspectiveCamera(24, 1, 0.1, 50);

  const gltf = await new GLTFLoader().loadAsync("assets/model/laprotator.glb");
  const model = gltf.scene;
  const studio = model.userData.studio;

  // Color management as in Blender: AgX, with the look's contrast, and the scene exposure
  agxLook(AGX_LOOKS[studio.look] ?? 1);
  renderer.toneMapping = THREE.AgXToneMapping;
  renderer.toneMappingExposure = 2 ** (studio.exposure || 0);

  // Light: the world plus the area lights as glowing panels, all reaching the model as image-based
  // light, so it gets the same soft highlights and reflections. This camera never turns, so the
  // render camera's view of the lights maps straight onto it.
  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(studioScene(studio), 0, 0.1, 100).texture;
  pmrem.dispose();
  model.traverse((o) => { if (o.isMesh && o.geometry.attributes._ao) bakedOcclusion(o.material); });

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
  const axis = new THREE.Vector3(0, 0, 1).applyQuaternion(tilt.quaternion); // the scope, in world space

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

  // How the near side of the device moves on screen as it turns (pixels per radian), for dragging
  const grip = new THREE.Vector2(1, 0);

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
    camera.updateMatrixWorld();

    // Take a point on the side of the scope facing the viewer, turn it a little, and see where it goes
    const toCam = camera.position.clone().normalize();
    const side = toCam.sub(axis.clone().multiplyScalar(axis.dot(toCam))).normalize().multiplyScalar(GRIP_RADIUS / length);
    const step = 0.01;
    const a = side.clone().project(camera);
    const b = side.clone().applyAxisAngle(axis, step).project(camera);
    grip.set(((b.x - a.x) / 2) * (w + bleed), (-(b.y - a.y) / 2) * h).divideScalar(step);
    draw();
  }

  function draw() { renderer.render(scene, camera); }

  // Motion: speed eases toward the target, so a hover glides to a stop at the angle it is on
  let angle = startAngle;
  let speed = reduceMotion ? 0 : SPEED;
  let held = false; // hover, keyboard focus or a tap
  let onScreen = true;
  let last = 0, frame = 0;
  let drag = null; // { id, x, y, t, moved, touch }
  spin.rotation.z = angle;

  function tick(t) {
    frame = 0;
    const dt = last ? Math.min((t - last) / 1000, 0.1) : 0;
    last = t;
    const target = held || reduceMotion ? 0 : SPEED;
    if (!drag) {
      speed += (target - speed) * (1 - Math.exp(-EASE * dt));
      if (Math.abs(speed) < 0.0005 && target === 0) speed = 0;
      angle += speed * dt;
    }
    spin.rotation.z = angle;
    draw();
    if (!drag && (speed !== 0 || target !== 0)) loop();
  }
  function loop() {
    if (!frame && onScreen && !document.hidden) frame = requestAnimationFrame(tick);
  }
  function hold(on) {
    held = on;
    last = 0;
    loop();
  }
  function turnBy(da) {
    angle += da;
    spin.rotation.z = angle;
    draw();
  }

  // Drag: the side facing you follows the pointer, like rolling a pen under your finger.
  // On touch screens only sideways swipes turn it, so up and down still scrolls the page.
  box.addEventListener("pointerdown", (e) => {
    if (e.button !== 0 || drag) return;
    drag = { id: e.pointerId, x: e.clientX, y: e.clientY, t: performance.now(), moved: false, touch: e.pointerType !== "mouse" };
    speed = 0;
    try { box.setPointerCapture(e.pointerId); } catch (err) { /* keep dragging without capture */ }
  });
  box.addEventListener("pointermove", (e) => {
    if (!drag || e.pointerId !== drag.id) return;
    const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
    if (!drag.moved && Math.hypot(dx, dy) < 4) return;
    if (!drag.moved) box.classList.add("is-dragging");
    drag.moved = true;
    const g2 = grip.lengthSq() || 1;
    const da = drag.touch ? (dx * Math.sign(grip.x || 1)) / Math.sqrt(g2) : (dx * grip.x + dy * grip.y) / g2;
    const now = performance.now();
    const dt = Math.max((now - drag.t) / 1000, 0.001);
    speed = 0.7 * speed + 0.3 * (da / dt); // smoothed, so a flick can carry on after release
    drag.x = e.clientX; drag.y = e.clientY; drag.t = now;
    turnBy(da);
  });
  function endDrag(e) {
    if (!drag || e.pointerId !== drag.id) return;
    const wasTap = !drag.moved;
    if (performance.now() - drag.t > 80) speed = 0; // held still before letting go: no flick
    speed = THREE.MathUtils.clamp(speed, -8, 8);
    if (reduceMotion) speed = 0;
    drag = null;
    box.classList.remove("is-dragging");
    if (wasTap && e.type === "pointerup" && e.pointerType !== "mouse") held = !held; // tap toggles on touch
    last = 0;
    loop();
  }
  box.addEventListener("pointerup", endDrag);
  box.addEventListener("pointercancel", endDrag);

  box.addEventListener("pointerenter", (e) => { if (e.pointerType === "mouse") hold(true); });
  box.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse" && !drag) hold(false); });
  box.addEventListener("lostpointercapture", (e) => { if (e.pointerType === "mouse" && !box.matches(":hover")) hold(false); });
  box.addEventListener("focus", () => { if (box.matches(":focus-visible")) hold(true); });
  box.addEventListener("blur", () => { if (held && !box.matches(":hover")) hold(false); });
  box.addEventListener("keydown", (e) => {
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    e.preventDefault();
    held = true;
    speed = 0;
    turnBy(e.key === "ArrowLeft" ? -KEY_STEP : KEY_STEP);
  });

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

// The Blender studio as a scene for the environment map: the world color all around, each area
// light a panel of its size and radiance, placed where the render camera sees it
function studioScene(studio) {
  const env = new THREE.Scene();
  env.background = new THREE.Color().setRGB(...studio.world);
  for (const L of studio.lights) {
    const color = new THREE.Color().setRGB(...L.color).multiplyScalar(L.radiance * LIGHT_SCALE);
    const panel = new THREE.Mesh(new THREE.PlaneGeometry(L.size[0], L.size[1]), new THREE.MeshBasicMaterial({ color, side: THREE.DoubleSide }));
    const a = L.axes;
    panel.matrixAutoUpdate = false;
    panel.matrix.set(a[0][0], a[0][1], a[0][2], L.position[0], a[1][0], a[1][1], a[1][2], L.position[1], a[2][0], a[2][1], a[2][2], L.position[2], 0, 0, 0, 1);
    env.add(panel);
  }
  return env;
}

// Blender's AgX looks grade in AgX log space, just before the AgX curve; three.js has the same spot
function agxLook(contrast) {
  if (contrast === 1) return;
  const chunk = THREE.ShaderChunk.tonemapping_pars_fragment;
  const at = "color = agxDefaultContrastApprox( color );";
  if (chunk.includes("/* agx look */") || !chunk.includes(at)) return;
  THREE.ShaderChunk.tonemapping_pars_fragment = chunk.replace(at, `/* agx look */ color = ( color - 0.4 ) * ${contrast.toFixed(3)} + 0.4;\n\t${at}`);
}

// Cycles ambient occlusion baked into each vertex (attribute _AO) darkens the studio light and its
// reflections in creases and between parts, as three.js does with an AO map
function bakedOcclusion(material) {
  material.onBeforeCompile = (shader) => {
    shader.vertexShader = "attribute vec4 _ao;\nvarying float vBakedAO;\n" +
      shader.vertexShader.replace("#include <begin_vertex>", "#include <begin_vertex>\n\tvBakedAO = _ao.x;");
    shader.fragmentShader = "varying float vBakedAO;\n" + shader.fragmentShader.replace("#include <aomap_fragment>", `
	float ambientOcclusion = vBakedAO;
	reflectedLight.indirectDiffuse *= ambientOcclusion;
	#if defined( USE_CLEARCOAT )
		clearcoatSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_ENVMAP ) && defined( STANDARD )
		float dotNV = saturate( dot( geometryNormal, geometryViewDir ) );
		reflectedLight.indirectSpecular *= computeSpecularOcclusion( dotNV, ambientOcclusion, material.roughness );
	#endif`);
  };
  material.customProgramCacheKey = () => "baked-ao";
}
