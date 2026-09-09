// ============================================================================
// Explicit GPU cleanup
// ----------------------------------------------------------------------------
// three.js frees nothing on its own. Removing an object from a scene drops the
// JavaScript reference, but its geometry and every texture it points at stay
// resident in the driver until dispose() is called on each one, which fires the
// event the renderer's internal caches listen for.
//
// The room never needed this: it loads one model and keeps it forever. The
// gallery swaps a city every time you click a country, so without this every
// city ever visited leaks its textures until the tab is reaped.
// ============================================================================

// Every texture-bearing slot across the built-in materials. Walking
// Object.values(material) and duck-typing on `.isTexture` looks tidier and is
// wrong: it also walks userData and picks up textures we do not own, so we end
// up disposing atlases something else is still drawing with.
const TEXTURE_KEYS = [
    'map', 'lightMap', 'aoMap', 'emissiveMap', 'bumpMap', 'normalMap',
    'displacementMap', 'roughnessMap', 'metalnessMap', 'alphaMap',
    'envMap', 'specularMap', 'gradientMap', 'matcap',
    'clearcoatMap', 'clearcoatNormalMap', 'clearcoatRoughnessMap',
    'iridescenceMap', 'iridescenceThicknessMap',
    'sheenColorMap', 'sheenRoughnessMap',
    'transmissionMap', 'thicknessMap', 'specularIntensityMap', 'specularColorMap',
];

function disposeMaterial(material, seen) {
    if (!material || seen.has(material)) return;
    seen.add(material);

    for (const key of TEXTURE_KEYS) {
        const tex = material[key];
        // userData.shared is our own opt-out, set at load time on anything handed
        // to more than one city. Nothing in three.js sets it.
        if (tex && tex.isTexture && !tex.userData?.shared && !seen.has(tex)) {
            seen.add(tex);
            tex.dispose();
        }
    }
    material.dispose();
}

/**
 * Detach a subtree and release everything it owns.
 *
 * Handles the two shapes that actually bite: a mesh whose `material` is an
 * ARRAY (how a multi-slot Blender mesh arrives), and meshes that SHARE a
 * material or geometry, which a naive traverse would dispose once per user.
 *
 * @param {THREE.Object3D} root
 * @returns {{geometries: number, materials: number, textures: number}} counts,
 *          for asserting in dev that a swap actually gave everything back.
 */
export function disposeObject3D(root) {
    const counts = { geometries: 0, materials: 0, textures: 0 };
    if (!root) return counts;

    root.parent?.remove(root);

    const seen = new Set();
    const geoSeen = new Set();

    root.traverse((obj) => {
        if (obj.geometry && !geoSeen.has(obj.geometry)) {
            geoSeen.add(obj.geometry);
            obj.geometry.dispose();
            counts.geometries++;
        }

        const mat = obj.material;
        if (!mat) return;

        if (Array.isArray(mat)) {
            for (const m of mat) disposeMaterial(m, seen);
        } else {
            disposeMaterial(mat, seen);
        }

        obj.material = null;
    });

    // Split the combined tally into materials vs textures.
    let tex = 0;
    for (const item of seen) if (item.isTexture) tex++;
    counts.textures = tex;
    counts.materials = seen.size - tex;

    root.clear();
    return counts;
}
