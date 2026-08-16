import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { OutlinePass } from 'three/addons/postprocessing/OutlinePass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import gsap from "gsap";
import { createRoomCube } from './room-cube.js';
import { initNotebook } from './notebook.js';

const canvas = document.querySelector("#experience-canvas");
const sizes = {
    width: window.innerWidth,
    height: window.innerHeight,
};

// One manager tracks the GLB AND the textures, so onLoad means "everything in".
const manager = new THREE.LoadingManager();

const textureLoader = new THREE.TextureLoader(manager);

const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath('draco/');

const loader = new GLTFLoader(manager);
loader.setDRACOLoader(dracoLoader);

const modals = {
    aboutme: document.querySelector(".modal.aboutme"),
    projects: document.querySelector(".modal.projects"),
    notebook: document.querySelector(".modal.notebook"),
    map: document.querySelector(".modal.map"),
    jersey: document.querySelector(".modal.jersey"),
    board: document.querySelector(".modal.board")
}

let touchHappened = false;
let isModalOpen = false;

// One consistent "touch-like" test for the touch-only affordances (beacons,
// tap forgiveness, the tour's tap hint). Camera/layout keep the existing
// 768px width breakpoint so desktop framing is untouched.
const coarsePointerQuery = window.matchMedia("(pointer: coarse)");
const isTouchLike = () => coarsePointerQuery.matches;

// "Things I read and learn" — card grid + in-modal iframe reader (src/notebook.js)
initNotebook(modals.notebook);

// Modal interactions
document.querySelectorAll(".window-control").forEach(button => {
    const handleAction = (e) => {
        e.preventDefault();
        e.stopPropagation();
        const modal = button.closest(".modal");
        
        if (button.classList.contains('close')) {
            hideModal(modal);
        } else if (button.classList.contains('maximize')) {
            modal.classList.toggle('maximized');
        }
    };

    button.addEventListener("touchend", (e) => {
        touchHappened = true;
        handleAction(e);
    }, { passive: false });

    button.addEventListener("click", (e) => {
        if (touchHappened) return;
        handleAction(e);
    }, { passive: false });
})

const showModal = (modal) => {
    isModalOpen = true;
    modal.style.display = "block";

    gsap.set(modal, { opacity: 0 });

    gsap.to(modal, {
        opacity: 1,
        duration: 0.5,
    });
}

const hideModal = (modal) => {
    gsap.to(modal, {
        opacity: 0,
        duration: 0.5,
        onComplete: () => {
            modal.style.display = "none";
            modal.classList.remove('maximized');
            isModalOpen = false;
        }
    });
}

// ---------------------------------------------------------------------------
// Ticket board (opened by the iPad)
// Reads public/tickets.json — produced at build time from the Obsidian vault by
// scripts/build-tickets.js, which already filtered out private tickets.
//
// Two tabs: Stories (projects → milestones → tickets) and Board (Kanban).
// Cards expand on click. Drag-and-drop is a READ view for visitors; it only
// unlocks after the owner authenticates (Cmd/Ctrl+Shift+E → password prompt →
// dev-only /__tickets/login exchanges the password in .env for a session
// token). The token lives in localStorage, never in the URL, and is sent with
// every /__tickets/update call, which persists the new status straight to the
// vault .md. Neither endpoint exists in the production build.
// ---------------------------------------------------------------------------
const BOARD_COLUMNS = [
    { key: "backlog", label: "Backlog" },
    { key: "todo", label: "To Do" },
    { key: "doing", label: "In Progress" },
    { key: "done", label: "Done" },
];

// A soft, glass-friendly palette. Projects are assigned a color by their order in
// the data so the mapping is stable across renders (Old Trafford always the same
// hue, etc.). Colors are used at low opacity as pill backgrounds — no neon.
const PROJECT_COLORS = [
    "#7dd3fc", // sky blue
    "#fca5a5", // coral
    "#6ee7b7", // mint
    "#fcd34d", // amber
    "#c4b5fd", // lilac
    "#f9a8d4", // pink
    "#93c5fd", // periwinkle
    "#fdba74", // orange
];

let projectColorMap = null;

// Build a stable project → color map from the tickets, once per data load.
function getProjectColor(project) {
    if (!projectColorMap) {
        projectColorMap = {};
        const order = boardData?.projects
            ? Object.keys(boardData.projects)
            : [...new Set((boardData?.tickets || []).map((t) => t.project).filter(Boolean))];
        order.forEach((slug, i) => {
            projectColorMap[slug] = PROJECT_COLORS[i % PROJECT_COLORS.length];
        });
    }
    return projectColorMap[project] || "#9ca3af";
}

const EDIT_TOKEN_STORAGE_KEY = "tickets-edit-token";
let editToken = localStorage.getItem(EDIT_TOKEN_STORAGE_KEY);

function isEditMode() {
    return Boolean(editToken);
}

let boardData = null;      // cached tickets.json payload
let boardLoading = null;   // in-flight fetch promise
let boardView = "stories"; // "stories" | "board"
let activeStory = null;    // project slug when drilled into a story

function escapeHtml(str) {
    return String(str ?? "").replace(/[&<>"']/g, (c) => (
        { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
    ));
}

function loadBoardData() {
    if (boardData) return Promise.resolve(boardData);
    if (boardLoading) return boardLoading;
    boardLoading = fetch("tickets.json", { cache: "no-store" })
        .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.status))))
        .then((data) => { boardData = data; projectColorMap = null; return data; })
        .catch((err) => {
            console.error("Failed to load tickets.json:", err);
            // Do NOT cache the failure: clear boardLoading so the next open retries
            // instead of being stuck on a permanently-empty board.
            boardLoading = null;
            throw err;
        });
    return boardLoading;
}

// ---- Card rendering -------------------------------------------------------

function renderTicketCard(t, showProject = false) {
    const detail = `
        <div class="ticket-detail">
            ${t.done_when ? `<p class="ticket-detail-row"><span class="ticket-detail-label">Done when</span>${escapeHtml(t.done_when)}</p>` : ""}
            ${t.project ? `<p class="ticket-detail-row"><span class="ticket-detail-label">Project</span>${escapeHtml(t.project)}</p>` : ""}
            ${t.milestone ? `<p class="ticket-detail-row"><span class="ticket-detail-label">Milestone</span>${escapeHtml(t.milestone)}</p>` : ""}
            ${Array.isArray(t.blocks) && t.blocks.length ? `<p class="ticket-detail-row"><span class="ticket-detail-label">Blocks</span>${t.blocks.map(escapeHtml).join(", ")}</p>` : ""}
        </div>`;
    // Colored project pill — shown on the Board tab (mixed columns) so you can tell
    // at a glance which project a card belongs to. Redundant in a story's own view.
    const pill = showProject && t.project
        ? `<span class="ticket-project" style="--proj:${getProjectColor(t.project)}">${escapeHtml(t.project)}</span>`
        : "";
    return `
        <div class="ticket-card ${t.status === "done" ? "is-done" : ""}"
             data-id="${escapeHtml(t.id)}"
             data-status="${escapeHtml(t.status || "")}">
            <div class="ticket-top">
                <span class="ticket-id">${escapeHtml(t.id)}</span>
                <span class="ticket-cat">${escapeHtml(t.category || "")}</span>
            </div>
            <p class="ticket-title">${escapeHtml(t.title)}</p>
            ${pill}
            ${detail}
        </div>`;
}

