import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import gsap from "gsap";

const canvas = document.querySelector("#experience-canvas");
const sizes = {
    width: window.innerWidth,
    height: window.innerHeight,
};

const textureLoader = new THREE.TextureLoader();

const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath('draco/');

// Loader
const manager = new THREE.LoadingManager();

const loader = new GLTFLoader(manager);
loader.setDRACOLoader(dracoLoader);

const modals = {
    aboutme: document.querySelector(".modal.aboutme"),
    projects: document.querySelector(".modal.projects"),
    book: document.querySelector(".modal.book"),
    map: document.querySelector(".modal.map"),
    jersey: document.querySelector(".modal.jersey"),
    board: document.querySelector(".modal.board")
}

let touchHappened = false;
let isModalOpen = false;

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
// Cards expand on click. Drag-and-drop is a READ view for visitors and only
// unlocks in edit mode (URL ?edit=<key>), where a drop PUTs the new status to a
// dev-only endpoint that rewrites the ticket .md in the vault. The vault stays
// the single source of truth; the production build has no write endpoint at all.
// ---------------------------------------------------------------------------
const BOARD_COLUMNS = [
    { key: "backlog", label: "Backlog" },
    { key: "todo", label: "To Do" },
    { key: "doing", label: "In Progress" },
    { key: "done", label: "Done" },
];

// Edit mode: drag-and-drop is enabled only when the URL carries ?edit=<key>.
// The dev middleware validates the key server-side; this is a UI gate, not the
// security boundary. Visitors without the key get a plain read-only board.
const EDIT_KEY = new URLSearchParams(window.location.search).get("edit");
const IS_EDIT = Boolean(EDIT_KEY);

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
        .then((data) => { boardData = data; return data; })
        .catch((err) => {
            console.error("Failed to load tickets.json:", err);
            return { tickets: [] };
        });
    return boardLoading;
}

// ---- Card rendering -------------------------------------------------------

