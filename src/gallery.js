// ============================================================================
// The travel gallery
// ----------------------------------------------------------------------------
// Lives inside the existing "Traveling" modal. Three layers:
//
//   WORLD  an SVG world map. Real country outlines, visited ones lit up and
//     |    clickable. SVG rather than 3D: a map is flat, vectors stay crisp at
//     |    any size, hit-testing is the browser's job, and every country is a
//     |    real focusable element so the keyboard works for free.
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
// Only the city layer is 3D. The renderer there is a SECOND WebGL context,
// separate from the room's. The
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
import { COUNTRY_PATHS, MAP_WIDTH, MAP_HEIGHT } from './data/world-map.js';

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

    let mapEl = null;        // the SVG world map (world view)
    let canvasEl = null;     // the WebGL canvas (city view)
    let cityGroup = null;
    let cityRoot = null;
    let buildingMeshes = [];

    // Made once, reused forever. Cloning a material per hover leaks one material
    // per event, which is thousands over a session; swapping which material a
    // mesh points at allocates nothing.
    let highlightMat = null;

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
        canvas.hidden = true;          // the map owns the stage until a city opens
        stageEl.appendChild(canvas);
        canvasEl = canvas;

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

        cityGroup = new THREE.Group();
        scene.add(cityGroup);

        highlightMat = new THREE.MeshBasicMaterial({ color: HIGHLIGHT_COLOR });

        dracoLoader = new DRACOLoader();
        dracoLoader.setDecoderPath('draco/');
        gltfLoader = new GLTFLoader();
        gltfLoader.setDRACOLoader(dracoLoader);

    }

    // Touch devices get a lower render resolution for the same reason the room
    // does: a dpr-3 framebuffer plus textures is what crashes mobile Safari.
    function renderScale() {
        const coarse = window.matchMedia('(pointer: coarse)').matches;
        return Math.min(window.devicePixelRatio, coarse ? 1.1 : 1.5);
    }

    // ---- world layer ------------------------------------------------------

    // The map is drawn once as SVG and then just shown or hidden. Every country
    // in the world is drawn, so the visited ones read as picked out of a real
    // map rather than floating alone; only the visited ones are interactive.
    function buildWorld() {
        if (mapEl) return mapEl;

        const visited = new Map(countries.map((c) => [c.iso, c]));
        const svgNS = 'http://www.w3.org/2000/svg';
        const svg = document.createElementNS(svgNS, 'svg');
        svg.setAttribute('viewBox', `0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`);
        svg.setAttribute('class', 'gallery-map');
        svg.setAttribute('role', 'group');
        svg.setAttribute('aria-label', 'World map. Countries visited are highlighted and can be opened.');

        // Everything unvisited first, as one flat backdrop layer.
        const base = document.createElementNS(svgNS, 'g');
        base.setAttribute('class', 'gallery-map-base');
        for (const [iso, entry] of Object.entries(COUNTRY_PATHS)) {
            if (visited.has(iso)) continue;
            const path = document.createElementNS(svgNS, 'path');
            path.setAttribute('d', entry.d);
            base.appendChild(path);
        }
        svg.appendChild(base);

        // Visited countries on top, each a real button so the keyboard reaches
        // it and hit-testing is the browser's problem rather than a raycast.
        const live = document.createElementNS(svgNS, 'g');
        live.setAttribute('class', 'gallery-map-live');
        for (const c of countries) {
            const entry = COUNTRY_PATHS[c.iso];
            if (!entry) {
                console.warn(`[gallery] no map shape for ${c.name} (iso ${c.iso})`);
                continue;
            }
            const path = document.createElementNS(svgNS, 'path');
            path.setAttribute('d', entry.d);
            path.setAttribute('class', 'gallery-country');
            path.setAttribute('tabindex', '0');
            path.setAttribute('role', 'button');
            path.setAttribute('aria-label', `${c.name}. ${c.blurb || ''}`.trim());
            path.dataset.slug = c.slug;

            const title = document.createElementNS(svgNS, 'title');
            title.textContent = c.name;
            path.appendChild(title);

            const enter = () => openCountry(c.slug);
            path.addEventListener('click', enter);
            path.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); enter(); }
            });
            live.appendChild(path);
        }
        svg.appendChild(live);

        mapEl = svg;
        stageEl.appendChild(svg);
        return svg;
    }

    function openCountry(slug) {
        const country = countryBySlug[slug];
        if (!country) return;
        // One city is the common case, so skip a pointless intermediate view.
        if (country.cities.length === 1) enterCity(country.cities[0]);
        else showCityChoices(country);
    }

    function showWorld() {
        view = VIEW.WORLD;
        detachCity();
        buildWorld();
        if (mapEl) mapEl.classList.remove('is-hidden');
        if (canvasEl) canvasEl.hidden = true;
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
        ensureRenderer();   // first city of the session pays for the context

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
        // Hand the stage over to the 3D canvas for the city view. `view` has to
        // flip before resize(), which no-ops while the canvas is hidden, and
        // the canvas has to be sized before the first render or it stays 0x0.
        if (mapEl) mapEl.classList.add('is-hidden');
        if (canvasEl) canvasEl.hidden = false;
        cityGroup.add(root);
        cityRoot = root;
        buildingMeshes = prepareCity(root, city);
        activeCity = slug;
        view = VIEW.CITY;
        resize();

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
        if (!renderer || !canvasEl || canvasEl.hidden) return;
        const r = stageEl.getBoundingClientRect();
        if (r.width < 2 || r.height < 2) return;
        renderer.setPixelRatio(renderScale());
        renderer.setSize(r.width, r.height, false);
        camera.aspect = r.width / r.height;
        camera.updateProjectionMatrix();
    }

    function tick() {
        raf = requestAnimationFrame(tick);
        // Nothing to draw while the SVG map owns the stage: the canvas is
        // hidden, so rendering into it is pure waste.
        if (!open || view !== VIEW.CITY || !renderer) return;
        resize();
        renderer.render(scene, camera);
    }

    // ---- public surface ---------------------------------------------------

    return {
        open() {
            // No renderer yet: the world view is SVG, so a visitor who only
            // looks at the map never creates a WebGL context at all.
            open = true;
            showWorld();
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
            highlightMat?.dispose();
            dracoLoader?.dispose();      // only here: doing it after city #1 would
            renderer?.dispose();         // kill the decoder before city #2
            renderer = null;
        },
    };
}