// ---- Board (Kanban) tab ---------------------------------------------------

function renderBoardView(tickets) {
    if (tickets.length === 0) {
        return `<div class="board-empty">No public tickets yet. Add some to the vault's Tickets/ folder and rebuild.</div>`;
    }
    return `<div class="board-columns" id="board-columns">${
        BOARD_COLUMNS.map((col) => {
            const items = tickets.filter((t) => t.status === col.key);
            const cards = items.length
                ? items.map((t) => renderTicketCard(t, true)).join("")
                : `<div class="board-column-empty">—</div>`;
            return `
                <div class="board-column" data-status="${col.key}">
                    <div class="board-column-head">
                        <span class="board-column-name">${col.label}</span>
                        <span class="board-column-count">${items.length}</span>
                    </div>
                    ${cards}
                </div>`;
        }).join("")
    }</div>`;
}

// ---- Stories tab ----------------------------------------------------------

function groupByProject(tickets) {
    const map = new Map();
    for (const t of tickets) {
        const key = t.project || "misc";
        if (!map.has(key)) map.set(key, []);
        map.get(key).push(t);
    }
    return map;
}

function renderStoriesList(tickets) {
    const groups = groupByProject(tickets);
    if (groups.size === 0) {
        return `<div class="board-empty">No stories yet.</div>`;
    }
    const cards = [...groups.entries()].map(([project, items]) => {
        const done = items.filter((t) => t.status === "done").length;
        const pct = items.length ? Math.round((done / items.length) * 100) : 0;
        return `
            <div class="story-card" data-project="${escapeHtml(project)}">
                <p class="story-name">${escapeHtml(project)}</p>
                <p class="story-meta">${items.length} ticket${items.length === 1 ? "" : "s"}</p>
                <div class="story-progress"><div class="story-progress-fill" style="width:${pct}%"></div></div>
                <span class="story-progress-label">${done}/${items.length} done</span>
            </div>`;
    }).join("");
    return `<div class="stories-grid">${cards}</div>`;
}

function renderStoryDetail(tickets, project) {
    const items = tickets.filter((t) => (t.project || "misc") === project);

    // Group this project's tickets by their milestone.
    const byMilestone = new Map();
    for (const t of items) {
        const key = t.milestone || "—";
        if (!byMilestone.has(key)) byMilestone.set(key, []);
        byMilestone.get(key).push(t);
    }

    // The ordered phase roadmap comes from the project note (tickets.json.projects).
    // Show EVERY phase in order — Phase 1, 2, 3... — including ones with no tickets
    // yet (rendered as "upcoming"), so the whole sequence is visible. Any milestone
    // that has tickets but isn't in the roadmap gets appended so nothing is lost.
    const roadmap = (boardData.projects && boardData.projects[project]?.milestones) || [];
    const seen = new Set();
    const phaseOrder = [];
    for (const name of roadmap) { phaseOrder.push(name); seen.add(name); }
    for (const name of byMilestone.keys()) { if (!seen.has(name)) phaseOrder.push(name); }

    const blocks = phaseOrder.map((milestone, i) => {
        const mtickets = byMilestone.get(milestone) || [];
        const upcoming = mtickets.length === 0;
        const body = upcoming
            ? `<div class="phase-upcoming">Not started yet</div>`
            : `<div class="milestone-tickets">${mtickets.map((t) => renderTicketCard(t)).join("")}</div>`;
        return `
            <div class="milestone-block ${upcoming ? "is-upcoming" : ""}">
                <div class="milestone-head">
                    <span class="phase-badge">Phase ${i + 1}</span>
                    <span class="milestone-name">${escapeHtml(milestone)}</span>
                    ${upcoming ? "" : `<span class="milestone-count">${mtickets.length} ticket${mtickets.length === 1 ? "" : "s"}</span>`}
                </div>
                ${body}
            </div>`;
    }).join("");

    return `
        <div class="story-detail-head">
            <button class="story-back" id="story-back">← Stories</button>
            <h2 class="story-detail-name">${escapeHtml(project)}</h2>
        </div>
        ${blocks}`;
}

// ---- Top-level render + wiring --------------------------------------------

function renderBoard(data) {
    const tickets = (data && data.tickets) || [];
    const viewEl = document.getElementById("board-view");
    if (!viewEl) return;

    // Edit badge + editable class only in edit mode.
    const badge = document.getElementById("board-edit-badge");
    if (badge) badge.style.display = isEditMode() ? "" : "none";
    modals.board.classList.toggle("editable", isEditMode());

    // Tab active state
    document.querySelectorAll(".board-tab").forEach((b) =>
        b.classList.toggle("active", b.dataset.view === boardView)
    );

    if (boardView === "board") {
        viewEl.innerHTML = renderBoardView(tickets);
        if (isEditMode()) wireDragAndDrop();
    } else if (activeStory) {
        viewEl.innerHTML = renderStoryDetail(tickets, activeStory);
    } else {
        viewEl.innerHTML = renderStoriesList(tickets);
    }
}

// Card expand (click), story navigation, and tabs — one delegated listener.
function wireBoardInteractions() {
    const viewEl = document.getElementById("board-view");
    const tabsEl = document.getElementById("board-tabs");
    if (!viewEl || viewEl.dataset.wired) return;
    viewEl.dataset.wired = "1";

    tabsEl.addEventListener("click", (e) => {
        const tab = e.target.closest(".board-tab");
        if (!tab) return;
        boardView = tab.dataset.view;
        if (boardView === "stories") activeStory = null;
        renderBoard(boardData);
    });

    viewEl.addEventListener("click", (e) => {
        // Back out of a story
        if (e.target.closest("#story-back")) {
            activeStory = null;
            renderBoard(boardData);
            return;
        }
        // Open a story
        const story = e.target.closest(".story-card");
        if (story) {
            activeStory = story.dataset.project;
            renderBoard(boardData);
            return;
        }
        // Expand/collapse a ticket card — but not the click that follows a drag.
        if (suppressNextCardClick) {
            suppressNextCardClick = false;
            return;
        }
        const card = e.target.closest(".ticket-card");
        if (card) card.classList.toggle("expanded");
    });
}

// ---- Drag-and-drop (edit mode only) ----------------------------------------
// Pointer-based, not native HTML5 drag: native drag hands the card's visual
// off to the browser (an opaque, jittery ghost image with no control over
// easing), which is what read as "not smooth." Driving position with
// pointermove instead means the card is a real DOM element we can transform
// every frame — it tracks the cursor exactly and eases into place on drop.

let dragState = null; // { id, card, startX, startY, offsetX, offsetY, placeholder }
let suppressNextCardClick = false; // set when a real drag happens, so the trailing click doesn't also expand the card

function wireDragAndDrop() {
    document.querySelectorAll(".ticket-card").forEach((card) => {
        card.addEventListener("pointerdown", onCardPointerDown);
    });
}