function renderTicketCard(t) {
    const detail = `
        <div class="ticket-detail">
            ${t.done_when ? `<p class="ticket-detail-row"><span class="ticket-detail-label">Done when</span>${escapeHtml(t.done_when)}</p>` : ""}
            ${t.project ? `<p class="ticket-detail-row"><span class="ticket-detail-label">Project</span>${escapeHtml(t.project)}</p>` : ""}
            ${t.milestone ? `<p class="ticket-detail-row"><span class="ticket-detail-label">Milestone</span>${escapeHtml(t.milestone)}</p>` : ""}
            ${Array.isArray(t.blocks) && t.blocks.length ? `<p class="ticket-detail-row"><span class="ticket-detail-label">Blocks</span>${t.blocks.map(escapeHtml).join(", ")}</p>` : ""}
        </div>`;
    return `
        <div class="ticket-card ${t.status === "done" ? "is-done" : ""}"
             data-id="${escapeHtml(t.id)}"
             ${IS_EDIT ? 'draggable="true"' : ""}>
            <div class="ticket-top">
                <span class="ticket-id">${escapeHtml(t.id)}</span>
                <span class="ticket-cat">${escapeHtml(t.category || "")}</span>
            </div>
            <p class="ticket-title">${escapeHtml(t.title)}</p>
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
                ? items.map(renderTicketCard).join("")
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
    // Group by milestone, preserving first-seen order.
    const byMilestone = new Map();
    for (const t of items) {
        const key = t.milestone || "—";
        if (!byMilestone.has(key)) byMilestone.set(key, []);
        byMilestone.get(key).push(t);
    }
    const blocks = [...byMilestone.entries()].map(([milestone, mtickets]) => `
        <div class="milestone-block">
            <div class="milestone-head">
                <span class="milestone-name">${escapeHtml(milestone)}</span>
                <span class="milestone-count">${mtickets.length} ticket${mtickets.length === 1 ? "" : "s"}</span>
            </div>
            <div class="milestone-tickets">${mtickets.map(renderTicketCard).join("")}</div>
        </div>`).join("");
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
    if (badge) badge.style.display = IS_EDIT ? "" : "none";
    modals.board.classList.toggle("editable", IS_EDIT);

    // Tab active state
    document.querySelectorAll(".board-tab").forEach((b) =>
        b.classList.toggle("active", b.dataset.view === boardView)
    );

    if (boardView === "board") {
        viewEl.innerHTML = renderBoardView(tickets);
        if (IS_EDIT) wireDragAndDrop();
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
        // Expand/collapse a ticket card (ignore while dragging)
        const card = e.target.closest(".ticket-card");
        if (card && !card.classList.contains("is-dragging")) {
            card.classList.toggle("expanded");
        }
    });
}

// ---- Drag-and-drop (edit mode only) ---------------------------------------

let draggedId = null;

function wireDragAndDrop() {
    const columns = document.querySelectorAll(".board-column");
    document.querySelectorAll(".ticket-card[draggable=true]").forEach((card) => {
        card.addEventListener("dragstart", (e) => {
            draggedId = card.dataset.id;
            card.classList.add("is-dragging");
            e.dataTransfer.effectAllowed = "move";
        });
        card.addEventListener("dragend", () => {
            card.classList.remove("is-dragging");
            draggedId = null;
        });
    });
    columns.forEach((col) => {
        col.addEventListener("dragover", (e) => {
            e.preventDefault();
            col.classList.add("drop-target");
        });
        col.addEventListener("dragleave", () => col.classList.remove("drop-target"));
        col.addEventListener("drop", (e) => {
            e.preventDefault();
            col.classList.remove("drop-target");
            const newStatus = col.dataset.status;
            if (draggedId) moveTicket(draggedId, newStatus);
        });
    });
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
        body: JSON.stringify({ id, status: newStatus, key: EDIT_KEY }),
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

function openBoard() {
    showModal(modals.board);
    const hydrate = (data) => {
        renderBoard(data);
        wireBoardInteractions();
    };
    if (boardData) hydrate(boardData);
    else loadBoardData().then(hydrate);
}

let manchesterObject = null;

const clickableObjects = ["macbook", "notebook_2", "map", "ggb", "jersey", "aboutme", "projects",
    "resume", "almaty", "vynil", "book_pink", "book_brown", "book_black", "ball", "rock", "candle",
    "ipad", "rubik", "tulips", "ole", "kzchoco", "apple-pencil"];
const raycasterObjects = [];

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();

const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });
renderer.outputColorSpace = THREE.SRGBColorSpace;

renderer.setSize(sizes.width, sizes.height);
renderer.setClearColor(0x000000);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

const scene = new THREE.Scene();

const camera = new THREE.PerspectiveCamera(45, sizes.width / sizes.height, 1, 1000);

function updateCameraForScreenSize() {
    if (sizes.width < 768) {
        camera.fov = 60;
        camera.position.set(-15, 10, 30);
    } else {
        camera.fov = 45;
        camera.position.set(-10, 7, 20);
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
controls.target = new THREE.Vector3(0, 1, 0);
controls.update();

// Mobile: enable two-finger pan and wider view range
function applyMobileControls() {
    if (window.innerWidth < 768) {
        controls.enablePan = true;
        controls.touches = {
            ONE: THREE.TOUCH.ROTATE,
            TWO: THREE.TOUCH.DOLLY_PAN
        };
        controls.minDistance = 4;
        controls.maxDistance = 28;
        controls.minAzimuthAngle = -Math.PI * 0.75;
        controls.maxAzimuthAngle = Math.PI * 0.15;
        controls.panSpeed = 0.8;

        // Clamp pan range so user can't drift too far
        controls.addEventListener('change', () => {
            const target = controls.target;
            target.x = Math.max(-6, Math.min(6, target.x));
            target.y = Math.max(-1, Math.min(5, target.y));
            target.z = Math.max(-6, Math.min(6, target.z));
        });
    } else {
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
    if (e.target.closest('.modal')) return;
    e.preventDefault();
    pointer.x = (e.touches[0].clientX / sizes.width) * 2 - 1;
    pointer.y = - (e.touches[0].clientY / sizes.height) * 2 + 1;
}, { passive: false });

window.addEventListener("touchend", (e) => {
    // Don't intercept touches inside modals
    if (e.target.closest('.modal')) return;
    e.preventDefault();
    handleRaycasterInteraction();
}, { passive: false });

function handleRaycasterInteraction() {
    if (isModalOpen) return;
    raycaster.setFromCamera(pointer, camera);
    const currentIntersects = raycaster.intersectObjects(raycasterObjects);

    if (currentIntersects.length > 0) {
        const object = currentIntersects[0].object;

        playClickAnimation(object);

        if (object.name.includes("resume")) {
            window.open("Nazym Zhiyengaliyeva Resume.pdf", "_blank", "noopener,noreferrer");
        }

        if (object.name.includes("aboutme") || object.name.includes("ggb")) {
            showModal(modals.aboutme);
        } else if (object.name.includes("projects") || object.name.includes("macbook")) {
            showModal(modals.projects);
        } else if (object.name.includes("notebook")) {
            showModal(modals.book);
        } else if (object.name.includes("map")) {
            showModal(modals.map);
        } else if (object.name.includes("jersey")) {
            showModal(modals.jersey);
        } else if (object.name.includes("ipad")) {
            openBoard();
        }
    }
};

window.addEventListener("click", handleRaycasterInteraction);


const loadingScreen = document.querySelector(".loading-screen");
const loadingScreenButton = document.querySelector(".loading-screen-button");

manager.onLoad = function () {
    loadingScreenButton.style.border = "8px solid #dfdfdf";
    loadingScreenButton.style.background = "#303848ff";
    loadingScreenButton.style.color = "#dfdfdf";
    loadingScreen.style.background = "#303848ff"
    loadingScreenButton.style.boxShadow = "rgba(0, 0, 0, 0.24) 0px 3px 8px";
    loadingScreenButton.textContent = "Enter!";
    loadingScreenButton.style.cursor = "pointer";
    loadingScreenButton.style.transition = "transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)";
    let isDisabled = false;

    function handleEnter() {
        if (isDisabled) return;

        loadingScreenButton.style.border = "8px solid #dfdfdf";
        loadingScreenButton.style.background = "#303848ff";
        loadingScreenButton.style.color = "#dfdfdf";
        loadingScreenButton.style.boxShadow = "none";
        loadingScreenButton.innerHTML = "Welcome to my 3D virtual room!<br> Interact with elements (play some music,<br> kick the ball, explore) to get to know me!";
        loadingScreen.style.background = "#303848ff";
        isDisabled = true;

        playReveal();
    }

    loadingScreenButton.addEventListener("mouseenter", () => {
        loadingScreenButton.style.transform = "scale(1.3)";
    });

    loadingScreenButton.addEventListener("touchend", (e) => {
        touchHappened = true;
        e.preventDefault();
        handleEnter();
    });

    loadingScreenButton.addEventListener("click", (e) => {
        if (touchHappened) return;
        handleEnter();
    });

    loadingScreenButton.addEventListener("mouseleave", () => {
        loadingScreenButton.style.transform = "none";
    });
};

function playReveal() {
    const tl = gsap.timeline();

    tl.to(loadingScreen, {
        scale: 0.5,
        duration: 2.0,
        delay: 0.25,
        ease: "back.in(1.8)",
    }).to(
        loadingScreen,
        {
            y: "200vh",
            duration: 1.3,
            ease: "back.in(1.8)",
            onComplete: () => {
                loadingScreen.remove();
            },
        },
        "-=0.1"
    );
}


const modelPath = "models/portfolio.glb";

loader.load(modelPath, (glb) => {
    const mesh = glb.scene;

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

        if (clickableObjects.some(objName => child.name.includes(objName))) {
            raycasterObjects.push(child);
            child.userData.initialScale = new THREE.Vector3().copy(child.scale);
            child.userData.initialPosition = new THREE.Vector3().copy(child.position);
            child.userData.initialRotation = new THREE.Euler().copy(child.rotation);
        }
    });

    mesh.position.set(0, 1.05, -1);
    scene.add(mesh);
},
    (progress) => {
        const percentage = (progress.loaded / progress.total * 100).toFixed(2);
        if (loadingScreenButton) {
            loadingScreenButton.textContent = `Loading...`;
        }
    },
    (error) => {
        console.error('Failed to load model:', error);
        if (loadingScreenButton) {
            loadingScreenButton.textContent = 'Failed to load model';
        }
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

    // Update camera
    camera.aspect = sizes.width / sizes.height;
    updateCameraForScreenSize();

    // Update renderer
    renderer.setSize(sizes.width, sizes.height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

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

    // Animate manchester
    if (manchesterObject) {
        manchesterObject.rotation.y += 0.05
    }

    // Raycaster (with grace period to prevent jitter)
    if (!isModalOpen) {
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

    renderer.render(scene, camera);

    requestAnimationFrame(animate);
};

animate();