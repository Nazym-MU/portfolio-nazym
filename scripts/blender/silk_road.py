"""
silk_road.py — Timurid / Bukharan building parts shared by samarkand.py and
bukhara.py: pointed-arch portals (pishtaq), ribbed melon domes, minarets
with lanterns, a whole madrasah front.

Everything is built at the origin facing -Y (toward the viewer) and
returned as a list of objects; the city script moves and turns them.
Materials are passed in so each city keeps its own palette, including the
`nightglow-*` ones that light up when the viewer switches to night.
"""

import math

import bmesh
from mathutils import Matrix, Vector

import diorama_kit as k


def arch_outline(w, h, n=10):
    """A pointed (lancet) arch: straight sides, two arcs meeting at a point."""
    spring = h - w * 0.75
    pts = [(-w / 2, 0.0), (w / 2, 0.0), (w / 2, spring)]
    for i in range(1, n + 1):
        t = i / n
        a = t * math.pi / 2
        pts.append((w / 2 - (w / 2) * (1 - math.cos(a)) * 1.0, spring + (h - spring) * math.sin(a)))
    for i in range(n - 1, 0, -1):
        t = i / n
        a = t * math.pi / 2
        pts.append((-(w / 2 - (w / 2) * (1 - math.cos(a))), spring + (h - spring) * math.sin(a)))
    pts.append((-w / 2, spring))
    return pts


def niche(name, w, h, depth, material, parent=None):
    """A pointed-arch panel standing in the XZ plane, `depth` thick toward -Y."""
    o = k.prism(name, arch_outline(w, h), depth, material=material, parent=parent)
    # prism extrudes up Z from an XY outline: stand it up into XZ.
    o.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
    return o


def pishtaq(tag, w, h, d, body, tile, inner, parent=None):
    """The portal: a tall block, a tiled frame, a deep pointed niche."""
    parts = [k.box(f"{tag}-block", (w, d, h), material=body, parent=parent)]
    parts.append(k.box(f"{tag}-frame", (w * 0.86, 0.004, h * 0.86), at=(0, -d / 2 - 0.002, h * 0.06), material=tile, parent=parent))
    n = niche(f"{tag}-niche", w * 0.58, h * 0.72, 0.006, inner, parent=parent)
    n.data.transform(Matrix.Translation((0, -d / 2 - 0.004, h * 0.08)))
    parts.append(n)
    parts.append(k.box(f"{tag}-cornice", (w + 0.004, d + 0.004, h * 0.04), at=(0, 0, h), material=tile, parent=parent))
    return parts