function onCardPointerDown(e) {
    // Only the primary button/touch, and not on an already-expanded card
    // (expanded cards show detail text that should stay selectable/clickable).
    if (e.button !== undefined && e.button !== 0) return;
    const card = e.currentTarget;
    if (card.classList.contains("expanded")) return;

    const rect = card.getBoundingClientRect();
    const startX = e.clientX;
    const startY = e.clientY;
    const offsetX = startX - rect.left;
    const offsetY = startY - rect.top;

    // Don't start a real drag until the pointer has moved a few pixels —
    // this preserves plain clicks (which expand the card) from becoming drags.
    let dragging = false;
    let placeholder = null;

    function onMove(ev) {
        const dx = ev.clientX - startX;
        const dy = ev.clientY - startY;

        if (!dragging) {
            if (Math.hypot(dx, dy) < 6) return;
            dragging = true;

            // Freeze the card's size, lift it out of layout, and leave a
            // same-sized placeholder so the column doesn't jump.
            placeholder = document.createElement("div");
            placeholder.className = "ticket-placeholder";
            placeholder.style.height = `${rect.height}px`;
            card.parentElement.insertBefore(placeholder, card);

            card.classList.add("is-dragging");
            card.style.width = `${rect.width}px`;
            card.style.left = `${rect.left}px`;
            card.style.top = `${rect.top}px`;
            document.body.appendChild(card);

            dragState = { id: card.dataset.id, card, offsetX, offsetY, placeholder };
        }

        card.style.left = `${ev.clientX - offsetX}px`;
        card.style.top = `${ev.clientY - offsetY}px`;

        const col = document.elementFromPoint(ev.clientX, ev.clientY)?.closest(".board-column");
        document.querySelectorAll(".board-column.drop-target").forEach((c) => {
            if (c !== col) c.classList.remove("drop-target");
        });
        if (col) col.classList.add("drop-target");
    }

    function onUp(ev) {
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);

        if (!dragging) return;
        suppressNextCardClick = true;

        const originalStatus = card.dataset.status;
        const col = document.elementFromPoint(ev.clientX, ev.clientY)?.closest(".board-column");
        document.querySelectorAll(".board-column.drop-target").forEach((c) => c.classList.remove("drop-target"));

        // If dropped on a different column, move the placeholder there first —
        // that's what makes the column reflow and gives us the real landing spot.
        if (col) col.appendChild(placeholder);
        const settleRect = placeholder.getBoundingClientRect();

        // Ease the card from the cursor position into the placeholder's spot,
        // then swap it back into normal flow and let the real re-render take over.
        card.style.transition = "left 0.18s cubic-bezier(0.2, 0.8, 0.2, 1), top 0.18s cubic-bezier(0.2, 0.8, 0.2, 1), transform 0.18s ease";
        card.style.left = `${settleRect.left}px`;
        card.style.top = `${settleRect.top}px`;
        card.style.transform = "scale(1) rotate(0deg)";

        const newStatus = col ? col.dataset.status : originalStatus;

        setTimeout(() => {
            card.style.transition = "";
            card.style.width = "";
            card.style.left = "";
            card.style.top = "";
            card.style.transform = "";
            card.classList.remove("is-dragging");
            placeholder.remove();
            dragState = null;
            if (newStatus !== originalStatus) {
                moveTicket(card.dataset.id, newStatus);
            } else {
                renderBoard(boardData); // snap back to its original spot
            }
        }, 180);
    }

    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
}

// Persist a status change to the vault via the dev-only endpoint, then re-render.
function moveTicket(id, newStatus) {
    const ticket = boardData.tickets.find((t) => t.id === id);
    if (!ticket || ticket.status === newStatus) return;

    const previous = ticket.status;
    ticket.status = newStatus; // optimistic
    renderBoard(boardData);

    fetch("/__tickets/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, status: newStatus, token: editToken }),
    })
        .then((r) => {
            if (!r.ok) throw new Error(r.status);
        })
        .catch((err) => {
            console.error("Failed to persist move, reverting:", err);
            ticket.status = previous; // roll back on failure
            renderBoard(boardData);
        });
}

// ---- Edit-mode authentication -----------------------------------------------
// No key in the URL. Cmd/Ctrl+Shift+E prompts for the password (kept only in
// .env, never shipped to the client); a correct password exchanges it for a
// session token via /__tickets/login. The token — not the password — is what
// lives in localStorage and travels with each /__tickets/update call.

async function tryEnableEditMode() {
    const password = window.prompt("Edit password:");
    if (!password) return;
    try {
        const res = await fetch("/__tickets/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ password }),
        });
        if (!res.ok) {
            window.alert("Wrong password.");
            return;
        }
        const { token } = await res.json();
        editToken = token;
        localStorage.setItem(EDIT_TOKEN_STORAGE_KEY, token);
        if (boardData) renderBoard(boardData);
    } catch (err) {
        console.error("Edit login failed:", err);
        window.alert("Couldn't reach the edit endpoint (is `npm run dev` running?).");
    }
}

window.addEventListener("keydown", (e) => {
    const isShortcut = (e.metaKey || e.ctrlKey) && e.shiftKey && e.key.toLowerCase() === "e";
    if (isShortcut) {
        e.preventDefault();
        tryEnableEditMode();
    }
});

function openBoard() {
    showModal(modals.board);
    const hydrate = (data) => {
        renderBoard(data);
        wireBoardInteractions();
    };
    if (boardData) {
        hydrate(boardData);
    } else {
        // Show the loading state that's already in the DOM, then hydrate on arrival.
        loadBoardData()
            .then(hydrate)
            .catch(() => {
                const viewEl = document.getElementById("board-view");
                if (viewEl) {
                    viewEl.innerHTML =
                        `<div class="board-empty">Couldn't load tickets. If you're running locally, make sure the dev server is up, then reopen.</div>`;
                }
            });
    }
}

let manchesterObject = null;
let roomCube = null; // live Rubik's cube replacing the baked prop (see room-cube.js)

const clickableObjects = ["macbook", "notebook_2", "map", "ggb", "jersey", "manchester", "aboutme",
    "projects", "resume", "almaty", "vynil", "book_pink", "book_brown", "book_black", "ball", "rock",
    "candle", "ipad", "rubik", "tulips", "ole", "kzchoco", "apple-pencil"];
const raycasterObjects = [];

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();

// Touch tap forgiveness: when the primary raycast misses, retry in a small
// screen-space cross around the tap (px offsets, converted to NDC) and accept
// the first hit. Desktop clicks never enter this path and stay exact.
const TOUCH_RETRY_OFFSETS_PX = [[14, 0], [-14, 0], [0, 14], [0, -14]];

const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });
renderer.outputColorSpace = THREE.SRGBColorSpace;

renderer.setSize(sizes.width, sizes.height);
renderer.setClearColor(0x000000);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

const scene = new THREE.Scene();

const camera = new THREE.PerspectiveCamera(45, sizes.width / sizes.height, 1, 1000);

// ---- Mobile close-up framing ------------------------------------------------
// The old mobile default (distance ~30 at fov 60) rendered the room tiny on
// phones. Once the GLB is in we measure the union box of the interactive
// desk/shelf region and derive the camera distance that fits its bounding
// sphere in BOTH the vertical and the horizontal fov at the current aspect
// (portrait's limiting axis is the horizontal one), approaching along the same
// view direction as the old default. Recomputed on resize/orientation change.
const MOBILE_FOV = 60;
const MOBILE_BASE_POSITION = new THREE.Vector3(-15, 11.5, 30);
const MOBILE_BASE_TARGET = new THREE.Vector3(0, 2.5, 0);
const FOCUS_OBJECT_KEYS = ["aboutme", "projects", "resume", "macbook", "notebook_2", "rubik"];

