// ============================================================================
// The travel gallery
// ----------------------------------------------------------------------------
// Lives inside the existing "Traveling" modal. Three layers:
//
//   WORLD  a low-poly globe/plate, one named mesh per visited country
//     |    click a country
//   CITY   that city's disc, loaded on demand and disposed on the way out
//     |    click a photo
//   PHOTO  a lightbox holding exactly one full-size image
//
// Two rules the whole design rests on:
//
//   1. Photos are DOM <img>, never three.js textures. A 1600x1200 photo costs
//      about 10MB of GPU memory as a texture and stays pinned until disposed,
//      while the browser evicts and re-decodes an <img> by itself. 300 photos
//      as textures would be ~3GB; as <img> it is a normal web page.
//
//   2. Exactly one city is resident. Leaving disposes it. The HTTP cache
//      already makes revisits fast, so an in-memory cache would buy ~50ms and
//      cost ~10MB per city held.
//
// The renderer here is a SECOND WebGL context, separate from the room's. The
// modal sits above the room canvas in z-order and its backdrop-filter blurs
// whatever is behind it, so painting the gallery into a region of the room's
// canvas would show a blurred room, not the gallery. The room stops rendering
// while a modal is open, so only one context ever draws at a time.
// ============================================================================

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { disposeObject3D } from './gallery/dispose.js';
import { countries, cities, countryBySlug, cityBySlug, thumbUrl } from './data/places.js';

// GLTFLoader runs names through PropertyBinding.sanitizeNodeName, which DELETES
// '.', '[', ']', ':' and '/'. Multi-primitive meshes also gain '_1' suffixes.
// Blender's ".001" duplicate suffix therefore arrives as "001" glued on, which
// matches nothing and reports no error. Same helper as the stadium's.
const norm = (name) => (name || '').replace(/_\d+$/, '').replace(/[\s[\].:/]/g, '');

const VIEW = { WORLD: 'world', CITY: 'city' };

// Mint, matching the site's --accent-emerald.
const HIGHLIGHT_COLOR = 0x6ee7b7;

