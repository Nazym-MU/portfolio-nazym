"""
diorama_kit.py — shared pieces for the city dioramas.

Every city is a toy on a round base, built by a script in this folder that
imports this kit. The site wraps each one in the same glass dome, so a city
script only models the ground and what stands on it.

Naming contract with the viewer (src/gallery.js):
  OBJ-<id>   a clickable thing. Its photos live under the same id in
             src/data/places.js. A multi-part object is one mesh or an empty
             parent named OBJ-<id> with the parts beneath it.
             Give it a custom property orbit = <seconds per lap> and the
             viewer turns it slowly about the base's centre (the London bus).
  DECO-...   scenery: drawn, never clickable.
Materials are plain colours; the viewer re-maps every colour into the ink
palette, so author them as you would see them in daylight. A material whose
name contains "glass" is drawn see-through.

Units: base radius 1.0, ground top at z = 0, Blender Z-up. Keep everything
under the dome: inside a hemisphere of radius 1.0 centred on the origin.
"""

import math
import os
import random

import bpy
import bmesh
from mathutils import Vector, Matrix
from mathutils.geometry import delaunay_2d_cdt

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
GROUND_Z = 0.0

_materials = {}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _materials.clear()


def mat(name, rgb, alpha=1.0):
    """rgb in sRGB 0..1 (as you would pick it), stored linear like Blender wants."""
    if name in _materials:
        return _materials[name]
    m = bpy.data.materials.new(name)
    lin = tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb)
    m.diffuse_color = (*lin, alpha)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*lin, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.8
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
    _materials[name] = m
    return m


def obj_from_bm(name, bm, material=None, smooth=False, parent=None):
    if smooth:
        for f in bm.faces:
            f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if material:
        o.data.materials.append(material)
    if parent:
        o.parent = parent
    return o


def empty(name, parent=None):
    o = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(o)
    if parent:
        o.parent = parent
    return o


def join(name, objs):
    """Merge many objects into one mesh (one draw call). Keeps materials."""
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = name
    o.data.name = name
    return o


# ---- primitives -------------------------------------------------------------

def cylinder(name, r, h, at=(0, 0, 0), segs=24, material=None, r_top=None, parent=None, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                          radius1=r, radius2=r if r_top is None else r_top, depth=h)
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(at) + Vector((0, 0, h / 2)))
    o = obj_from_bm(name, bm, material, parent=parent)
    if smooth:
        smooth_by_angle(o)
    return o


def box(name, size, at=(0, 0, 0), material=None, parent=None):
    """size (x, y, z); `at` is the centre of the BOTTOM face."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, verts=bm.verts, vec=Vector(size))
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(at) + Vector((0, 0, size[2] / 2)))
    return obj_from_bm(name, bm, material, parent=parent)


def sphere(name, r, at=(0, 0, 0), material=None, parent=None, subdiv=3):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(at))
    return obj_from_bm(name, bm, material, smooth=True, parent=parent)


def lathe(name, profile, segs=32, at=(0, 0, 0), material=None, parent=None, smooth=True):
    """Revolve [(r, z), ...] bottom to top about Z. r == 0 points become a pole."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r <= 1e-6:
            rings.append([bm.verts.new((at[0], at[1], at[2] + z))])
            continue
        rings.append([bm.verts.new((at[0] + r * math.cos(2 * math.pi * i / segs),
                                    at[1] + r * math.sin(2 * math.pi * i / segs),
                                    at[2] + z)) for i in range(segs)])
    for a, b in zip(rings, rings[1:]):
        for i in range(segs):
            if len(a) == 1 and len(b) == 1:
                continue
            if len(a) == 1:
                bm.faces.new((a[0], b[i], b[(i + 1) % segs]))
            elif len(b) == 1:
                bm.faces.new((a[i], a[(i + 1) % segs], b[0]))
            else:
                bm.faces.new((a[i], a[(i + 1) % segs], b[(i + 1) % segs], b[i]))
    if len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))
    if len(rings[-1]) > 1:
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj_from_bm(name, bm, material, parent=parent)
    if smooth:
        smooth_by_angle(o)
    return o


