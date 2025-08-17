import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const canvas = document.querySelector("#experience-canvas");
const sizes = {
    width: window.innerWidth,
    height: window.innerHeight,
};

let manchesterObject = null;

const clickableObjects = ["macbook", "book", "map", "ggb", "jersey", "almaty", "rubik", "aboutme", "projects", "kzchoco", "resume"];
const raycasterObjects = [];

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();

const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });
renderer.outputColorSpace = THREE.SRGBColorSpace;

renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setClearColor(0x000000);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

document.body.appendChild(renderer.domElement);


const scene = new THREE.Scene();

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

const ambientLight = new THREE.AmbientLight(0xffffff, 0.3);
scene.add(ambientLight);

const spotLight = new THREE.SpotLight(0xffffff, 3, 100, 0.2, 0.5);
spotLight.position.set(0, 25, 0);
spotLight.castShadow = true;
spotLight.shadow.bias = -0.001
scene.add(spotLight);

// Event listeners

window.addEventListener("mousemove", (e) => {
    pointer.x = (e.clientX / sizes.width) * 2 - 1;
    pointer.y = - (e.clientY / sizes.height) * 2 + 1;
});

window.addEventListener("click", (e) => {
    raycaster.setFromCamera(pointer, camera);
    const currentIntersects = raycaster.intersectObjects(raycasterObjects);

    if (currentIntersects.length > 0) {
        const object = currentIntersects[0].object;

        if (object.name.includes("resume")) {
            window.open("/public/Nazym Zhiyengaliyeva Resume.pdf", "_blank", "noopener,noreferrer");
        }
    }
})

// Loader
const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath("public/draco/");

const loader = new GLTFLoader().setPath('public/');
loader.setDRACOLoader(dracoLoader);
loader.load('portfolio.glb', (glb) => {
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
        }
    });

    mesh.position.set(0, 1.05, -1);
    scene.add(mesh)
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
})

const animate = () => {
    controls.update();

    // Animate manchester
   if (manchesterObject) {
        manchesterObject.rotation.y += 0.05
   }

   // Raycaster
   raycaster.setFromCamera(pointer, camera);
   const currentIntersects = raycaster.intersectObjects(raycasterObjects);

   for (let i = 0; i < currentIntersects.length; i++) {
    currentIntersects[i].object.material.color.set(0xff0000);
   }

   if (currentIntersects.length > 0) {
    const currentIntersectObject = currentIntersects[0].object;

    if (clickableObjects.some(objName => currentIntersectObject.name.includes(objName))) {
        document.body.style.cursor = "pointer";
    } else {
        document.body.style.cursor = "default";
    }
  } else {
    document.body.style.cursor = "default";
  }
    
    renderer.render(scene, camera);

    requestAnimationFrame(animate);
};

animate();