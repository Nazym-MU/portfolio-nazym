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
dracoLoader.setDecoderPath('public/draco/');

// Loader
const manager = new THREE.LoadingManager();

const loader = new GLTFLoader(manager);
loader.setDRACOLoader(dracoLoader);

const modals = {
    aboutme: document.querySelector(".modal.aboutme"),
    projects: document.querySelector(".modal.projects"),
    book: document.querySelector(".modal.book"),
    map: document.querySelector(".modal.map"),
    jersey: document.querySelector(".modal.jersey")
}

let touchHappened = false;

document.querySelectorAll(".close").forEach(button => {
    button.addEventListener("touchend", (e) => {
        touchHappened = true;
        e.preventDefault();
        const modal = e.target.closest(".modal");
        hideModal(modal);
    }, {passive: false});

    button.addEventListener("click", (e) => {
        if (touchHappened) return;
        e.preventDefault();
        const modal = e.target.closest(".modal");
        hideModal(modal);
    }, {passive: false});
})

const showModal = (modal) => {
    modal.style.display = "block";

    gsap.set(modal, {opacity: 0});

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
        }
    });
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
camera.position.set(-10, 7, 20);


const textureMap = {
    aboutme: "public/textures/palka-texture.webp",
    projects: "public/textures/palka-texture.webp",
    Cylinder: "public/textures/wall.webp",
    book_black: "public/textures/black-book-texture.webp",
    book_brown: "public/textures/brown-book.webp",
    book_pink: "public/textures/book-pink-texture.webp",
    goal_tor: "public/textures/goal-tor.webp",
    notebook_2: "public/textures/notebook-2-texture.webp",
    rock_1: "public/textures/rock-1.webp",
    rock_2: "public/textures/rock-2.webp",
    background: "public/textures/background-texture.webp",
    ball: "public/textures/ball.webp",
    bed: "public/textures/bed.webp",
    candle: "public/textures/candle.webp",
    floor: "public/textures/floor-texture.webp",
    'frame-1': "public/textures/frame-1-texture.webp",
    'frame-2': "public/textures/frames-texture.webp",
    'frame-3': "public/textures/frames-texture.webp",
    'frame-4': "public/textures/frames-texture.webp",
    'frame-5': "public/textures/frames-texture.webp",
    goalpost: "public/textures/goalpost.webp",
    grass: "public/textures/grass-small.webp",
    'grass-2': "public/textures/grass-small.webp",
    ipad: "public/textures/ipad.webp",
    macbook: "public/textures/mac-texture.webp",
    shelf: "public/textures/shelf-texture.webp",
    vynil: "public/textures/shelf-texture.webp",
    notebook_1: "public/textures/notebook-texture.webp",
    palka: "public/textures/palka-texture.webp",
    pillow: "public/textures/pillow-texture.webp",
    resume: "public/textures/resume-texture.webp",
    roof: "public/textures/roof-texture.webp",
    rubik: "public/textures/rubik-texture.webp",
    rug: "public/textures/rug.webp",
    table: "public/textures/table-texture.webp",
    tulips: "public/textures/tulips.webp",
    vase: "public/textures/vase-texture.webp",
    wall: "public/textures/wall.webp",
    field: "public/textures/roof-texture.webp",
    chair: "public/textures/table-texture.webp",
    'chair-wheel': "public/textures/ipad.webp",
    phone: "public/textures/ipad.webp",
    'bruno-frame': "public/textures/ipad.webp",
    almaty: "public/textures/almaty.webp",
    manchester: "public/textures/bruno.webp",
    lingard: "public/textures/lingard.webp",
    ole: "public/textures/ole.webp",
    kzchoco: "public/textures/kzchoco.webp",
    map: "public/textures/map.webp",
    'never-gonna-stop': "public/textures/tifo.webp",
    ggb: "public/textures/ggb.webp",
    jersey:  "public/textures/jersey.webp",
    'apple-pencil': "public/textures/mac-texture.webp"
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
    e.preventDefault();
    pointer.x = (e.touches[0].clientX / sizes.width) * 2 - 1;
    pointer.y = - (e.touches[0].clientY / sizes.height) * 2 + 1;
}, { passive: false });

window.addEventListener("touchend", (e) => {
    e.preventDefault();
    handleRaycasterInteraction();
}, { passive: false });

