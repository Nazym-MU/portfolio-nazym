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
            alpha: false,
            premultipliedAlpha: false
        });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.setClearColor(0x1a1a2e, 1.0);
        
        // Shadow and lighting settings
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.outputColorSpace = THREE.SRGBColorSpace;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.5;
        this.renderer.useLegacyLights = false;
        this.renderer.physicallyCorrectLights = true;

        const container = document.getElementById('canvas-container');
        if (container) {
            container.appendChild(this.renderer.domElement);
            this.renderer.domElement.style.position = 'absolute';
            this.renderer.domElement.style.top = '0';
            this.renderer.domElement.style.left = '0';
            this.renderer.domElement.style.zIndex = '1';
            this.renderer.domElement.style.display = 'block';
        }

        // Setup controls, lighting, model, and events
        this.setupControls();
        this.setupLighting();
        this.loadModel();
        this.setupEventListeners();
        this.animate();
    }

    setupControls() {
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        
        this.controls.minPolarAngle = Math.PI / 6; // 30 degrees from top
        this.controls.maxPolarAngle = Math.PI / 2.2; // Not quite 90 degrees
        
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

        const hemisphereLight = new THREE.HemisphereLight(0x87ceeb, 0x362d1d, 0.8);
        this.scene.add(hemisphereLight);

        const rimLight = new THREE.DirectionalLight(0x4a90e2, 1.0);
        rimLight.position.set(-10, 5, -10);
        this.scene.add(rimLight);

        this.lights = {
            ambient: ambientLight,
            directional: directionalLight,
            point1: pointLight1,
            point2: pointLight2,
            point3: pointLight3,
            hemisphere: hemisphereLight,
            rim: rimLight
        };
    }

    loadModel() {
        // Setup DRACO loader for compression
        const dracoLoader = new DRACOLoader();
        dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/');
        dracoLoader.preload();
        
        const loader = new GLTFLoader();
        loader.setDRACOLoader(dracoLoader);


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
                        const hoverMeshes = [
                            'map', 'almaty', 'notebook', 'resume', 'aboutme', 'projects', 'macbook', 
                            'Plane012_1', 'jersey', 'Plane003_1', 'ggb', 
                        ];
                        const isHoverMesh = hoverMeshes.some(meshName => 
                            child.name.toLowerCase().includes(meshName.toLowerCase())
                        );
                        
                        if (isHoverMesh) {
                            this.hoverObjects.push(child);
                            // Store initial transform data for hover effects
                            child.userData.initialScale = new THREE.Vector3().copy(child.scale);
                            child.userData.initialPosition = new THREE.Vector3().copy(child.position);
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
                
                // Hide loading screen with modern animation
                const loadingScreen = document.getElementById('loading');
                if (loadingScreen) {
                    loadingScreen.classList.add('fade-out');
                    setTimeout(() => {
                        loadingScreen.style.display = 'none';
                    }, 500);
                }
                
                // Show welcome popup after a brief delay
                setTimeout(() => {
                    this.showWelcomePopup();
                }, 0);
                
            },
            (progress) => {
                // Show loading progress with modern styling
                const percentComplete = (progress.loaded / progress.total) * 100;
                const loadingBar = document.getElementById('loading-bar');
                const loadingPercentage = document.getElementById('loading-percentage');
                
                if (loadingBar) {
                    loadingBar.style.width = `${percentComplete}%`;
                }
                if (loadingPercentage) {
                    loadingPercentage.textContent = `${Math.round(percentComplete)}%`;
                }
                
            },
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
        // Ignore clicks on UI elements
        if (event.target.closest('.popup') || 
            event.target.closest('.large-popup') ||
            event.target.tagName === 'BUTTON') {
            return;
        }

        if (this.currentHover) {
            this.handleMeshClick(this.currentHover);
        } else {
            // Manual raycasting check as fallback
            this.mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
            this.mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
            this.raycaster.setFromCamera(this.mouse, this.camera);
            
            if (this.model) {
                const allMeshes = [];
                this.model.traverse((child) => {
                    if (child.isMesh) {
                        allMeshes.push(child);
                    }
                });
                
                const intersects = this.raycaster.intersectObjects(allMeshes);
                if (intersects.length > 0) {
                    const clickedMesh = intersects[0].object;
                    
                    // Check if this mesh is interactive
                    if (this.hoverObjects.includes(clickedMesh)) {
                        this.handleMeshClick(clickedMesh);
                    }
                }
            }
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
        
    }

    resetHover(mesh) {
        if (!mesh.userData.isHoverable) return;
        
        // Reset to initial values
        mesh.scale.copy(mesh.userData.initialScale);
        mesh.position.copy(mesh.userData.initialPosition);
    }

    handleMeshClick(mesh) {
        const meshName = mesh.name.toLowerCase();
        
        // Handle different mesh interactions based on actual mesh names
        if (meshName.includes('resume')) {
            window.open('/Nazym Zhiyengaliyeva Resume.pdf', '_blank');
        } else if (meshName.includes('map')) {
            this.showMapPopup();
        } else if (meshName.includes('almaty')) {
            this.showAlmatyPopup();
        } else if (meshName.includes('notebook')) {
            this.showNotebookPopup();
        } else if (meshName.includes('aboutme') || meshName.includes('ggb')) {
            this.showAboutOverlay();
        } else if (meshName.includes('projects')) {
            this.showProjectsOverlay();
        } else if (meshName.includes('jersey')) {
            this.showJerseyPopup();
        } else if (meshName.includes('macbook') || meshName.includes('Plane003_1')) {
            this.showProjectsOverlay();
        } else if (meshName.includes('Plane012_1')) {
            this.showPhonePopup();
        }
        
        // Add click animation
        this.animateClick(mesh);
    }

    // Popup methods for small informational popups
    showMapPopup() {
        this.createPopup('map-popup', `
            <h3>🗺️ Travel & Adventure</h3>
            <p>I love traveling and these are the places I've been to!</p>
        `);
    }

    showAlmatyPopup() {
        this.createPopup('almaty-popup', `
            <h3>🏔️ Almaty, Kazakhstan</h3>
            <p>I'm from Almaty, Kazakhstan, a very special city to me. Known for its beautiful mountains and rich culture!</p>
        `);
    }

    showNotebookPopup() {
        this.createPopup('notebook-popup', `
            <h3>📓 My Blog</h3>
            <p>Welcome to my digital thoughts and experiences!</p>
            <a href="https://medium.com/@nazym" target="_blank" class="blog-btn">Visit My Medium Blog</a>
        `);
    }

    showJerseyPopup() {
        this.createPopup('jersey-popup', `
            <h3>⚽ Manchester United</h3>
            <p>Glory Glory Man United! I'm a passionate supporter of Manchester United and love everything about this incredible club.</p>
        `);
    }

    showPhonePopup() {
        this.createPopup('phone-popup', `
            <h3>📱 Always Connected</h3>
            <p>Ready to chat and collaborate! Feel free to reach out for any opportunities or just to say hello.</p>
        `);
    }

    // Large popup methods for detailed content
    showAboutOverlay() {
        this.createLargePopup('about-popup', `
            <div class="large-popup-header">
                <h3>About Me</h3>
                <button class="close-btn" onclick="this.closest('.large-popup').remove()">&times;</button>
            </div>
            <div class="large-popup-content">
                <div class="about-content">
                    <div class="about-text">
                        <h3>Hi, I'm Nazym Zhiyengaliyeva!</h3>
                        <p>I'm a passionate developer with experience in web development, 3D graphics, and user experience design. Originally from the beautiful city of Almaty, Kazakhstan, I bring a unique perspective to technology and design.</p>
                        
                        <h4>What I Do:</h4>
                        <ul>
                            <li>Frontend Development with React, Vue.js, and vanilla JavaScript</li>
                            <li>3D Graphics and WebGL with Three.js</li>
                            <li>Backend Development with Node.js and Python</li>
                            <li>UI/UX Design and User Experience</li>
                        </ul>

                        <h4>Technologies I Love:</h4>
                        <div class="tech-stack">
                            <span class="tech-item">JavaScript</span>
                            <span class="tech-item">TypeScript</span>
                            <span class="tech-item">React</span>
                            <span class="tech-item">Vue.js</span>
                            <span class="tech-item">Three.js</span>
                            <span class="tech-item">Node.js</span>
                            <span class="tech-item">Python</span>
                            <span class="tech-item">Blender</span>
                        </div>
                    </div>
                    
                    <div class="contact-info">
                        <h4>Let's Connect!</h4>
                        <div class="contact-links">
                            <p>📧 <a href="mailto:nazym.zhiyengaliyeva@example.com">nazym.zhiyengaliyeva@example.com</a></p>
                            <p>💼 <a href="https://linkedin.com/in/nazym-zhiyengaliyeva" target="_blank">LinkedIn Profile</a></p>
                            <p>🐙 <a href="https://github.com/nazym-zhiyengaliyeva" target="_blank">GitHub Profile</a></p>
                            <p>📝 <a href="https://medium.com/@nazym" target="_blank">Medium Blog</a></p>
                            <p>📱 <a href="tel:+1234567890">+1 (234) 567-890</a></p>
                        </div>
                    </div>
                </div>
            </div>
        `);
    }

    showProjectsOverlay() {
        this.createLargePopup('projects-popup', `
            <div class="large-popup-header">
                <h3>My Projects</h3>
                <button class="close-btn" onclick="this.closest('.large-popup').remove()">&times;</button>
            </div>
            <div class="large-popup-content">
                <div class="project-grid">
                    <div class="project-card">
                        <div class="project-image">
                            <div class="placeholder-img">🌐</div>
                        </div>
                        <div class="project-info">
                            <h3>3D Portfolio Website</h3>
                            <p>An interactive 3D portfolio built with Three.js and Blender, featuring Draco compression and responsive design.</p>
                            <div class="tech-stack">
                                <span class="tech-tag">Three.js</span>
                                <span class="tech-tag">Blender</span>
                                <span class="tech-tag">JavaScript</span>
                                <span class="tech-tag">WebGL</span>
                            </div>
                            <div class="project-links">
                                <a href="#" target="_blank" class="btn-demo">Live Demo</a>
                                <a href="#" target="_blank" class="btn-github">GitHub</a>
                            </div>
                        </div>
                    </div>

                    <div class="project-card">
                        <div class="project-image">
                            <div class="placeholder-img">⚛️</div>
                        </div>
                        <div class="project-info">
                            <h3>React Task Manager</h3>
                            <p>A modern task management application with drag-and-drop functionality, built with React and styled-components.</p>
                            <div class="tech-stack">
                                <span class="tech-tag">React</span>
                                <span class="tech-tag">TypeScript</span>
                                <span class="tech-tag">Styled Components</span>
                                <span class="tech-tag">Node.js</span>
                            </div>
                            <div class="project-links">
                                <a href="#" target="_blank" class="btn-demo">Live Demo</a>
                                <a href="#" target="_blank" class="btn-github">GitHub</a>
                            </div>
                        </div>
                    </div>

                    <div class="project-card">
                        <div class="project-image">
                            <div class="placeholder-img">🎮</div>
                        </div>
                        <div class="project-info">
                            <h3>WebGL Game Engine</h3>
                            <p>A lightweight 2D game engine built from scratch using WebGL and modern JavaScript, featuring physics and particle systems.</p>
                            <div class="tech-stack">
                                <span class="tech-tag">WebGL</span>
                                <span class="tech-tag">JavaScript</span>
                                <span class="tech-tag">GLSL</span>
                                <span class="tech-tag">Canvas</span>
                            </div>
                            <div class="project-links">
                                <a href="#" target="_blank" class="btn-demo">Live Demo</a>
                                <a href="#" target="_blank" class="btn-github">GitHub</a>
                            </div>
                        </div>
                    </div>

                    <div class="project-card">
                        <div class="project-image">
                            <div class="placeholder-img">📊</div>
                        </div>
                        <div class="project-info">
                            <h3>Data Visualization Dashboard</h3>
                            <p>An interactive dashboard for data visualization using D3.js and Vue.js, with real-time updates and responsive charts.</p>
                            <div class="tech-stack">
                                <span class="tech-tag">Vue.js</span>
                                <span class="tech-tag">D3.js</span>
                                <span class="tech-tag">Python</span>
                                <span class="tech-tag">Flask</span>
                            </div>
                            <div class="project-links">
                                <a href="#" target="_blank" class="btn-demo">Live Demo</a>
                                <a href="#" target="_blank" class="btn-github">GitHub</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `);
    }

    // Welcome popup for first-time visitors
    showWelcomePopup() {
        this.createLargePopup('welcome-popup', `
            <div class="welcome-popup-content">
                <div class="welcome-header">
                    <h1 class="welcome-title">Welcome to My Virtual Room!</h1>
                </div>
                
                <div class="welcome-body">
                    <p>This is my virtual space. <strong>Click on objects</strong> throughout the room to learn more about me</p>
    
                </div>
                
                <button class="welcome-button" onclick="this.closest('.large-popup').remove()">
                    Let's gooooooo!
                </button>
            </div>
        `);
    }

    createPopup(id, content) {
        // Remove existing popup if any
        const existing = document.getElementById(id);
        if (existing) existing.remove();

        const popup = document.createElement('div');
        popup.id = id;
        popup.className = 'popup';
        popup.innerHTML = `
            <div class="popup-content">
                <button class="close-btn" onclick="this.closest('.popup').remove()">&times;</button>
                ${content}
            </div>
        `;
        
        // Ensure popup is visible
        popup.style.cssText = `
            position: fixed !important;
            top: 50% !important;
            left: 50% !important;
            transform: translate(-50%, -50%) !important;
            z-index: 999999 !important;
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            background: rgba(15, 15, 35, 0.98) !important;
            border: 2px solid #4a90e2 !important;
            border-radius: 20px !important;
            color: white !important;
            max-width: 450px !important;
            width: 90% !important;
            padding: 1rem !important;
        `;
        
        document.body.appendChild(popup);

        // Auto-close after 8 seconds
        setTimeout(() => {
            if (document.getElementById(id)) {
                popup.remove();
            }
        }, 8000);
    }

    createLargePopup(id, content) {
        // Remove existing large popup if any
        const existing = document.getElementById(id);
        if (existing) existing.remove();

        const popup = document.createElement('div');
        popup.id = id;
        popup.className = 'large-popup';
        popup.innerHTML = content;
        
        // Ensure popup is visible
        popup.style.cssText = `
            position: fixed !important;
            top: 50% !important;
            left: 50% !important;
            transform: translate(-50%, -50%) !important;
            z-index: 999999 !important;
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            background: rgba(15, 15, 35, 0.98) !important;
            border: 2px solid #4a90e2 !important;
            border-radius: 24px !important;
            color: white !important;
            max-width: 90vw !important;
            max-height: 85vh !important;
            width: 850px !important;
            padding: 2rem !important;
        `;
        
        document.body.appendChild(popup);

        // Add click outside to close
        popup.addEventListener('click', (e) => {
            if (e.target === popup) {
                popup.remove();
            }
        });

        // Add escape key to close
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                popup.remove();
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);
        
        return popup;
    }

    animateClick(mesh) {
        if (!mesh.userData.isHoverable) return;
        
        // Quick scale animation for click feedback
        const originalScale = mesh.userData.initialScale.clone();
        const clickScale = originalScale.clone().multiplyScalar(0.9);
        
        // Scale down quickly
        mesh.scale.copy(clickScale);
        
        // Scale back to hover state after short delay
        setTimeout(() => {
            if (this.currentHover === mesh) {
                // If still hovering, return to hover scale
                mesh.scale.copy(originalScale).multiplyScalar(1.1);
            } else {
                // If not hovering, return to normal scale
                mesh.scale.copy(originalScale);
            }
        }, 150);
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        
        // Update controls
        this.controls.update();
        
        // Render the scene
        this.renderer.render(this.scene, this.camera);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.room3D = new Room3DViewer();
});
