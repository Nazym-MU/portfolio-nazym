#!/usr/bin/env node
/**
 * build-world-map.mjs
 *
 * Turns Natural Earth country boundaries into `src/data/world-map.js`: one SVG
 * path per country, keyed by ISO code, in a plain equirectangular projection.
 *
 * Run once (or when the country list changes). The output is committed, so the
 * site itself needs no geo dependency and makes no network request for it.
 *
 *   node scripts/build-world-map.mjs [path/to/ne_110m_admin_0_countries.geojson]
 *
 * Source: https://github.com/nvkelso/natural-earth-vector (public domain).
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const IN = process.argv[2] || resolve(__dirname, '../.cache/ne110.geojson');
const OUT = resolve(__dirname, '../src/data/world-map.js');

// Equirectangular: longitude and latitude map straight onto x and y. Simple,
// undistorted near the equator, and it keeps countries where people expect
// them on a rectangle. Antarctica is dropped: it eats a third of the height
// and nobody is clicking it.
const W = 2000, H = 1000;
const MIN_LAT = -60;

const project = ([lon, lat]) => [
    ((lon + 180) / 360) * W,
    ((90 - lat) / 180) * H,
];

// Douglas-Peucker. At 110m resolution the raw rings carry far more detail than
// a 2000px-wide map can show, and the file is mostly wasted decimals.
function simplify(points, tolerance) {
    if (points.length < 3) return points;
    let maxDist = 0, index = 0;
    const [ax, ay] = points[0];
    const [bx, by] = points[points.length - 1];
    const dx = bx - ax, dy = by - ay;
    const len = Math.hypot(dx, dy) || 1;

    for (let i = 1; i < points.length - 1; i++) {
        const [px, py] = points[i];
        const dist = Math.abs((px - ax) * dy - (py - ay) * dx) / len;
        if (dist > maxDist) { maxDist = dist; index = i; }
    }
    if (maxDist <= tolerance) return [points[0], points[points.length - 1]];
    return [
        ...simplify(points.slice(0, index + 1), tolerance).slice(0, -1),
        ...simplify(points.slice(index), tolerance),
    ];
}

const round = (n) => Math.round(n * 10) / 10;

// Douglas-Peucker measures deviation from the chord between the FIRST and LAST
// points. On a closed ring those coincide, the chord has zero length, and every
// point measures as zero deviation, so the whole country collapses to a dot.
// Split the ring at the point farthest from the start and simplify each half.
function simplifyRing(pts, tolerance) {
    if (pts.length < 4) return pts;
    const [sx, sy] = pts[0];
    let far = 1, farDist = -1;
    for (let i = 1; i < pts.length; i++) {
        const d = Math.hypot(pts[i][0] - sx, pts[i][1] - sy);
        if (d > farDist) { farDist = d; far = i; }
    }
    const first = simplify(pts.slice(0, far + 1), tolerance);
    const second = simplify(pts.slice(far), tolerance);
    return [...first.slice(0, -1), ...second];
}

function ringToPath(ring, tolerance) {
    let pts = ring.map(project).filter(([, y]) => Number.isFinite(y));
    pts = simplifyRing(pts, tolerance);
    if (pts.length < 3) return '';
    // A ring smaller than a couple of pixels is invisible; skip the bytes.
    const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
    if (Math.max(...xs) - Math.min(...xs) < 1.5 && Math.max(...ys) - Math.min(...ys) < 1.5) return '';
    return 'M' + pts.map(([x, y]) => `${round(x)} ${round(y)}`).join('L') + 'Z';
}

function geometryToPath(geom, tolerance) {
    if (!geom) return '';
    const polys = geom.type === 'Polygon' ? [geom.coordinates]
        : geom.type === 'MultiPolygon' ? geom.coordinates
            : [];
    // Outer ring only. Holes (lakes) are not worth the bytes at this scale.
    return polys.map((poly) => ringToPath(poly[0], tolerance)).filter(Boolean).join('');
}

const geo = JSON.parse(readFileSync(IN, 'utf8'));
const out = {};
let skipped = 0;

for (const f of geo.features) {
    const p = f.properties;
    const iso = p.ISO_A2_EH && p.ISO_A2_EH !== '-99' ? p.ISO_A2_EH : p.ISO_A2;
    const name = p.NAME || p.name;
    if (!iso || iso === '-99' || name === 'Antarctica') { skipped++; continue; }

    // Clip the far south before projecting, so dropping Antarctica does not
    // leave stray slivers. A ring is an array of [lon, lat] pairs; a Polygon is
    // an array of rings; a MultiPolygon is an array of Polygons.
    const clipRing = (ring) => ring.filter(([, lat]) => lat >= MIN_LAT);
    const clipPoly = (poly) => poly.map(clipRing).filter((r) => r.length > 2);
    const geom = f.geometry.type === 'Polygon'
        ? { type: 'Polygon', coordinates: clipPoly(f.geometry.coordinates) }
        : { type: 'MultiPolygon', coordinates: f.geometry.coordinates.map(clipPoly).filter((poly) => poly.length) };

    const d = geometryToPath(geom, 0.8);
    if (!d) { skipped++; continue; }
    out[iso] = { name, d };
}

const body = Object.entries(out)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([iso, v]) => `    ${iso}: { name: ${JSON.stringify(v.name)}, d: ${JSON.stringify(v.d)} },`)
    .join('\n');

writeFileSync(OUT, `// Generated by scripts/build-world-map.mjs. Do not edit by hand.
// Country outlines from Natural Earth 110m (public domain), projected
// equirectangular onto a ${W}x${H} viewBox, Douglas-Peucker simplified, and
// rounded to 0.1px. Antarctica and anything below ${MIN_LAT} degrees are dropped.
export const MAP_WIDTH = ${W};
export const MAP_HEIGHT = ${H};

export const COUNTRY_PATHS = {
${body}
};
`);

const bytes = Buffer.byteLength(readFileSync(OUT));
console.log(`${Object.keys(out).length} countries written (${skipped} skipped), ${(bytes / 1024).toFixed(0)}KB -> src/data/world-map.js`);