def ribbed_dome(tag, r, h, material, ribs=20, depth=0.08, drum_h=0.0, drum_mat=None, finial=None, parent=None, segs=None):
    """A Timurid melon dome: bulging past its drum, fluted with ribs."""
    segs = segs or ribs * 3
    parts = []
    if drum_h > 0:
        parts.append(k.cylinder(f"{tag}-drum", r * 0.9, drum_h, segs=segs, material=drum_mat or material, parent=parent))
    bm = bmesh.new()
    rings = []
    N = 14
    for j in range(N + 1):
        t = j / N
        bulge = 1.0 + 0.16 * math.sin(math.pi * min(t * 1.6, 1.0))
        rr = r * 0.9 * bulge * math.cos(t * math.pi / 2) ** 0.85
        z = drum_h + h * math.sin(t * math.pi / 2) ** 1.1
        ring = []
        for i in range(segs):
            th = 2 * math.pi * i / segs
            flute = 1 - depth * (0.5 + 0.5 * math.cos(ribs * th)) * (1 - t)
            ring.append(bm.verts.new((rr * flute * math.cos(th), rr * flute * math.sin(th), z)))
        rings.append(ring)
    top = bm.verts.new((0, 0, drum_h + h + 0.002))
    for a, b in zip(rings, rings[1:]):
        for i in range(segs):
            bm.faces.new((a[i], a[(i + 1) % segs], b[(i + 1) % segs], b[i]))
    for i in range(segs):
        bm.faces.new((rings[-1][i], rings[-1][(i + 1) % segs], top))
    bm.faces.new(list(reversed(rings[0])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    d = k.obj_from_bm(f"{tag}-dome", bm, material, parent=parent)
    k.smooth_by_angle(d, 50)
    parts.append(d)
    if finial is not None:
        parts.append(k.cylinder(f"{tag}-finial", r * 0.05, h * 0.25, at=(0, 0, drum_h + h), segs=6, r_top=0.0, material=finial, parent=parent))
    return parts


def minaret(tag, r0, r1, h, body, band, lantern, cap, bands=4, parent=None, cap_dome=True):
    """A tapering minaret, tile bands up it, an arcaded lantern and a cap."""
    parts = [k.cylinder(f"{tag}-shaft", r0, h, r_top=r1, segs=16, material=body, parent=parent)]
    for i in range(bands):
        z = h * (0.2 + 0.7 * i / max(bands - 1, 1))
        rz = r0 + (r1 - r0) * z / h
        parts.append(k.cylinder(f"{tag}-band-{i}", rz * 1.04, h * 0.035, at=(0, 0, z), segs=16, material=band, parent=parent))
    parts.append(k.cylinder(f"{tag}-gallery", r1 * 1.35, h * 0.03, at=(0, 0, h), segs=16, material=band, parent=parent))
    parts.append(k.cylinder(f"{tag}-lantern", r1 * 1.1, h * 0.09, at=(0, 0, h + h * 0.03), segs=16, material=lantern, parent=parent))
    if cap_dome:
        parts.append(k.cylinder(f"{tag}-cap", r1 * 1.2, h * 0.08, at=(0, 0, h + h * 0.12), r_top=0.0, segs=16, material=cap, parent=parent))
    return parts


def madrasah(tag, w, d, h, mat, parent=None, minarets=True, domes=2, portal_scale=1.0):
    """A madrasah front: facade with arcaded cells, a central pishtaq, corner
    minarets and ribbed domes behind. `mat` is a dict of materials:
    body, tile, inner, dome, lantern, window."""
    parts = [k.box(f"{tag}-facade", (w, d, h), material=mat["body"], parent=parent)]
    # Two storeys of small pointed-arch cells either side of the portal.
    cells = 4
    for side in (-1, 1):
        for row in range(2):
            for c in range(cells):
                x = side * (w * 0.2 + (c + 0.5) * (w * 0.28) / cells)
                n = niche(f"{tag}-cell-{side}-{row}-{c}", w * 0.045, h * 0.34, 0.003, mat["window"], parent=parent)
                n.data.transform(Matrix.Translation((x, -d / 2 - 0.0015, h * (0.08 + row * 0.46))))
                parts.append(n)
    pw, ph = w * 0.36 * portal_scale, h * 1.75 * portal_scale
    for o in pishtaq(f"{tag}-portal", pw, ph, d * 1.15, mat["body"], mat["tile"], mat["inner"], parent=parent):
        o.data.transform(Matrix.Translation((0, -d * 0.1, 0)))
        parts.append(o)
    if minarets:
        for side in (-1, 1):
            for o in minaret(f"{tag}-minaret-{side}", w * 0.04, w * 0.032, h * 2.0, mat["body"], mat["tile"], mat["lantern"], mat["dome"], parent=parent):
                o.data.transform(Matrix.Translation((side * (w / 2 - w * 0.02), -d / 2 + w * 0.02, 0)))
                parts.append(o)
    for i in range(domes):
        x = (i - (domes - 1) / 2) * w * 0.5
        for o in ribbed_dome(f"{tag}-dome-{i}", w * 0.11, w * 0.12, mat["dome"], drum_h=h * 0.4, drum_mat=mat["body"], parent=parent):
            o.data.transform(Matrix.Translation((x, d * 0.1, h)))
            parts.append(o)
    return parts


def place_all(parts, x, y, z, rot_deg):
    m = Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(rot_deg), 4, "Z")
    for o in parts:
        o.data.transform(m)
    return parts
