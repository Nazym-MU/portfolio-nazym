"""
astana.py — the Astana diorama, after Nazym's own model of it.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python scripts/blender/astana.py

Layout (Blender top view, +Y is the back of the toy):

        pyramid
   ~~~~~~~~~~~~~~~~~~~~ Ishim ~~~~~~~~~~~~~~~~~~~~
     bridge                          tower  tower
               Baiterek
               (plaza)                 Nur Alem + Expo petals
   Khan Shatyr
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
import diorama_kit as k  # noqa: E402
import bpy  # noqa: E402


def bpy_obj(name):
    return bpy.data.objects[name]

k.reset()

grass = k.mat("grass", (0.62, 0.72, 0.42))
earth = k.mat("earth", (0.55, 0.42, 0.30))
plaza = k.mat("plaza", (0.86, 0.78, 0.64))
water = k.mat("river", (0.16, 0.25, 0.45))
tree = k.mat("tree", (0.18, 0.32, 0.22))
white = k.mat("white", (0.95, 0.95, 0.93))
gold = k.mat("gold", (0.88, 0.58, 0.24))
facade = k.mat("facade-blue", (0.20, 0.32, 0.62))
sand = k.mat("sand", (0.90, 0.82, 0.66))
tent = k.mat("tent", (0.80, 0.83, 0.95))
dark = k.mat("dark", (0.26, 0.27, 0.32))

k.base(grass, earth)


# ---- the Ishim --------------------------------------------------------------
def river_y(x):
    return 0.30 + 0.17 * x + 0.07 * math.sin(2.6 * x + 0.5)


river_pts = [(x / 100, river_y(x / 100)) for x in range(-105, 106, 3)]
k.ribbon("DECO-river", river_pts, 0.13, material=water)


# ---- Baiterek on its plaza --------------------------------------------------
PX, PY = -0.12, 0.02


def circle(r, n=64, cx=PX, cy=PY):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


k.prism("DECO-plaza", circle(0.22), 0.006, holes=[circle(0.16)], material=plaza)
k.prism("DECO-plaza-core", circle(0.05), 0.006, material=plaza)

baiterek = k.empty("OBJ-baiterek")
k.cylinder("baiterek-plinth", 0.045, 0.02, at=(PX, PY, 0.0), material=dark, parent=baiterek)
k.cylinder("baiterek-stem", 0.028, 0.40, at=(PX, PY, 0.02), r_top=0.016, material=white, parent=baiterek)
for i in range(10):
    a = 2 * math.pi * i / 10
    pts = []
    for s in range(9):
        t = s / 8
        # Out and back in: the branches make a cup the sphere sits in.
        r = 0.012 + 0.062 * math.sin(math.pi * 0.75 * t)
        z = 0.32 + 0.22 * t
        pts.append((PX + r * math.cos(a), PY + r * math.sin(a), z))
    k.tube(f"baiterek-branch-{i}", pts, 0.0045, material=white, segs=5, parent=baiterek)
k.sphere("baiterek-sphere", 0.062, at=(PX, PY, 0.50), material=gold, parent=baiterek)


# ---- Khan Shatyr ------------------------------------------------------------
KX, KY, KH = -0.54, -0.40, 0.34
profile = [(0.24 * (1 - t) ** 1.7 + 0.006, KH * t) for t in [i / 16 for i in range(17)]]
profile.append((0.0, KH))
khan = k.lathe("OBJ-khan-shatyr", profile, segs=40, at=(KX, KY, 0.0), material=tent)
# The tent leans: its tip sits off-centre, toward the city.
for v in khan.data.vertices:
    v.co.x += 0.07 * (v.co.z / KH) ** 1.6
k.tube("khan-shatyr-mast", [(KX + 0.07, KY, KH - 0.01), (KX + 0.085, KY, KH + 0.05)], 0.004,
       material=white, segs=5, parent=khan)


# ---- Palace of Peace and Reconciliation ------------------------------------
pyramid = k.empty("OBJ-pyramid")
PYX, PYY = -0.22, 0.72
body = k.cylinder("pyramid-body", 0.19, 0.14, at=(PYX, PYY, 0), r_top=0.06, segs=4,
                  material=sand, parent=pyramid, smooth=False)
cap = k.cylinder("pyramid-glass", 0.06, 0.065, at=(PYX, PYY, 0.14), r_top=0.0, segs=4,
                 material=facade, parent=pyramid, smooth=False)
for o in (body, cap):
    # A 4-sided cone is a diamond; turn it square to the river.
    me = o.data
    rot = Matrix.Rotation(math.radians(45), 4, "Z")
    for v in me.vertices:
        local = v.co - Vector((PYX, PYY, 0))
        v.co = Vector((PYX, PYY, 0)) + rot @ local


# ---- Abu Dhabi Plaza --------------------------------------------------------
adp = k.empty("OBJ-abu-dhabi-plaza")
k.box("adp-tower", (0.13, 0.13, 0.66), at=(0.50, 0.22, 0), material=facade, parent=adp)
k.box("adp-crown", (0.134, 0.134, 0.035), at=(0.50, 0.22, 0.66), material=sand, parent=adp)
k.box("adp-tower-2", (0.08, 0.095, 0.38), at=(0.665, 0.18, 0), material=facade, parent=adp)
k.box("adp-crown-2", (0.084, 0.099, 0.02), at=(0.665, 0.18, 0.38), material=sand, parent=adp)


# ---- Expo: Nur Alem and its petals -----------------------------------------
FX, FY = 0.38, -0.36
k.cylinder("nur-alem-ring", 0.08, 0.012, at=(FX, FY, 0), material=dark)
k.sphere("OBJ-nur-alem", 0.1, at=(FX, FY, 0.098), material=facade, subdiv=4)


def petal(angle, d0, d1, w, n=18):
    """A lens pointing away from the flower centre, with a hollow middle."""
    ax, ay = math.cos(angle), math.sin(angle)
    nx, ny = -ay, ax

    def lens(scale):
        mid = (d0 + d1) / 2
        half = (d1 - d0) / 2 * scale
        pts = []
        for side in (1, -1):
            rng = range(n + 1) if side == 1 else range(n, -1, -1)
            for i in rng:
                t = i / n
                s = mid - half + 2 * half * t
                hw = w * scale * math.sin(math.pi * t) ** 0.75 * side
                pts.append((FX + ax * s + nx * hw, FY + ay * s + ny * hw))
        return pts[:-1]
    return lens(1.0), lens(0.58)


petal_objs = []
for i in range(5):
    a = 2 * math.pi * i / 5 + 0.3
    outer, hole = petal(a, 0.20, 0.44, 0.10)
    petal_objs.append(k.prism(f"expo-petal-{i}", outer, 0.05, holes=[hole], material=facade))
    small, _ = petal(a + math.pi / 5, 0.125, 0.2, 0.035)
    petal_objs.append(k.prism(f"expo-bud-{i}", small, 0.03, material=facade))
k.join("OBJ-expo", petal_objs)


# ---- Atyrau bridge over the Ishim ------------------------------------------
BX = -0.56
by = river_y(BX)
tangent = Vector((1, 0.17 + 0.07 * 2.6 * math.cos(2.6 * BX + 0.5))).normalized()
across = Vector((-tangent.y, tangent.x))
bridge = k.empty("OBJ-atyrau-bridge")
deck = k.box("bridge-deck", (0.05, 0.26, 0.012), at=(BX, by, 0.004), material=white, parent=bridge)
deck.rotation_euler = (0, 0, math.atan2(across.y, across.x) - math.pi / 2)
deck.location = (0, 0, 0)
# box() bakes its offset into the mesh; rotate about the bridge centre instead.
for v in deck.data.vertices:
    rel = v.co - Vector((BX, by, 0))
    v.co = Vector((BX, by, 0)) + Matrix.Rotation(deck.rotation_euler.z, 4, "Z") @ rel
deck.rotation_euler = (0, 0, 0)
for side in (-1, 1):
    pts = []
    for s in range(21):
        u = -1 + 2 * s / 20
        h = 0.2 * (1 - u * u)
        lean = -side * 0.035 * (1 - u * u)
        p = Vector((BX, by)) + across * (u * 0.15) + tangent * (side * 0.035 + lean)
        pts.append((p.x, p.y, 0.012 + h))
    k.tube(f"bridge-arch-{side}", pts, 0.006, material=white, segs=6, parent=bridge)


# ---- bigger landmarks (scaled about their footprints) ----------------------
k.grow(baiterek, 1.2, (PX, PY, 0))
k.grow(khan, 1.25, (KX, KY, 0))
k.grow(pyramid, 1.25, (PYX, PYY, 0))
k.grow(bpy_obj("OBJ-nur-alem"), 1.15, (FX, FY, 0))
k.grow(bpy_obj("OBJ-expo"), 1.12, (FX, FY, 0))
k.grow(bpy_obj("nur-alem-ring"), 1.15, (FX, FY, 0))
k.grow(bridge, 1.15, (BX, by, 0))


# ---- trees ------------------------------------------------------------------
keep_out = [
    (PX, PY, 0.25), (0.50, 0.22, 0.12), (0.665, 0.18, 0.08), (PYX, PYY, 0.25),
    (FX, FY, 0.52), (KX + 0.03, KY, 0.33), (BX, by, 0.2),
]
keep_out += [(x, y, 0.11) for x, y in river_pts]
ring_trees = [(PX + 0.11 * math.cos(a), PY + 0.11 * math.sin(a))
              for a in [2 * math.pi * i / 7 + 0.2 for i in range(7)]]
k.forest("DECO-trees", 110, tree, keep_out, seed=5, extra=ring_trees, h=(0.09, 0.15))

k.export("astana")