let mobileFocusView = null; // { position, target, distance, headroom }; null on desktop / pre-load

function computeMobileFocusView() {
    if (sizes.width >= 768 || raycasterObjects.length === 0) {
        mobileFocusView = null;
        return;
    }
    scene.updateMatrixWorld(true);
    const box = new THREE.Box3();
    let found = false;
    raycasterObjects.forEach((o) => {
        if (FOCUS_OBJECT_KEYS.some((key) => o.name.includes(key))) {
            box.expandByObject(o);
            found = true;
        }
    });
    if (!found) { mobileFocusView = null; return; }
    box.expandByScalar(0.4); // a little breathing room around the desk/shelf

    const center = box.getCenter(new THREE.Vector3());
    const radius = box.getBoundingSphere(new THREE.Sphere()).radius;
    const vFov = THREE.MathUtils.degToRad(MOBILE_FOV);
    const hFov = 2 * Math.atan(Math.tan(vFov / 2) * (sizes.width / sizes.height));
    // The larger of the two required fit distances wins (portrait → horizontal).
    const distance = Math.max(
        radius / Math.tan(vFov / 2),
        radius / Math.tan(hFov / 2)
    ) * 1.08;
    const dir = MOBILE_BASE_POSITION.clone().sub(MOBILE_BASE_TARGET).normalize();
    const position = center.clone().add(dir.multiplyScalar(distance));
    // Vertical headroom left above the region at this distance — used to cap
    // the Rubik's cube jump so it can't leave the closer frame.
    const headroom = distance * Math.tan(vFov / 2) - (box.max.y - center.y);
    mobileFocusView = { position, target: center, distance, headroom };
}

// Camera and target y are both raised 1.5 from the original framing (7/10 and 1),
// which slides the whole room lower on screen without changing the viewing angle
// (equivalent to shifting the model down).
function getDefaultView() {
    if (sizes.width < 768) {
        return mobileFocusView
            ? { fov: MOBILE_FOV, position: mobileFocusView.position.clone(), target: mobileFocusView.target.clone() }
            : { fov: MOBILE_FOV, position: MOBILE_BASE_POSITION.clone(), target: MOBILE_BASE_TARGET.clone() };
    }
    return { fov: 45, position: new THREE.Vector3(-10, 8.5, 20), target: new THREE.Vector3(0, 2.5, 0) };
}

function updateCameraForScreenSize() {
    const view = getDefaultView();
    camera.fov = view.fov;
    camera.position.copy(view.position);
    // The measured mobile framing also re-aims the target at the desk region
    // (never mid-tour — the tour's own tweens own the target then).
    if (sizes.width < 768 && mobileFocusView && !tourActive) {
        controls.target.copy(view.target);
    }
    camera.updateProjectionMatrix();
}

updateCameraForScreenSize();


const textureMap = {
    aboutme: "textures/palka-texture.webp",
    projects: "textures/palka-texture.webp",
    Cylinder: "textures/wall.webp",
    book_black: "textures/black-book-texture.webp",
    book_brown: "textures/brown-book.webp",
    book_pink: "textures/book-pink-texture.webp",
    goal_tor: "textures/goal-tor.webp",
    notebook_2: "textures/notebook-2-texture.webp",
    rock_1: "textures/rock-1.webp",
    rock_2: "textures/rock-2.webp",
    background: "textures/background-texture.webp",
    ball: "textures/ball.webp",
    bed: "textures/bed.webp",
    candle: "textures/candle.webp",
    floor: "textures/floor-texture.webp",
    'frame-1': "textures/frame-1-texture.webp",
    'frame-2': "textures/frames-texture.webp",
    'frame-3': "textures/frames-texture.webp",
    'frame-4': "textures/frames-texture.webp",
    'frame-5': "textures/frames-texture.webp",
    goalpost: "textures/goalpost.webp",
    grass: "textures/grass-small.webp",
    'grass-2': "textures/grass-small.webp",
    ipad: "textures/ipad.webp",
    macbook: "textures/mac-texture.webp",
    shelf: "textures/shelf-texture.webp",
    vynil: "textures/shelf-texture.webp",
    notebook_1: "textures/notebook-texture.webp",
    palka: "textures/palka-texture.webp",
    pillow: "textures/pillow-texture.webp",
    resume: "textures/resume-texture.webp",
    roof: "textures/roof-texture.webp",
    rubik: "textures/rubik-texture.webp",
    rug: "textures/rug.webp",
    table: "textures/table-texture.webp",
    tulips: "textures/tulips.webp",
    vase: "textures/vase-texture.webp",
    wall: "textures/wall.webp",
    field: "textures/roof-texture.webp",
    chair: "textures/table-texture.webp",
    'chair-wheel': "textures/ipad.webp",
    phone: "textures/ipad.webp",
    'bruno-frame': "textures/ipad.webp",
    almaty: "textures/almaty.webp",
    manchester: "textures/bruno.webp",
    lingard: "textures/lingard.webp",
    ole: "textures/ole.webp",
    kzchoco: "textures/kzchoco.webp",
    map: "textures/map.webp",
    'never-gonna-stop': "textures/tifo.webp",
    ggb: "textures/ggb.webp",
    jersey: "textures/jersey.webp",
    'apple-pencil': "textures/mac-texture.webp"
}

const loadedTextures = {};

Object.entries(textureMap).forEach(([key, path]) => {
    const texture = textureLoader.load(path);
    texture.flipY = false;
    texture.colorSpace = THREE.SRGBColorSpace;
    loadedTextures[key] = texture;
});

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.enablePan = false;
controls.minDistance = 5;
controls.maxDistance = 20;
controls.minAzimuthAngle = -Math.PI / 2;
controls.maxAzimuthAngle = 0;
controls.minPolarAngle = 0;
controls.maxPolarAngle = Math.PI / 2;
controls.autoRotate = false;
controls.target = getDefaultView().target.clone();
controls.update();

// Mobile: enable two-finger pan and wider view range
// Clamp pan range so user can't drift too far. Named so re-applying on resize
// never stacks duplicate listeners (EventDispatcher dedupes same references).
const clampMobilePanTarget = () => {
    const target = controls.target;
    target.x = Math.max(-6, Math.min(6, target.x));
    target.y = Math.max(0, Math.min(6, target.y));
    target.z = Math.max(-6, Math.min(6, target.z));
};

function applyMobileControls() {
    if (window.innerWidth < 768) {
        controls.enablePan = true;
        controls.touches = {
            ONE: THREE.TOUCH.ROTATE,
            TWO: THREE.TOUCH.DOLLY_PAN
        };
        // Never let minDistance block the closer measured default framing.
        controls.minDistance = mobileFocusView
            ? Math.min(4, mobileFocusView.distance * 0.6)
            : 4;
        controls.maxDistance = 28;
        controls.minAzimuthAngle = -Math.PI * 0.75;
        controls.maxAzimuthAngle = Math.PI * 0.15;
        controls.panSpeed = 0.8;

        controls.addEventListener('change', clampMobilePanTarget);
    } else {
        controls.removeEventListener('change', clampMobilePanTarget);
        controls.enablePan = false;
        controls.minDistance = 5;
        controls.maxDistance = 20;
        controls.minAzimuthAngle = -Math.PI / 2;
        controls.maxAzimuthAngle = 0;
    }
}
applyMobileControls();

