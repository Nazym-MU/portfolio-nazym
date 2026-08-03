// ============================================================================
// Sketch landing page
// ----------------------------------------------------------------------------
// A page torn from a sketchbook: off-white paper, handwritten ink, and a Rubik's
// cube rendered as flat 2D pencil-and-ink linework (no lights, MeshBasicMaterial
// fills + inverted-hull black outlines with a hand-drawn "boiling" wobble). The
// cube starts in a fixed scramble. Clicking it plays a ~8s solve, and on the last
// turn the sketch dissolves into full 3D as the camera pushes into the room scene
// (owned by main.js) — one continuous motion, no page navigation.
//
// The cube mechanics (26 cubie meshes reparented onto a temporary pivot Group per
// turn, then snapped) were verified headless: 50 random moves keep positions and
// quaternions clean to machine epsilon, and scramble+solve returns every cubie
// home exactly.
// ============================================================================

import * as THREE from 'three';
import gsap from 'gsap';

// ---- Config ----------------------------------------------------------------

// The SOLVE sequence Nazym provided. The cube starts in the state this solves,
// i.e. the initial scramble is the inverse of this. Clicking replays this to solve.
const SOLVE_SEQUENCE =
    "U2 F2 U' F' U R2 L' F' R2 U2 B2 R2 L2 D L2 U' F2 D B2 U F2".split(/\s+/);

// 21 moves over ~8s → ~380ms per quarter turn, which stays legible (a shorter
// 10–14 move scramble would hit the task's 5s target, but Nazym chose to keep
// all 21 and extend the budget).
const TOTAL_SOLVE_SECONDS = 8.0;

// Dimmed standard cube colors (not too bright), one per face.
const STICKER = {
    U: 0xe8e2d0, // white  -> warm off-white
    D: 0xdcc23f, // yellow -> muted gold
    F: 0x3f7a3f, // green  -> forest
    B: 0x2f6ea8, // blue   -> dusty blue
    R: 0xc24039, // red    -> brick
    L: 0xd4863a, // orange -> burnt orange
};
const PLASTIC = 0x1a1a1a; // cube body / inner facelets

const SPACING = 1.06;      // gap between cubie centers so seams read as ink lines
const OUTLINE_SCALE = 1.035;

const prefersReducedMotion =
    window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const isMobile = window.matchMedia && window.matchMedia('(max-width: 768px)').matches;

// ---- Notation --------------------------------------------------------------

const FACE_AXIS = {
    U: { axis: 'y', sign: 1 },
    D: { axis: 'y', sign: -1 },
    R: { axis: 'x', sign: 1 },
    L: { axis: 'x', sign: -1 },
    F: { axis: 'z', sign: 1 },
    B: { axis: 'z', sign: -1 },
};
const AXIS_VEC = {
    x: new THREE.Vector3(1, 0, 0),
    y: new THREE.Vector3(0, 1, 0),
    z: new THREE.Vector3(0, 0, 1),
};

// A clockwise quarter-turn of a face, viewed from outside the cube, is a
// rotation of -90° about the face's outward normal (right-hand rule). The
// outward normal is sign * axis, so the rotation about the +axis is
// -sign * 90°. Verified against the solver's facelet pattern: this convention
// reproduces the entered scramble state exactly (53/54 net match, remaining
// cell was a screenshot misread — a legal state can't differ by one sticker).
function rotationSign(face) {
    return -FACE_AXIS[face].sign;
}

// Parse a token like "U", "U'", "U2" → { face, turns } where turns is +1/-1/±2.
function parseMove(token) {
    const face = token[0];
    if (token.endsWith('2')) return { face, turns: 2 };
    if (token.endsWith("'")) return { face, turns: -1 };
    return { face, turns: 1 };
}

// Invert a move token (for building the scramble from the solve).
function invertMove(token) {
    const face = token[0];
    if (token.endsWith('2')) return face + '2';
    if (token.endsWith("'")) return face;
    return face + "'";
}

// Scramble = inverse of the solve: reverse order, invert each move.
const SCRAMBLE_SEQUENCE = SOLVE_SEQUENCE.slice().reverse().map(invertMove);

// ============================================================================
// Cube construction
// ============================================================================

const cubeRoot = new THREE.Group();
const cubies = [];            // the 26 movable cubie groups
const wobbleMaterials = [];   // outline materials whose shader we advance ~8fps