export function initGallery(stageEl, { filmstripEl, titleEl, backEl, onStatus } = {}) {
    let renderer = null;
    let scene = null;
    let camera = null;
    let raf = null;
    let open = false;

    let view = VIEW.WORLD;
    let activeCity = null;

    let worldGroup = null;
    let cityGroup = null;
    let cityRoot = null;
    let countryMeshes = [];
    let buildingMeshes = [];

    // Made once, reused forever. Cloning a material per hover leaks one material
    // per event, which is thousands over a session; swapping which material a
    // mesh points at allocates nothing.
    let highlightMat = null;

    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();

    // Rising counter so a slow load that lands after a newer click is dropped
    // instead of adding a second disc to the scene.
    let loadToken = 0;
    const inFlight = new Map();

    let gltfLoader = null;
    let dracoLoader = null;

    // ---- setup ------------------------------------------------------------

    function ensureRenderer() {
        if (renderer) return;

        const canvas = document.createElement('canvas');
        canvas.className = 'gallery-canvas';
        stageEl.appendChild(canvas);

        renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
        renderer.outputColorSpace = THREE.SRGBColorSpace;
        renderer.setPixelRatio(renderScale());
        renderer.setClearColor(0x000000, 0);

        // A reaped context is otherwise a permanently black rectangle with no
        // explanation. Recovery needs a reload; at least say so.
        canvas.addEventListener('webglcontextlost', (e) => {
            e.preventDefault();
            onStatus?.('The 3D view ran out of memory. Reload the page to bring it back.');
        });

        scene = new THREE.Scene();
        camera = new THREE.PerspectiveCamera(45, 1, 0.01, 100);

        // Unlit baked textures, same as the room, so a city disc costs no
        // lighting work. Ambient only, for the placeholder boxes' sake.
        scene.add(new THREE.AmbientLight(0xffffff, 0.9));
        const key = new THREE.DirectionalLight(0xffffff, 0.9);
        key.position.set(3, 6, 2);
        scene.add(key);

        worldGroup = new THREE.Group();
        cityGroup = new THREE.Group();
        scene.add(worldGroup, cityGroup);

        highlightMat = new THREE.MeshBasicMaterial({ color: HIGHLIGHT_COLOR });

        dracoLoader = new DRACOLoader();
        dracoLoader.setDecoderPath('draco/');
        gltfLoader = new GLTFLoader();
        gltfLoader.setDRACOLoader(dracoLoader);

        stageEl.addEventListener('pointerdown', onPointerDown);
        buildWorld();
    }

    // Touch devices get a lower render resolution for the same reason the room
    // does: a dpr-3 framebuffer plus textures is what crashes mobile Safari.
    function renderScale() {
        const coarse = window.matchMedia('(pointer: coarse)').matches;
        return Math.min(window.devicePixelRatio, coarse ? 1.1 : 1.5);
    }

    // ---- world layer ------------------------------------------------------

    // Placeholder geometry, deliberately. The whole flow is proved against boxes
    // before any Blender work exists, so a later problem with a real model is
    // unambiguously a model problem. Swapping in world.glb should need no code
    // change here beyond loading it: the names are the contract.
    function buildWorld() {
        countryMeshes = [];
        const spacing = 1.5;
        const startX = -((countries.length - 1) * spacing) / 2;

        countries.forEach((c, i) => {
            const mesh = new THREE.Mesh(
                new THREE.BoxGeometry(1, 0.25, 1),
                new THREE.MeshBasicMaterial({ color: 0x9aa3ad })
            );
            mesh.name = c.mesh;              // CTRY-<slug>
            mesh.position.set(startX + i * spacing, 0, 0);
            worldGroup.add(mesh);
            countryMeshes.push(mesh);
        });

        camera.position.set(0, 2.4, 4.2);
        camera.lookAt(0, 0, 0);
    }

    function showWorld() {
        view = VIEW.WORLD;
        detachCity();
        worldGroup.visible = true;
        camera.position.set(0, 2.4, 4.2);
        camera.lookAt(0, 0, 0);
        renderFilmstrip(null);
        if (titleEl) titleEl.textContent = 'Places I have been';
        if (backEl) backEl.hidden = true;
        onStatus?.('');
    }

    // ---- city layer -------------------------------------------------------

    function placeholderCity(city) {
        const root = new THREE.Group();
        root.name = `CITY-${city.slug}`;

        const disc = new THREE.Mesh(
            new THREE.CylinderGeometry(1, 1, 0.08, 48),
            new THREE.MeshBasicMaterial({ color: 0x2f3540 })
        );
        disc.name = 'DECO-disc';
        root.add(disc);

        // One box per distinct building named in this city's photos, so hover
        // highlighting has something real to resolve against.
        const ids = [...new Set(city.photos.map((p) => p.building).filter(Boolean))];
        const n = Math.max(ids.length, 3);
        ids.forEach((id, i) => {
            const a = (i / n) * Math.PI * 2;
            const h = 0.3 + (i % 3) * 0.18;
            const b = new THREE.Mesh(
                new THREE.BoxGeometry(0.18, h, 0.18),
                new THREE.MeshBasicMaterial({ color: 0xd8dde3 })
            );
            b.name = `BLD-${id}`;
            b.position.set(Math.cos(a) * 0.55, h / 2 + 0.04, Math.sin(a) * 0.55);
            root.add(b);
        });

        return root;
    }

    function prepareCity(root, city) {
        const buildings = [];
        root.traverse((obj) => {
            const n = norm(obj.name);
            if (obj.isMesh && n.startsWith('BLD-')) {
                obj.userData.buildingId = n.slice(4);
                // Keep the original so highlighting can put it back. Never mutate
                // the baked material in place.
                obj.userData.baseMaterial = obj.material;
                buildings.push(obj);
            }
        });

        if (import.meta.env?.DEV) {
            const have = new Set(buildings.map((b) => b.userData.buildingId));
            for (const p of city.photos) {
                if (p.building && !have.has(p.building)) {
                    console.warn(`[gallery] ${city.slug}: photo "${p.slug}" wants building "${p.building}", which is not in the model`);
                }
            }
        }
        return buildings;
    }

    function loadCityModel(city) {
        if (inFlight.has(city.slug)) return inFlight.get(city.slug);
        const p = new Promise((res, rej) => {
            gltfLoader.load(city.model, (gltf) => res(gltf.scene), undefined, rej);
        }).finally(() => inFlight.delete(city.slug));
        inFlight.set(city.slug, p);
        return p;
    }

    async function enterCity(slug) {
        const city = cityBySlug[slug];
        if (!city) return;

        const token = ++loadToken;
        if (titleEl) titleEl.textContent = city.name;
        if (backEl) backEl.hidden = false;

        let root;
        if (city.model) {
            onStatus?.('Loading…');
            try {
                const loaded = await loadCityModel(city);
                if (token !== loadToken) return;   // a newer click won
                root = loaded.clone(true);
            } catch {
                if (token !== loadToken) return;
                // A city whose model fails still shows its photos rather than
                // presenting a dead empty disc.
                onStatus?.('');
                root = placeholderCity(city);
            }
        } else {
            root = placeholderCity(city);
        }
        if (token !== loadToken) return;

        detachCity();
        worldGroup.visible = false;
        cityGroup.add(root);
        cityRoot = root;
        buildingMeshes = prepareCity(root, city);
        activeCity = slug;
        view = VIEW.CITY;

        frameCity(root);
        renderFilmstrip(city);
        onStatus?.('');
    }

    function frameCity(root) {
        const box = new THREE.Box3().setFromObject(root);
        const size = box.getSize(new THREE.Vector3());
        const center = box.getCenter(new THREE.Vector3());
        const r = Math.max(size.x, size.y, size.z) || 1;
        camera.position.set(center.x + r * 1.1, center.y + r * 0.8, center.z + r * 1.1);
        camera.lookAt(center);
    }

    function detachCity() {
        if (!cityRoot) return;
        // Clear any highlight first: disposing a mesh while it points at the
        // shared highlight material would take that material with it, and every
        // later city would highlight to black.
        setHighlight(null);
        disposeObject3D(cityRoot);
        cityRoot = null;
        buildingMeshes = [];
        activeCity = null;
    }

    // ---- highlighting -----------------------------------------------------

    function setHighlight(buildingId) {
        for (const b of buildingMeshes) {
            b.material = (buildingId && b.userData.buildingId === buildingId)
                ? highlightMat
                : b.userData.baseMaterial;
        }
    }

    // ---- filmstrip (DOM) --------------------------------------------------

    function renderFilmstrip(city) {
        if (!filmstripEl) return;

        if (!city || !city.photos.length) {
            filmstripEl.replaceChildren();
            filmstripEl.hidden = true;
            return;
        }
        filmstripEl.hidden = false;

        const frag = document.createDocumentFragment();
        for (const photo of city.photos) {
            const fig = document.createElement('figure');
            fig.className = 'gallery-thumb';

            const img = document.createElement('img');
            img.src = thumbUrl(photo.slug);
            img.alt = photo.caption || '';
            img.loading = 'lazy';       // only decode what is near the viewport
            img.decoding = 'async';
            if (photo.w && photo.h) { img.width = photo.w; img.height = photo.h; }

            const cap = document.createElement('figcaption');
            cap.textContent = photo.caption || '';

            fig.append(img, cap);

            // A photo with no building highlights nothing, which is a normal
            // case rather than an error.
            if (photo.building) {
                fig.addEventListener('pointerenter', () => setHighlight(photo.building));
                fig.addEventListener('pointerleave', () => setHighlight(null));
                fig.addEventListener('focusin', () => setHighlight(photo.building));
                fig.addEventListener('focusout', () => setHighlight(null));
            }
            frag.appendChild(fig);
        }
        filmstripEl.replaceChildren(frag);
    }

    // ---- interaction ------------------------------------------------------

    function onPointerDown(e) {
        if (view !== VIEW.WORLD) return;

        const r = stageEl.getBoundingClientRect();
        pointer.x = ((e.clientX - r.left) / r.width) * 2 - 1;
        pointer.y = -((e.clientY - r.top) / r.height) * 2 + 1;

        raycaster.setFromCamera(pointer, camera);
        const hits = raycaster.intersectObjects(countryMeshes, true);
        if (!hits.length) return;

        // Resolve a sub-mesh to its named ancestor, the same walk the room does.
        let obj = hits[0].object;
        while (obj && !norm(obj.name).startsWith('CTRY-')) obj = obj.parent;
        if (!obj) return;

        const slug = norm(obj.name).slice(5);
        const country = countryBySlug[slug];
        if (!country) {
            console.warn('[gallery] clicked a country mesh with no data:', obj.name);
            return;
        }
        // One city is the common case, so skip a pointless intermediate view.
        if (country.cities.length === 1) enterCity(country.cities[0]);
        else showCityChoices(country);
    }

    function showCityChoices(country) {
        if (!filmstripEl) return;
        if (titleEl) titleEl.textContent = country.name;
        if (backEl) backEl.hidden = false;
        filmstripEl.hidden = false;

        const frag = document.createDocumentFragment();
        for (const slug of country.cities) {
            const city = cityBySlug[slug];
            if (!city) continue;
            const btn = document.createElement('button');
            btn.className = 'gallery-city-chip';
            btn.textContent = city.name;
            btn.addEventListener('click', () => enterCity(slug));
            frag.appendChild(btn);
        }
        filmstripEl.replaceChildren(frag);
    }

    // ---- loop -------------------------------------------------------------

    function resize() {
        if (!renderer) return;
        const r = stageEl.getBoundingClientRect();
        if (r.width < 2 || r.height < 2) return;
        renderer.setPixelRatio(renderScale());
        renderer.setSize(r.width, r.height, false);
        camera.aspect = r.width / r.height;
        camera.updateProjectionMatrix();
    }

    function tick() {
        raf = requestAnimationFrame(tick);
        if (!open) return;
        resize();
        renderer.render(scene, camera);
    }

    // ---- public surface ---------------------------------------------------

    return {
        open() {
            ensureRenderer();
            open = true;
            showWorld();
            resize();
            if (!raf) tick();
        },
        close() {
            open = false;
            if (raf) { cancelAnimationFrame(raf); raf = null; }
            // Give the city's textures back on close: the modal may sit unopened
            // for the rest of the session.
            detachCity();
        },
        showWorld,
        goCity: enterCity,
        isOpen: () => open,
        stats: () => renderer?.info.memory ?? null,
        dispose() {
            this.close();
            if (worldGroup) disposeObject3D(worldGroup);
            highlightMat?.dispose();
            dracoLoader?.dispose();      // only here: doing it after city #1 would
            renderer?.dispose();         // kill the decoder before city #2
            renderer = null;
        },
    };
}
