// ============================================================================
// The travel gallery
// ----------------------------------------------------------------------------
// Lives inside the existing "Traveling" modal, drawn in the Dear United ink
// style (toon bands, ink outlines, paper grain under a night sky). Three steps:
//
//   WORLD    a globe modelled in Blender (scripts/blender/build-globe.py).
//     |      Visited countries are raised and coloured; drag to spin it.
//     |      click a country
//   COUNTRY  the globe turns to face it and its cities stand up as pins.
//     |      click a pin (or its label)
//   CITY     that city's toy diorama under a glass dome, loaded on demand and
//            disposed on the way out. Every OBJ-<id> in it is clickable and
//            opens its photos in the panel beside the stage.
//
// Rules carried over from the first version:
//   1. Photos are DOM <img>, never three.js textures. A 1600x1200 photo costs
//      about 10MB of GPU memory as a texture; as an <img> the browser evicts
//      and re-decodes it by itself.
//   2. Exactly one city is resident. Leaving disposes it.
//   3. Its own WebGL context, separate from the room's; the room stops drawing
//      while a modal is open, so only one context ever draws at a time.
// ============================================================================

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { disposeObject3D } from './gallery/dispose.js';
import { InkPipeline } from './gallery/ink/pipeline.js';
import { createSky, createLights } from './gallery/ink/sky.js';
import { inkify, inkSolid, highlightTwin, forgetMaterials } from './gallery/ink/materials.js';
import { countries, countryBySlug, countryByIso, cityBySlug, thumbUrl, fullUrl } from './data/places.js';

// GLTFLoader runs names through PropertyBinding.sanitizeNodeName, which DELETES
// '.', '[', ']', ':' and '/'. Multi-primitive meshes also gain '_1' suffixes.
const norm = (name) => (name || '').replace(/_\d+$/, '').replace(/[\s[\].:/]/g, '');

const VIEW = { WORLD: 'world', COUNTRY: 'country', CITY: 'city' };
const GLOBE_URL = 'models/gallery/globe.glb';

// Globe palette (sRGB). Muted to sit inside the ink look rather than shout.
const OCEAN = '#2f4468';
const LAND = '#b9b4a6';
const TONES = {
    mint: '#86c9a8', sky: '#8cb4dc', amber: '#e3bd62', rose: '#e09aa2',
    violet: '#ad9bd8', sand: '#dcae84', red: '#d46e66',
};
const PIN = '#ffd27a';
const LIFT = 1.012;          // visited countries stand proud of the rest

// Same mapping as build-globe.py, after glTF's Z-up -> Y-up conversion.
function latLon(lat, lon, r = 1) {
    const la = THREE.MathUtils.degToRad(lat), lo = THREE.MathUtils.degToRad(lon);
    return new THREE.Vector3(Math.cos(la) * Math.cos(lo), Math.sin(la), -Math.cos(la) * Math.sin(lo)).multiplyScalar(r);
}

const prettify = (id) => id.replace(/-/g, ' ').replace(/^./, (c) => c.toUpperCase());
const reducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const easeInOut = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

