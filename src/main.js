import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

class Room3DViewer {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.model = null;
        this.lights = {};
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        this.hoverObjects = [];
        this.currentHover = null;
        
        this.init();
    }

    init() {
        // Create scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x1a1a2e);

        // Create camera
        this.camera = new THREE.PerspectiveCamera(
            75,
            window.innerWidth / window.innerHeight,
            0.1,
            1000
        );
        this.camera.position.set(-20, 15, 20);

        // Create renderer
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true,
            alpha: true 
        });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        
        // Shadow and lighting settings
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.outputColorSpace = THREE.SRGBColorSpace;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.5;
        
        this.renderer.useLegacyLights = false;
        this.renderer.physicallyCorrectLights = true;

        const container = document.getElementById('canvas-container');
        container.appendChild(this.renderer.domElement);

        // Setup controls
        this.setupControls();

        // Setup lighting
        this.setupLighting();

        // Load 3D model
        this.loadModel();

        // Setup event listeners
        this.setupEventListeners();

        // Start render loop
        this.animate();
    }

    setupControls() {
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        
        // Limit vertical rotation (prevent going under the floor or too high)
        this.controls.minPolarAngle = Math.PI / 6; // 30 degrees from top
        this.controls.maxPolarAngle = Math.PI / 2.2; // Not quite 90 degrees
        
        // Limit horizontal rotation for a more controlled view
        this.controls.minAzimuthAngle = -Math.PI / 2; // -90 degrees
        this.controls.maxAzimuthAngle = 0;  // 90 degrees
        
        // Zoom limits
        this.controls.minDistance = 3;
        this.controls.maxDistance = 15;
        
        // Smooth controls
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        
        // Disable panning to keep the model centered
        this.controls.enablePan = false;
    }

    setupLighting() {
        // Stronger ambient light for better base visibility
        const ambientLight = new THREE.AmbientLight(0x404040, 1.2);
        this.scene.add(ambientLight);

        // Main directional light (sun-like) - Enhanced intensity
        const directionalLight = new THREE.DirectionalLight(0xffffff, 2.5);
        directionalLight.position.set(10, 10, 5);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        directionalLight.shadow.camera.near = 0.5;
        directionalLight.shadow.camera.far = 50;
        directionalLight.shadow.camera.left = -20;
        directionalLight.shadow.camera.right = 20;
        directionalLight.shadow.camera.top = 20;
        directionalLight.shadow.camera.bottom = -20;
        this.scene.add(directionalLight);

        // Multiple point lights for better room illumination
        const pointLight1 = new THREE.PointLight(0xfff5e6, 1.5, 25);
        pointLight1.position.set(5, 8, 5);
        pointLight1.castShadow = true;
        this.scene.add(pointLight1);

        const pointLight2 = new THREE.PointLight(0xffe4b5, 1.2, 20);
        pointLight2.position.set(-5, 6, -5);
        pointLight2.castShadow = true;
        this.scene.add(pointLight2);

        const pointLight3 = new THREE.PointLight(0xe6f3ff, 1.0, 15);
        pointLight3.position.set(0, 8, 0);
        this.scene.add(pointLight3);

        // Hemisphere light for natural outdoor lighting - Enhanced
        const hemisphereLight = new THREE.HemisphereLight(0x87ceeb, 0x362d1d, 0.8);
        this.scene.add(hemisphereLight);

        // Add rim lighting for better definition
        const rimLight = new THREE.DirectionalLight(0x4a90e2, 1.0);
        rimLight.position.set(-10, 5, -10);
        this.scene.add(rimLight);

        // Store lights for debugging
        this.lights = {
            ambient: ambientLight,
            directional: directionalLight,
            point1: pointLight1,
            point2: pointLight2,
            point3: pointLight3,
            hemisphere: hemisphereLight,
            rim: rimLight
        };

        console.log('Lighting setup complete with enhanced illumination');
    }

    loadModel() {
        // Setup DRACO loader for compression
        const dracoLoader = new DRACOLoader();
        dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/');
        dracoLoader.preload();
        
        const loader = new GLTFLoader();
        loader.setDRACOLoader(dracoLoader);
        
        const loadingElement = document.getElementById('loading');

        loader.load(
            '/portfolio.glb',
            (gltf) => {
                this.model = gltf.scene;
                
                // Enable shadows and enhance materials for all meshes
                this.model.traverse((child) => {
                    if (child.isMesh) {
                        child.castShadow = true;
                        child.receiveShadow = true;
                        
                        // Check if this mesh should have hover interactions
                        const hoverMeshes = ['map', 'resume', 'almaty', 'aboutme', 'projects', 'macbook', 'phone', 'notebook', 'jersey'];
                        const isHoverMesh = hoverMeshes.some(meshName => 
                            child.name.toLowerCase().includes(meshName.toLowerCase())
                        );
                        
                        if (isHoverMesh) {
                            this.hoverObjects.push(child);
                            // Store initial transform data for hover effects
                            child.userData.initialScale = new THREE.Vector3().copy(child.scale);
                            child.userData.initialPosition = new THREE.Vector3().copy(child.position);
                            child.userData.initialRotation = new THREE.Euler().copy(child.rotation);
                            child.userData.isHoverable = true;
                        }
                        
                        // Enhance material appearance and lighting response
                        if (child.material) {
                            // Ensure material responds to lighting
                            child.material.envMapIntensity = 1.2;
                            
                            // Make materials more responsive to lighting
                            if (child.material.isMeshStandardMaterial || child.material.isMeshPhysicalMaterial) {
                                child.material.roughness = Math.min(child.material.roughness + 0.1, 1.0);
                                child.material.metalness = Math.max(child.material.metalness - 0.1, 0.0);
                            }
                            
                            // For basic materials, convert to standard material for better lighting
                            if (child.material.isMeshBasicMaterial) {
                                const newMaterial = new THREE.MeshStandardMaterial({
                                    color: child.material.color,
                                    map: child.material.map,
                                    roughness: 0.8,
                                    metalness: 0.1
                                });
                                child.material = newMaterial;
                            }
                            
                            child.material.needsUpdate = true;
                        }
                    }
                });

                // Add to scene
                this.scene.add(this.model);
                
                // Hide loading
                if (loadingElement) {
                    loadingElement.style.display = 'none';
                }
                
                console.log('3D Model loaded successfully');
            },
            (progress) => {
                // Show loading progress
                const percentComplete = (progress.loaded / progress.total) * 100;
                const loadingElement = document.getElementById('loading');
                const loadingBar = document.getElementById('loading-bar');
                
                if (loadingElement) {
                    loadingElement.querySelector('div').textContent = `Loading: ${Math.round(percentComplete)}%`;
                }
                if (loadingBar) {
                    loadingBar.style.width = `${percentComplete}%`;
                }
            },
            (error) => {
                console.error('Error loading 3D model:', error);
                if (loadingElement) {
                    loadingElement.textContent = 'Error loading model';
                }
            }
        );
    }

    setupEventListeners() {
        // Handle window resize
        window.addEventListener('resize', () => {
            this.camera.aspect = window.innerWidth / window.innerHeight;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(window.innerWidth, window.innerHeight);
        });

        // Handle visibility change (pause when tab is hidden for performance)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.controls.enabled = false;
            } else {
                this.controls.enabled = true;
            }
        });

        // Mouse move event for hover detection
        window.addEventListener('mousemove', (event) => {
            this.onMouseMove(event);
        });

        // Click events for interactions
        window.addEventListener('click', (event) => {
            this.onMouseClick(event);
        });
    }

    onMouseMove(event) {
        // Calculate mouse position in normalized device coordinates
        this.mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
        this.mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

        // Update raycaster
        this.raycaster.setFromCamera(this.mouse, this.camera);

        // Check for intersections with hover objects
        const intersects = this.raycaster.intersectObjects(this.hoverObjects);

        if (intersects.length > 0) {
            const hoveredObject = intersects[0].object;
            
            if (this.currentHover !== hoveredObject) {
                // Reset previous hover
                if (this.currentHover && this.currentHover.userData.isHoverable) {
                    this.resetHover(this.currentHover);
                }
                
                // Apply hover effect
                this.currentHover = hoveredObject;
                this.applyHoverEffect(hoveredObject);
                
                // Change cursor
                document.body.style.cursor = 'pointer';
            }
        } else {
            // No intersection
            if (this.currentHover) {
                this.resetHover(this.currentHover);
                this.currentHover = null;
                document.body.style.cursor = 'default';
            }
        }
    }

    onMouseClick(event) {
        if (this.currentHover) {
            this.handleMeshClick(this.currentHover);
        }
    }

    applyHoverEffect(mesh) {
        if (!mesh.userData.isHoverable) return;
        
        // Scale up slightly on hover
        const hoverScale = 1.1;
        mesh.scale.copy(mesh.userData.initialScale).multiplyScalar(hoverScale);
        
        // Slight position offset for floating effect
        mesh.position.copy(mesh.userData.initialPosition);
        mesh.position.y += 0.05;
        
        // Slight rotation for dynamic effect
        mesh.rotation.copy(mesh.userData.initialRotation);
        mesh.rotation.y += 0.1;
    }

    resetHover(mesh) {
        if (!mesh.userData.isHoverable) return;
        
        // Reset to initial values
        mesh.scale.copy(mesh.userData.initialScale);
        mesh.position.copy(mesh.userData.initialPosition);
        mesh.rotation.copy(mesh.userData.initialRotation);
    }

    handleMeshClick(mesh) {
        const meshName = mesh.name.toLowerCase();
        
        // Handle different mesh interactions
        if (meshName.includes('resume')) {
            // Open resume PDF
            window.open('/Nazym Zhiyengaliyeva Resume.pdf', '_blank');
        } else if (meshName.includes('map')) {
            console.log('Map clicked - could show location');
        } else if (meshName.includes('macbook') || meshName.includes('notebook')) {
            // Could show portfolio/projects
            console.log('Laptop clicked - could show projects');
        } else if (meshName.includes('phone')) {
            // Could show contact info
            console.log('Phone clicked - could show contact info');
        } else if (meshName.includes('jersey')) {
            // Could show education info
            console.log('Manchester clicked - could show education');
        } else if (meshName.includes('almaty')) {
            // Could show education info
            console.log('Manchester clicked - could show education');
        } else if (meshName.includes('aboutme') || meshName.includes('projects')) {
            // Could show specific projects or achievements
            console.log('Number clicked');
        } else if (meshName.includes('almaty')) {
            // Could show specific projects or achievements
            console.log('Almaty clicked');
        } else {
            console.log(`Clicked on: ${mesh.name}`);
        }
        
        // Add a click animation
        this.animateClick(mesh);
    }

    animateClick(mesh) {
        if (!mesh.userData.isHoverable) return;
        
        // Quick scale animation on click
        const originalScale = mesh.scale.clone();
        const clickScale = originalScale.clone().multiplyScalar(0.9);
        
        // Scale down
        mesh.scale.copy(clickScale);
        
        // Scale back up after a short delay
        setTimeout(() => {
            mesh.scale.copy(originalScale);
        }, 100);
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new Room3DViewer();
});
