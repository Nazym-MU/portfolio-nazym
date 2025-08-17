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

const clickableObjects = ["macbook", "book", "map", "ggb", "jersey", "aboutme", "projects", "resume"];
const raycasterObjects = [];

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();

const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });
renderer.outputColorSpace = THREE.SRGBColorSpace;

renderer.setSize(sizes.width, sizes.height);
renderer.setClearColor(0x000000);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x2a2a3a)

const camera = new THREE.PerspectiveCamera(45, sizes.width / sizes.height, 1, 1000);
camera.position.set(-10, 7, 20);

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

const groundGeometry = new THREE.PlaneGeometry(20, 20, 32, 32);
groundGeometry.rotateX(-Math.PI / 2);
const groundMaterial = new THREE.MeshStandardMaterial({
    color: 0x111111,
    side: THREE.DoubleSide
});

const groundMesh = new THREE.Mesh(groundGeometry, groundMaterial);
groundMesh.castShadow = false;
groundMesh.receiveShadow = true;
scene.add(groundMesh);

const ambientLight = new THREE.AmbientLight(0x404080, 0.4) // Soft blue ambient
scene.add(ambientLight)

const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
directionalLight.position.set(10, 10, 5)
directionalLight.castShadow = true
scene.add(directionalLight)

const pointLight1 = new THREE.PointLight(0xff6b9d, 0.6, 100)
pointLight1.position.set(-20, 10, 10)
scene.add(pointLight1)

const pointLight2 = new THREE.PointLight(0x6bcfff, 0.6, 100)
pointLight2.position.set(20, 10, -10)
scene.add(pointLight2)

const pointLight3 = new THREE.PointLight(0xffeb3b, 0.4, 100)
pointLight3.position.set(0, -10, 20)
scene.add(pointLight3)

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

        if (object.name.includes("resume")) {
            window.open("Nazym Zhiyengaliyeva Resume.pdf", "_blank", "noopener,noreferrer");
        }

        if (object.name.includes("aboutme") || object.name.includes("ggb")) {
            showModal(modals.aboutme);
        } else if (object.name.includes("projects") || object.name.includes("macbook")) {
            showModal(modals.projects);
        } else if (object.name.includes("book")) {
            showModal(modals.book);
        } else if (object.name.includes("map")) {
            showModal(modals.map);
        } else if (object.name.includes("jersey")) {
            showModal(modals.jersey);
        }
    }
};

window.addEventListener("click", handleRaycasterInteraction);

const manager = new THREE.LoadingManager();
const loadingScreen = document.querySelector(".loading-screen");
const loadingScreenButton = document.querySelector(".loading-screen-button");

manager.onLoad = function () {
    loadingScreenButton.style.border = "8px solid #2a0f4e";
    loadingScreenButton.style.background = "#401d49";
    loadingScreenButton.style.color = "#e6dede";
    loadingScreenButton.style.boxShadow = "rgba(0, 0, 0, 0.24) 0px 3px 8px";
    loadingScreenButton.textContent = "Enter!";
    loadingScreenButton.style.cursor = "pointer";
    loadingScreenButton.style.transition = "transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)";
    let isDisabled = false;

    function handleEnter() {
        if (isDisabled) return;

        loadingScreenButton.style.border = "8px solid #6e5e9c";
        loadingScreenButton.style.background = "#ead7ef";
        loadingScreenButton.style.color = "#6e5e9c";
        loadingScreenButton.style.boxShadow = "none";
        loadingScreenButton.textContent = "Welcome to my 3D virtual room! Interact with elements to get to know me <3";
        loadingScreen.style.background = "#ead7ef";
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
        duration: 1.2,
        delay: 0.25,
        ease: "back.in(1.8)",
    }).to(
        loadingScreen,
        {
            y: "200vh",
            rotateX: 45,
            rotateY: -35,
            duration: 1.2,
            ease: "back.in(1.8)",
            onComplete: () => {
                loadingScreen.remove();
            },
        },
        "-=0.1"
    );
}

// Loader
const dracoLoader = new DRACOLoader();
const isProduction = window.location.protocol === 'https:' || window.location.hostname !== 'localhost';
const dracoPath = isProduction ? './draco/' : './draco/';
const modelPath = isProduction ? 'portfolio.glb' : 'public/portfolio.glb';
dracoLoader.setDecoderPath(dracoPath);

const loader = new GLTFLoader(manager);
loader.setDRACOLoader(dracoLoader);

const modelPaths = ['portfolio.glb', './portfolio.glb', 'public/portfolio.glb'];
let loadAttempt = 0;

function tryLoadModel() {
    if (loadAttempt >= modelPaths.length) {
        console.error('Failed to load model from all attempted paths');
        return;
    }
    
    const currentPath = modelPaths[loadAttempt];
    console.log(`Attempting to load model from: ${currentPath}`);
    
    loader.load(
        currentPath,
        (glb) => {
            console.log('Model loaded successfully from:', currentPath);
            const mesh = glb.scene;

            mesh.traverse((child) => {
                if (child.isMesh) {
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
            console.log('Loading progress:', progress);
        },
        (error) => {
            console.error(`Failed to load from ${currentPath}:`, error);
            loadAttempt++;
            tryLoadModel();
        }
    );
}

tryLoadModel();


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
                    card.style.display = 'block'
                } else {
                    card.style.display = 'none'
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

function playHoverAnimation(object, isHovering) {
    gsap.killTweensOf(object.scale);
    gsap.killTweensOf(object.rotation);
    gsap.killTweensOf(object.position);

    if (isHovering) {
        gsap.to(object.scale, {
            x: object.userData.initialScale.x * 1.4, 
            y: object.userData.initialScale.y * 1.4, 
            z: object.userData.initialScale.z * 1.4,
            duration: 0.5,
            ease: "bounce.out(1.8)",
        });
    } else {
        gsap.to(object.scale, {
            x: object.userData.initialScale.x, 
            y: object.userData.initialScale.y, 
            z: object.userData.initialScale.z,
            duration: 0.5,
            ease: "bounce.out(1.8)",
        });
        gsap.to(object.rotation, {
            y: object.userData.initialRotation.y, 
            duration: 0.5,
            ease: "bounce.out(1.8)",
        });
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