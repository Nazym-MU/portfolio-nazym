#!/usr/bin/env node
/**
 * build-manchester.mjs
 *
 * Packs the LEGO Old Trafford from the Dear United site into one ordinary
 * city .glb for the travel gallery: every brick becomes an instance
 * (EXT_mesh_gpu_instancing, which GLTFLoader turns into InstancedMesh), the
 * stadium is scaled onto a round base like every other diorama, and each brick
 * instance is tagged with its stand (node extras) so a click resolves to a
 * stand and its photos.
 *
 *   node scripts/build-manchester.mjs [path/to/old-trafford/public/models/lego]
 *
 * Re-run whenever the LEGO export (lego-trafford/tools/export-lego.py) changes.
 */
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { NodeIO, MathUtils } from '@gltf-transform/core';
import { ALL_EXTENSIONS, EXTMeshGPUInstancing } from '@gltf-transform/extensions';
import { draco, prune, dedup } from '@gltf-transform/functions';
import draco3d from 'draco3dgltf';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SRC = resolve(process.argv[2] || resolve(__dirname, '../../old-trafford/public/models/lego'));
const OUT = resolve(__dirname, '../public/models/gallery/cities/manchester.glb');

// Source collection -> clickable object id. Seats belong to their stand.
const STANDS = {
    'Field': 'pitch',
    'East-Stand': 'east-stand',
    'Seats-East-Stand': 'east-stand',
    'Stretford-End': 'stretford-end',
    'Stretford-End-seats': 'stretford-end',
    'SAF-stand': 'sir-alex-ferguson-stand',
    'SBC-stand': 'sir-bobby-charlton-stand',
};

// Where the stadium sits on the base: its footprint's half-diagonal is scaled
// to this radius, leaving a ring of pavement around it under the dome.
const FIT_RADIUS = 0.97;
const BASE = { r: 1.0, depth: 0.14, segs: 96 };
// sRGB picks for the base, matching the other dioramas' plinths.
const PAVEMENT = [0.62, 0.64, 0.66];
const EARTH = [0.55, 0.42, 0.30];

const lin = (c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);

const io = new NodeIO()
    .registerExtensions(ALL_EXTENSIONS)
    .registerDependencies({
        'draco3d.decoder': await draco3d.createDecoderModule(),
        'draco3d.encoder': await draco3d.createEncoderModule(),
    });

const doc = await io.read(resolve(SRC, 'types.glb'));
const info = JSON.parse(readFileSync(resolve(SRC, 'instances.json'), 'utf8'));
const bin = readFileSync(resolve(SRC, 'instances.bin'));
const M = new Float32Array(bin.buffer, bin.byteOffset, bin.byteLength / 4);

const root = doc.getRoot();
const buffer = root.listBuffers()[0];
const meshByName = new Map(root.listMeshes().map((m) => [m.getName(), m]));
const instancing = doc.createExtension(EXTMeshGPUInstancing).setRequired(true);

// The bricks' own palette. The site re-inks every colour, so these stay true.
const brickMats = info.materials.map((def) => {
    const m = doc.createMaterial(def.name).setBaseColorFactor([...def.color, 1]);
    if (def.kind === 'glass') m.setAlphaMode('BLEND').setBaseColorFactor([...def.color, def.opacity ?? 0.35]);
    return m;
});
const dsCache = new Map();
const doubleSided = (m) => {
    if (!dsCache.has(m)) dsCache.set(m, m.clone().setDoubleSided(true));
    return dsCache.get(m);
};