// Build one cubie at grid coords (gx,gy,gz) each in {-1,0,1}. Each cubie is a
// small Group holding: the plastic body, six sticker quads (only on outward
// faces), and an inverted-hull outline mesh for the ink silhouette.
function makeCubie(gx, gy, gz) {
    const cubie = new THREE.Group();
    cubie.position.set(gx * SPACING, gy * SPACING, gz * SPACING);

    // Plastic body — flat dark fill, slightly inset so stickers sit proud.
    const body = new THREE.Mesh(
        new THREE.BoxGeometry(1, 1, 1),
        new THREE.MeshBasicMaterial({ color: PLASTIC })
    );
    cubie.add(body);

    // Sticker quads on outward-facing sides.
    const stickerGeo = new THREE.PlaneGeometry(0.82, 0.82);
    const faces = [
        { cond: gx === 1, color: STICKER.R, pos: [0.5, 0, 0], rot: [0, Math.PI / 2, 0] },
        { cond: gx === -1, color: STICKER.L, pos: [-0.5, 0, 0], rot: [0, -Math.PI / 2, 0] },
        { cond: gy === 1, color: STICKER.U, pos: [0, 0.5, 0], rot: [-Math.PI / 2, 0, 0] },
        { cond: gy === -1, color: STICKER.D, pos: [0, -0.5, 0], rot: [Math.PI / 2, 0, 0] },
        { cond: gz === 1, color: STICKER.F, pos: [0, 0, 0.5], rot: [0, 0, 0] },
        { cond: gz === -1, color: STICKER.B, pos: [0, 0, -0.5], rot: [0, Math.PI, 0] },
    ];
    for (const f of faces) {
        if (!f.cond) continue;
        const mat = new THREE.MeshBasicMaterial({
            color: f.color,
            side: THREE.DoubleSide,
        });
        // Stash both the sketch (flat) color and a slightly richer "rendered"
        // color; the transition lerps between them per-material.
        mat.userData.sketchColor = new THREE.Color(f.color);
        mat.userData.renderedColor = new THREE.Color(f.color).multiplyScalar(1.15);
        const q = new THREE.Mesh(stickerGeo, mat);
        q.position.set(...f.pos);
        q.rotation.set(...f.rot);
        // Nudge outward a hair to avoid z-fighting with the body.
        q.position.multiplyScalar(1.001);
        cubie.add(q);
    }

    // Inverted-hull outline: a scaled-up backface-only black shell that renders
    // as an ink silhouette behind the fill. Its vertices boil via a vertex shader.
    const outlineMat = makeWobbleMaterial();
    wobbleMaterials.push(outlineMat);
    const outline = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), outlineMat);
    outline.scale.setScalar(OUTLINE_SCALE);
    cubie.add(outline);

    cubie.userData.grid = new THREE.Vector3(gx, gy, gz);
    cubie.userData.home = cubie.position.clone();
    return cubie;
}

// Hand-drawn "boiling line" outline material. A vertex shader displaces each
// vertex by a small pseudo-noise offset keyed off a seed uniform we bump ~8fps
// (not every frame), so the silhouette jitters like hand-drawn animation instead
// of sitting as a clean vector edge. A `uRendered` uniform (0→1) fades the ink to
// nothing for the sketch→3D transition.
function makeWobbleMaterial() {
    return new THREE.ShaderMaterial({
        side: THREE.BackSide,
        transparent: true,
        uniforms: {
            uSeed: { value: 0 },
            uAmount: { value: 0.028 },
            uRendered: { value: 0 }, // 0 = full ink, 1 = gone
            uInk: { value: new THREE.Color(0x1c1c1c) },
        },
        vertexShader: /* glsl */`
            uniform float uSeed;
            uniform float uAmount;
            // cheap hash noise
            float hash(vec3 p) {
                p = fract(p * 0.3183099 + 0.1);
                p *= 17.0;
                return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
            }
            void main() {
                vec3 pos = position;
                // seed shifts the sample point so the noise "boils" between frames
                float n1 = hash(floor(position * 3.0) + uSeed);
                float n2 = hash(floor(position * 3.0) + uSeed + 7.31);
                float n3 = hash(floor(position * 3.0) + uSeed + 13.7);
                vec3 offset = (vec3(n1, n2, n3) - 0.5) * 2.0 * uAmount;
                pos += offset;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
            }
        `,
        fragmentShader: /* glsl */`
            uniform vec3 uInk;
            uniform float uRendered;
            void main() {
                // ink fades out as the scene becomes "rendered"
                float a = 1.0 - uRendered;
                if (a <= 0.001) discard;
                gl_FragColor = vec4(uInk, a);
            }
        `,
    });
}