const groundGeometry = new THREE.CircleGeometry(12, 64);
groundGeometry.rotateX(-Math.PI / 2);
const groundMaterial = new THREE.MeshStandardMaterial({
    color: 0x70798c,
    side: THREE.DoubleSide
});

// Event listeners

window.addEventListener("mousemove", (e) => {
    touchHappened = false;
    pointer.x = (e.clientX / sizes.width) * 2 - 1;
    pointer.y = - (e.clientY / sizes.height) * 2 + 1;
});

window.addEventListener("touchstart", (e) => {
    // Floating UI (welcome card, hint button) handles its own touches.
    if (e.target.closest('.modal, .welcome-popup, .hint-button, .tour-tooltip')) return;
    e.preventDefault();
    pointer.x = (e.touches[0].clientX / sizes.width) * 2 - 1;
    pointer.y = - (e.touches[0].clientY / sizes.height) * 2 + 1;
}, { passive: false });

window.addEventListener("touchend", (e) => {
    // Don't intercept touches inside modals or the floating UI
    if (e.target.closest('.modal, .welcome-popup, .hint-button, .tour-tooltip')) return;
    e.preventDefault();
    handleRaycasterInteraction(e);
}, { passive: false });

function handleRaycasterInteraction(e) {
    // Clicks that land on the floating UI belong to its own handlers.
    if (e && e.target && e.target.closest && e.target.closest('.hint-button, .welcome-popup, .tour-tooltip')) return;
    if (isWelcomeOpen) {
        // Any click outside the welcome card dismisses it (and does nothing else).
        hideWelcome();
        return;
    }
    if (tourActive) {
        // During the tour a click advances to the next stop.
        advanceTour();
        return;
    }
    if (isModalOpen) return;
    raycaster.setFromCamera(pointer, camera);
    let currentIntersects = raycaster.intersectObjects(raycasterObjects);

    // Touch forgiveness: a fingertip is far wider than a pixel, so when a tap
    // narrowly misses, retry in a small cross around it and take the first hit.
    if (currentIntersects.length === 0 && e && e.type === "touchend") {
        const retryPointer = new THREE.Vector2();
        for (const [dx, dy] of TOUCH_RETRY_OFFSETS_PX) {
            retryPointer.set(
                pointer.x + (dx / sizes.width) * 2,
                pointer.y - (dy / sizes.height) * 2
            );
            raycaster.setFromCamera(retryPointer, camera);
            currentIntersects = raycaster.intersectObjects(raycasterObjects);
            if (currentIntersects.length > 0) break;
        }
    }

    if (currentIntersects.length > 0) {
        dismissBeacons(); // the visitor found something tappable — job done
        let object = currentIntersects[0].object;

        // Resolve sub-meshes (e.g. the live cube's unnamed cubies) to their
        // named clickable ancestor, mirroring the hover loop. GLB meshes are
        // named themselves, so the walk stops immediately for them.
        let temp = object;
        while (temp) {
            if (clickableObjects.some(objName => temp.name.includes(objName))) {
                object = temp;
                break;
            }
            temp = temp.parent;
        }

        playClickAnimation(object);

        if (object.name.includes("resume")) {
            window.open("Nazym Zhiyengaliyeva Resume.pdf", "_blank", "noopener,noreferrer");
        }

        if (object.name.includes("aboutme") || object.name.includes("ggb")) {
            showModal(modals.aboutme);
        } else if (object.name.includes("projects") || object.name.includes("macbook")) {
            showModal(modals.projects);
        } else if (object.name.includes("notebook")) {
            showModal(modals.notebook);
        } else if (object.name.includes("map")) {
            showModal(modals.map);
        } else if (object.name.includes("jersey") || object.name.includes("manchester")) {
            showModal(modals.jersey);
        } else if (object.name.includes("ipad")) {
            openBoard();
        }
    }
};

window.addEventListener("click", handleRaycasterInteraction);


// ---- Loading → reveal → welcome --------------------------------------------
// The canvas starts hidden (opacity 0, see .experience-canvas in CSS) behind a
// minimal dot-pulse loader. Once the LoadingManager reports everything in (GLB +
// textures), the loader fades away, the room fades up, the hint button appears,
// and the welcome card greets the visitor.
const loaderEl = document.getElementById("room-loader");
const welcomeEl = document.getElementById("welcome-popup");
const hintButton = document.getElementById("hint-button");
const tooltipEl = document.getElementById("tour-tooltip");

let isWelcomeOpen = false;

function showWelcome() {
    welcomeEl.style.display = "block";
    // xPercent keeps the card horizontally centered while gsap owns transform.
    gsap.set(welcomeEl, { xPercent: -50, y: 16, scale: 0.96, autoAlpha: 0 });
    gsap.to(welcomeEl, { y: 0, scale: 1, autoAlpha: 1, duration: 0.6, ease: "power3.out" });
    isWelcomeOpen = true;
}

function hideWelcome() {
    if (!isWelcomeOpen) return;
    isWelcomeOpen = false;
    showBeacons(); // touch-only "what can I tap?" dots (no-op on fine pointers)
    gsap.to(welcomeEl, {
        y: 10,
        scale: 0.97,
        autoAlpha: 0,
        duration: 0.35,
        ease: "power2.in",
        onComplete: () => { welcomeEl.style.display = "none"; },
    });
}

document.getElementById("welcome-close").addEventListener("click", (e) => {
    e.stopPropagation();
    hideWelcome();
});

document.getElementById("welcome-tour").addEventListener("click", (e) => {
    e.stopPropagation();
    hideWelcome();
    startTour();
});

let roomRevealed = false;
manager.onLoad = function () {
    if (roomRevealed) return;
    roomRevealed = true;
    gsap.to(loaderEl, {
        autoAlpha: 0,
        duration: 0.4,
        onComplete: () => loaderEl.remove(),
    });
    gsap.to(canvas, { opacity: 1, duration: 0.8, ease: "power2.out" });
    gsap.to(hintButton, { autoAlpha: 1, duration: 0.6, delay: 0.5 });
    gsap.delayedCall(0.9, showWelcome);
};

// ---- Guided tour ------------------------------------------------------------
// The "?" button flies the camera to the three main areas (about-me sign,
// projects sign, resume) in sequence, outlining each with a postprocessing
// OutlinePass so the focus is unmistakable. Clicking anywhere (or the auto
// timer) advances; Esc or the "?" again cancels and restores the default view.
// The composer is only used while the tour runs — the normal render path stays
// plain renderer.render().
const composer = new EffectComposer(renderer);
composer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
composer.setSize(sizes.width, sizes.height);
composer.addPass(new RenderPass(scene, camera));
const outlinePass = new OutlinePass(new THREE.Vector2(sizes.width, sizes.height), scene, camera);
outlinePass.edgeStrength = 4;
outlinePass.edgeGlow = 0.6;
outlinePass.edgeThickness = 1.5;
outlinePass.pulsePeriod = 2.5;
outlinePass.visibleEdgeColor.set("#ffffff");
outlinePass.hiddenEdgeColor.set("#4b5563");
composer.addPass(outlinePass);
composer.addPass(new OutputPass());