// ---- group bricks by (type, material) -------------------------------------
// One instanced node per pair keeps draw calls where Dear United has them
// (splitting by stand as well tripled them). Which stand each instance belongs
// to rides along in the node's extras, so a click still resolves to a stand.
const groups = new Map();
for (let i = 0; i < info.count; i++) {
    const [ti, mi] = info.bricks[i];
    const key = `${ti}|${mi}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(i);
}
const OBJECT_IDS = [...new Set(Object.values(STANDS))];
const objectOf = (bi) => OBJECT_IDS.indexOf(STANDS[info.groups[info.bricks[bi][2]]]);

// ---- framing: centre the footprint, sit it on y = 0, scale onto the base ---
const { min, max } = info.bounds;
const cx = (min[0] + max[0]) / 2, cz = (min[2] + max[2]) / 2;
const half = Math.hypot(max[0] - min[0], max[2] - min[2]) / 2;
const S = FIT_RADIUS / half;

const scene = doc.createScene('manchester');
const stadium = doc.createNode('DECO-stadium')
    .setScale([S, S, S])
    .setTranslation([-cx * S, -min[1] * S, -cz * S]);

const meshCache = new Map();
function meshFor(ti, mi) {
    const key = `${ti}|${mi}`;
    if (meshCache.has(key)) return meshCache.get(key);
    const type = info.types[ti];
    const src = meshByName.get(type.name);
    if (!src) throw new Error(`types.glb has no mesh "${type.name}"`);
    const def = info.materials[mi];
    const prims = src.listPrimitives();
    const mesh = doc.createMesh(`${type.name}|${def.name}`);
    for (const p of prims) {
        // Multi-part bricks (stickers, two-tone) keep each part's own colour;
        // everything else takes the brick's material. Glass is always glass.
        let mat = prims.length > 1 && def.kind !== 'glass' ? p.getMaterial() : brickMats[mi];
        if (def.kind === 'sticker' && prims.length === 1) mat = p.getMaterial() || mat;
        if (type.doubleSided && mat) mat = doubleSided(mat);
        mesh.addPrimitive(p.clone().setMaterial(mat));
    }
    meshCache.set(key, mesh);
    return mesh;
}

const t = [0, 0, 0], r = [0, 0, 0, 1], s = [1, 1, 1];
for (const [key, list] of groups) {
    const [ti, mi] = key.split('|');
    const T = new Float32Array(list.length * 3);
    const R = new Float32Array(list.length * 4);
    const Sc = new Float32Array(list.length * 3);
    list.forEach((bi, k) => {
        const o = bi * 12;
        // Row-major 3x4 -> column-major 4x4.
        const m = [
            M[o], M[o + 4], M[o + 8], 0,
            M[o + 1], M[o + 5], M[o + 9], 0,
            M[o + 2], M[o + 6], M[o + 10], 0,
            M[o + 3], M[o + 7], M[o + 11], 1,
        ];
        MathUtils.decompose(m, t, r, s);
        T.set(t, k * 3); R.set(r, k * 4); Sc.set(s, k * 3);
    });
    const acc = (arr, type) => doc.createAccessor().setType(type).setArray(arr).setBuffer(buffer);
    const inst = instancing.createInstancedMesh()
        .setAttribute('TRANSLATION', acc(T, 'VEC3'))
        .setAttribute('ROTATION', acc(R, 'VEC4'))
        .setAttribute('SCALE', acc(Sc, 'VEC3'));
    const node = doc.createNode(`DECO-bricks:${info.types[+ti].name}`)
        .setMesh(meshFor(+ti, +mi))
        .setExtension('EXT_mesh_gpu_instancing', inst)
        // The viewer reads these as OBJ-<objectIds[instanceObject[i]]>.
        .setExtras({ objectIds: OBJECT_IDS, instanceObject: list.map(objectOf) });
    stadium.addChild(node);
}

// ---- the base --------------------------------------------------------------
function basePrimitive(top) {
    const pos = [], nrm = [], idx = [];
    const { r: R0, depth, segs } = BASE;
    if (top) {
        pos.push(0, 0, 0); nrm.push(0, 1, 0);
        for (let i = 0; i <= segs; i++) {
            const a = (i / segs) * Math.PI * 2;
            pos.push(Math.cos(a) * R0, 0, -Math.sin(a) * R0); nrm.push(0, 1, 0);
            if (i) idx.push(0, i, i + 1);
        }
    } else {
        for (let i = 0; i <= segs; i++) {
            const a = (i / segs) * Math.PI * 2, x = Math.cos(a), z = -Math.sin(a);
            pos.push(x * R0, 0, z * R0, x * R0, -depth, z * R0);
            nrm.push(x, 0, z, x, 0, z);
            if (i) { const b = (i - 1) * 2; idx.push(b, b + 1, b + 2, b + 2, b + 1, b + 3); }
        }
        // underside
        const c = pos.length / 3;
        pos.push(0, -depth, 0); nrm.push(0, -1, 0);
        for (let i = 0; i <= segs; i++) {
            const a = (i / segs) * Math.PI * 2;
            pos.push(Math.cos(a) * R0, -depth, -Math.sin(a) * R0); nrm.push(0, -1, 0);
            if (i) idx.push(c, c + i + 1, c + i);
        }
    }
    const mat = doc.createMaterial(top ? 'pavement' : 'earth')
        .setBaseColorFactor([...(top ? PAVEMENT : EARTH).map(lin), 1]);
    return doc.createPrimitive()
        .setAttribute('POSITION', doc.createAccessor().setType('VEC3').setArray(new Float32Array(pos)).setBuffer(buffer))
        .setAttribute('NORMAL', doc.createAccessor().setType('VEC3').setArray(new Float32Array(nrm)).setBuffer(buffer))
        .setIndices(doc.createAccessor().setType('SCALAR').setArray(new Uint16Array(idx)).setBuffer(buffer))
        .setMaterial(mat);
}
const baseMesh = doc.createMesh('DECO-base').addPrimitive(basePrimitive(true)).addPrimitive(basePrimitive(false));
const base = doc.createNode('DECO-base').setMesh(baseMesh);

// Swap the type library's scene for the city.
for (const sc of root.listScenes()) if (sc !== scene) sc.dispose();
for (const n of root.listNodes()) if (!n.getMesh()?.getName()?.includes('|') 
    && !n.getName().startsWith('DECO-') && !n.getExtension('EXT_mesh_gpu_instancing')) n.dispose();
scene.addChild(base).addChild(stadium);
root.setDefaultScene(scene);

await doc.transform(
    prune(),
    dedup(),
    draco({ method: 'edgebreaker', quantizePosition: 14, quantizeNormal: 10 }),
);
await io.write(OUT, doc);

const tris = [...groups.values()].length;
console.log(`[manchester] ${info.count} bricks in ${tris} instanced nodes (draw calls), scale ${S.toFixed(3)} -> ${OUT}`);