function buildCube() {
    for (let x = -1; x <= 1; x++)
        for (let y = -1; y <= 1; y++)
            for (let z = -1; z <= 1; z++) {
                if (x === 0 && y === 0 && z === 0) continue; // skip invisible center
                const cubie = makeCubie(x, y, z);
                cubeRoot.add(cubie);
                cubies.push(cubie);
            }
}

// ============================================================================
// Face turns via pivot reparenting
// ============================================================================

// Cubies currently in the layer for `face`, chosen by their *rounded* grid slot
// along the face axis so float drift never mis-selects a layer.
function layerFor(face) {
    const { axis, sign } = FACE_AXIS[face];
    return cubies.filter(
        (c) => Math.round(c.position[axis] / SPACING) === sign
    );
}

// Snap a cubie back onto the integer grid and to an axis-aligned orientation, so
// accumulated float error can never deform the cube over many turns.
function snapCubie(c) {
    c.position.set(
        Math.round(c.position.x / SPACING) * SPACING,
        Math.round(c.position.y / SPACING) * SPACING,
        Math.round(c.position.z / SPACING) * SPACING
    );
    snapQuaternion(c.quaternion);
    c.updateMatrix();
}

const QUAT_SNAPS = [0, 0.5, -0.5, Math.SQRT1_2, -Math.SQRT1_2, 1, -1];
function snapQuaternion(q) {
    const nearest = (v) => {
        let best = QUAT_SNAPS[0], bd = Infinity;
        for (const c of QUAT_SNAPS) {
            const d = Math.abs(c - v);
            if (d < bd) { bd = d; best = c; }
        }
        return best;
    };
    q.set(nearest(q.x), nearest(q.y), nearest(q.z), nearest(q.w));
    q.normalize();
}

// Instantly apply a quarter turn (no animation). Used to set the initial scramble.
function applyTurnInstant(face, turns) {
    const { axis } = FACE_AXIS[face];
    const pivot = new THREE.Group();
    cubeRoot.add(pivot);
    const layer = layerFor(face);
    layer.forEach((c) => pivot.attach(c)); // attach() preserves world transform
    pivot.rotateOnAxis(AXIS_VEC[axis], (Math.PI / 2) * turns * rotationSign(face));
    pivot.updateMatrixWorld(true);
    layer.forEach((c) => cubeRoot.attach(c));
    cubeRoot.remove(pivot);
    layer.forEach(snapCubie);
}

// Animate a single quarter turn (turns = ±1) with a slight overshoot so it feels
// tactile. `double` runs two quarter turns back to back. Returns a Promise.
let turnInFlight = false;
function animateTurn(face, turns, seconds) {
    return new Promise((resolve) => {
        const { axis } = FACE_AXIS[face];
        const pivot = new THREE.Group();
        cubeRoot.add(pivot);
        const layer = layerFor(face);
        layer.forEach((c) => pivot.attach(c));

        const target = (Math.PI / 2) * turns * rotationSign(face);
        const state = { t: 0 };
        gsap.to(state, {
            t: 1,
            duration: seconds,
            ease: 'back.out(1.4)', // slight overshoot
            onUpdate: () => {
                pivot.setRotationFromAxisAngle(AXIS_VEC[axis], target * state.t);
            },
            onComplete: () => {
                pivot.setRotationFromAxisAngle(AXIS_VEC[axis], target);
                pivot.updateMatrixWorld(true);
                layer.forEach((c) => cubeRoot.attach(c));
                cubeRoot.remove(pivot);
                layer.forEach(snapCubie);
                resolve();
            },
        });
    });
}

// Set the cube to the fixed scramble instantly (its starting state).
function applyScramble() {
    for (const tok of SCRAMBLE_SEQUENCE) {
        const { face, turns } = parseMove(tok);
        if (turns === 2) { applyTurnInstant(face, 1); applyTurnInstant(face, 1); }
        else applyTurnInstant(face, turns);
    }
}

