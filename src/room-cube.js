// ============================================================================
// Live Rubik's cube on the table
// ----------------------------------------------------------------------------
// Ported from the old sketch landing page's cube: same 26-cubie construction,
// sticker colors, and pivot-reparenting face turns with grid/quaternion
// snapping (verified numerically clean over 50+ moves). The sketch-specific
// parts (inverted-hull ink outline, wobble shader, sketch→rendered transition)
// are dropped — in the room it reads as a clean unlit cube, matching the
// baked-texture look of everything else.
//
// The cube starts in the same fixed scramble the landing page used (the
// inverse of SOLVE_SEQUENCE, applied instantly). Clicking it makes it jump off
// the table, solve — or, if already solved, re-scramble — itself midair while
// slowly spinning, then drop back onto its spot with a bounce.
// ============================================================================

import * as THREE from 'three';
import gsap from 'gsap';

// The SOLVE sequence from the landing page. The cube starts in the state this
// solves, i.e. the initial scramble is the inverse of this.
const SOLVE_SEQUENCE =
    "U2 F2 U' F' U R2 L' F' R2 U2 B2 R2 L2 D L2 U' F2 D B2 U F2".split(/\s+/);

// 21 moves over ~7s → ~330ms per quarter turn. The re-scramble uses the same
// pacing in the other direction.
const TOTAL_SOLVE_SECONDS = 7.0;

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

const SPACING = 1.06;               // gap between cubie centers so seams read as dark lines
const CUBE_SPAN = 2 * SPACING + 1;  // overall edge length in local units

const JUMP_HEIGHT = 1.7;  // world units the cube rises off the table

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
// outward normal is sign * axis, so the rotation about the +axis is -sign * 90°.
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
// Factory
// ============================================================================

