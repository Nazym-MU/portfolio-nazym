"""
cairo.py — Egypt in one dome, west to east the way the land lies:

   GIZA (desert)          | NILE |  CAIRO              | RED SEA (deep)
   Khufu, Khafre,           feluccas  the city,             beach, palms,
   Menkaure, the Sphinx,    palm      Khan el-Khalili's     a fringing reef that
   a resting camel caravan  banks     bazaar lanes          drops away, corals,
                                                            divers, fish, boats

The Red Sea is genuinely deeper: the plinth drops away under it, the water
is see-through (glass-sea-46) and the rim there is a glass wall, so the reef
can be seen from the side like an aquarium.

Moving things use the viewer's `shuttle` extras with `pingpong` (there and
back, turning at each end) and `bob` (steps): camels, feluccas, the dive
boat, divers, fish. Each mover's geometry faces local +X, its empty is
turned to face along its path.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python scripts/blender/cairo.py

Reference points (well known): Khufu, Khafre and Menkaure stand on a
diagonal, Khafre keeping a cap of its white casing at the top; the Sphinx
lies by Khafre's causeway facing east; Khan
el-Khalili is a maze of lanes under hanging lanterns; the Red Sea's reefs
fringe the shore and drop away steeply.
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
import diorama_kit as k  # noqa: E402

k.reset()

sand = k.mat("desert-sand", (0.92, 0.80, 0.56))
earth = k.mat("earth", (0.62, 0.48, 0.34))
limestone = k.mat("pyramid-limestone", (0.86, 0.74, 0.52))
casing = k.mat("casing-white", (0.96, 0.92, 0.82))
sphinx_m = k.mat("sphinx-stone", (0.84, 0.70, 0.48))
green = k.mat("nile-green", (0.46, 0.66, 0.34))
nile = k.mat("nile", (0.30, 0.52, 0.62))
seabed = k.mat("seabed-deep", (0.36, 0.52, 0.64))
reef_rock = k.mat("reef-shelf", (0.80, 0.74, 0.60))
sea = k.mat("glass-sea-46", (0.10, 0.46, 0.80))
rim_glass = k.mat("glass-sea-rim-40", (0.12, 0.42, 0.74))
cairo_wall = k.mat("cairo-sand", (0.88, 0.78, 0.60))
cairo_wall2 = k.mat("cairo-ochre", (0.80, 0.64, 0.44))
glow = k.mat("lamp-yellow", (1.0, 0.82, 0.42))
white = k.mat("white", (0.96, 0.96, 0.95))
dark = k.mat("dark", (0.16, 0.16, 0.20))
palm_trunk = k.mat("palm-trunk", (0.58, 0.44, 0.30))
palm_leaf = k.mat("palm-leaf", (0.30, 0.56, 0.28))
camel = k.mat("camel", (0.80, 0.62, 0.40))
saddle = k.mat("saddle-red", (0.80, 0.20, 0.18))
lanterns = [k.mat(n, c) for n, c in [("neon-fanous-red", (1.0, 0.3, 0.2)), ("neon-fanous-blue", (0.3, 0.6, 1.0)),
                                      ("neon-fanous-green", (0.35, 0.95, 0.5)), ("neon-fanous-gold", (1.0, 0.8, 0.3))]]
spices = [k.mat(n, c) for n, c in [("spice-red", (0.84, 0.26, 0.16)), ("spice-yellow", (0.96, 0.78, 0.18)),
                                    ("spice-orange", (0.94, 0.52, 0.18)), ("spice-green", (0.44, 0.60, 0.26))]]
awnings = [k.mat(n, c) for n, c in [("awning-red", (0.78, 0.20, 0.18)), ("awning-blue", (0.20, 0.36, 0.70)),
                                     ("awning-green", (0.20, 0.54, 0.36)), ("awning-gold", (0.90, 0.66, 0.22))]]
corals = [k.mat(n, c) for n, c in [("coral-pink", (0.98, 0.44, 0.58)), ("coral-orange", (1.0, 0.56, 0.22)),
                                    ("coral-purple", (0.62, 0.36, 0.82)), ("coral-yellow", (0.98, 0.86, 0.30)),
                                    ("coral-teal", (0.20, 0.76, 0.70)), ("coral-red", (0.90, 0.20, 0.24))]]
fish_c = [k.mat(n, c) for n, c in [("fish-yellow", (1.0, 0.84, 0.10)), ("fish-blue", (0.18, 0.46, 0.96)),
                                    ("fish-orange", (1.0, 0.50, 0.10)), ("fish-white", (0.96, 0.96, 0.98))]]
wetsuit = k.mat("wetsuit", (0.10, 0.12, 0.16))
tank = k.mat("dive-tank", (0.98, 0.80, 0.10))
hull_blue = k.mat("hull-blue", (0.16, 0.36, 0.70))

# ---- the plinth sits lower, so the sea can be deep -----------------------------
BASE_TOP = -0.12
base = k.base(sand, earth, depth=0.02)
base.data.transform(Matrix.Translation((0, 0, BASE_TOP)))


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def nile_x(y):
    # East of centre, so Giza's pyramids stand well clear of it on the desert.
    return 0.05 + 0.03 * math.sin(3.0 * y + 0.4)


def shore_x(y):
    return 0.46 + 0.06 * math.sin(2.6 * y + 1.0)


SEA_LEVEL = -0.004


def height(x, y):
    """Desert and city at 0; the Nile a shallow channel; the Red Sea a beach,
    a reef shelf, then a steep drop to the deep floor."""
    d = x - shore_x(y)
    if d > 0:
        if d < 0.03:
            return -0.012 * d / 0.03
        if d < 0.12:
            return -0.035 + 0.006 * math.sin(40 * y) * math.sin(30 * x)
        t = smoothstep(0.12, 0.19, d)
        return -0.035 + (-0.11 + 0.035) * t + 0.006 * math.sin(23 * x + 3) * math.sin(19 * y) * t
    h = 0.0
    dn = abs(x - nile_x(y))
    if dn < 0.05:
        h = -0.016 * (1 - smoothstep(0.035, 0.05, dn))
    # Gentle dunes on the Giza side.
    if x < nile_x(y) - 0.08:
        h += 0.012 * math.sin(9 * x + 2) * math.sin(7 * y) + 0.008
    return h


RINGS, SEGS, R_EDGE = 64, 200, 0.995
bm = bmesh.new()
grid = [[bm.verts.new((0, 0, height(0, 0)))]]
for j in range(1, RINGS + 1):
    r = R_EDGE * j / RINGS
    grid.append([bm.verts.new((r * math.cos(2 * math.pi * i / SEGS), r * math.sin(2 * math.pi * i / SEGS),
                               height(r * math.cos(2 * math.pi * i / SEGS), r * math.sin(2 * math.pi * i / SEGS))))
                 for i in range(SEGS)])
for a, b in zip(grid, grid[1:]):
    for i in range(SEGS):
        if len(a) == 1:
            bm.faces.new((a[0], b[i], b[(i + 1) % SEGS]))
        else:
            bm.faces.new((a[i], a[(i + 1) % SEGS], b[(i + 1) % SEGS], b[i]))
land = k.obj_from_bm("DECO-land", bm)
for m in (sand, green, seabed, reef_rock, nile):
    land.data.materials.append(m)
for p in land.data.polygons:
    c = p.center
    d = c.x - shore_x(c.y)
    dn = abs(c.x - nile_x(c.y))
    if d > 0.03:
        p.material_index = 3 if d < 0.12 else 2        # reef shelf rock, then sandy deep floor
    elif dn < 0.04:
        p.material_index = 4
    elif dn < 0.1 and d < -0.02:
        p.material_index = 1                            # the green ribbon of the Nile's banks
    else:
        p.material_index = 0
    p.use_smooth = True
k.smooth_by_angle(land, 35)

# The rim: earth under the land, a glass wall where the sea is, down to the plinth.
bm = bmesh.new()
top_v, bot_v, is_sea = [], [], []
for i in range(SEGS):
    a = 2 * math.pi * i / SEGS
    x, y = R_EDGE * math.cos(a), R_EDGE * math.sin(a)
    h = height(x, y)
    sea_here = (x - shore_x(y)) > 0.02
    top_v.append(bm.verts.new((x, y, max(h, SEA_LEVEL) if sea_here else h)))
    bot_v.append(bm.verts.new((x, y, BASE_TOP)))
    is_sea.append(sea_here)
rim = None
faces_sea = []
for i in range(SEGS):
    j = (i + 1) % SEGS
    f = bm.faces.new((bot_v[i], bot_v[j], top_v[j], top_v[i]))
    faces_sea.append(is_sea[i] and is_sea[j])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
rim = k.obj_from_bm("DECO-rim", bm)
rim.data.materials.append(earth)
rim.data.materials.append(rim_glass)
for p, s_ in zip(rim.data.polygons, faces_sea):
    p.material_index = 1 if s_ else 0

# The sea's surface: see-through, over everything below sea level east of the shore.
bm = bmesh.new()
pts = []
for i in range(SEGS + 1):
    a = -math.pi / 2 + math.pi * i / SEGS
    pts.append((R_EDGE * math.cos(a), R_EDGE * math.sin(a)))
outline = [(x, y) for x, y in pts if x > shore_x(y) + 0.005]
coast = [(shore_x(y) + 0.005, y) for y in [outline[-1][1] - (outline[-1][1] - outline[0][1]) * t / 40 for t in range(1, 40)]]
k.prism("DECO-red-sea-surface", outline + coast, 0.002, z0=SEA_LEVEL - 0.002, material=sea)
# The Nile's water.
k.ribbon("DECO-nile", [(nile_x(y / 100), y / 100) for y in range(-100, 101, 3)], 0.07, z=-0.006, material=nile, clip=0.99)


def ground(x, y):
    return height(x, y)


def stand(o, x, y, rot=0.0, extra=0.0):
    o.data.transform(Matrix.Translation((x, y, ground(x, y) + extra)) @ Matrix.Rotation(math.radians(rot), 4, "Z"))
    return o


# ---- the pyramids ---------------------------------------------------------------
def pyramid(name, cx, cy, side, h, cap=False):
    root = k.empty(name)
    name = name[4:]          # parts must not start with OBJ- themselves
    r = side / math.sqrt(2)
    z = ground(cx, cy)
    if cap:
        body = k.cylinder(f"{name}-body", r, h * 0.82, at=(0, 0, 0), r_top=r * 0.18, segs=4, material=limestone, parent=root, smooth=False)
        top = k.cylinder(f"{name}-casing", r * 0.18, h * 0.18, at=(0, 0, h * 0.82), r_top=0.0, segs=4, material=casing, parent=root, smooth=False)
        parts = [body, top]
    else:
        parts = [k.cylinder(f"{name}-body", r, h, at=(0, 0, 0), r_top=0.0, segs=4, material=limestone, parent=root, smooth=False)]
    # Stepped courses: a few faint bands round the faces.
    for i in range(1, 6):
        t = i / 7
        parts.append(k.cylinder(f"{name}-course-{i}", r * (1 - t) + 0.0015, 0.002, at=(0, 0, h * t), segs=4,
                                material=casing if cap and t > 0.82 else sphinx_m, parent=root, smooth=False))
    for o in parts:
        o.data.transform(Matrix.Translation((cx, cy, z - 0.004)) @ Matrix.Rotation(math.radians(45 - 8), 4, "Z"))
    return root


KH = (-0.36, 0.44)
pyramid("OBJ-khufu", *KH, 0.36, 0.25)
pyramid("OBJ-khafre", -0.64, 0.0, 0.32, 0.23, cap=True)
pyramid("OBJ-menkaure", -0.58, -0.42, 0.18, 0.12)
q = k.empty("DECO-queens-pyramids")
for i in range(3):
    # The queens' pyramids, south-east of Khufu, still on the plateau.
    x, y = KH[0] + 0.14 + i * 0.05, KH[1] - 0.26 + i * 0.02
    for o in [k.cylinder(f"queen-{i}", 0.035, 0.05, at=(0, 0, 0), r_top=0.0, segs=4, material=limestone, parent=q, smooth=False)]:
        o.data.transform(Matrix.Translation((x, y, ground(x, y) - 0.003)) @ Matrix.Rotation(math.radians(37), 4, "Z"))


# ---- the Sphinx, lying by Khafre's causeway, facing east toward the Nile --------
# A lion lying down, about three times as long as it is high: a long back
# rising to the shoulders, rounded haunches, the front legs stretched far out
# in front, an upright chest, and a human head in the striped nemes headdress
# whose flaps fall either side of the face, the cobra on the brow.
SX, SY = -0.3, -0.05
sphinx = k.empty("OBJ-sphinx")
stone_dk = k.mat("sphinx-stone-dark", (0.72, 0.58, 0.38))
nemes_m = k.mat("nemes", (0.86, 0.74, 0.52))
sp = []


def blob(name, c, r, m=sphinx_m, floor=0.0):
    o = k.sphere(name, 1.0, material=m, parent=sphinx, subdiv=3)
    for v in o.data.vertices:
        v.co.z = max(v.co.z, -1.0 + floor)
    o.data.transform(Matrix.Translation(c) @ Matrix.Diagonal((r[0], r[1], r[2], 1)))
    sp.append(o)
    return o


# The body: one continuous loft, not blobs. Height and width along its
# length: rounded haunches at the back, a gentle dip, rising to the shoulders.
def body_h(t):
    return (0.022 + 0.008 * math.exp(-((t - 0.14) / 0.1) ** 2) + 0.018 * smoothstep(0.55, 0.92, t)) * min(1.0, (t / 0.07) ** 0.5)


def body_w(t):
    return (0.024 + 0.005 * math.exp(-((t - 0.14) / 0.1) ** 2) + 0.006 * smoothstep(0.6, 0.92, t)) * min(1.0, (t / 0.07) ** 0.5)


X0, X1, NS, NR = -0.11, 0.055, 26, 18
bmb = bmesh.new()
rings = []
for i in range(NS + 1):
    t = i / NS
    x = X0 + (X1 - X0) * t
    h, w = max(body_h(t), 0.002), max(body_w(t), 0.002)
    ring = []
    for j in range(NR + 1):
        a = math.pi * j / NR               # 0..pi over the top, flat underneath
        c, sn = math.cos(a), math.sin(a)
        ring.append(bmb.verts.new((x, w * math.copysign(abs(c) ** 0.55, c), h * abs(sn) ** 0.6)))
    rings.append(ring)
for r0, r1 in zip(rings, rings[1:]):
    for j in range(NR):
        bmb.faces.new((r0[j], r0[j + 1], r1[j + 1], r1[j]))
for ring in (rings[0], rings[-1]):
    bmb.faces.new(ring)
bmesh.ops.recalc_face_normals(bmb, faces=bmb.faces)
body = k.obj_from_bm("sphinx-body", bmb, sphinx_m, parent=sphinx)
k.smooth_by_angle(body, 60)
sp.append(body)
for sy in (-1, 1):
    # Back legs folded along the flanks, front legs stretched out ahead.
    sp.append(k.box(f"sphinx-hind-{sy}", (0.05, 0.012, 0.012), at=(-0.07, sy * 0.028, 0.0), material=sphinx_m, parent=sphinx))
    sp.append(k.box(f"sphinx-foreleg-{sy}", (0.085, 0.015, 0.013), at=(0.07, sy * 0.017, 0.0), material=sphinx_m, parent=sphinx))
    paw = blob(f"sphinx-paw-{sy}", (0.112, sy * 0.017, 0.007), (0.01, 0.009, 0.007), floor=0.9)
# Head: the nemes (a broad cloth framing the face, flaps down to the chest).
HX, HZ = 0.05, 0.045
sp.append(k.box("sphinx-nemes-back", (0.028, 0.034, 0.03), at=(HX - 0.008, 0, HZ), material=nemes_m, parent=sphinx))
for sy in (-1, 1):
    flap = k.box(f"sphinx-nemes-flap-{sy}", (0.008, 0.008, 0.032), at=(HX + 0.012, sy * 0.016, HZ - 0.018), material=nemes_m, parent=sphinx)
    sp.append(flap)
for j in range(4):   # stripes across the headcloth
    sp.append(k.box(f"sphinx-nemes-stripe-{j}", (0.029, 0.035, 0.0025), at=(HX - 0.008, 0, HZ + 0.004 + j * 0.0065), material=stone_dk, parent=sphinx))
sp.append(k.box("sphinx-face", (0.016, 0.022, 0.024), at=(HX + 0.012, 0, HZ + 0.002), material=sphinx_m, parent=sphinx))
sp.append(k.box("sphinx-nose", (0.004, 0.005, 0.006), at=(HX + 0.021, 0, HZ + 0.01), material=stone_dk, parent=sphinx))
sp.append(k.box("sphinx-brow", (0.003, 0.016, 0.0025), at=(HX + 0.0205, 0, HZ + 0.018), material=stone_dk, parent=sphinx))
sp.append(k.cylinder("sphinx-uraeus", 0.0025, 0.007, at=(HX + 0.02, 0, HZ + 0.024), segs=6, material=stone_dk, parent=sphinx))
sp.append(k.box("sphinx-beard", (0.005, 0.006, 0.01), at=(HX + 0.018, 0, HZ - 0.012), material=stone_dk, parent=sphinx))
# The enclosure it was carved out of, and the causeway up to Khafre.
sp.append(k.box("sphinx-enclosure", (0.28, 0.12, 0.004), at=(0.0, 0, -0.004), material=k.mat("enclosure", (0.80, 0.66, 0.44)), parent=sphinx))
for o in sp:
    stand(o, SX, SY)
cw = k.box("DECO-causeway", (0.24, 0.018, 0.004), material=k.mat("causeway", (0.82, 0.70, 0.50)))
cw.data.transform(Matrix.Translation(((SX - 0.64) / 2 - 0.02, (SY + 0.0) / 2, ground(SX, SY))) @ Matrix.Rotation(math.atan2(0.0 - SY, -0.64 - SX), 4, "Z"))


# ---- movers ------------------------------------------------------------------------
def mover(name, start, end, period, phase=0.0, bob=0.0, bob_hz=1.5, parent=None):
    """An empty at `start` facing `end`; the viewer walks it there and back."""
    e = k.empty(name, parent=parent)
    e.location = start
    d = Vector(end) - Vector(start)
    e.rotation_euler = (0, 0, math.atan2(d.y, d.x))
    e["shuttle"] = [d.x, d.y, d.z]
    e["period"] = period
    e["phase"] = phase
    e["pingpong"] = 1
    if bob:
        e["bob"] = bob
        e["bobHz"] = bob_hz
    return e


# ---- the camel caravan, standing in the desert before the pyramids ------------
caravan = k.empty("OBJ-camels")
C0, C1 = Vector((-0.44, -0.3, 0.0)), Vector((-0.16, -0.26, 0.0))
for i in range(4):
    off = Vector((0.045 * i, 0.007 * i, 0))
    a, b = C0 + off, C1 + off
    a.z = ground(a.x, a.y)
    b.z = ground(b.x, b.y)
    # Still, not walking: she found the animation ugly.
    c = k.empty(f"camel-{i}", parent=caravan)
    c.location = a.lerp(b, 0.4)
    c.rotation_euler = (0, 0, math.atan2(b.y - a.y, b.x - a.x))
    parts = []
    body = k.sphere(f"camel-{i}-body", 1.0, material=camel, parent=c, subdiv=2)
    body.data.transform(Matrix.Translation((0, 0, 0.034)) @ Matrix.Diagonal((0.022, 0.011, 0.011, 1)))
    hump = k.sphere(f"camel-{i}-hump", 0.011, at=(-0.002, 0, 0.046), material=camel, parent=c, subdiv=2)
    neck = k.tube(f"camel-{i}-neck", [(0.016, 0, 0.036), (0.028, 0, 0.05), (0.032, 0, 0.058)], 0.0045, material=camel, segs=5, parent=c)
    head = k.sphere(f"camel-{i}-head", 1.0, material=camel, parent=c, subdiv=2)
    head.data.transform(Matrix.Translation((0.038, 0, 0.058)) @ Matrix.Diagonal((0.009, 0.005, 0.005, 1)))
    for lx in (-0.014, 0.014):
        for ly in (-0.006, 0.006):
            k.cylinder(f"camel-{i}-leg-{lx}-{ly}", 0.0022, 0.026, at=(lx, ly, 0.0), segs=5, material=camel, parent=c)
    if i % 2 == 0:
        k.box(f"camel-{i}-saddle", (0.016, 0.022, 0.006), at=(-0.002, 0, 0.054), material=saddle, parent=c)
        k.cylinder(f"camel-{i}-rider", 0.005, 0.02, at=(-0.002, 0, 0.058), segs=6, material=k.mat("rider-white", (0.95, 0.95, 0.92)), parent=c)
        k.sphere(f"camel-{i}-rider-head", 0.0045, at=(-0.002, 0, 0.082), material=k.mat("keffiyeh", (0.9, 0.3, 0.3)), parent=c, subdiv=1)


# ---- the Nile: palm banks, feluccas sailing up and down ---------------------------
fel = k.empty("OBJ-feluccas")
for i, (y0, y1, ph) in enumerate([(-0.62, 0.0, 0.0), (0.1, 0.62, 0.4)]):
    a = Vector((nile_x(y0), y0, -0.006))
    b = Vector((nile_x(y1), y1, -0.006))
    f = mover(f"felucca-{i}", a, b, 30.0, phase=ph, parent=fel)
    hull = k.box(f"felucca-{i}-hull", (0.05, 0.016, 0.008), material=k.mat("felucca-wood", (0.62, 0.40, 0.24)), parent=f)
    for v in hull.data.vertices:
        if abs(v.co.x) > 0.02:
            v.co.y *= 0.3
            v.co.z += 0.003
    k.tube(f"felucca-{i}-mast", [(0.004, 0, 0.004), (0.006, 0, 0.07)], 0.0012, material=dark, segs=4, parent=f)
    sail = k.prism(f"felucca-{i}-sail", [(-0.024, 0.008), (0.012, 0.012), (0.008, 0.075)], 0.0015, material=white, parent=f)
    sail.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))


dates = k.mat("dates", (0.66, 0.30, 0.14))


def palm(tag, x, y, h, z=None):
    zz = ground(x, y) if z is None else z
    return k.palm(tag, x, y, zz, h, palm_trunk, palm_leaf, fruit_mat=dates, seed=hash(tag) & 0xffff)


palms = []
rnd = random.Random(5)
for i in range(30):
    y = -0.9 + i * 0.062
    for side in (-1, 1):
        x = nile_x(y) + side * rnd.uniform(0.055, 0.085)
        if math.hypot(x, y) > 0.94 or (side < 0 and abs(y - SY) < 0.07):
            continue
        if rnd.random() < 0.42:
            palms += palm(f"nile-palm-{i}-{side}", x, y, rnd.uniform(0.07, 0.095))
# The Red Sea beach: palms and umbrellas along the shore.
for i in range(14):
    y = -0.6 + i * 0.09
    x = shore_x(y) - 0.025
    if math.hypot(x, y) > 0.92:
        continue
    palms += palm(f"beach-palm-{i}", x, y, rnd.uniform(0.06, 0.08))
    if i % 2 == 0:
        palms.append(k.cylinder(f"umbrella-pole-{i}", 0.0012, 0.03, at=(x + 0.01, y + 0.03, ground(x, y)), segs=4, material=white))
        palms.append(k.cylinder(f"umbrella-{i}", 0.016, 0.008, at=(x + 0.01, y + 0.03, ground(x, y) + 0.028), r_top=0.0, segs=8,
                                material=awnings[i % 4], smooth=False))
k.join("DECO-palms", palms)


# ---- Cairo: Khan el-Khalili and the city ------------------------------------------
kh = k.empty("OBJ-khan-el-khalili")
KX, KY = 0.24, -0.34
kparts = []
# A small grid of lanes; stalls with awnings, hanging fanous lanterns, spice cones.
for row in range(3):
    for col in range(4):
        x = -0.09 + col * 0.06
        y = -0.07 + row * 0.07
        kparts.append(k.box(f"kh-shop-{row}-{col}", (0.045, 0.04, 0.045 + 0.01 * ((row + col) % 2)), at=(x, y + 0.015, 0),
                            material=[cairo_wall, cairo_wall2][(row + col) % 2], parent=kh))
        kparts.append(k.box(f"kh-awning-{row}-{col}", (0.046, 0.016, 0.003), at=(x, y - 0.012, 0.03), material=awnings[(row * 4 + col) % 4], parent=kh))
        for j in range(3):
            kparts.append(k.cylinder(f"kh-spice-{row}-{col}-{j}", 0.005, 0.01, at=(x - 0.012 + j * 0.012, y - 0.014, 0.0), r_top=0.0, segs=8,
                                     material=spices[(row + col + j) % 4], parent=kh))
        kparts.append(k.sphere(f"kh-lantern-{row}-{col}", 0.0045, at=(x + 0.014, y - 0.022, 0.024), material=lanterns[(row + col) % 4], parent=kh, subdiv=1))
# The old gate and a minaret over the bazaar.
kparts.append(k.box("kh-gate", (0.05, 0.02, 0.07), at=(0.0, -0.13, 0), material=cairo_wall2, parent=kh))
kparts.append(k.box("kh-gate-door", (0.018, 0.022, 0.04), at=(0.0, -0.13, 0), material=dark, parent=kh))
kparts.append(k.cylinder("kh-minaret", 0.008, 0.14, at=(0.12, 0.1, 0), r_top=0.006, segs=8, material=cairo_wall, parent=kh))
kparts.append(k.cylinder("kh-minaret-top", 0.01, 0.02, at=(0.12, 0.1, 0.14), r_top=0.002, segs=8, material=cairo_wall2, parent=kh))
for o in kparts:
    stand(o, KX, KY)

# The city between the Nile and the sea: flat-roofed blocks with lit windows.
city = []
for i in range(48):
    y = rnd.uniform(-0.2, 0.5)
    x = rnd.uniform(nile_x(y) + 0.11, shore_x(y) - 0.07)
    if math.hypot(x - KX, y - KY) < 0.15:
        continue
    w, h = rnd.uniform(0.025, 0.04), rnd.uniform(0.03, 0.08)
    city.append(stand(k.box(f"cb-{i}", (w, w, h), material=[cairo_wall, cairo_wall2][i % 2]), x, y, rot=rnd.uniform(-15, 15)))
    city.append(stand(k.box(f"cb-win-{i}", (w + 0.002, w + 0.002, 0.003), material=glow), x, y, extra=h * 0.55))
k.join("DECO-cairo-city", city)


# ---- the Red Sea, underwater --------------------------------------------------------
# A fringing reef along the shelf, a coral wall where it drops away, and the
# deep sandy floor with sea grass and coral pinnacles. Corals of many kinds,
# each built to read as itself; static parts joined per material.
X = lambda v: Matrix.Translation(v)                       # noqa: E731
RZ = lambda a: Matrix.Rotation(a, 4, "Z")                 # noqa: E731
RY = lambda a: Matrix.Rotation(a, 4, "Y")                 # noqa: E731
RX = lambda a: Matrix.Rotation(a, 4, "X")                 # noqa: E731
DG = lambda x, y, z: Matrix.Diagonal((x, y, z, 1))        # noqa: E731
rock_m = k.mat("reef-boulder", (0.62, 0.58, 0.52))
grass_m = k.mat("sea-grass", (0.30, 0.62, 0.36))
sponge_c = [k.mat("sponge-purple", (0.52, 0.30, 0.74)), k.mat("sponge-orange", (0.98, 0.50, 0.16)),
            k.mat("sponge-yellow", (0.98, 0.80, 0.22))]
sponge_in = k.mat("sponge-inside", (0.22, 0.14, 0.26))
clam_mantle = k.mat("clam-mantle", (0.30, 0.42, 0.92))
star_m = k.mat("starfish", (0.96, 0.40, 0.22))
anemone_m = k.mat("anemone", (0.98, 0.72, 0.58))
reef_parts = []


def staghorn(tag, x, y, z, m, size=1.0):
    """Branching coral: a trunk that forks, and forks again, tips upturned."""
    def branch(p, d, length, depth, idx):
        q = p + d * length
        mid = p + d * (length * 0.5) + Vector((0, 0, 0.002))
        reef_parts.append(k.tube(f"{tag}-b{idx}", [tuple(p), tuple(mid), tuple(q)], 0.0022 * size * (0.7 + 0.15 * depth), material=m, segs=5))
        if depth == 0:
            reef_parts.append(k.sphere(f"{tag}-tip{idx}", 0.0024 * size, at=tuple(q), material=m, subdiv=1))
            return
        for j in range(2 + (depth > 1)):
            a = rnd.uniform(0, 2 * math.pi)
            nd = (d * 0.6 + Vector((0.6 * math.cos(a), 0.6 * math.sin(a), 0.5))).normalized()
            branch(q, nd, length * 0.72, depth - 1, idx * 3 + j + 1)
    for j in range(3):
        a = 2 * math.pi * j / 3 + rnd.random()
        branch(Vector((x, y, z)), Vector((0.4 * math.cos(a), 0.4 * math.sin(a), 0.9)).normalized(), 0.012 * size, 2, j)


def brain(tag, x, y, z, m, r):
    """Brain coral: a dome with meandering grooves pressed into it."""
    o = k.sphere(tag, r, material=m, subdiv=4)
    for v in o.data.vertices:
        c = v.co
        if c.z < -r * 0.35:
            c.z = -r * 0.35
        th = math.atan2(c.y, c.x)
        groove = 0.07 * math.sin(14 * th + 9 * c.z / r) * math.sin(11 * c.z / r + 3 * th)
        v.co = c * (1 + groove)
    o.data.transform(X((x, y, z + r * 0.3)))
    reef_parts.append(o)


def table(tag, x, y, z, m, r):
    """Table coral: a short stem under stacked, wavy-edged plates."""
    reef_parts.append(k.cylinder(f"{tag}-stem", r * 0.18, r * 0.9, at=(x, y, z), r_top=r * 0.12, segs=8, material=m))
    for j, (rr, dz) in enumerate([(1.0, 0.9), (0.72, 1.12), (0.45, 1.3)]):
        pl = k.cylinder(f"{tag}-plate{j}", r * rr, r * 0.08, segs=18, material=m)
        for v in pl.data.vertices:
            a = math.atan2(v.co.y, v.co.x)
            if math.hypot(v.co.x, v.co.y) > r * rr * 0.9:
                v.co.z += r * 0.06 * math.sin(6 * a)
        pl.data.transform(X((x, y, z + r * dz)))
        reef_parts.append(pl)


def sea_fan(tag, x, y, z, m, h):
    """Gorgonian sea fan: a flat lattice of branches standing on edge."""
    rot = rnd.uniform(0, math.pi)
    segs = []

    def grow_(p, ang, length, depth):
        q = p + Vector((math.cos(ang) * length, 0, math.sin(ang) * length))
        segs.append((p, q))
        if depth:
            for da in (-0.45, 0.45):
                grow_(q, ang + da + rnd.uniform(-0.1, 0.1), length * 0.75, depth - 1)
    grow_(Vector((0, 0, 0)), math.pi / 2, h * 0.32, 4)
    for i, (p, q) in enumerate(segs):
        t = k.tube(f"{tag}-s{i}", [tuple(p), tuple(q)], 0.0011, material=m, segs=3)
        t.data.transform(X((x, y, z)) @ RZ(rot))
        reef_parts.append(t)


def tube_sponge(tag, x, y, z, m):
    for j in range(4):
        a = 2 * math.pi * j / 4 + rnd.random()
        dx, dy = 0.006 * math.cos(a), 0.006 * math.sin(a)
        h = rnd.uniform(0.018, 0.03)
        reef_parts.append(k.cylinder(f"{tag}-t{j}", 0.0035, h, at=(x + dx, y + dy, z), r_top=0.0042, segs=10, material=m))
        reef_parts.append(k.cylinder(f"{tag}-in{j}", 0.0032, 0.001, at=(x + dx, y + dy, z + h), segs=10, material=sponge_in))


def barrel_sponge(tag, x, y, z, m):
    o = k.lathe(tag, [(0.006, 0.0), (0.011, 0.01), (0.012, 0.02), (0.01, 0.026), (0.0085, 0.026), (0.0, 0.016)], segs=16, material=m)
    o.data.transform(X((x, y, z)))
    reef_parts.append(o)


def soft_coral(tag, x, y, z, m):
    reef_parts.append(k.cylinder(f"{tag}-stalk", 0.003, 0.01, at=(x, y, z), segs=6, material=m))
    for j in range(9):
        a, e = rnd.uniform(0, 2 * math.pi), rnd.uniform(0.2, 1.2)
        reef_parts.append(k.sphere(f"{tag}-puff{j}", 0.004, at=(x + 0.007 * math.cos(a) * math.cos(e), y + 0.007 * math.sin(a) * math.cos(e),
                                                                z + 0.012 + 0.006 * math.sin(e)), material=m, subdiv=1))


def anemone(tag, x, y, z):
    reef_parts.append(k.cylinder(f"{tag}-foot", 0.008, 0.004, at=(x, y, z), segs=12, material=anemone_m))
    for j in range(18):
        a = 2 * math.pi * j / 18
        rr = 0.004 + 0.003 * (j % 2)
        reef_parts.append(k.tube(f"{tag}-ten{j}", [(x + rr * math.cos(a), y + rr * math.sin(a), z + 0.004),
                                                 (x + (rr + 0.004) * math.cos(a), y + (rr + 0.004) * math.sin(a), z + 0.011),
                                                 (x + (rr + 0.007) * math.cos(a), y + (rr + 0.007) * math.sin(a), z + 0.014)],
                                 0.0009, material=anemone_m, segs=3))


def giant_clam(tag, x, y, z):
    for sy in (-1, 1):
        sh = k.sphere(f"{tag}-shell{sy}", 1.0, material=k.mat("clam-shell", (0.86, 0.84, 0.78)), subdiv=2)
        for v in sh.data.vertices:
            v.co.y = sy * abs(v.co.y)
            v.co.z += 0.12 * math.sin(10 * math.atan2(v.co.z, v.co.x)) * abs(v.co.y)
        sh.data.transform(X((x, y, z + 0.006)) @ DG(0.016, 0.008, 0.008))
        reef_parts.append(sh)
    m = k.box(f"{tag}-mantle", (0.026, 0.006, 0.003), material=clam_mantle)
    m.data.transform(X((x, y, z + 0.012)))
    reef_parts.append(m)


def starfish(tag, x, y, z):
    pts = []
    for j in range(10):
        a = math.pi / 2 + 2 * math.pi * j / 10
        rr = 0.009 if j % 2 == 0 else 0.0035
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    st = k.prism(tag, pts, 0.002, material=star_m)
    st.data.transform(X((x, y, z + 0.001)) @ RZ(rnd.uniform(0, 1)))
    reef_parts.append(st)


def boulder(tag, x, y, z, r):
    o = k.sphere(tag, r, material=rock_m, subdiv=2)
    for v in o.data.vertices:
        v.co *= 1 + 0.18 * math.sin(7 * v.co.x / r + 3) * math.sin(5 * v.co.y / r)
        v.co.z = max(v.co.z, -r * 0.3)
    o.data.transform(X((x, y, z)) @ DG(1, 1, 0.7))
    reef_parts.append(o)


def sea_grass(tag, x, y, z):
    for j in range(7):
        a = rnd.uniform(0, 2 * math.pi)
        dx, dy = 0.006 * math.cos(a), 0.006 * math.sin(a)
        h = rnd.uniform(0.014, 0.024)
        reef_parts.append(k.tube(f"{tag}-blade{j}", [(x + dx, y + dy, z), (x + dx * 1.3, y + dy * 1.3, z + h * 0.6), (x + dx * 2, y + dy * 2, z + h)],
                                 0.0008, material=grass_m, segs=3))


def reef_point(d_lo, d_hi, y_lo=-0.62, y_hi=0.62):
    for _ in range(50):
        y = rnd.uniform(y_lo, y_hi)
        x = shore_x(y) + rnd.uniform(d_lo, d_hi)
        if math.hypot(x, y) < 0.93:
            return x, y, ground(x, y)
    return None


reef = k.empty("OBJ-coral-reef")
# The shelf: dense, all kinds.
for i in range(46):
    p = reef_point(0.035, 0.12)
    if not p:
        continue
    x, y, z = p
    kind = i % 9
    m = corals[i % len(corals)]
    if kind in (0, 5):
        staghorn(f"stag{i}", x, y, z, m, size=rnd.uniform(0.9, 1.3))
    elif kind == 1:
        brain(f"brain{i}", x, y, z, corals[[3, 4, 1][i % 3]], rnd.uniform(0.009, 0.014))
    elif kind == 2:
        table(f"table{i}", x, y, z, corals[[4, 1, 0][i % 3]], rnd.uniform(0.014, 0.02))
    elif kind == 3:
        sea_fan(f"fan{i}", x, y, z, corals[[2, 5, 0][i % 3]], rnd.uniform(0.03, 0.045))
    elif kind == 4:
        tube_sponge(f"tube{i}", x, y, z, sponge_c[i % 3])
    elif kind == 6:
        soft_coral(f"soft{i}", x, y, z, corals[[0, 2, 5][i % 3]])
    elif kind == 7:
        boulder(f"rock{i}", x, y, z, rnd.uniform(0.01, 0.016))
        staghorn(f"stagr{i}", x, y, z + 0.008, corals[(i + 2) % 6], size=0.7)
    else:
        giant_clam(f"clam{i}", x, y, z)
# Anemones with their clownfish (the clownfish swim, below).
anemones = []
for i in range(4):
    p = reef_point(0.05, 0.1, -0.4 + i * 0.22, -0.3 + i * 0.22)
    if p:
        anemone(f"anem{i}", *p)
        anemones.append(p)
# The drop-off wall and the deep floor: barrel sponges, fans, pinnacles, grass.
for i in range(26):
    p = reef_point(0.13, 0.4)
    if not p:
        continue
    x, y, z = p
    kind = i % 6
    if kind == 0:
        barrel_sponge(f"barrel{i}", x, y, z, sponge_c[i % 3])
    elif kind == 1:
        sea_fan(f"dfan{i}", x, y, z, corals[2], rnd.uniform(0.04, 0.055))
    elif kind == 2:
        # A coral pinnacle (bommie): a rock tower crowned with coral.
        boulder(f"bommie{i}a", x, y, z, 0.018)
        boulder(f"bommie{i}b", x, y, z + 0.018, 0.013)
        table(f"bommie{i}t", x, y, z + 0.03, corals[4], 0.012)
        staghorn(f"bommie{i}s", x + 0.01, y, z + 0.02, corals[0], size=0.8)
    elif kind == 3:
        starfish(f"star{i}", x, y, z)
    else:
        sea_grass(f"grass{i}", x, y, z)
cr = k.join("reef-corals", reef_parts)
cr.parent = reef


# ---- fish: real shapes, swimming there and back ----------------------------------
FISH = {
    # name: (body colour, length, height, bands colour or None)
    "clownfish": (k.mat("clownfish-orange", (1.0, 0.46, 0.08)), 0.008, 0.0045, white),
    "butterflyfish": (k.mat("butterflyfish-yellow", (1.0, 0.86, 0.10)), 0.008, 0.0075, dark),
    "angelfish": (k.mat("angelfish-blue", (0.16, 0.30, 0.86)), 0.011, 0.008, k.mat("angelfish-yellow", (1.0, 0.82, 0.1))),
    "parrotfish": (k.mat("parrotfish-teal", (0.16, 0.72, 0.62)), 0.016, 0.007, k.mat("parrotfish-pink", (0.96, 0.46, 0.66))),
    "anthias": (k.mat("anthias-orange", (1.0, 0.52, 0.38)), 0.004, 0.002, None),
}


def make_fish(tag, kind, parent, at=(0, 0, 0), s=1.0):
    """A fish facing +X: body, forked tail, dorsal fin, eyes, and its bands."""
    col, L, H, band = FISH[kind]
    L, H = L * s, H * s
    ox, oy, oz = at
    body = k.sphere(f"{tag}-body", 1.0, material=col, parent=parent, subdiv=2)
    body.data.transform(X((ox, oy, oz)) @ DG(L, H * 0.42, H))
    tail = k.prism(f"{tag}-tail", [(0, 0), (-L * 0.75, H * 0.85), (-L * 0.55, 0), (-L * 0.75, -H * 0.85)], H * 0.12, material=col, parent=parent)
    tail.data.transform(X((ox - L * 0.85, oy + H * 0.06, oz)) @ RX(math.radians(90)))
    fin = k.prism(f"{tag}-dorsal", [(-L * 0.6, 0), (L * 0.3, 0), (-L * 0.4, H * 0.7)], H * 0.1, material=band or col, parent=parent)
    fin.data.transform(X((ox, oy + H * 0.05, oz + H * 0.7)) @ RX(math.radians(90)))
    for sy in (-1, 1):
        k.sphere(f"{tag}-eye{sy}", H * 0.18, at=(ox + L * 0.62, oy + sy * H * 0.33, oz + H * 0.22), material=white, parent=parent, subdiv=1)
        k.sphere(f"{tag}-pupil{sy}", H * 0.1, at=(ox + L * 0.68, oy + sy * H * 0.38, oz + H * 0.22), material=dark, parent=parent, subdiv=1)
    if band is not None and kind in ("clownfish", "angelfish"):
        for j, bx in enumerate((0.45, 0.0, -0.5)):
            b = k.cylinder(f"{tag}-band{j}", 1.0, L * 0.12, segs=12, material=band, parent=parent)
            b.data.transform(X((ox + L * bx, oy, oz)) @ RY(math.radians(90)) @ DG(H * 0.95, H * 0.45, 1))
    if kind == "butterflyfish":
        b = k.cylinder(f"{tag}-eyeband", 1.0, L * 0.14, segs=12, material=dark, parent=parent)
        b.data.transform(X((ox + L * 0.6, oy, oz)) @ RY(math.radians(90)) @ DG(H * 0.9, H * 0.44, 1))
    if kind == "parrotfish":
        k.box(f"{tag}-beak", (L * 0.18, H * 0.4, H * 0.3), at=(ox + L * 1.0, oy, oz - H * 0.15), material=band, parent=parent)


fish = k.empty("OBJ-reef-fish")
# Clownfish pairs, hovering round their anemones.
for i, (x, y, z) in enumerate(anemones):
    a = Vector((x - 0.012, y, z + 0.02))
    sh = mover(f"clown-{i}", a, a + Vector((0.024, 0.006, 0)), 6.0, phase=rnd.random(), bob=0.002, bob_hz=0.9, parent=fish)
    make_fish(f"clown{i}a", "clownfish", sh)
    make_fish(f"clown{i}b", "clownfish", sh, at=(-0.012, 0.008, 0.004), s=0.85)
# Butterflyfish and angelfish in pairs, parrotfish alone, along the reef.
for i, kind in enumerate(["butterflyfish", "angelfish", "parrotfish", "butterflyfish", "angelfish", "parrotfish"]):
    p = reef_point(0.06, 0.32)
    if not p:
        continue
    x, y, z = p
    a = Vector((x, y, max(z + 0.025, -0.085)))
    b = a + Vector((rnd.uniform(-0.03, 0.03), rnd.uniform(0.07, 0.13) * (1 if y < 0 else -1), 0))
    sh = mover(f"{kind}-{i}", a, b, rnd.uniform(10, 15), phase=rnd.random(), bob=0.002, bob_hz=0.7, parent=fish)
    make_fish(f"{kind}{i}a", kind, sh)
    if kind != "parrotfish":
        make_fish(f"{kind}{i}b", kind, sh, at=(-0.016, 0.01, 0.003), s=0.9)
# A shimmering swarm of anthias over the shelf.
for g in range(2):
    p = reef_point(0.06, 0.11, -0.3 + g * 0.4, -0.1 + g * 0.4)
    if not p:
        continue
    x, y, z = p
    a = Vector((x, y, z + 0.035))
    sh = mover(f"anthias-{g}", a, a + Vector((0.0, 0.06, 0.004)), 8.0, phase=g * 0.5, bob=0.003, bob_hz=1.1, parent=fish)
    for j in range(16):
        make_fish(f"anth{g}-{j}", "anthias", sh, at=(rnd.uniform(-0.02, 0.02), rnd.uniform(-0.012, 0.012), rnd.uniform(-0.008, 0.01)))

# A sea turtle cruising over the deep floor.
turtle = k.empty("OBJ-sea-turtle")
p0 = Vector((shore_x(-0.2) + 0.24, -0.2, -0.06))
tt = mover("turtle", p0, p0 + Vector((0.02, 0.3, 0.006)), 26.0, phase=0.2, bob=0.003, bob_hz=0.35, parent=turtle)
shell = k.sphere("turtle-shell", 1.0, material=k.mat("turtle-shell", (0.48, 0.38, 0.22)), parent=tt, subdiv=3)
for v in shell.data.vertices:
    v.co.z = max(v.co.z, -0.25)
shell.data.transform(DG(0.024, 0.018, 0.009))
for j in range(5):   # the scute pattern
    k.cylinder(f"turtle-scute{j}", 0.0045, 0.0015, at=(-0.012 + j * 0.006, 0, 0.008), segs=6, material=k.mat("turtle-scute", (0.62, 0.50, 0.30)), parent=tt)
skin = k.mat("turtle-skin", (0.56, 0.62, 0.48))
k.sphere("turtle-head", 0.006, at=(0.028, 0, 0.001), material=skin, parent=tt, subdiv=2)
for sx, sy, ln in ((0.012, 1, 0.022), (0.012, -1, 0.022), (-0.016, 1, 0.012), (-0.016, -1, 0.012)):
    fl = k.box(f"turtle-flipper{sx}{sy}", (ln * 0.5, ln, 0.002), material=skin, parent=tt)
    fl.data.transform(X((sx, sy * (0.016 + ln * 0.4), 0)) @ RZ(math.radians(-25 * sy)))


# ---- scuba divers: properly kitted, swimming slowly over the reef --------------
divers = k.empty("OBJ-scuba-divers")
skin2 = k.mat("diver-skin", (0.86, 0.68, 0.52))
bcd = k.mat("bcd-blue", (0.12, 0.32, 0.72))
fin_m = k.mat("fin-yellow", (1.0, 0.85, 0.1))
for i, (y0, y1, x_off, depth, ph) in enumerate([(-0.32, 0.02, 0.15, -0.055, 0.0), (0.38, 0.08, 0.24, -0.07, 0.4)]):
    a = Vector((shore_x(y0) + x_off, y0, depth))
    b = Vector((shore_x(y1) + x_off, y1, depth))
    dv = mover(f"diver-{i}", a, b, 44.0, phase=ph, bob=0.003, bob_hz=0.4, parent=divers)
    # Swimming flat, facing +X: torso, vest, tank, head and mask, arms, legs, fins.
    torso = k.sphere(f"diver{i}-torso", 1.0, material=wetsuit, parent=dv, subdiv=2)
    torso.data.transform(DG(0.014, 0.0065, 0.0055))
    k.box(f"diver{i}-bcd", (0.018, 0.0145, 0.006), at=(0.0, 0, -0.0005), material=bcd, parent=dv)
    tk = k.cylinder(f"diver{i}-tank", 0.0036, 0.022, segs=10, material=tank, parent=dv)
    tk.data.transform(X((-0.004, 0, 0.007)) @ RY(math.radians(90)) @ X((0, 0, -0.011)))
    k.cylinder(f"diver{i}-valve", 0.0012, 0.003, at=(0.0075, 0, 0.0065), segs=6, material=dark, parent=dv)
    k.sphere(f"diver{i}-head", 0.0045, at=(0.019, 0, 0.0025), material=wetsuit, parent=dv, subdiv=2)
    k.box(f"diver{i}-mask", (0.0025, 0.0065, 0.003), at=(0.0235, 0, 0.0015), material=k.mat("mask-lens", (0.55, 0.85, 1.0)), parent=dv)
    k.box(f"diver{i}-reg", (0.002, 0.002, 0.002), at=(0.023, 0, -0.0015), material=dark, parent=dv)
    for sy in (-1, 1):
        k.tube(f"diver{i}-arm{sy}", [(0.01, sy * 0.006, 0.0), (0.016, sy * 0.009, -0.004), (0.024, sy * 0.007, -0.006)], 0.0016, material=wetsuit, segs=5, parent=dv)
        k.sphere(f"diver{i}-hand{sy}", 0.0016, at=(0.025, sy * 0.007, -0.006), material=skin2, parent=dv, subdiv=1)
        k.tube(f"diver{i}-leg{sy}", [(-0.012, sy * 0.003, 0.0), (-0.02, sy * 0.004, 0.001), (-0.028, sy * 0.0035, 0.0)], 0.0019, material=wetsuit, segs=5, parent=dv)
        fin = k.prism(f"diver{i}-fin{sy}", [(0, -0.0025), (-0.014, -0.0035), (-0.014, 0.0035), (0, 0.0025)], 0.0008, material=fin_m, parent=dv)
        fin.data.transform(X((-0.029, sy * 0.0035, -0.0004)))
    for j in range(6):   # a column of bubbles rising from the regulator
        k.sphere(f"diver{i}-bubble{j}", 0.0012 + 0.0004 * j, at=(0.022 - j * 0.0015, 0.001 * (j % 2), 0.004 + j * 0.008), material=white, parent=dv, subdiv=1)


boats = k.empty("OBJ-dive-boats")
for i, (y0, y1, x_off, ph, colour) in enumerate([(-0.55, 0.15, 0.3, 0.0, hull_blue), (0.45, -0.05, 0.18, 0.5, k.mat("hull-white", (0.96, 0.96, 0.96)))]):
    a = Vector((shore_x(y0) + x_off, y0, SEA_LEVEL))
    b = Vector((shore_x(y1) + x_off, y1, SEA_LEVEL))
    bt = mover(f"dive-boat-{i}", a, b, 34.0, phase=ph, bob=0.002, bob_hz=0.6, parent=boats)
    hull = k.box(f"boat-{i}-hull", (0.07, 0.024, 0.014), at=(0, 0, -0.004), material=white, parent=bt)
    for v in hull.data.vertices:
        if v.co.x > 0.025:
            v.co.y *= 0.35
    k.box(f"boat-{i}-stripe", (0.071, 0.025, 0.004), at=(0, 0, 0.001), material=colour, parent=bt)
    k.box(f"boat-{i}-cabin", (0.03, 0.018, 0.014), at=(-0.008, 0, 0.01), material=white, parent=bt)
    k.box(f"boat-{i}-windows", (0.031, 0.019, 0.005), at=(-0.008, 0, 0.015), material=k.mat("neon-boat-window", (0.5, 0.85, 1.0)), parent=bt)
    # The divers-down flag: red with a white diagonal.
    k.cylinder(f"boat-{i}-flagpole", 0.0008, 0.03, at=(-0.03, 0, 0.01), segs=4, material=dark, parent=bt)
    k.box(f"boat-{i}-flag", (0.012, 0.001, 0.009), at=(-0.024, 0, 0.032), material=k.mat("flag-red", (0.9, 0.12, 0.12)), parent=bt)
    k.box(f"boat-{i}-flag-stripe", (0.014, 0.0012, 0.0015), at=(-0.024, 0, 0.036), material=white, parent=bt).data.transform(
        Matrix.Translation((-0.024, 0, 0.036)) @ Matrix.Rotation(math.radians(35), 4, "Y") @ Matrix.Translation((0.024, 0, -0.036)))

k.export("cairo")