def prism(name, outline, height, z0=0.0, holes=(), material=None, parent=None):
    """Extrude a 2D outline [(x, y), ...] (with optional hole outlines) upward."""
    verts, faces = [], []
    for ring in (outline, *holes):
        faces.append(list(range(len(verts), len(verts) + len(ring))))
        verts.extend(ring)
    out_v, _e, out_f, *_ = delaunay_2d_cdt([Vector(p) for p in verts], [], faces, 2, 1e-7)
    bm = bmesh.new()
    bot = [bm.verts.new((v.x, v.y, z0)) for v in out_v]
    top = [bm.verts.new((v.x, v.y, z0 + height)) for v in out_v]
    count = {}
    for f in out_f:
        bm.faces.new([top[i] for i in f])
        bm.faces.new([bot[i] for i in reversed(f)])
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            key = (min(a, b), max(a, b))
            count[key] = count.get(key, ()) + ((a, b),)
    for key, uses in count.items():
        if len(uses) == 1:
            a, b = uses[0]
            bm.faces.new((bot[a], bot[b], top[b], top[a]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from_bm(name, bm, material, parent=parent)


def tube(name, points, r, material=None, segs=8, parent=None):
    """A round tube along a polyline of 3D points (for arches, rails, cables)."""
    bm = bmesh.new()
    rings = []
    pts = [Vector(p) for p in points]
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        a = t.orthogonal().normalized()
        b = t.cross(a)
        rings.append([bm.verts.new(p + (a * math.cos(2 * math.pi * k / segs) +
                                        b * math.sin(2 * math.pi * k / segs)) * r) for k in range(segs)])
    for ra, rb in zip(rings, rings[1:]):
        for k in range(segs):
            bm.faces.new((ra[k], ra[(k + 1) % segs], rb[(k + 1) % segs], rb[k]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj_from_bm(name, bm, material, parent=parent)
    smooth_by_angle(o)
    return o


def place(o, rot=(0, 0, 0), at=(0, 0, 0)):
    """Rotate (degrees, XYZ) about the origin, then move. Baked into the mesh,
    so the exported node keeps an identity transform."""
    m = Matrix.Translation(at) @ Matrix.Rotation(math.radians(rot[2]), 4, "Z") \
        @ Matrix.Rotation(math.radians(rot[1]), 4, "Y") @ Matrix.Rotation(math.radians(rot[0]), 4, "X")
    o.data.transform(m)
    o.data.update()
    return o


def torus(name, R, r, at=(0, 0, 0), rot=(0, 0, 0), segs=48, tube_segs=8, material=None, parent=None):
    pts = [(R * math.cos(2 * math.pi * i / segs), R * math.sin(2 * math.pi * i / segs), 0)
           for i in range(segs + 1)]
    o = tube(name, pts, r, material=material, segs=tube_segs, parent=parent)
    return place(o, rot, at)


def grow(o, f, anchor):
    """Scale an object (and everything parented under it) by f about a point
    on the ground, baked into the meshes. Used to make the landmarks read
    bigger and fill the base without re-deriving every coordinate."""
    ax, ay, az = anchor
    m = Matrix.Translation((ax, ay, az)) @ Matrix.Scale(f, 4) @ Matrix.Translation((-ax, -ay, -az))
    stack = [o]
    while stack:
        x = stack.pop()
        if x.type == "MESH":
            x.data.transform(m)
            x.data.update()
        stack.extend(x.children)
    return o


def smooth_by_angle(o, angle=35):
    me = o.data
    for p in me.polygons:
        p.use_smooth = True
    bm = bmesh.new()
    bm.from_mesh(me)
    lim = math.radians(angle)
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0) > lim:
            e.smooth = False
    bm.to_mesh(me)
    bm.free()


# ---- scenery ----------------------------------------------------------------

def base(top_mat, side_mat, r=1.0, depth=0.14, segs=96):
    """The round plinth every city stands on. Top at z = 0."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                          radius1=r, radius2=r, depth=depth)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, -depth / 2))
    o = obj_from_bm("DECO-base", bm)
    o.data.materials.append(top_mat)
    o.data.materials.append(side_mat)
    for p in o.data.polygons:
        p.material_index = 0 if p.normal.z > 0.9 else 1
    return o


def inset_base(inner_mat, road_mat, side_mat, r=1.0, inner_r=0.8, rise=0.05, depth=0.14, segs=96):
    """A plinth with a raised inner disc, as if inset (I) and pulled up: the
    ring between the two circles is a road at z = 0, the land is at z = rise."""
    outer = base(road_mat, side_mat, r=r, depth=depth, segs=segs)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                          radius1=inner_r, radius2=inner_r, depth=rise)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, rise / 2))
    land = obj_from_bm("DECO-land", bm)
    land.data.materials.append(inner_mat)
    land.data.materials.append(side_mat)
    for p in land.data.polygons:
        p.material_index = 0 if p.normal.z > 0.9 else 1
    return outer, land


def ribbon(name, centerline, width, z=0.004, material=None, clip=0.985):
    """A flat strip along a 2D path (rivers, roads), clipped to the base."""
    pts = [Vector(p) for p in centerline if Vector(p).length < clip]
    left, right = [], []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        n = Vector((-t.y, t.x))
        left.append(p + n * width / 2)
        right.append(p - n * width / 2)
    bm = bmesh.new()
    L = [bm.verts.new((p.x, p.y, z)) for p in left]
    R = [bm.verts.new((p.x, p.y, z)) for p in right]
    for i in range(len(pts) - 1):
        bm.faces.new((R[i], R[i + 1], L[i + 1], L[i]))
    return obj_from_bm(name, bm, material)


def forest(name, count, material, keep_out, seed=3, r_max=0.92, h=(0.07, 0.12), extra=(),
           z=0.0, round_crowns=False, trunk_mat=None):
    """Scatter cone trees across the base, avoiding keep_out circles
    [(x, y, radius), ...]. Joined into one mesh so the lot is one draw call."""
    rnd = random.Random(seed)
    spots = list(extra)
    tries = 0
    while len(spots) < count + len(extra) and tries < count * 200:
        tries += 1
        a, d = rnd.uniform(0, 2 * math.pi), r_max * math.sqrt(rnd.random())
        x, y = d * math.cos(a), d * math.sin(a)
        if any((x - kx) ** 2 + (y - ky) ** 2 < kr ** 2 for kx, ky, kr in keep_out):
            continue
        if any((x - sx) ** 2 + (y - sy) ** 2 < 0.07 ** 2 for sx, sy in spots):
            continue
        spots.append((x, y))
    bm = bmesh.new()
    trunks = bmesh.new()
    for x, y in spots:
        hh = rnd.uniform(*h)
        if round_crowns:
            # A London plane: a short trunk and a ball of leaves.
            g = bmesh.ops.create_cone(trunks, cap_ends=True, cap_tris=False, segments=6,
                                      radius1=0.008, radius2=0.006, depth=hh * 0.5)
            bmesh.ops.translate(trunks, verts=g["verts"], vec=(x, y, z + hh * 0.25))
            g = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=hh * 0.38)
            bmesh.ops.translate(bm, verts=g["verts"], vec=(x, y, z + hh * 0.72))
        else:
            g = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True, segments=7,
                                      radius1=hh * 0.26, radius2=0.0, depth=hh)
            bmesh.ops.translate(bm, verts=g["verts"], vec=(x, y, z + hh / 2))
    crowns = obj_from_bm(name, bm, material)
    if round_crowns and trunk_mat:
        t = obj_from_bm(name + "-trunks", trunks, trunk_mat)
        return join(name, [crowns, t])
    trunks.free()
    return crowns


def export(slug):
    out = os.path.join(REPO, "public", "models", "gallery", "cities", f"{slug}.glb")
    blend = os.path.expanduser(f"~/Downloads/Models/travel/{slug}.blend")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    os.makedirs(os.path.dirname(blend), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=out, export_format="GLB", export_apply=True, export_extras=True,
        export_materials="EXPORT", export_normals=True, export_texcoords=False,
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=7,
        export_draco_position_quantization=14,
        export_draco_normal_quantization=10,
    )
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    print(f"[diorama] wrote {out} and {blend}")