function handleRaycasterInteraction() {
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


const modelPath = "public/models/portfolio.glb";

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


document.addEventListener('DOMContentLoaded', function() {
    const searchBar = document.getElementById('project-search')
    const filterBtns = document.querySelectorAll('.filter-btn')
    const projectCards = document.querySelectorAll('.project-card')
    
    // Search
    if (searchBar) {
        searchBar.addEventListener('input', function() {
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
        btn.addEventListener('click', function() {
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
    const windowControls = document.querySelectorAll('.window-control')
    
    modals.forEach(modal => {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.attributeName === 'style' && modal.style.display === 'block') {
                    modal.classList.add('show')
                } else if (mutation.attributeName === 'style' && modal.style.display === 'none') {
                    modal.classList.remove('show')
                }
            })
        })
        observer.observe(modal, { attributes: true })
    })
    
    // Window control animations
    windowControls.forEach(control => {
        control.addEventListener('click', function() {
            if (this.classList.contains('close')) {
                const modal = this.closest('.modal')
                modal.style.display = 'none'
            }
        })
    })
})


// Event listeners
window.addEventListener("resize", () => {
    sizes.width = window.innerWidth;
    sizes.height = window.innerHeight;
    
    // Update camera
    camera.aspect = sizes.width / sizes.height
    camera.updateProjectionMatrix();

    // Update renderer
    renderer.setSize(sizes.width, sizes.height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
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
                vynilAudio = new Audio('public/blackbird.mp3');
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
                duration: 0.5,
                ease: "power2.out",
            });
            gsap.to(object.position, {
                y: object.userData.initialPosition.y + 0.2,
                duration: 0.5,
                ease: "power2.out"
            });
        // tulips
        } else if (objectName.includes('tulips') || (objectName.includes('rock'))) {
            gsap.to(object.position, {
                y: object.userData.initialPosition.y + 0.13,
                duration: 0.5,
                ease: "power2.out"
            });
        // vynil         
        } else if (objectName.includes('vynil')) {
            gsap.to(object.scale, {
                x: object.userData.initialScale.x * 1.08, 
                y: object.userData.initialScale.y * 1.08, 
                z: object.userData.initialScale.z * 1.08,
                duration: 0.5,
                ease: "power2.out"
            });
            gsap.to(object.position, {
                x: object.userData.initialPosition.x - 0.4,
                y: object.userData.initialPosition.y - 0.4,
                z: object.userData.initialPosition.z - 0.5,
                duration: 0.5,
                ease: "power2.out"
            });
        // candle and books
         } else if (objectName.includes('candle') || (objectName.includes('book_b')) || (objectName.includes('book_pink'))) {
            gsap.to(object.scale, {
                x: object.userData.initialScale.x * 1.1, 
                y: object.userData.initialScale.y * 1.1, 
                z: object.userData.initialScale.z * 1.1,
                duration: 0.5,
                ease: "power2.out",
            });
            gsap.to(object.position, {
                x: object.userData.initialPosition.x - 0.4,
                y: object.userData.initialPosition.y + 0.1,
                z: object.userData.initialPosition.z - 0.5,
                duration: 0.5,
                ease: "power2.out",
            });
        // about me and projects
        } else if (objectName.includes('aboutme')) {
                gsap.to(object.rotation, {
                    z: object.userData.initialRotation.z + 0.05,
                    duration: 0.5,
                    ease: "power2.out",
                }); 
                gsap.to(object.position, {
                    y: object.userData.initialPosition.y + 0.4 ,
                    duration: 0.5,
                    ease: "power2.out",
                }); 
        } else if (objectName.includes('projects')) {
            gsap.to(object.rotation, {
                z: object.userData.initialRotation.z - 0.05,
                duration: 0.5,
                ease: "power2.out",
            });
        } else {
            gsap.to(object.scale, {
                x: object.userData.initialScale.x * 1.1, 
                y: object.userData.initialScale.y * 1.1, 
                z: object.userData.initialScale.z * 1.1,
                duration: 0.5,
                ease: "power2.out",
            });
        }
    } else {
        if (!objectName.includes('ball')) {
            gsap.to(object.scale, {
                x: object.userData.initialScale.x, 
                y: object.userData.initialScale.y, 
                z: object.userData.initialScale.z,
                duration: 0.5,
                ease: "power2.out",
            });
            gsap.to(object.rotation, {
                x: object.userData.initialRotation.x,
                y: object.userData.initialRotation.y,
                z: object.userData.initialRotation.z,
                duration: 0.5,
                ease: "power2.out",
            });
            gsap.to(object.position, {
                x: object.userData.initialPosition.x,
                y: object.userData.initialPosition.y,
                z: object.userData.initialPosition.z,
                duration: 0.5,
                ease: "power2.out",
            });
        }
    }
}

let currentIntersectObject = null;

const animate = () => {
    controls.update();

    // Animate manchester
   if (manchesterObject) {
        manchesterObject.rotation.y += 0.05
   }

   // Raycaster
   raycaster.setFromCamera(pointer, camera);
   const currentIntersects = raycaster.intersectObjects(raycasterObjects);

   if (currentIntersects.length > 0) {
    const intersectedObject = currentIntersects[0].object;

    if (clickableObjects.some(objName => intersectedObject.name.includes(objName))) {
        if (currentIntersectObject != intersectedObject) {
            if (currentIntersectObject) {
                playHoverAnimation(currentIntersectObject, false);
            }
            currentIntersectObject = intersectedObject;
            playHoverAnimation(currentIntersectObject, true);
        }
        document.body.style.cursor = "pointer";
    } else {
        document.body.style.cursor = "default";
    }
  } else {
    if (currentIntersectObject) {
        playHoverAnimation(currentIntersectObject, false);
        currentIntersectObject = false;
    }
    document.body.style.cursor = "default";
  }
    
    renderer.render(scene, camera);

    requestAnimationFrame(animate);
};

animate();