// Play the solve. Each token gets an equal slice of the total budget; doubles use
// their slice for two half-speed quarters so the whole thing lands on time.
async function playSolve() {
    if (turnInFlight) return;
    turnInFlight = true;
    const per = TOTAL_SOLVE_SECONDS / SOLVE_SEQUENCE.length;
    for (let i = 0; i < SOLVE_SEQUENCE.length; i++) {
        const { face, turns } = parseMove(SOLVE_SEQUENCE[i]);
        if (turns === 2) {
            await animateTurn(face, 1, per / 2);
            await animateTurn(face, 1, per / 2);
        } else {
            await animateTurn(face, turns, per);
        }
        // Kick off the transition as the final turn completes, not after.
        if (i === SOLVE_SEQUENCE.length - 1) startTransition();
    }
    turnInFlight = false;
}

// ============================================================================
// Renderer / scene / camera
// ============================================================================

const canvas = document.getElementById('sketch-canvas');
const landingEl = document.getElementById('sketch-landing');

// On mobile we don't run WebGL at all — the SVG fallback covers it.
let renderer, scene, camera, rafId;

// The cube renders into a bounded canvas placed BELOW the copy (see CSS), not the
// full window, so it can never sit behind the text. We size the renderer + camera
// to the canvas element's own box.
function canvasSize() {
    const r = canvas.getBoundingClientRect();
    return { w: Math.max(1, r.width), h: Math.max(1, r.height) };
}

function initGL() {
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    const { w, h } = canvasSize();
    renderer.setSize(w, h, false); // false: don't override the CSS box size
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0); // transparent; paper shows through

    scene = new THREE.Scene(); // NO lights, by design

    camera = new THREE.PerspectiveCamera(35, w / h, 0.1, 100);
    // Pulled back so the cube reads small within its box.
    camera.position.set(4.6, 3.7, 6.8);
    camera.lookAt(0, 0, 0);

    // Tilt the whole cube to a pleasant 3/4 sketch angle.
    cubeRoot.rotation.set(0, -Math.PI / 12, 0);
    scene.add(cubeRoot);
}

// Advance the boiling-line seed at ~8fps regardless of render framerate.
let lastWobble = 0;
const WOBBLE_INTERVAL = 1000 / 8;
let wobbleSeed = 0;

function tick(now) {
    rafId = requestAnimationFrame(tick);
    if (now - lastWobble >= WOBBLE_INTERVAL) {
        lastWobble = now;
        wobbleSeed += 1.0;
        for (const m of wobbleMaterials) m.uniforms.uSeed.value = wobbleSeed;
    }
    renderer.render(scene, camera);
}

function onResize() {
    if (!renderer) return;
    const { w, h } = canvasSize();
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h, false);
}

// ============================================================================
// Transition: sketch → rendered → into the room
// ============================================================================

let transitioning = false;
function startTransition({ instant = false } = {}) {
    if (transitioning) return;
    transitioning = true;

    const copy = document.getElementById('sketch-copy');
    const cue = document.getElementById('sketch-cue');

    const DUR = instant ? 0 : 1.8; // 1.5–2s continuous move

    // The old transition let the sketch cube (and its black inverted-hull ink
    // outline) grow large and semi-transparent OVER the room, which read as an
    // ugly jagged border. Instead: kill the ink outline immediately, drop the
    // sticker fills into the paper, and dissolve the whole sketch layer early so
    // the room owns the frame for most of the move. The camera push still gives
    // the "diving in" feel while the sketch is disappearing.

    // 1) Kill the boiling-line ink outline fast — it must not linger as a border.
    const ink = { v: 0 };
    gsap.to(ink, {
        v: 1,
        duration: DUR * 0.28,
        ease: 'power2.in',
        onUpdate: () => {
            for (const m of wobbleMaterials) m.uniforms.uRendered.value = ink.v;
        },
    });

    // 2) Warm the sticker fills toward "rendered" as they fade.
    const shade = { v: 0 };
    gsap.to(shade, {
        v: 1,
        duration: DUR * 0.6,
        ease: 'power2.out',
        onUpdate: () => {
            cubeRoot.traverse((o) => {
                const mat = o.material;
                if (mat && mat.userData && mat.userData.sketchColor) {
                    mat.color.copy(mat.userData.sketchColor).lerp(
                        mat.userData.renderedColor, shade.v
                    );
                }
            });
        },
    });

    // 3) Push the camera toward the cube — the "diving in" motion.
    if (camera) {
        gsap.to(camera.position, {
            x: 0, y: 0.2, z: 1.4,
            duration: DUR,
            ease: 'power2.in',
            onUpdate: () => camera.lookAt(0, 0, 0),
        });
    }

    // 4) Fade the HTML text and cue out early.
    if (copy) gsap.to(copy, { opacity: 0, duration: DUR * 0.45, ease: 'power2.in' });
    if (cue) gsap.to(cue, { opacity: 0, duration: DUR * 0.3 });

    // Fade the cube canvas itself ahead of the layer dissolve, so the cube growing
    // into the camera never clips hard against its bounded box edge on screen.
    if (canvas) gsap.to(canvas, { opacity: 0, duration: DUR * 0.5, ease: 'power2.in' });

    // 5) Reveal the room beneath.
    if (window.__revealRoom) window.__revealRoom({ duration: DUR * 0.7 });

    // 6) Dissolve the ENTIRE sketch layer (paper + cube canvas together) over the
    //    front half of the move, so the room — not a translucent cube — fills the
    //    frame for the rest of it. One clean crossfade, no bordered overlay.
    gsap.to(landingEl, {
        opacity: 0,
        duration: DUR * 0.5,
        delay: DUR * 0.15,
        ease: 'power2.inOut',
        onComplete: () => {
            landingEl.style.display = 'none';
            if (rafId) cancelAnimationFrame(rafId);
            try { localStorage.setItem('nz_seen_sketch', '1'); } catch (e) { /* ignore */ }
        },
    });
}