export function createRoomCube() {
    // Two-level rig so the animations never fight each other:
    // - `group` owns the world placement (position/quaternion/base scale) and
    //   the jump/hover height. Named "rubik" so main.js's name-based raycast
    //   dispatch picks it up.
    // - `cubeRoot` (child) owns the local flourishes: squash/stretch scale,
    //   hover scale, and the slow airborne spin.
    const group = new THREE.Group();
    group.name = 'rubik';
    const cubeRoot = new THREE.Group();
    group.add(cubeRoot);

    const cubies = []; // the 26 movable cubie groups

    // ---- Construction ------------------------------------------------------

    const stickerGeo = new THREE.PlaneGeometry(0.82, 0.82);

    // Build one cubie at grid coords (gx,gy,gz) each in {-1,0,1}: a dark
    // plastic body plus sticker quads on the outward-facing sides only.
    function makeCubie(gx, gy, gz) {
        const cubie = new THREE.Group();
        cubie.position.set(gx * SPACING, gy * SPACING, gz * SPACING);

        const body = new THREE.Mesh(
            new THREE.BoxGeometry(1, 1, 1),
            new THREE.MeshBasicMaterial({ color: PLASTIC })
        );
        cubie.add(body);

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
            const q = new THREE.Mesh(
                stickerGeo,
                new THREE.MeshBasicMaterial({ color: f.color, side: THREE.DoubleSide })
            );
            q.position.set(...f.pos);
            q.rotation.set(...f.rot);
            // Nudge outward a hair to avoid z-fighting with the body.
            q.position.multiplyScalar(1.001);
            cubie.add(q);
        }
        cubie.userData.home = cubie.position.clone(); // solved-state transform
        return cubie;
    }

    for (let x = -1; x <= 1; x++)
        for (let y = -1; y <= 1; y++)
            for (let z = -1; z <= 1; z++) {
                if (x === 0 && y === 0 && z === 0) continue; // skip invisible center
                const cubie = makeCubie(x, y, z);
                cubeRoot.add(cubie);
                cubies.push(cubie);
            }

    // ---- Face turns via pivot reparenting ----------------------------------

    // Cubies currently in the layer for `face`, chosen by their *rounded* grid
    // slot along the face axis so float drift never mis-selects a layer.
    function layerFor(face) {
        const { axis, sign } = FACE_AXIS[face];
        return cubies.filter(
            (c) => Math.round(c.position[axis] / SPACING) === sign
        );
    }

    // Snap a cubie back onto the integer grid and to an axis-aligned
    // orientation, so accumulated float error can never deform the cube.
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

    // Instantly apply a quarter turn (no animation). Used for the initial scramble.
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

    // Animate a single quarter turn (turns = ±1) with a slight overshoot so it
    // feels tactile. Returns a Promise.
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

    // Play a sequence; each token gets an equal slice of the total budget, and
    // doubles use their slice for two half-speed quarters so it lands on time.
    async function playSequence(tokens) {
        const per = TOTAL_SOLVE_SECONDS / tokens.length;
        for (const tok of tokens) {
            const { face, turns } = parseMove(tok);
            if (turns === 2) {
                await animateTurn(face, 1, per / 2);
                await animateTurn(face, 1, per / 2);
            } else {
                await animateTurn(face, turns, per);
            }
        }
    }

    // Set the cube to the fixed landing-page scramble (its starting state).
    for (const tok of SCRAMBLE_SEQUENCE) {
        const { face, turns } = parseMove(tok);
        if (turns === 2) { applyTurnInstant(face, 1); applyTurnInstant(face, 1); }
        else applyTurnInstant(face, turns);
    }

    // ---- Placement / interaction -------------------------------------------

    let solved = false; // starts scrambled, exactly like the old landing page
    let busy = false;   // re-entrancy guard: clicks during the routine do nothing
    let restY = 0;
    let jumpHeight = JUMP_HEIGHT;

    // Cap the jump so the closer mobile framing never sends the cube out of
    // frame; Infinity (or anything >= the default) restores the full jump.
    function limitJumpHeight(maxRise) {
        jumpHeight = Math.min(JUMP_HEIGHT, Math.max(0.5, maxRise));
    }

    // Place the cube where the baked prop sat: same center, same orientation,
    // scaled so its overall edge length matches the prop's size.
    function placeAt(position, quaternion, size) {
        group.position.copy(position);
        group.quaternion.copy(quaternion);
        group.scale.setScalar(size / CUBE_SPAN);
        restY = position.y;
    }

    // Restrained hover on the inner root, so it can never fight the jump
    // tweens (which live on `group`) and is simply ignored mid-routine.
    function setHover(isHovering) {
        if (busy) return;
        gsap.killTweensOf(cubeRoot.scale);
        const s = isHovering ? 1.08 : 1;
        gsap.to(cubeRoot.scale, { x: s, y: s, z: s, duration: 0.5, ease: 'expo.out' });
    }

    // The whole click routine: squash → jump → hover + spin while the sequence
    // plays → settle the spin → fall back with a bounce and a landing squash.
    async function onClick() {
        if (busy) return;
        busy = true;
        gsap.killTweensOf(cubeRoot.scale);

        // Anticipation: a quick squash against the table...
        await gsap.to(cubeRoot.scale, { x: 1.12, y: 0.8, z: 1.12, duration: 0.16, ease: 'power2.out' });

        // ...then launch, the scale recovering with a small overshoot mid-air.
        gsap.to(cubeRoot.scale, { x: 1, y: 1, z: 1, duration: 0.45, ease: 'back.out(2.5)' });
        await gsap.to(group.position, { y: restY + jumpHeight, duration: 0.55, ease: 'power2.out' });

        // Airborne: a gentle bob plus a slow spin so the turns read from all sides.
        const bob = gsap.to(group.position, {
            y: `+=${jumpHeight * 0.08}`,
            duration: 1.1, ease: 'sine.inOut', yoyo: true, repeat: -1,
        });
        const spin = gsap.to(cubeRoot.rotation, {
            y: Math.PI * 4, duration: TOTAL_SOLVE_SECONDS + 1, ease: 'sine.inOut',
        });

        await playSequence(solved ? SCRAMBLE_SEQUENCE : SOLVE_SEQUENCE);
        solved = !solved;

        // Land the spin on a full revolution so the cube faces exactly as it
        // took off, then zero it out silently (visually identical).
        bob.kill();
        spin.kill();
        const fullTurn = Math.PI * 2;
        await gsap.to(cubeRoot.rotation, {
            y: Math.ceil(cubeRoot.rotation.y / fullTurn) * fullTurn,
            duration: 0.5, ease: 'power1.inOut',
        });
        cubeRoot.rotation.y = 0;

        // Fall back onto its spot with a bounce, plus a small landing squash.
        await gsap.to(group.position, { y: restY, duration: 0.9, ease: 'bounce.out' });
        await gsap.to(cubeRoot.scale, {
            x: 1.06, y: 0.92, z: 1.06, duration: 0.09, ease: 'power2.out', yoyo: true, repeat: 1,
        });
        cubeRoot.scale.setScalar(1);

        busy = false;
    }

    return { group, placeAt, onClick, setHover, limitJumpHeight };
}