const TOUR_STOPS = [
    { key: "aboutme", title: "About Me", line: "Click the sign to learn who I am." },
    { key: "projects", title: "Projects", line: "My projects live on the MacBook." },
    { key: "resume", title: "Résumé", line: "Grab my resume here." },
];
const TOUR_FLIGHT_S = 1.2;   // camera flight per stop
const TOUR_HOLD_MS = 2700;   // dwell time once framed

let tourActive = false;
let tourIndex = -1;
let tourTimer = null;

function tourObjectsFor(key) {
    return raycasterObjects.filter((o) => o.name.includes(key));
}

// Frame an object from its world bounding box, approaching from the same side
// as the default view so the flight stays inside the OrbitControls angle window.
function frameForObjects(objects) {
    const box = new THREE.Box3();
    objects.forEach((o) => box.expandByObject(o));
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);
    // Fit the object in BOTH fovs: portrait's horizontal fov is narrower than
    // the vertical one, so the larger of the two required distances wins.
    // On landscape/desktop min(vFov, hFov) is the vertical fov — unchanged.
    const vFov = THREE.MathUtils.degToRad(camera.fov);
    const hFov = 2 * Math.atan(Math.tan(vFov / 2) * camera.aspect);
    const fitDist = (maxDim / 2) / Math.tan(Math.min(vFov, hFov) / 2);
    const distance = THREE.MathUtils.clamp(fitDist * 2.1, 4, camera.aspect < 1 ? 20 : 14);
    const dir = getDefaultView().position.clone().sub(center).normalize();
    const position = center.clone().add(dir.multiplyScalar(distance));
    // Stay above the target plane so the polar limit is never crossed.
    position.y = Math.max(position.y, center.y + 0.4);
    return { position, target: center };
}

function moveCamera(position, target, duration, onComplete) {
    gsap.killTweensOf(camera.position);
    gsap.killTweensOf(controls.target);
    gsap.to(camera.position, { x: position.x, y: position.y, z: position.z, duration, ease: "power2.inOut" });
    gsap.to(controls.target, { x: target.x, y: target.y, z: target.z, duration, ease: "power2.inOut", onComplete });
}

function showTooltip(title, line, showTapHint = false) {
    tooltipEl.querySelector(".tour-tooltip-title").textContent = title;
    tooltipEl.querySelector(".tour-tooltip-line").textContent = line;
    tooltipEl.querySelector(".tour-tooltip-hint").hidden = !showTapHint;
    tooltipEl.style.display = "block";
    gsap.killTweensOf(tooltipEl);
    gsap.set(tooltipEl, { xPercent: -50 });
    gsap.fromTo(tooltipEl, { autoAlpha: 0, y: 12 }, { autoAlpha: 1, y: 0, duration: 0.45, ease: "power3.out" });
}

function hideTooltip(fast = false) {
    gsap.killTweensOf(tooltipEl);
    gsap.to(tooltipEl, {
        autoAlpha: 0,
        y: 8,
        duration: fast ? 0.2 : 0.4,
        ease: "power2.in",
        onComplete: () => { tooltipEl.style.display = "none"; },
    });
}

function goToStop(index) {
    tourIndex = index;
    const stop = TOUR_STOPS[index];
    const objects = tourObjectsFor(stop.key);
    if (objects.length === 0) { // object missing from the GLB — skip the stop
        advanceTour();
        return;
    }
    outlinePass.selectedObjects = objects;
    const view = frameForObjects(objects);
    moveCamera(view.position, view.target, TOUR_FLIGHT_S);
    // First stop only, touch devices only: teach that a tap advances.
    showTooltip(stop.title, stop.line, index === 0 && isTouchLike());
    tourTimer = setTimeout(advanceTour, TOUR_FLIGHT_S * 1000 + TOUR_HOLD_MS);
}

// Final stop: fly home, clear the outline, leave a parting hint that fades out.
function finishTour() {
    tourIndex = TOUR_STOPS.length; // sentinel: past the last object stop
    outlinePass.selectedObjects = [];
    const view = getDefaultView();
    moveCamera(view.position, view.target, 1.4);
    showTooltip("Explore", "Click on things around the room for more about me.");
    tourTimer = setTimeout(() => endTour(false), 4200);
}

function advanceTour() {
    if (!tourActive) return;
    clearTimeout(tourTimer);
    const next = tourIndex + 1;
    if (next < TOUR_STOPS.length) goToStop(next);
    else if (tourIndex < TOUR_STOPS.length) finishTour();
    else endTour(false); // click during the final message dismisses it early
}

function startTour() {
    dismissBeacons(); // the tour explains the room better than the dots do
    hideWelcome();
    if (tourActive) { // the "?" toggles: a second press cancels
        endTour(true);
        return;
    }
    if (raycasterObjects.length === 0) return; // GLB not in yet
    tourActive = true;
    tourIndex = -1;
    controls.enabled = false;
    goToStop(0);
}

// restore=true means we were interrupted mid-tour and must fly home ourselves.
function endTour(restore) {
    clearTimeout(tourTimer);
    tourTimer = null;
    tourIndex = TOUR_STOPS.length; // a click during the flight home won't resume stops
    outlinePass.selectedObjects = [];
    hideTooltip(true);
    const done = () => {
        tourActive = false;
        controls.enabled = true;
    };
    if (restore) {
        const view = getDefaultView();
        moveCamera(view.position, view.target, 0.9, done);
    } else {
        done();
    }
}

hintButton.addEventListener("click", (e) => {
    e.stopPropagation();
    startTour();
});

window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        if (tourActive) endTour(true);
        else if (isWelcomeOpen) hideWelcome();
    }
});


// ---- Touch beacons ----------------------------------------------------------
// Coarse-pointer stand-in for desktop hover: small pulsing glass dots anchored
// to the main tappable objects, projected to screen space every frame from the
// object's box center (stored in object-local coords so they ride along with
// the cube's jump / hover motion). They fade in once the welcome card is
// dismissed, and permanently fade out for the session as soon as the visitor
// taps any interactive object, starts the tour, or ~12s pass.
const BEACON_KEYS = ["aboutme", "projects", "resume", "notebook_2", "rubik", "macbook"];
const BEACON_AUTO_HIDE_MS = 12000;

const beaconLayer = document.getElementById("beacon-layer");
const beacons = []; // { object, localCenter, el }
let beaconsShown = false;
let beaconsDismissed = false;
let beaconTimer = null;
const beaconWorld = new THREE.Vector3();

// Called once from the GLB callback, when every anchor object exists.
function setupBeacons() {
    if (!isTouchLike() || !beaconLayer) return;
    scene.updateMatrixWorld(true);
    BEACON_KEYS.forEach((key) => {
        const object = raycasterObjects.find((o) => o.name.includes(key));
        if (!object) return;
        const box = new THREE.Box3().expandByObject(object);
        const localCenter = object.worldToLocal(box.getCenter(new THREE.Vector3()));
        const el = document.createElement("div");
        el.className = "beacon-dot";
        beaconLayer.appendChild(el);
        beacons.push({ object, localCenter, el });
    });
}

function showBeacons() {
    if (beaconsDismissed || beaconsShown || beacons.length === 0) return;
    beaconsShown = true;
    gsap.to(beaconLayer, { autoAlpha: 1, duration: 0.8, delay: 0.35, ease: "power2.out" });
    beaconTimer = setTimeout(dismissBeacons, BEACON_AUTO_HIDE_MS);
}