// ============================================================================
// Interaction wiring
// ============================================================================

function wireClickToSolve() {
    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    let solved = false;

    function triggerSolve() {
        if (solved || transitioning) return;
        solved = true;
        playSolve(); // never autoplays — only fires from a user click
    }

    function tryHit(clientX, clientY) {
        if (solved || transitioning) return;
        const rect = canvas.getBoundingClientRect();
        // Ignore clicks outside the cube's box.
        if (clientX < rect.left || clientX > rect.right ||
            clientY < rect.top || clientY > rect.bottom) return;
        pointer.x = ((clientX - rect.left) / rect.width) * 2 - 1;
        pointer.y = -((clientY - rect.top) / rect.height) * 2 + 1;
        raycaster.setFromCamera(pointer, camera);
        const hits = raycaster.intersectObjects(cubeRoot.children, true);
        if (hits.length > 0) triggerSolve();
    }

    canvas.addEventListener('click', (e) => tryHit(e.clientX, e.clientY));
    canvas.addEventListener('touchend', (e) => {
        if (e.changedTouches && e.changedTouches.length) {
            const t = e.changedTouches[0];
            tryHit(t.clientX, t.clientY);
        }
    }, { passive: true });
}

// ============================================================================
// Boot
// ============================================================================

function bootMobileFallback() {
    // No WebGL. The SVG sketch + copy are already in the DOM; wire the enter button.
    const enter = document.getElementById('sketch-mobile-enter');
    if (enter) {
        enter.addEventListener('click', () => {
            // Reveal the room and dismiss the landing (no cube solve on mobile).
            if (window.__revealRoom) window.__revealRoom({ duration: 1.0 });
            gsap.to(landingEl, {
                opacity: 0, duration: 0.6,
                onComplete: () => { landingEl.style.display = 'none'; },
            });
            try { localStorage.setItem('nz_seen_sketch', '1'); } catch (e) { /* ignore */ }
        });
    }
}

function boot() {
    buildCube();
    applyScramble();  // set the fixed starting scramble
    initGL();
    rafId = requestAnimationFrame(tick);
    wireClickToSolve();
    window.addEventListener('resize', onResize);

    // Reduced motion: skip the solve animation. Show the cube already solved
    // (leave it scrambled? no — the point is "solve it and step inside", so we
    // present the solved state) and run the transition instantly into the room.
    if (prefersReducedMotion) {
        // Apply the solve instantly so the cube reads as solved, then hand off.
        for (const tok of SOLVE_SEQUENCE) {
            const { face, turns } = parseMove(tok);
            if (turns === 2) { applyTurnInstant(face, 1); applyTurnInstant(face, 1); }
            else applyTurnInstant(face, turns);
        }
        // Give the room a beat to load, then transition with no motion.
        const go = () => startTransition({ instant: true });
        if (window.__roomAssetsReady) window.__roomAssetsReady.then(go);
        else go();
    }
}

if (isMobile) {
    bootMobileFallback();
} else {
    boot();
}
