"""
build-globe.py — the travel gallery's globe, modelled from data.

Every country in Natural Earth 110m becomes its own raised piece on an ocean
sphere: a curved top cap plus side walls, like a puzzle piece pressed into a
ball. The walls are what make the ink renderer draw borders, so neighbouring
countries are given slightly different heights on purpose.

Run headless (writes the .glb the site loads, and a .blend to keep editing):

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python scripts/blender/build-globe.py

Conventions the viewer (src/gallery/globe.js) relies on:
  - ocean radius 1.0, centred at the origin;
  - each country is a mesh named CTRY-<ISO2>, e.g. CTRY-GB, CTRY-KZ;
  - lat/lon (deg) -> Blender (cos la cos lo, cos la sin lo, sin la). After the
    glTF Y-up conversion that is three.js (cos la cos lo, sin la, -cos la sin lo).
  - walls reach well below the ocean, so the viewer can lift a country by
    scaling it about the origin without opening a gap underneath.
"""

import json
import math
import os
import random

import bpy
import bmesh
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, ".cache", "ne110.geojson")
OUT_GLB = os.path.join(REPO, "public", "models", "gallery", "globe.glb")
OUT_BLEND = os.path.expanduser("~/Downloads/Models/travel/globe.blend")

TOP = 1.012          # land surface, before per-country jitter
JITTER = 0.0045      # height variation between countries, so borders ink
BOTTOM = 0.955       # wall foot, safely under the ocean even when lifted
STEP = 2.5           # degrees: max boundary segment and interior grid pitch

OCEAN = (0.106, 0.165, 0.286)   # linear rgb; the viewer re-inks everything
LAND = (0.62, 0.64, 0.66)


def iso_of(props):
    eh = props.get("ISO_A2_EH")
    iso = eh if eh and eh != "-99" else props.get("ISO_A2")
    return None if not iso or iso == "-99" else iso


def to_sphere(lon, lat, r):
    lo, la = math.radians(lon), math.radians(lat)
    return Vector((math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la))) * r


def densify(ring):
    """Split ring edges longer than STEP so the cap follows the curvature."""
    out = []
    pts = ring[:-1] if ring[0] == ring[-1] else ring
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]
        n = max(1, math.ceil(max(abs(b[0] - a[0]), abs(b[1] - a[1])) / STEP))
        for k in range(n):
            t = k / n
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def point_in_ring(x, y, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def polygon_tris(rings):
    """Constrained Delaunay of one polygon (outer ring + holes) in lon/lat,
    with a grid of interior points so no triangle is too big to bend."""
    rings = [densify(r) for r in rings]
    verts, faces = [], []
    for r in rings:
        faces.append(list(range(len(verts), len(verts) + len(r))))
        verts.extend(r)
    outer = rings[0]
    xs = [p[0] for p in outer]
    ys = [p[1] for p in outer]
    g = STEP
    x = math.floor(min(xs) / g) * g + g / 2
    while x < max(xs):
        y = math.floor(min(ys) / g) * g + g / 2
        while y < max(ys):
            if point_in_ring(x, y, outer) and not any(point_in_ring(x, y, h) for h in rings[1:]):
                verts.append((x, y))
            y += g
        x += g
    out_v, _e, out_f, *_ = delaunay_2d_cdt([Vector(p) for p in verts], [], faces, 2, 1e-7)
    return [(v.x, v.y) for v in out_v], [list(f) for f in out_f]


def build_country(name, polys, top):
    bm = bmesh.new()
    for rings in polys:
        v2, f2 = polygon_tris(rings)
        used = sorted({i for f in f2 for i in f})
        top_v = {}
        bot_v = {}
        for i in used:
            lon, lat = v2[i]
            top_v[i] = bm.verts.new(to_sphere(lon, lat, top))
            bot_v[i] = bm.verts.new(to_sphere(lon, lat, BOTTOM))
        edge_count = {}
        for f in f2:
            try:
                face = bm.faces.new([top_v[i] for i in f])
                face.smooth = True
            except ValueError:
                continue
            for k in range(len(f)):
                a, b = f[k], f[(k + 1) % len(f)]
                key = (min(a, b), max(a, b))
                edge_count[key] = edge_count.get(key, 0) + 1
                edge_count.setdefault(("dir",) + key, (a, b))
        # Boundary edges belong to exactly one triangle; extrude those down.
        for key, n in list(edge_count.items()):
            if key[0] == "dir" or n != 1:
                continue
            a, b = edge_count[("dir",) + key]
            try:
                wall = bm.faces.new([top_v[b], top_v[a], bot_v[a], bot_v[b]])
                wall.smooth = False
            except ValueError:
                pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # Outward-facing check: recalc can flip a whole closed-less shell inward.
    for f in bm.faces:
        if f.smooth and f.normal.dot(f.calc_center_median()) < 0:
            f.normal_flip()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    return obj


def material(name, rgb, rough=0.9):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    return m


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    random.seed(11)
    col = bpy.data.collections.new("Globe")
    bpy.context.scene.collection.children.link(col)

    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=1.0)
    ocean = bpy.context.active_object
    ocean.name = "OCEAN"
    ocean.data.name = "OCEAN"
    for p in ocean.data.polygons:
        p.use_smooth = True
    for c in ocean.users_collection:
        c.objects.unlink(ocean)
    col.objects.link(ocean)
    ocean.data.materials.append(material("ocean", OCEAN, 0.6))

    land = material("land", LAND)
    data = json.load(open(SRC))
    seen = set()
    for feat in data["features"]:
        props = feat["properties"]
        iso = iso_of(props)
        if not iso or iso in seen:
            continue
        seen.add(iso)
        geom = feat["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        top = TOP + random.uniform(-JITTER / 2, JITTER / 2)
        obj = build_country(f"CTRY-{iso}", polys, top)
        obj["country"] = props["NAME"]
        obj.data.materials.append(land)
        col.objects.link(obj)

    print(f"[globe] {len(seen)} countries")
    os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=OUT_GLB,
        export_format="GLB",
        export_apply=True,
        export_extras=True,
        export_materials="EXPORT",
        export_normals=True,
        export_texcoords=False,
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=7,
        export_draco_position_quantization=14,
        export_draco_normal_quantization=10,
    )
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    print(f"[globe] wrote {OUT_GLB} and {OUT_BLEND}")


main()
