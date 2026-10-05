// Turns whatever GLTFLoader produced into the Dear United ink look: toon bands,
// colours pulled through the muted palette, warm "lamp" colours glowing.
// Ported from old-trafford/src/lego/render/materials.js and generalised from
// LEGO brick definitions to any glTF material.
//
// Highlight has two paths, because the two kinds of mesh differ:
//   - plain meshes swap to a highlighted twin of their material (cached);
//   - InstancedMesh (the LEGO stadium) uses instanceColor.r as a per-instance
//     highlight amount, read by the shader patch below, so one stand can light
//     up inside a mesh that holds bricks from all of them.
import * as THREE from 'three'
import { inkColor, GLOW, HIGHLIGHT, INK_GLSL, inkUniforms } from './palette.js'

let gradientMap = null
export function toonGradient() {
  if (gradientMap) return gradientMap
  // Low-contrast Chrona bands: 0.55 / 0.8 / 1.0
  const data = new Uint8Array([0.55, 0.8, 1.0].map((v) => Math.round(v * 255)))
  gradientMap = new THREE.DataTexture(data, 3, 1, THREE.RedFormat)
  gradientMap.minFilter = gradientMap.magFilter = THREE.NearestFilter
  gradientMap.generateMipmaps = false
  gradientMap.needsUpdate = true
  return gradientMap
}

const highlightUniform = { value: HIGHLIGHT.clone() }

function patch(material, { inkTexture = false } = {}) {
  const ink = inkUniforms()
  material.onBeforeCompile = (shader) => {
    shader.uniforms.uHighlight = highlightUniform
    Object.assign(shader.uniforms, ink)
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform vec3 uHighlight;\n' + (inkTexture ? INK_GLSL : ''))
      .replace(
        '#include <map_fragment>',
        inkTexture
          ? `#ifdef USE_MAP
  vec4 texel = texture2D( map, vMapUv );
  vec3 s = inkMapSRGB( pow( texel.rgb, vec3( 1.0 / 2.2 ) ) );
  diffuseColor.rgb *= pow( s, vec3( 2.2 ) );
#endif`
          : '#include <map_fragment>'
      )
      .replace(
        '#include <color_fragment>',
        `#if defined( USE_COLOR ) || defined( USE_INSTANCING_COLOR )
  diffuseColor.rgb = mix( diffuseColor.rgb, uHighlight, vColor.r * 0.75 );
  totalEmissiveRadiance += uHighlight * vColor.r * 0.35;
#endif`
      )
  }
  material.customProgramCacheKey = () => (inkTexture ? 'ink-tex' : 'ink')
  return material
}

const cache = new Map()

/** The ink twin of a glTF material. Cached per source material. */
export function inkMaterial(src) {
  if (cache.has(src)) return cache.get(src)
  const c = src.color || new THREE.Color(1, 1, 1)
  const lin = [c.r, c.g, c.b]
  const m = new THREE.MeshToonMaterial({ color: inkColor(lin), gradientMap: toonGradient() })
  m.name = src.name
  m.side = src.side
  const glass = /glass|transparent/i.test(src.name) || src.transparent || src.opacity < 1
  if (glass) {
    m.transparent = true
    m.opacity = Math.min(src.opacity ?? 0.35, 0.5)
    m.depthWrite = false
    m.emissive = GLOW.clone().multiplyScalar(0.18)
  } else if (src.map) {
    m.map = src.map
    m.color.set(0xffffff)
    // Stickers sit flush on the brick behind them and z-fight without this.
    m.polygonOffset = true
    m.polygonOffsetFactor = -2
    m.polygonOffsetUnits = -2
  }
  // Glow goes by NAME only. The colour test Dear United uses also catches
  // sandstone and beige walls (Big Ben lit up like a lamp), so dioramas opt in
  // by calling a material lamp-*, glow-* or exactly gold; the LEGO set's own yellow and
  // beige keep glowing as they do on Dear United.
  // (nightglow-* is excluded: it only glows at night, see below.)
  if (!glass && !/^nightglow-/i.test(src.name) && /lamp|glow|flood|^gold$|^yellow$|^beige$/i.test(src.name)) {
    m.color.copy(GLOW)
    m.emissive = GLOW.clone().multiplyScalar(0.55)
  }
  // Screens and billboards (neon-*) glow in their OWN colour, un-muted: Times
  // Square and Shibuya are supposed to be the loudest things in the dome.
  if (!glass && /^neon-/i.test(src.name)) {
    m.color.setRGB(c.r, c.g, c.b)
    m.emissive = new THREE.Color(c.r, c.g, c.b).multiplyScalar(0.7)
  }
  // nightglow-*: an ordinary colour by day that lights up after dark (the
  // floodlit minarets of Bukhara). setNight() blends between the two.
  if (!glass && /^nightglow-/i.test(src.name)) {
    const own = new THREE.Color(c.r, c.g, c.b)
    // Brick and clay warm toward floodlight gold; tiles and domes keep their
    // turquoise and just shine.
    const warm = /dome|tile/i.test(src.name) ? 0.08 : 0.4
    m.userData.nightGlow = { day: m.color.clone(), night: own.clone().lerp(GLOW, warm), emissive: own.clone().lerp(GLOW, warm + 0.05) }
    m.emissive = new THREE.Color(0, 0, 0)
  }
  patch(m, { inkTexture: !!m.map })
  m.userData.glass = glass
  cache.set(src, m)
  return m
}

/** Blend nightglow materials between day (t = 0) and night (t = 1). */
export function setNight(materials, t) {
  for (const m of materials) {
    const g = m.userData.nightGlow
    if (!g) continue
    m.color.lerpColors(g.day, g.night, t)
    m.emissive.copy(g.emissive).multiplyScalar(1.05 * t)
  }
}

/** A flat-colour ink material from an sRGB hex, for things the viewer builds. */
export function inkSolid(hex, { emissive = 0 } = {}) {
  const m = new THREE.MeshToonMaterial({ color: new THREE.Color(hex), gradientMap: toonGradient() })
  if (emissive) m.emissive = new THREE.Color(hex).multiplyScalar(emissive)
  return patch(m)
}

const twins = new WeakMap()
/** The highlighted twin of an ink material (for plain, non-instanced meshes). */
export function highlightTwin(m) {
  let t = twins.get(m)
  if (!t) {
    t = m.clone()
    t.color = m.color.clone().lerp(HIGHLIGHT, 0.6)
    t.emissive = HIGHLIGHT.clone().multiplyScalar(0.3)
    t.onBeforeCompile = m.onBeforeCompile
    t.customProgramCacheKey = m.customProgramCacheKey
    twins.set(m, t)
  }
  return t
}

/** Swap every material in a loaded city for its ink twin. Returns the
 *  materials created, so the caller can dispose them with the city. */
export function inkify(root) {
  const made = new Set()
  root.traverse((o) => {
    if (!o.isMesh) return
    const conv = (mm) => { const n = inkMaterial(mm); made.add(n); return n }
    o.material = Array.isArray(o.material) ? o.material.map(conv) : conv(o.material)
    const glass = (Array.isArray(o.material) ? o.material : [o.material]).some((x) => x.userData.glass)
    if (glass) o.renderOrder = 2
    o.userData.glass = glass
    if (o.isInstancedMesh && !o.instanceColor) {
      o.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(o.count * 3), 3)
    }
  })
  return made
}

export function forgetMaterials(list) {
  for (const m of list) {
    for (const [k, v] of cache) if (v === m) cache.delete(k)
    const t = twins.get(m)
    if (t) t.dispose()
    m.dispose()
  }
}
