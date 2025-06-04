import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

class Room3DViewer {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.model = null;
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
        this.camera.position.set(5, 5, 5);

        // Create renderer with enhanced settings for better lighting
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true,
            alpha: true 
        });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        
        // Enhanced shadow and lighting settings
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.outputColorSpace = THREE.SRGBColorSpace;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.5; // Increased for brighter lighting
        
        // Enable physically correct lighting
        this.renderer.useLegacyLights = false;
        this.renderer.physicallyCorrectLights = true;

        // Add renderer to DOM
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
        this.controls.maxAzimuthAngle = Math.PI / 2;  // 90 degrees
        
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

        // Optional: Add light helpers for debugging (uncomment to see light positions)
        // this.addLightHelpers();
    }

    addLightHelpers() {
        // Add helpers to visualize light positions
        if (this.lights?.directional) {
            const directionalHelper = new THREE.DirectionalLightHelper(this.lights.directional, 2);
            this.scene.add(directionalHelper);
        }

        if (this.lights?.point1) {
            const pointHelper1 = new THREE.PointLightHelper(this.lights.point1, 1);
            this.scene.add(pointHelper1);
        }

        if (this.lights?.point2) {
            const pointHelper2 = new THREE.PointLightHelper(this.lights.point2, 1);
            this.scene.add(pointHelper2);
        }

        if (this.lights?.point3) {
            const pointHelper3 = new THREE.PointLightHelper(this.lights.point3, 1);
            this.scene.add(pointHelper3);
        }

        console.log('Light helpers added for debugging');
    }

    loadModel() {
        const loader = new GLTFLoader();
        const loadingElement = document.getElementById('loading');

        loader.load(
            '/model-low.glb',
            (gltf) => {
                this.model = gltf.scene;
                
                // Enable shadows and enhance materials for all meshes
                this.model.traverse((child) => {
                    if (child.isMesh) {
                        child.castShadow = true;
                        child.receiveShadow = true;
                        
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

                console.log('Model materials enhanced for better lighting response');

                // Center and scale the model if needed
                const box = new THREE.Box3().setFromObject(this.model);
                const center = box.getCenter(new THREE.Vector3());
                const size = box.getSize(new THREE.Vector3());
                
                // Center the model
                this.model.position.x = -center.x;
                this.model.position.y = -center.y;
                this.model.position.z = -center.z;

                // Scale if too big or small
                const maxDimension = Math.max(size.x, size.y, size.z);
                if (maxDimension > 10) {
                    const scale = 8 / maxDimension;
                    this.model.scale.multiplyScalar(scale);
                }

                this.scene.add(this.model);
                
                // Hide loading text
                loadingElement.style.display = 'none';

                // Focus camera on the model
                this.focusOnModel();
            },
            (progress) => {
                const percentComplete = (progress.loaded / progress.total * 100);
                loadingElement.textContent = `Loading 3D Model... ${Math.round(percentComplete)}%`;
            },
            (error) => {
                console.error('Error loading model:', error);
                loadingElement.textContent = 'Error loading 3D model. Please check if the file exists.';
                loadingElement.style.color = '#ff6b6b';
            }
        );
    }

    focusOnModel() {
        if (this.model) {
            const box = new THREE.Box3().setFromObject(this.model);
            const size = box.getSize(new THREE.Vector3());
            const maxDimension = Math.max(size.x, size.y, size.z);
            
            // Position camera at a good distance
            const distance = maxDimension * 1.5;
            this.camera.position.set(distance, distance * 0.8, distance);
            this.camera.lookAt(0, 0, 0);
            
            // Update controls target
            this.controls.target.set(0, 0, 0);
            this.controls.update();
        }
    }

    setupEventListeners() {
        // Handle window resize
        window.addEventListener('resize', () => {
            this.camera.aspect = window.innerWidth / window.innerHeight;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(window.innerWidth, window.innerHeight);
        });

        // Handle visibility change (pause when tab is hidden)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.controls.enabled = false;
            } else {
                this.controls.enabled = true;
            }
        });

        // Lighting controls
        this.setupLightingControls();
    }

    setupLightingControls() {
        // Ambient light control
        const ambientSlider = document.getElementById('ambient-intensity');
        if (ambientSlider) {
            ambientSlider.addEventListener('input', (e) => {
                if (this.lights?.ambient) {
                    this.lights.ambient.intensity = parseFloat(e.target.value);
                }
            });
        }

        // Directional light control
        const directionalSlider = document.getElementById('directional-intensity');
        if (directionalSlider) {
            directionalSlider.addEventListener('input', (e) => {
                if (this.lights?.directional) {
                    this.lights.directional.intensity = parseFloat(e.target.value);
                }
            });
        }

        // Point lights control
        const pointSlider = document.getElementById('point-intensity');
        if (pointSlider) {
            pointSlider.addEventListener('input', (e) => {
                const intensity = parseFloat(e.target.value);
                if (this.lights?.point1) this.lights.point1.intensity = intensity;
                if (this.lights?.point2) this.lights.point2.intensity = intensity * 0.8;
                if (this.lights?.point3) this.lights.point3.intensity = intensity * 0.7;
            });
        }

        // Hemisphere light control
        const hemisphereSlider = document.getElementById('hemisphere-intensity');
        if (hemisphereSlider) {
            hemisphereSlider.addEventListener('input', (e) => {
                if (this.lights?.hemisphere) {
                    this.lights.hemisphere.intensity = parseFloat(e.target.value);
                }
            });
        }
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        
        // Update controls
        this.controls.update();
        
        // Render scene
        this.renderer.render(this.scene, this.camera);
    }
}

// Initialize the 3D viewer when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new Room3DViewer();
});