// Permanent for the session — the dots only answer "what can I tap?" once.
function dismissBeacons() {
    if (beaconsDismissed || beacons.length === 0) return;
    beaconsDismissed = true;
    clearTimeout(beaconTimer);
    gsap.killTweensOf(beaconLayer);
    gsap.to(beaconLayer, { autoAlpha: 0, duration: 0.5, ease: "power2.in" });
}

// Runs each frame from the render loop while the dots are up.
function updateBeacons() {
    if (!beaconsShown || beaconsDismissed) return;
    for (const b of beacons) {
        beaconWorld.copy(b.localCenter);
        b.object.localToWorld(beaconWorld);
        beaconWorld.project(camera);
        const behind = beaconWorld.z > 1;
        const offscreen = Math.abs(beaconWorld.x) > 1 || Math.abs(beaconWorld.y) > 1;
        if (behind || offscreen) {
            b.el.style.visibility = "hidden";
            continue;
        }
        b.el.style.visibility = "visible";
        const x = (beaconWorld.x * 0.5 + 0.5) * sizes.width;
        const y = (-beaconWorld.y * 0.5 + 0.5) * sizes.height;
        b.el.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px)`;
    }
}

// On the closer mobile framing the cube's 1.7-unit jump could clear the top of
// the frame (mostly a landscape-phone risk — portrait has generous vertical
// headroom since its limiting axis is horizontal). Cap it from the measured
// headroom; Infinity restores the cube's own default.
function capRubikJumpForFrame() {
    if (!roomCube) return;
    roomCube.limitJumpHeight(mobileFocusView ? mobileFocusView.headroom - 0.3 : Infinity);
}

const modelPath = "models/portfolio.glb";

loader.load(modelPath, (glb) => {
    const mesh = glb.scene;
    const rubikPropMeshes = [];

    mesh.traverse((child) => {
        if (child.isMesh) {
            Object.keys(textureMap).forEach((key) => {
                if (child.name.includes(key)) {
                    const material = new THREE.MeshBasicMaterial({
                        map: loadedTextures[key]
                    });

                    child.material = material;
                }
            })
            child.castShadow = true;
            child.receiveShadow = true;
        }

        if (child.name.includes("manchester")) {
            manchesterObject = child;
        }

        // The baked rubik prop is replaced by the live procedural cube below:
        // collect it here (for measuring) and keep it out of raycasting.
        if (child.name.includes("rubik")) {
            rubikPropMeshes.push(child);
        } else if (clickableObjects.some(objName => child.name.includes(objName))) {
            raycasterObjects.push(child);
            child.userData.initialScale = new THREE.Vector3().copy(child.scale);
            child.userData.initialPosition = new THREE.Vector3().copy(child.position);
            child.userData.initialRotation = new THREE.Euler().copy(child.rotation);
        }
    });

    mesh.position.set(0, 1.05, -1);
    scene.add(mesh);

    // Swap the baked rubik prop for the live cube: measure where the prop sits
    // in world space, hide it (the GLB file itself is untouched), and drop the
    // procedural cube into the same spot at the same size and orientation. It
    // starts in the exact scramble the old landing-page cube used.
    if (rubikPropMeshes.length > 0) {
        mesh.updateMatrixWorld(true);
        const propBox = new THREE.Box3();
        rubikPropMeshes.forEach((m) => propBox.expandByObject(m));
        const propCenter = propBox.getCenter(new THREE.Vector3());
        const propSize = propBox.getSize(new THREE.Vector3());
        const propQuat = rubikPropMeshes[0].getWorldQuaternion(new THREE.Quaternion());
        rubikPropMeshes.forEach((m) => { m.visible = false; });

        roomCube = createRoomCube();
        roomCube.placeAt(propCenter, propQuat, Math.max(propSize.x, propSize.y, propSize.z));
        scene.add(roomCube.group);
        raycasterObjects.push(roomCube.group);
    }

    // Mobile: everything measurable is in — compute the close-up desk framing
    // and snap the (still hidden, pre-reveal) camera to it. No-op on desktop.
    computeMobileFocusView();
    if (mobileFocusView) {
        applyMobileControls();
        updateCameraForScreenSize();
        controls.update();
        capRubikJumpForFrame();
    }
    setupBeacons();
},
    undefined,
    (error) => {
        console.error('Failed to load model:', error);
    }
);


document.addEventListener('DOMContentLoaded', function () {
    const searchBar = document.getElementById('project-search')
    const filterBtns = document.querySelectorAll('.filter-btn')
    const projectCards = document.querySelectorAll('.project-card')

    // Search
    if (searchBar) {
        searchBar.addEventListener('input', function () {
            const searchTerm = this.value.toLowerCase()
            projectCards.forEach(card => {
                const title = card.querySelector('h4').textContent.toLowerCase()
                if (title.includes(searchTerm)) {
                    card.style.display = 'block'
                } else {
                    card.style.display = 'none'
                }
            })
        })
    }

    // Filter functionality
    filterBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            // Update active button
            filterBtns.forEach(b => b.classList.remove('active'))
            this.classList.add('active')

            const filter = this.getAttribute('data-filter')

            projectCards.forEach(card => {
                if (filter === 'all' || card.getAttribute('data-category') === filter) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            })
        })
    })

    const modals = document.querySelectorAll('.modal')

    modals.forEach(modal => {
        const observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (mutation) {
                if (mutation.attributeName === 'style' && modal.style.display === 'block') {
                    modal.classList.add('show')
                } else if (mutation.attributeName === 'style' && modal.style.display === 'none') {
                    modal.classList.remove('show')
                }
            })
        })
        observer.observe(modal, { attributes: true })
    })
})


// Event listeners
window.addEventListener("resize", () => {
    sizes.width = window.innerWidth;
    sizes.height = window.innerHeight;

    // Update camera (mobile framing depends on the aspect — rebuild it first)
    camera.aspect = sizes.width / sizes.height;
    computeMobileFocusView();
    updateCameraForScreenSize();
    capRubikJumpForFrame();

    // Update renderer + composer (the composer forwards setSize to its passes)
    renderer.setSize(sizes.width, sizes.height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    composer.setSize(sizes.width, sizes.height);
    composer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // Re-apply mobile/desktop controls
    applyMobileControls();
});

let vynilAudio = null;
let isVinylPlaying = false;
let ballRolledOut = false;

function playClickAnimation(object) {
    const objectName = object.name.toLowerCase();

    // ball
    if (objectName.includes('ball')) {
        gsap.killTweensOf(object.position);
        gsap.killTweensOf(object.rotation);

        if (ballRolledOut) {
            ballRolledOut = false;
            gsap.to(object.position, {
                z: object.userData.initialPosition.z,
                duration: 5.0,
                ease: "power2.out",
            });
            gsap.to(object.rotation, {
                x: object.userData.initialRotation.x,
                duration: 5.0,
                ease: "power2.out",
            });
        } else {
            ballRolledOut = true;
            gsap.to(object.position, {
                z: object.userData.initialPosition.z - 3.5,
                duration: 5.0,
                ease: "power2.out",
            });
            gsap.to(object.rotation, {
                x: object.userData.initialRotation.x - Math.PI * 4,
                duration: 5.0,
                ease: "power2.out",
            });
        }
    }
    // rubik's cube — jumps off the table and solves/scrambles itself midair.
    // The routine guards its own re-entrancy, so clicks mid-animation are no-ops.
    else if (objectName.includes('rubik')) {
        if (roomCube) roomCube.onClick();
    }
    // vynil
    else if (objectName.includes('vynil')) {
        if (isVinylPlaying && vynilAudio) {
            vynilAudio.pause();
            vynilAudio.currentTime = 0;
            isVinylPlaying = false;
        } else {
            if (!vynilAudio) {
                vynilAudio = new Audio('blackbird.mp3');
            }
            vynilAudio.play();
            isVinylPlaying = true;
        }
    }
}

function playHoverAnimation(object, isHovering) {
    const objectName = object.name.toLowerCase();
    if (objectName.includes('ball')) {
        return;
    }
    // The cube has its own restrained hover (on its inner root) so the generic
    // scale — and the killTweensOf below — can never fight its jump animation.
    if (objectName.includes('rubik')) {
        if (roomCube) roomCube.setHover(isHovering);
        return;
    }
    // The Bruno frame spins every frame in the render loop, so only its scale
    // may be tweened here — resetting rotation would fight the spin.
    if (objectName.includes('manchester')) {
        gsap.killTweensOf(object.scale);
        const k = isHovering ? 1.12 : 1;
        gsap.to(object.scale, {
            x: object.userData.initialScale.x * k,
            y: object.userData.initialScale.y * k,
            z: object.userData.initialScale.z * k,
            duration: isHovering ? 0.8 : 0.6,
            ease: isHovering ? "expo.out" : "power3.out",
        });
        return;
    }

    gsap.killTweensOf(object.scale);
    gsap.killTweensOf(object.rotation);
    gsap.killTweensOf(object.position);


    if (isHovering) {
        // mac
        if (objectName.includes('macbook') || (objectName.includes('notebook_2'))) {
            gsap.to(object.scale, {
                x: object.userData.initialScale.x * 1.4,
                y: object.userData.initialScale.y * 1.4,
                z: object.userData.initialScale.z * 1.4,
                duration: 0.8,
                ease: "expo.out",
            });
            gsap.to(object.position, {
                y: object.userData.initialPosition.y + 0.2,
                duration: 0.8,
                ease: "expo.out"
            });
            // tulips
        } else if (objectName.includes('tulips') || (objectName.includes('rock'))) {
            gsap.to(object.position, {
                y: object.userData.initialPosition.y + 0.13,
                duration: 0.8,
                ease: "expo.out"
            });
            // vynil         
        } else if (objectName.includes('vynil')) {
            gsap.to(object.scale, {
                x: object.userData.initialScale.x * 1.08,
                y: object.userData.initialScale.y * 1.08,
                z: object.userData.initialScale.z * 1.08,
                duration: 0.8,
                ease: "expo.out"
            });
            gsap.to(object.position, {
                x: object.userData.initialPosition.x - 0.4,
                y: object.userData.initialPosition.y - 0.4,
                z: object.userData.initialPosition.z - 0.5,
                duration: 0.8,
                ease: "expo.out"
            });
            // candle and books
        } else if (objectName.includes('candle') || (objectName.includes('book_b')) || (objectName.includes('book_pink'))) {
            gsap.to(object.scale, {
                x: object.userData.initialScale.x * 1.06,
                y: object.userData.initialScale.y * 1.06,
                z: object.userData.initialScale.z * 1.06,
                duration: 0.8,
                ease: "expo.out",
            });
            // about me and projects
        } else if (objectName.includes('aboutme')) {
            gsap.to(object.rotation, {
                z: object.userData.initialRotation.z + 0.05,
                duration: 0.8,
                ease: "expo.out",
            });
            gsap.to(object.position, {
                y: object.userData.initialPosition.y + 0.4,
                duration: 0.8,
                ease: "expo.out",
            });
        } else if (objectName.includes('projects')) {
            gsap.to(object.rotation, {
                z: object.userData.initialRotation.z - 0.05,
                duration: 0.8,
                ease: "expo.out",
            });
        } else {
            gsap.to(object.scale, {
                x: object.userData.initialScale.x * 1.1,
                y: object.userData.initialScale.y * 1.1,
                z: object.userData.initialScale.z * 1.1,
                duration: 0.8,
                ease: "expo.out",
            });
        }
    } else {
        if (!objectName.includes('ball')) {
            gsap.to(object.scale, {
                x: object.userData.initialScale.x,
                y: object.userData.initialScale.y,
                z: object.userData.initialScale.z,
                duration: 0.6,
                ease: "power3.out",
            });
            gsap.to(object.rotation, {
                x: object.userData.initialRotation.x,
                y: object.userData.initialRotation.y,
                z: object.userData.initialRotation.z,
                duration: 0.6,
                ease: "power3.out",
            });
            gsap.to(object.position, {
                x: object.userData.initialPosition.x,
                y: object.userData.initialPosition.y,
                z: object.userData.initialPosition.z,
                duration: 0.6,
                ease: "power3.out",
            });
        }
    }
}

let currentIntersectObject = null;
let hoverGraceFrames = 0;
const HOVER_GRACE_PERIOD = 10;

const animate = () => {
    controls.update();

    // Keep the touch beacons glued to their objects (no-op once dismissed)
    updateBeacons();

    // Animate manchester
    if (manchesterObject) {
        manchesterObject.rotation.y += 0.05
    }

    // Raycaster (with grace period to prevent jitter); paused during the tour
    // so hover animations don't fight the camera flight/outline.
    if (!isModalOpen && !tourActive) {
        raycaster.setFromCamera(pointer, camera);
        const currentIntersects = raycaster.intersectObjects(raycasterObjects, true);

        let foundClickable = null;
        if (currentIntersects.length > 0) {
            let intersectedObject = currentIntersects[0].object;

            // Find the actual clickable ancestor if it's a sub-mesh
            let temp = intersectedObject;
            while (temp) {
                if (clickableObjects.some(objName => temp.name.includes(objName))) {
                    foundClickable = temp;
                    break;
                }
                temp = temp.parent;
            }
        }

        if (foundClickable) {
            hoverGraceFrames = 0;
            if (currentIntersectObject !== foundClickable) {
                if (currentIntersectObject) {
                    playHoverAnimation(currentIntersectObject, false);
                }
                currentIntersectObject = foundClickable;
                playHoverAnimation(currentIntersectObject, true);
            }
            document.body.style.cursor = "pointer";
        } else if (currentIntersectObject) {
            hoverGraceFrames++;
            if (hoverGraceFrames > HOVER_GRACE_PERIOD) {
                playHoverAnimation(currentIntersectObject, false);
                currentIntersectObject = null;
                hoverGraceFrames = 0;
                document.body.style.cursor = "default";
            } else {
                document.body.style.cursor = "pointer";
            }
        } else {
            document.body.style.cursor = "default";
        }
    } else {
        if (currentIntersectObject) {
            playHoverAnimation(currentIntersectObject, false);
            currentIntersectObject = null;
            hoverGraceFrames = 0;
        }
        document.body.style.cursor = "default";
    }

    // The composer (with the OutlinePass) only runs while the tour is active.
    if (tourActive) {
        composer.render();
    } else {
        renderer.render(scene, camera);
    }

    requestAnimationFrame(animate);
};

animate();