export function initGallery(stageEl, { titleEl, backEl, onStatus } = {}) {
    let renderer = null, pipeline = null, camera = null, controls = null, sky = null;
    let canvasEl = null, labelsEl = null, tipEl = null, photosEl = null;
    let raf = null, open = false, lastT = 0;
    let view = VIEW.WORLD;

    // world
    let worldScene = null, globe = null, globeLoading = null;
    const countryMeshes = new Map();       // iso -> mesh (visited only)
    let pins = null, pinLabels = [];
    let activeCountry = null;

    // city
    let cityScene = null, cityRoot = null, cityMaterials = null, dome = null;
    let activeCity = null, orbiters = [], shuttles = [];
    let objectIndex = new Map();           // id -> { meshes: [], instances: [{ mesh, idx: [] }] }
    let hovered = null, selected = null;
    let loadToken = 0;

    let flight = null;                     // camera tween
    let gltfLoader = null, dracoLoader = null;
    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    let pointerIn = false, downAt = null;

    // ---- setup ------------------------------------------------------------

    function ensureRenderer() {
        if (renderer) return true;
        const canvas = document.createElement('canvas');
        canvas.className = 'gallery-canvas';
        canvasEl = canvas;
        try {
            renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: false });
        } catch {
            onStatus?.('This browser cannot draw the 3D globe.');
            return false;
        }
        renderer.outputColorSpace = THREE.SRGBColorSpace;
        renderer.autoClear = false;
        renderer.setPixelRatio(renderScale());

        // A reaped context is otherwise a permanently black rectangle.
        canvas.addEventListener('webglcontextlost', (e) => {
            e.preventDefault();
            onStatus?.('The 3D view ran out of memory. Reload the page to bring it back.');
        });

        labelsEl = document.createElement('div');
        labelsEl.className = 'gallery-labels';
        tipEl = document.createElement('div');
        tipEl.className = 'gallery-tip';
        tipEl.hidden = true;
        photosEl = document.createElement('div');
        photosEl.className = 'gallery-photos';
        photosEl.hidden = true;
        // Click on the backdrop (not a photo) closes; Esc too.
        photosEl.addEventListener('click', (e) => { if (e.target === photosEl) select(null); });
        stageEl.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !photosEl.hidden) select(null); });
        // The canvas goes first so the floating head stays above it.
        stageEl.prepend(canvas);
        stageEl.append(labelsEl, tipEl, photosEl);

        camera = new THREE.PerspectiveCamera(40, 1, 0.01, 60);
        camera.position.set(0, 0.6, 3.2);
        sky = createSky(30);

        worldScene = new THREE.Scene();
        worldScene.add(createLights(new THREE.Vector3(), 1.6));
        cityScene = new THREE.Scene();
        cityScene.add(createLights(new THREE.Vector3(0, 0.3, 0), 1.6));

        pipeline = new InkPipeline(renderer, { scene: worldScene, sky, camera, unit: 0.05 });

        controls = new OrbitControls(camera, canvas);
        controls.enableDamping = !reducedMotion();
        controls.dampingFactor = 0.06;
        controls.enablePan = false;
        controls.rotateSpeed = 0.6;
        controls.zoomSpeed = 0.7;
        controls.addEventListener('start', () => { controls.autoRotate = false; flight = null; });

        dracoLoader = new DRACOLoader();
        dracoLoader.setDecoderPath('draco/');
        gltfLoader = new GLTFLoader();
        gltfLoader.setDRACOLoader(dracoLoader);

        canvas.addEventListener('pointermove', onPointerMove);
        canvas.addEventListener('pointerleave', () => { pointerIn = false; setHover(null); });
        canvas.addEventListener('pointerdown', (e) => { downAt = { x: e.clientX, y: e.clientY, t: performance.now() }; });
        canvas.addEventListener('pointerup', onPointerUp);
        return true;
    }

    // Touch devices get a lower render resolution, as in the room: a dpr-3
    // framebuffer is what crashes mobile Safari. The ink pass also renders the
    // scene twice, which is the other reason to keep this clamped.
    function renderScale() {
        const coarse = window.matchMedia('(pointer: coarse)').matches;
        return Math.min(window.devicePixelRatio, coarse ? 1.1 : 1.5);
    }

    // ---- world: the globe -------------------------------------------------

    function loadGlobe() {
        if (globe) return Promise.resolve(globe);
        if (globeLoading) return globeLoading;
        onStatus?.('Loading the globe…');
        globeLoading = new Promise((res, rej) => gltfLoader.load(GLOBE_URL, (g) => res(g.scene), undefined, rej))
            .then((root) => {
                const land = inkSolid(LAND);
                const toneMats = {};
                root.traverse((o) => {
                    if (!o.isMesh) return;
                    const n = norm(o.name) || norm(o.parent?.name);
                    if (n === 'OCEAN') {
                        o.material = inkSolid(OCEAN);
                        return;
                    }
                    const iso = n.startsWith('CTRY-') ? n.slice(5) : null;
                    const c = iso && countryByIso[iso];
                    if (c) {
                        const hex = TONES[c.tone] || TONES.mint;
                        o.material = toneMats[hex] ||= inkSolid(hex, { emissive: 0.08 });
                        o.scale.setScalar(LIFT);
                        o.userData.country = c;
                        o.userData.baseMaterial = o.material;
                        countryMeshes.set(iso, o);
                    } else {
                        o.material = land;
                    }
                });
                for (const c of countries) {
                    if (!countryMeshes.has(c.iso)) console.warn(`[gallery] globe has no CTRY-${c.iso} (${c.name})`);
                }
                globe = root;
                worldScene.add(globe);
                onStatus?.('');
                return globe;
            })
            .catch((err) => {
                globeLoading = null;
                onStatus?.('The globe could not load.');
                throw err;
            });
        return globeLoading;
    }

    function useWorldScene() {
        pipeline.scene = worldScene;
        pipeline.hideInNormalPass = [];
        pipeline.uniforms.uDepthK.value = 0.004;
        pipeline.uniforms.uUnit.value = 0.05;
        camera.near = 0.05; camera.far = 60; camera.updateProjectionMatrix();
        controls.target.set(0, 0, 0);
        controls.minDistance = 1.55;
        controls.maxDistance = 4.2;
        controls.minPolarAngle = 0.15;
        controls.maxPolarAngle = Math.PI - 0.15;
    }

    async function showWorld() {
        if (!ensureRenderer()) return;
        leaveCity();
        clearPins();
        view = VIEW.WORLD;
        activeCountry = null;
        useWorldScene();
        if (titleEl) titleEl.textContent = 'Places I have been';
        setBack(null);
        try { await loadGlobe(); } catch { return; }
        if (view !== VIEW.WORLD) return;
        const dir = camera.position.clone().normalize();
        flyTo(dir, 3.2);
        controls.autoRotate = !reducedMotion();
        controls.autoRotateSpeed = 0.35;
    }

    function countryDirection(c) {
        const list = (c.cities || []).map((s) => cityBySlug[s]).filter((x) => x && x.lat != null);
        if (list.length) {
            const v = new THREE.Vector3();
            for (const x of list) v.add(latLon(x.lat, x.lon));
            return v.normalize();
        }
        const mesh = countryMeshes.get(c.iso);
        if (!mesh) return new THREE.Vector3(0, 0, 1);
        mesh.geometry.computeBoundingBox();
        return mesh.geometry.boundingBox.getCenter(new THREE.Vector3()).normalize();
    }

    function openCountry(slug) {
        const c = countryBySlug[slug];
        if (!c) return;
        leaveCity();
        useWorldScene();
        view = VIEW.COUNTRY;
        activeCountry = c;
        controls.autoRotate = false;
        setHover(null);
        if (titleEl) titleEl.textContent = c.name;
        setBack('Back to the globe', showWorld);

        const list = (c.cities || []).map((s) => cityBySlug[s]).filter(Boolean);
        // Small countries need a closer look to tell the pins apart.
        flyTo(countryDirection(c), list.length > 1 ? 1.75 : 2.1);
        clearPins();
        if (!list.length) {
            onStatus?.('Nothing from here is up yet.');
            return;
        }
        onStatus?.('');
        buildPins(list);
    }

    // Pins are 3D (so the ink draws them and the globe hides the far ones),
    // with a DOM label each so they are real buttons for keyboard and screen
    // readers, positioned every frame by projection.
    function buildPins(list) {
        pins = new THREE.Group();
        const stemMat = inkSolid('#efe9dc');
        const headMat = inkSolid(PIN, { emissive: 0.35 });
        for (const city of list) {
            if (city.lat == null) continue;
            const up = latLon(city.lat, city.lon).normalize();
            const pin = new THREE.Group();
            const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.0035, 0.0035, 0.07, 6), stemMat);
            stem.position.y = 0.035;
            const head = new THREE.Mesh(new THREE.SphereGeometry(0.014, 16, 12), headMat);
            head.position.y = 0.075;
            pin.add(stem, head);
            pin.position.copy(up).multiplyScalar(1.01);
            pin.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), up);
            pin.userData.city = city;
            stem.userData.city = city; head.userData.city = city;
            pins.add(pin);

            const btn = document.createElement('button');
            btn.className = 'gallery-pin-label';
            btn.textContent = city.name;
            btn.addEventListener('click', () => enterCity(city.slug));
            labelsEl.appendChild(btn);
            pinLabels.push({ el: btn, pin });
        }
        worldScene.add(pins);
    }

    function clearPins() {
        if (pins) {
            worldScene.remove(pins);
            disposeObject3D(pins);
            pins = null;
        }
        for (const { el } of pinLabels) el.remove();
        pinLabels = [];
    }

    const _v = new THREE.Vector3(), _cam = new THREE.Vector3();
    function placeLabels() {
        if (!pinLabels.length) return;
        const r = stageEl.getBoundingClientRect();
        _cam.copy(camera.position).normalize();
        for (const { el, pin } of pinLabels) {
            _v.set(0, 0.1, 0).applyQuaternion(pin.quaternion).add(pin.position);
            const facing = pin.position.clone().normalize().dot(_cam);
            _v.project(camera);
            const vis = facing > 0.15 && _v.z < 1;
            el.style.opacity = vis ? '1' : '0';
            el.style.pointerEvents = vis ? 'auto' : 'none';
            el.tabIndex = vis ? 0 : -1;
            el.style.transform = `translate(${((_v.x + 1) / 2) * r.width}px, ${((1 - _v.y) / 2) * r.height}px) translate(-50%, -100%)`;
        }
    }

    // ---- camera flights ---------------------------------------------------

    function flyTo(dir, dist, target = new THREE.Vector3()) {
        const from = camera.position.clone().sub(controls.target);
        const to = dir.clone().normalize().multiplyScalar(dist);
        if (reducedMotion()) {
            controls.target.copy(target);
            camera.position.copy(target).add(to);
            controls.update();
            return;
        }
        flight = {
            start: performance.now(), dur: 1100,
            fromDir: from.clone().normalize(), fromLen: from.length(), fromTarget: controls.target.clone(),
            toDir: to.clone().normalize(), toLen: dist, toTarget: target.clone(),
        };
    }

    // Wall-clock, not per-frame: a slow device should arrive on time, not
    // crawl there.
    function stepFlight() {
        if (!flight) return;
        flight.t = Math.min(1, (performance.now() - flight.start) / flight.dur);
        const k = easeInOut(flight.t);
        const q = new THREE.Quaternion().setFromUnitVectors(flight.fromDir, flight.toDir);
        const dir = flight.fromDir.clone().applyQuaternion(new THREE.Quaternion().slerp(q, k));
        const len = THREE.MathUtils.lerp(flight.fromLen, flight.toLen, k);
        controls.target.lerpVectors(flight.fromTarget, flight.toTarget, k);
        camera.position.copy(controls.target).addScaledVector(dir, len);
        if (flight.t >= 1) flight = null;
    }

    // ---- city: the diorama ------------------------------------------------

    function buildDome() {
        const g = new THREE.Group();
        g.name = 'dome';
        const R = 1.14, Y = -0.14;
        // A dark turned-wood stand the base sits on, wider than the dome.
        const stand = new THREE.Mesh(new THREE.CylinderGeometry(R + 0.04, R + 0.08, 0.1, 96), inkSolid('#3a3346'));
        stand.position.y = Y - 0.05;
        g.add(stand);
        // Glass: a fresnel rim, nearly clear face-on. Kept out of the normal
        // pass, or its depth would hide every ink line inside it.
        const glass = new THREE.Mesh(
            new THREE.SphereGeometry(R, 64, 32, 0, Math.PI * 2, 0, Math.PI / 2),
            new THREE.ShaderMaterial({
                transparent: true, depthWrite: false, side: THREE.DoubleSide,
                uniforms: { uTint: { value: new THREE.Color('#cfe0ff') } },
                vertexShader: /* glsl */`
                    varying vec3 vN; varying vec3 vV;
                    void main() {
                        vec4 mv = modelViewMatrix * vec4(position, 1.0);
                        vN = normalize(normalMatrix * normal); vV = normalize(-mv.xyz);
                        gl_Position = projectionMatrix * mv;
                    }`,
                fragmentShader: /* glsl */`
                    uniform vec3 uTint; varying vec3 vN; varying vec3 vV;
                    void main() {
                        float f = pow(1.0 - abs(dot(normalize(vN), normalize(vV))), 2.6);
                        gl_FragColor = vec4(uTint, 0.04 + 0.42 * f);
                    }`,
            })
        );
        glass.position.y = Y;
        glass.renderOrder = 5;
        g.add(glass);
        // A few stars caught in the glass, as in the Astana original.
        const n = 140, pos = new Float32Array(n * 3);
        let seed = 3;
        const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
        for (let i = 0; i < n; i++) {
            const u = rnd() * Math.PI * 2, v = 0.12 + 0.88 * rnd();
            const s = Math.sqrt(1 - v * v);
            pos.set([Math.cos(u) * s * R * 0.995, Y + v * R * 0.995, Math.sin(u) * s * R * 0.995], i * 3);
        }
        const sg = new THREE.BufferGeometry();
        sg.setAttribute('position', new THREE.BufferAttribute(pos, 3));
        const stars = new THREE.Points(sg, new THREE.PointsMaterial({
            size: 1.6, sizeAttenuation: false, color: 0xf2efe6, transparent: true, opacity: 0.7, depthWrite: false,
        }));
        stars.renderOrder = 6;
        g.add(stars);
        g.userData.noInk = [glass, stars];
        return g;
    }

    function indexObjects(root) {
        const index = new Map();
        const entry = (id) => {
            if (!index.has(id)) index.set(id, { meshes: [], instances: [] });
            return index.get(id);
        };
        orbiters = [];
        shuttles = [];
        root.traverse((o) => {
            if (o.userData.orbit) orbiters.push(o);
            // A shuttle (the Koktobe cable car's cabins) slides from where it
            // was placed by `shuttle` (Blender axes: x, y, z-up) and dips by
            // `sag` mid-way, like the cable it hangs from; then wraps round.
            const sh = o.userData.shuttle;
            if (Array.isArray(sh) && sh.length === 3) {
                shuttles.push({
                    o,
                    start: o.position.clone(),
                    d: new THREE.Vector3(sh[0], sh[2], -sh[1]),
                    period: o.userData.period || 30,
                    phase: o.userData.phase || 0,
                    sag: o.userData.sag || 0,
                });
            }
            if (!o.isMesh) return;
            // Instanced bricks carry their stand per instance (build-manchester.mjs).
            let src = o;
            while (src && !src.userData.objectIds && src !== root) src = src.parent;
            if (o.isInstancedMesh && src?.userData.objectIds) {
                const { objectIds, instanceObject } = src.userData;
                const by = new Map();
                instanceObject.forEach((k, i) => {
                    if (!by.has(k)) by.set(k, []);
                    by.get(k).push(i);
                });
                for (const [k, idx] of by) entry(objectIds[k]).instances.push({ mesh: o, idx });
                o.userData.objectIds = objectIds;
                o.userData.instanceObject = instanceObject;
                return;
            }
            for (let p = o; p && p !== root.parent; p = p.parent) {
                const n = norm(p.name);
                if (n.startsWith('OBJ-')) {
                    const id = n.slice(4);
                    o.userData.objectId = id;
                    o.userData.baseMaterial = o.material;
                    entry(id).meshes.push(o);
                    break;
                }
            }
        });
        return index;
    }

    function objectIdOf(hit) {
        const o = hit.object;
        if (o.isInstancedMesh && o.userData.objectIds && hit.instanceId != null) {
            return o.userData.objectIds[o.userData.instanceObject[hit.instanceId]];
        }
        return o.userData.objectId || null;
    }

    function paintObject(id, on) {
        const e = objectIndex.get(id);
        if (!e) return;
        for (const m of e.meshes) {
            const base = m.userData.baseMaterial;
            m.material = on ? (Array.isArray(base) ? base.map(highlightTwin) : highlightTwin(base)) : base;
        }
        for (const { mesh, idx } of e.instances) {
            const a = mesh.instanceColor.array;
            for (const i of idx) a[i * 3] = on ? 1 : 0;
            mesh.instanceColor.needsUpdate = true;
        }
    }

    function refreshHighlight(prev) {
        for (const id of prev) if (id && id !== hovered && id !== selected) paintObject(id, false);
        if (hovered) paintObject(hovered, true);
        if (selected) paintObject(selected, true);
    }

    function setHover(id) {
        if (id === hovered) return;
        const prev = [hovered];
        hovered = id;
        refreshHighlight(prev);
    }

    function select(id) {
        const prev = [selected];
        selected = id;
        refreshHighlight(prev);
        showPhotos(id);
    }

    async function enterCity(slug) {
        const city = cityBySlug[slug];
        if (!city || !ensureRenderer()) return;
        const token = ++loadToken;
        if (titleEl) titleEl.textContent = city.name;
        const country = countryBySlug[city.country];
        setBack(country ? `Back to ${country.name}` : 'Back to the globe',
            () => (country ? openCountry(country.slug) : showWorld()));

        if (!city.model) {
            // A city without a diorama yet: photos only.
            clearPins();
            onStatus?.('No model of this city yet.');
            return;
        }
        onStatus?.('Loading…');
        let root;
        try {
            root = await new Promise((res, rej) => gltfLoader.load(city.model, (g) => res(g.scene), undefined, rej));
        } catch {
            if (token === loadToken) onStatus?.(`${city.name} could not load.`);
            return;
        }
        if (token !== loadToken) { disposeObject3D(root); return; }

        leaveCity();
        clearPins();
        setHover(null);
        setCountryHover(null);
        cityMaterials = inkify(root);
        cityRoot = root;
        objectIndex = indexObjects(root);
        if (import.meta.env?.DEV) {
            for (const id of Object.keys(city.objects || {})) {
                if (!objectIndex.has(id)) console.warn(`[gallery] ${city.slug}: no OBJ-${id} in the model`);
            }
            for (const id of objectIndex.keys()) {
                if (!city.objects?.[id]) console.warn(`[gallery] ${city.slug}: OBJ-${id} has no entry in places.js`);
            }
        }
        dome = buildDome();
        cityScene.add(dome, root);

        activeCity = slug;
        selected = null;
        view = VIEW.CITY;
        pipeline.scene = cityScene;
        pipeline.hideInNormalPass = dome.userData.noInk;
        // Line thresholds scale with the scene: dioramas are ~2 units across,
        // their smallest parts (rails, bricks) a few hundredths.
        pipeline.uniforms.uDepthK.value = 0.006;
        pipeline.uniforms.uUnit.value = 0.03;
        camera.near = 0.02; camera.far = 40; camera.updateProjectionMatrix();
        controls.autoRotate = false;
        controls.minDistance = 0.9;
        controls.maxDistance = 4.2;
        controls.minPolarAngle = 0.2;
        controls.maxPolarAngle = Math.PI / 2 - 0.05;
        controls.target.set(0, 0.12, 0);
        flight = null;
        // Close enough that the dome fills the window.
        camera.position.set(0, 1.2, 2.6);
        controls.update();
        onStatus?.('');
    }

    function leaveCity() {
        if (tipEl) tipEl.hidden = true;
        if (photosEl) { photosEl.hidden = true; photosEl.replaceChildren(); }
        if (!cityRoot) return;
        hovered = null; selected = null;
        cityScene.remove(cityRoot, dome);
        // Ink materials first (they are cached by source material), then the
        // geometry and whatever textures the model brought.
        forgetMaterials(cityMaterials || []);
        disposeObject3D(cityRoot);
        disposeObject3D(dome);
        cityRoot = null; dome = null; cityMaterials = null;
        objectIndex = new Map();
        orbiters = [];
        shuttles = [];
        activeCity = null;
    }

    // ---- back arrow and floating photos (DOM, over the stage) ------------

    function setBack(label, fn) {
        if (!backEl) return;
        backEl.hidden = !label;
        if (label) {
            backEl.setAttribute('aria-label', label);
            backEl.title = label;
        }
        backEl.onclick = fn || null;
    }

    // A clicked object's photos drop onto the scene as a fan of polaroids;
    // clicking one shows it large. Nothing sits beside the stage.
    function showPhotos(id) {
        if (!photosEl) return;
        if (!id) {
            photosEl.hidden = true;
            photosEl.replaceChildren();
            return;
        }
        const city = cityBySlug[activeCity];
        const info = city?.objects?.[id] || {};
        const name = info.name || prettify(id);
        const photos = info.photos || [];
        tipEl.hidden = true;

        const title = document.createElement('p');
        title.className = 'gallery-photos-name';
        title.textContent = name;

        const fan = document.createElement('div');
        fan.className = 'gallery-polaroids';
        // Deterministic tilts so the same object always lands the same way.
        const tilt = (i) => `${(((i * 37 + id.length * 11) % 13) - 6) * 0.9}deg`;
        if (!photos.length) {
            const card = document.createElement('figure');
            card.className = 'gallery-polaroid is-empty';
            card.style.setProperty('--tilt', tilt(0));
            const blank = document.createElement('div');
            blank.className = 'gallery-polaroid-blank';
            blank.textContent = 'Photos coming soon';
            card.appendChild(blank);
            fan.appendChild(card);
        }
        photos.forEach((photo, i) => {
            const card = document.createElement('figure');
            card.className = 'gallery-polaroid';
            card.tabIndex = 0;
            card.style.setProperty('--tilt', tilt(i));
            card.style.animationDelay = `${Math.min(i, 8) * 45}ms`;
            const img = document.createElement('img');
            img.src = thumbUrl(photo.slug);
            img.alt = photo.caption || name;
            img.loading = 'lazy';
            img.decoding = 'async';
            card.appendChild(img);
            if (photo.caption) {
                const cap = document.createElement('figcaption');
                cap.textContent = photo.caption;
                card.appendChild(cap);
            }
            const open = () => showPhotoFull(photo, name);
            card.addEventListener('click', open);
            card.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); } });
            fan.appendChild(card);
        });
        photosEl.replaceChildren(title, fan);
        photosEl.hidden = false;
    }

    function showPhotoFull(photo, name) {
        const fig = document.createElement('figure');
        fig.className = 'gallery-photo-full';
        const img = document.createElement('img');
        img.src = fullUrl(photo.slug);
        img.alt = photo.caption || name;
        img.decoding = 'async';
        fig.appendChild(img);
        // Back to the fan, not out of the object.
        fig.addEventListener('click', () => showPhotos(selected));
        photosEl.replaceChildren(fig);
    }

    // ---- picking ----------------------------------------------------------

    function pick(e) {
        const r = canvasEl.getBoundingClientRect();
        pointer.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
        raycaster.setFromCamera(pointer, camera);
        if (view === VIEW.CITY) {
            if (!cityRoot) return null;
            for (const hit of raycaster.intersectObject(cityRoot, true)) {
                if (hit.object.userData.glass) continue;
                return { object: objectIdOf(hit) };
            }
            return null;
        }
        if (!globe) return null;
        const targets = [...countryMeshes.values()];
        if (pins) targets.push(...pins.children.flatMap((g) => g.children));
        const ocean = globe.getObjectByName('OCEAN');
        if (ocean) targets.push(ocean);
        const hit = raycaster.intersectObjects(targets, false)[0];
        if (!hit) return null;
        if (hit.object.userData.city) return { city: hit.object.userData.city };
        if (hit.object.userData.country) return { country: hit.object.userData.country };
        return null;
    }

    let hoverCountry = null;
    function setCountryHover(c) {
        if (c === hoverCountry) return;
        if (hoverCountry) {
            const m = countryMeshes.get(hoverCountry.iso);
            if (m) m.material = m.userData.baseMaterial;
        }
        hoverCountry = c;
        if (c) {
            const m = countryMeshes.get(c.iso);
            if (m) m.material = highlightTwin(m.userData.baseMaterial);
        }
    }

    let lastMove = null;
    function onPointerMove(e) {
        pointerIn = true;
        lastMove = e;
    }

    function hoverFromPointer() {
        if (!lastMove || !pointerIn) return;
        const e = lastMove;
        lastMove = null;
        const hit = pick(e);
        let label = null;
        if (view === VIEW.CITY) {
            setHover(hit?.object || null);
            const city = cityBySlug[activeCity];
            if (hit?.object) label = city?.objects?.[hit.object]?.name || prettify(hit.object);
        } else {
            setCountryHover(hit?.country || null);
            if (hit?.country) label = hit.country.name;
            if (hit?.city) label = hit.city.name;
        }
        canvasEl.style.cursor = label ? 'pointer' : 'grab';
        if (label) {
            const r = stageEl.getBoundingClientRect();
            tipEl.textContent = label;
            tipEl.style.transform = `translate(${e.clientX - r.left + 14}px, ${e.clientY - r.top + 12}px)`;
            tipEl.hidden = false;
        } else {
            tipEl.hidden = true;
        }
    }

    function onPointerUp(e) {
        if (!downAt) return;
        const moved = Math.hypot(e.clientX - downAt.x, e.clientY - downAt.y);
        const quick = performance.now() - downAt.t < 600;
        downAt = null;
        if (moved > 6 || !quick) return;      // that was a drag, not a click
        const hit = pick(e);
        if (view === VIEW.CITY) {
            if (hit?.object) select(hit.object === selected ? null : hit.object);
            return;
        }
        if (hit?.city) return enterCity(hit.city.slug);
        if (hit?.country) {
            tipEl.hidden = true;
            setCountryHover(null);
            return openCountry(hit.country.slug);
        }
    }

    // ---- loop -------------------------------------------------------------

    function resize() {
        const r = stageEl.getBoundingClientRect();
        if (r.width < 2 || r.height < 2) return false;
        const pr = renderScale();
        const w = Math.round(r.width), h = Math.round(r.height);
        if (canvasEl.width !== Math.floor(w * pr) || canvasEl.height !== Math.floor(h * pr)) {
            renderer.setPixelRatio(pr);
            renderer.setSize(w, h, false);
            pipeline.setSize(w, h, pr);
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
        }
        return true;
    }

    function tick(t) {
        raf = requestAnimationFrame(tick);
        if (!open || !renderer) return;
        const dt = Math.min(0.05, (t - (lastT || t)) / 1000);
        lastT = t;
        if (!resize()) return;
        stepFlight();
        if (!flight) controls.update();
        else camera.lookAt(controls.target);
        if (!reducedMotion()) {
            for (const o of orbiters) o.rotation.y += (dt * Math.PI * 2) / o.userData.orbit;
            const now = t / 1000;
            for (const s of shuttles) {
                const u = (now / s.period + s.phase) % 1;
                s.o.position.copy(s.start).addScaledVector(s.d, u);
                s.o.position.y -= s.sag * 4 * u * (1 - u);
            }
        }
        hoverFromPointer();
        sky.follow(camera);
        pipeline.render();
        if (view === VIEW.COUNTRY) placeLabels();
    }

    // ---- public surface ---------------------------------------------------

    return {
        open() {
            open = true;
            if (!ensureRenderer()) return;
            showWorld();
            if (!raf) { lastT = 0; raf = requestAnimationFrame(tick); }
        },
        close() {
            open = false;
            if (raf) { cancelAnimationFrame(raf); raf = null; }
            // Give the city back on close: the modal may sit unopened for the
            // rest of the session. The globe is small and stays.
            leaveCity();
            clearPins();
        },
        showWorld,
        goCountry: openCountry,
        goCity: enterCity,
        isOpen: () => open,
        stats: () => renderer?.info.memory ?? null,
        debug: () => ({ cam: camera?.position.toArray(), target: controls?.target.toArray(), flight: !!flight, view, shuttles: shuttles.map((s) => s.o.position.toArray().map((v) => +v.toFixed(3))) }),
        dispose() {
            this.close();
            controls?.dispose();
            dracoLoader?.dispose();
            if (globe) disposeObject3D(globe);
            renderer?.dispose();
            renderer = null;
        },
    };
}
