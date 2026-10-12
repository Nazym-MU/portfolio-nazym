"""
istanbul.py — the Istanbul diorama, the way Nazym saw it: from the
Touristanbul bus, which drives the road ring round the edge.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python scripts/blender/istanbul.py

                Galata Tower, Beyoğlu          |B|   Asian side (Üsküdar)
   ~~~~~ Golden Horn ~~~~ [Galata Bridge] ~~~~~~|o|
     Grand Bazaar                               |s|
          Hagia Sophia   Sultanahmet square     |p|
     Blue Mosque         simit truck            |.|
   (cats everywhere; the Touristanbul bus going round the outside)

Reference points (looked up): the Blue Mosque is a cascade of domes and
semi-domes building up to the central dome, with six fluted pencil
minarets with conical caps (four with three balconies, two with two) and an
arcaded, domed forecourt; Hagia Sophia is the great dome on a ring of
windows between semi-domes, heavy buttresses, rose-ochre walls and four
minarets; Galata Tower is a round stone tower, a viewing gallery high up,
a conical roof; the Galata Bridge has two levels, fishermen along its top
railings and restaurants underneath, a tram down the middle.
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

road = k.mat("asphalt", (0.32, 0.32, 0.36))
earth = k.mat("earth", (0.50, 0.42, 0.34))
paint = k.mat("road-white", (0.95, 0.95, 0.92))
paving = k.mat("paving", (0.84, 0.80, 0.72))
grass = k.mat("park-green", (0.50, 0.66, 0.42))
water = k.mat("bosphorus", (0.24, 0.48, 0.66))
lead = k.mat("lead-grey", (0.58, 0.62, 0.68))
hs_wall = k.mat("hagia-rose", (0.88, 0.62, 0.50))
bm_wall = k.mat("blue-mosque-stone", (0.86, 0.86, 0.84))
stone = k.mat("stone", (0.80, 0.74, 0.62))
white = k.mat("white", (0.96, 0.96, 0.95))
glow = k.mat("lamp-yellow", (1.0, 0.82, 0.42))
dark = k.mat("dark", (0.16, 0.16, 0.20))
red = k.mat("turkish-red", (0.82, 0.08, 0.12))
leaf = k.mat("tree", (0.32, 0.52, 0.32))
trunk = k.mat("trunk", (0.38, 0.28, 0.22))
houses = [k.mat(n, c) for n, c in [("house-cream", (0.92, 0.86, 0.72)), ("house-ochre", (0.88, 0.70, 0.46)),
                                    ("house-rose", (0.86, 0.62, 0.56)), ("house-blue", (0.62, 0.72, 0.84)),
                                    ("house-green", (0.66, 0.78, 0.62))]]
roof_red = k.mat("roof-terracotta", (0.70, 0.30, 0.20))
lamps = [k.mat(n, c) for n, c in [("neon-lamp-ruby", (1.0, 0.25, 0.3)), ("neon-lamp-amber", (1.0, 0.7, 0.2)),
                                   ("neon-lamp-teal", (0.2, 0.9, 0.8)), ("neon-lamp-violet", (0.7, 0.4, 1.0))]]
simit_m = k.mat("simit-crust", (0.78, 0.48, 0.20))
cat_cols = [k.mat(n, c) for n, c in [("cat-ginger", (0.94, 0.56, 0.20)), ("cat-grey-tabby", (0.56, 0.56, 0.58)),
                                      ("cat-white", (0.96, 0.95, 0.92)), ("cat-black", (0.14, 0.14, 0.16)),
                                      ("cat-cream", (0.92, 0.80, 0.62))]]

# ---- the base: a road ring round the outside, the land raised inside ---------
k.base(road, earth)
dashes = []
for i in range(56):
    a = 360 * i / 56
    d = k.box(f"dash-{i}", (0.035, 0.008, 0.002), material=paint)
    k.place(d, rot=(0, 0, a + 90), at=(0.91 * math.cos(math.radians(a)), 0.91 * math.sin(math.radians(a)), 0))
    dashes.append(d)
k.join("DECO-road-marks", dashes)

LAND_R, G = 0.8, 0.05
WATER_Z = G + 0.002          # water lies flat on the land: clean banks, no saw-teeth


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def bos_x(y):
    """The Bosphorus: down the right of the land, a gentle S."""
    return 0.4 + 0.07 * math.sin(2.4 * y + 0.6)


def horn_y(x):
    """The Golden Horn: off the Bosphorus, westward."""
    return 0.18 + 0.06 * math.sin(3.0 * x + 1.0)


def water_depth(x, y):
    d_bos = abs(x - bos_x(y)) - 0.07
    d_horn = abs(y - horn_y(x)) - 0.045 if x < bos_x(y) else 9.0
    return min(d_bos, d_horn)        # < 0 inside the water


def height(x, y):
    r = math.hypot(x, y)
    if r > LAND_R:
        return 0.0
    return G


RINGS, SEGS = 40, 200
bm = bmesh.new()
grid = [[bm.verts.new((0, 0, height(0, 0)))]]
for j in range(1, RINGS + 1):
    r = LAND_R * j / RINGS * 0.999
    grid.append([bm.verts.new((r * math.cos(2 * math.pi * i / SEGS), r * math.sin(2 * math.pi * i / SEGS),
                               height(r * math.cos(2 * math.pi * i / SEGS), r * math.sin(2 * math.pi * i / SEGS))))
                 for i in range(SEGS)])
skirt = [bm.verts.new((LAND_R * math.cos(2 * math.pi * i / SEGS), LAND_R * math.sin(2 * math.pi * i / SEGS), 0.0)) for i in range(SEGS)]
for a, b in zip(grid + [skirt], grid[1:] + [skirt]):
    if a is b:
        continue
    for i in range(SEGS):
        if len(a) == 1:
            bm.faces.new((a[0], b[i], b[(i + 1) % SEGS]))
        else:
            bm.faces.new((a[i], a[(i + 1) % SEGS], b[(i + 1) % SEGS], b[i]))
land = k.obj_from_bm("DECO-land", bm)
for m in (paving, earth, water):
    land.data.materials.append(m)
for p in land.data.polygons:
    c = p.center
    if math.hypot(c.x, c.y) > LAND_R - 0.004:
        p.material_index = 1
    else:
        p.material_index = 0
    p.use_smooth = True
k.smooth_by_angle(land, 40)
# The water surfaces.
k.ribbon("DECO-bosphorus", [(bos_x(y / 100), y / 100) for y in range(-82, 83, 2)], 0.15, z=WATER_Z, material=water, clip=LAND_R - 0.01)
horn = [(x / 100, horn_y(x / 100)) for x in range(-82, int(bos_x(0.2) * 100), 2)]
k.ribbon("DECO-golden-horn", horn, 0.1, z=WATER_Z + 0.0008, material=water, clip=LAND_R - 0.01)


def stand(o, x, y, rot=0.0, extra=0.0):
    o.data.transform(Matrix.Translation((x, y, height(x, y) + extra)) @ Matrix.Rotation(math.radians(rot), 4, "Z"))
    return o


def place(parts, x, y, rot=0.0, extra=0.0):
    for o in parts:
        stand(o, x, y, rot=rot, extra=extra)
    return parts


def dome(name, r, at, material=lead, parent=None, half=False):
    o = k.sphere(name, r, material=material, parent=parent, subdiv=3)
    for v in o.data.vertices:
        v.co.z = max(v.co.z, 0.0)
        if half and v.co.x < 0:
            v.co.x = 0.0
    o.data.transform(Matrix.Translation(at))
    return o


def minaret(name, x, y, h, balconies, parent, body=white):
    """A pencil minaret: slender, fluted, balconies, a sharp conical cap."""
    parts = [k.cylinder(f"{name}-shaft", 0.0065, h, at=(x, y, 0), r_top=0.0055, segs=12, material=body, parent=parent)]
    for b in range(balconies):
        z = h * (0.55 + 0.17 * b)
        parts.append(k.cylinder(f"{name}-balcony{b}", 0.0095, 0.004, at=(x, y, z), segs=12, material=body, parent=parent))
    parts.append(k.cylinder(f"{name}-cap", 0.0058, h * 0.2, at=(x, y, h), r_top=0.0, segs=12, material=lead, parent=parent))
    return parts


# ---- the Blue Mosque: a cascade of domes, six minarets, the forecourt --------
BM = (-0.3, -0.4)
bmq = k.empty("OBJ-blue-mosque")
parts = [k.box("bmq-hall", (0.17, 0.17, 0.05), material=bm_wall, parent=bmq)]
parts.append(k.cylinder("bmq-drum", 0.05, 0.03, at=(0, 0, 0.07), segs=28, material=bm_wall, parent=bmq))
for i in range(16):
    a = 2 * math.pi * i / 16
    parts.append(k.box(f"bmq-win{i}", (0.008, 0.002, 0.012), at=(0.0505 * math.cos(a), 0.0505 * math.sin(a), 0.078), material=glow, parent=bmq))
    parts[-1].data.transform(Matrix.Translation((0.0505 * math.cos(a), 0.0505 * math.sin(a), 0)) @ Matrix.Rotation(a + math.pi / 2, 4, "Z")
                             @ Matrix.Translation((-0.0505 * math.cos(a), -0.0505 * math.sin(a), 0)))
parts.append(dome("bmq-dome", 0.05, (0, 0, 0.1), parent=bmq))
parts.append(k.cylinder("bmq-finial", 0.003, 0.02, at=(0, 0, 0.15), segs=6, r_top=0.0, material=k.mat("gold", (0.96, 0.76, 0.3)), parent=bmq))
for i in range(4):   # the four semi-domes cascading down from it
    a = math.pi / 2 * i
    sd = dome(f"bmq-semi{i}", 0.036, (0, 0, 0), parent=bmq, half=True)
    sd.data.transform(Matrix.Translation((0.04 * math.cos(a), 0.04 * math.sin(a), 0.07)) @ Matrix.Rotation(a, 4, "Z"))
    parts.append(sd)
    for s_ in (-1, 1):   # and the smaller exedrae beside each
        ex = dome(f"bmq-ex{i}{s_}", 0.016, (0, 0, 0), parent=bmq)
        ex.data.transform(Matrix.Translation((0.065 * math.cos(a) - s_ * 0.035 * math.sin(a), 0.065 * math.sin(a) + s_ * 0.035 * math.cos(a), 0.05)))
        parts.append(ex)
for sx in (-1, 1):
    for sy in (-1, 1):
        parts.append(dome(f"bmq-corner{sx}{sy}", 0.02, (sx * 0.06, sy * 0.06, 0.05), parent=bmq))
        parts += minaret(f"bmq-min{sx}{sy}", sx * 0.095, sy * 0.095, 0.24, 3, bmq)
# The forecourt in front (toward -Y), arcaded with little domes, two more minarets.
parts.append(k.box("bmq-court", (0.17, 0.13, 0.03), at=(0, -0.15, 0), material=bm_wall, parent=bmq))
parts.append(k.box("bmq-court-yard", (0.13, 0.09, 0.031), at=(0, -0.15, 0.0), material=paving, parent=bmq))
for i in range(6):
    for side in (-1, 1):
        parts.append(dome(f"bmq-portico{i}{side}", 0.009, (-0.07 + i * 0.028, -0.15 + side * 0.055, 0.03), parent=bmq))
parts.append(k.cylinder("bmq-fountain", 0.012, 0.012, at=(0, -0.15, 0.031), segs=8, material=bm_wall, parent=bmq, smooth=False))
parts.append(dome("bmq-fountain-dome", 0.012, (0, -0.15, 0.043), parent=bmq))
for sx in (-1, 1):
    parts += minaret(f"bmq-court-min{sx}", sx * 0.09, -0.215, 0.2, 2, bmq)
place(parts, *BM, rot=10)


# ---- Hagia Sophia: the great dome on its ring of windows, buttresses -------
HS = (0.06, -0.2)
hs = k.empty("OBJ-hagia-sophia")
parts = [k.box("hs-body", (0.2, 0.16, 0.06), material=hs_wall, parent=hs)]
parts.append(k.cylinder("hs-drum", 0.055, 0.022, at=(0, 0, 0.06), segs=40, material=hs_wall, parent=hs))
for i in range(20):   # the famous ring of windows at the dome's base
    a = 2 * math.pi * i / 20
    w_ = k.box(f"hs-win{i}", (0.008, 0.002, 0.012), material=glow, parent=hs)
    w_.data.transform(Matrix.Translation((0.0555 * math.cos(a), 0.0555 * math.sin(a), 0.065)) @ Matrix.Rotation(a + math.pi / 2, 4, "Z"))
    parts.append(w_)
big = dome("hs-dome", 0.056, (0, 0, 0.082), parent=hs)
for v in big.data.vertices:          # shallower than a hemisphere
    v.co.z = 0.082 + (v.co.z - 0.082) * 0.62
parts.append(big)
for sx in (-1, 1):   # semi-domes east and west, half-domes stepping down
    sd = dome(f"hs-semi{sx}", 0.045, (0, 0, 0), parent=hs, half=True)
    sd.data.transform(Matrix.Translation((sx * 0.045, 0, 0.06)) @ Matrix.Rotation(0 if sx > 0 else math.pi, 4, "Z") @ Matrix.Diagonal((1, 1, 0.7, 1)))
    parts.append(sd)
    for sy in (-1, 1):
        parts.append(dome(f"hs-small{sx}{sy}", 0.018, (sx * 0.075, sy * 0.04, 0.06), parent=hs))
# Heavy buttresses along the north and south walls.
for sy in (-1, 1):
    for i in range(3):
        b_ = k.box(f"hs-buttress{sy}{i}", (0.024, 0.03, 0.075), at=(-0.05 + i * 0.05, sy * 0.09, 0), material=hs_wall, parent=hs)
        parts.append(b_)
# Four minarets at the corners (two plain brick, two slender white).
for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
    parts += minaret(f"hs-min{i}", sx * 0.12, sy * 0.1, 0.2, 1, hs, body=hs_wall if i % 2 else white)
place(parts, *HS, rot=-8)
# Sultanahmet square between them, with plane trees and benches.
sq = k.prism("DECO-sultanahmet", [(-0.16, -0.62), (0.06, -0.62), (0.1, -0.4), (-0.12, -0.4)], 0.003, z0=G, material=k.mat("square-stone", (0.86, 0.82, 0.74)))


# ---- the Grand Bazaar: a field of little domes, a gate, lamps for sale ------
GB = (-0.4, -0.04)
gb = k.empty("OBJ-grand-bazaar")
parts = [k.box("gb-halls", (0.22, 0.14, 0.035), material=stone, parent=gb)]
for i in range(6):
    for j in range(4):
        parts.append(dome(f"gb-dome{i}{j}", 0.014, (-0.09 + i * 0.036, -0.05 + j * 0.034, 0.035), parent=gb))
parts.append(k.box("gb-gate", (0.05, 0.02, 0.06), at=(0, -0.075, 0), material=stone, parent=gb))
parts.append(k.box("gb-gate-arch", (0.02, 0.022, 0.035), at=(0, -0.075, 0), material=dark, parent=gb))
parts.append(k.box("gb-gate-sign", (0.03, 0.022, 0.006), at=(0, -0.076, 0.045), material=k.mat("gold", (0.96, 0.76, 0.3)), parent=gb))
# The Turkish mosaic lamps hanging along the front.
for i in range(10):
    x = -0.1 + i * 0.022
    parts.append(k.cylinder(f"gb-lamp-cord{i}", 0.0006, 0.01, at=(x, -0.085, 0.028), segs=3, material=dark, parent=gb))
    parts.append(k.sphere(f"gb-lamp{i}", 0.005, at=(x, -0.085, 0.024), material=lamps[i % 4], parent=gb, subdiv=1))
place(parts, *GB, rot=5)


# ---- Galata Tower and Beyoğlu ------------------------------------------------
GT = (-0.24, 0.46)
gt = k.empty("OBJ-galata-tower")
parts = [k.cylinder("gt-body", 0.03, 0.16, r_top=0.027, segs=24, material=stone, parent=gt)]
parts.append(k.cylinder("gt-gallery", 0.034, 0.006, at=(0, 0, 0.13), segs=24, material=stone, parent=gt))
for i in range(12):
    a = 2 * math.pi * i / 12
    w_ = k.box(f"gt-arch{i}", (0.008, 0.002, 0.018), material=glow, parent=gt)
    w_.data.transform(Matrix.Translation((0.0275 * math.cos(a), 0.0275 * math.sin(a), 0.138)) @ Matrix.Rotation(a + math.pi / 2, 4, "Z"))
    parts.append(w_)
parts.append(k.cylinder("gt-roof", 0.031, 0.07, at=(0, 0, 0.16), r_top=0.0, segs=24, material=lead, parent=gt))
parts.append(k.cylinder("gt-finial", 0.0015, 0.015, at=(0, 0, 0.23), segs=5, material=k.mat("gold", (0.96, 0.76, 0.3)), parent=gt))
for i in range(4):
    parts.append(k.box(f"gt-window{i}", (0.006, 0.002, 0.01), material=glow, parent=gt))
    parts[-1].data.transform(Matrix.Translation((0, -0.03, 0.03 + i * 0.025)))
place(parts, *GT)


# ---- the Galata Bridge over the Golden Horn ----------------------------------
GBX = -0.12
gbr = k.empty("OBJ-galata-bridge")
y0, y1 = horn_y(GBX) - 0.075, horn_y(GBX) + 0.075
L = y1 - y0
ym = (y0 + y1) / 2
parts = [k.box("br-upper", (0.045, L, 0.006), at=(GBX, ym, G + 0.012), material=k.mat("bridge-grey", (0.70, 0.72, 0.74)), parent=gbr),
         k.box("br-tram", (0.008, L, 0.002), at=(GBX, ym, G + 0.018), material=dark, parent=gbr),
         k.box("br-lower", (0.04, L * 0.8, 0.006), at=(GBX, ym, WATER_Z), material=stone, parent=gbr)]
for i in range(4):
    parts.append(k.box(f"br-pier{i}", (0.04, 0.006, 0.014), at=(GBX, y0 + 0.01 + i * L / 3.2, WATER_Z), material=stone, parent=gbr))
for i in range(6):   # restaurants on the lower level, lit
    parts.append(k.box(f"br-restaurant{i}", (0.042, 0.016, 0.006), at=(GBX, y0 + 0.02 + i * L * 0.13, WATER_Z + 0.003), material=glow, parent=gbr))
for side in (-1, 1):
    parts.append(k.box(f"br-rail{side}", (0.002, L, 0.006), at=(GBX + side * 0.022, ym, G + 0.018), material=dark, parent=gbr))
    for i in range(7):   # fishermen with long rods over the rail
        y = y0 + 0.012 + i * L / 7
        parts.append(k.cylinder(f"br-fisher{side}{i}", 0.0028, 0.012, at=(GBX + side * 0.017, y, G + 0.018), segs=6, material=cat_cols[(i + side) % 5], parent=gbr))
        parts.append(k.sphere(f"br-fisher-head{side}{i}", 0.0025, at=(GBX + side * 0.017, y, G + 0.033), material=dark, parent=gbr, subdiv=1))
        parts.append(k.tube(f"br-rod{side}{i}", [(GBX + side * 0.017, y, G + 0.028), (GBX + side * 0.05, y, G + 0.046)], 0.0006, material=dark, segs=3, parent=gbr))
        parts.append(k.tube(f"br-line{side}{i}", [(GBX + side * 0.05, y, G + 0.046), (GBX + side * 0.055, y, WATER_Z)], 0.0003, material=white, segs=3, parent=gbr))


# ---- the simit truck --------------------------------------------------------
ST = (-0.08, -0.52)
st = k.empty("OBJ-simit-truck")
parts = [k.box("st-cab", (0.024, 0.032, 0.026), at=(0.034, 0, 0.006), material=red, parent=st),
         k.box("st-windscreen", (0.002, 0.026, 0.01), at=(0.047, 0, 0.018), material=k.mat("cab-glass", (0.6, 0.8, 0.95)), parent=st),
         k.box("st-body", (0.05, 0.034, 0.03), at=(0.0, 0, 0.006), material=red, parent=st),
         k.box("st-display", (0.04, 0.0025, 0.016), at=(-0.002, -0.0175, 0.016), material=k.mat("display-glass", (0.85, 0.92, 0.95)), parent=st),
         k.box("st-sign", (0.04, 0.003, 0.007), at=(-0.002, -0.018, 0.034), material=white, parent=st),
         k.box("st-awning", (0.05, 0.014, 0.002), at=(-0.002, -0.024, 0.036), material=k.mat("awning-white", (0.96, 0.94, 0.9)), parent=st)]
for wx in (-0.016, 0.034):
    for wy in (-1, 1):
        w_ = k.cylinder(f"st-wheel{wx}{wy}", 0.0065, 0.004, segs=12, material=dark, parent=st)
        w_.data.transform(Matrix.Translation((wx, wy * 0.017, 0.0065)) @ Matrix.Rotation(math.radians(90), 4, "X"))
        parts.append(w_)
# Simit stacked on poles in the display, and a ring held up on the counter.
for i in range(3):
    for j in range(3):
        sm = k.torus(f"st-simit{i}{j}", 0.0048, 0.0018, at=(-0.016 + i * 0.014, -0.018, 0.019 + j * 0.0045), segs=14, tube_segs=4, material=simit_m, parent=st)
        parts.append(sm)
place(parts, *ST, rot=25)


# ---- bigger landmarks, each grown about its own footprint ------------------
def grow_in_place(o, f):
    pts = []
    stack = [o]
    while stack:
        x_ = stack.pop()
        if x_.type == "MESH":
            pts += [x_.matrix_world @ v.co for v in x_.data.vertices]
        stack.extend(x_.children)
    cx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2
    cy = (min(p.y for p in pts) + max(p.y for p in pts)) / 2
    k.grow(o, f, (cx, cy, height(cx, cy)))


for o, f in [(bmq, 1.4), (hs, 1.4), (gb, 1.3), (gt, 1.5), (st, 1.6)]:
    grow_in_place(o, f)


# ---- the Asian side and Beyoğlu: tidy rows of houses with red roofs -------
fill = []
rnd = random.Random(11)
rows = [(-0.48, 0.38, -0.34, 0.6), (-0.12, 0.36, 0.06, 0.56), (-0.6, 0.34, -0.66, 0.5),        # Beyoğlu, round Galata
        (0.54, -0.5, 0.6, 0.3), (0.62, -0.3, 0.68, 0.12), (0.5, 0.36, 0.56, 0.6),              # the Asian side
        (-0.62, -0.26, -0.5, -0.5), (0.2, -0.5, 0.3, -0.62), (0.2, 0.02, 0.28, -0.24)]
for ri, (x0, y0_, x1, y1_) in enumerate(rows):
    n = max(2, int(math.hypot(x1 - x0, y1_ - y0_) / 0.045))
    for i in range(n):
        t = (i + 0.5) / n
        x, y = x0 + (x1 - x0) * t, y0_ + (y1_ - y0_) * t
        if math.hypot(x, y) > LAND_R - 0.04 or water_depth(x, y) < 0.03:
            continue
        h = 0.03 + 0.012 * ((ri + i) % 3)
        fill.append(stand(k.box(f"h-{ri}-{i}", (0.032, 0.036, h), material=houses[(ri + i) % 5]), x, y, rot=10 * (ri % 3)))
        rf = k.cylinder(f"h-roof-{ri}-{i}", 0.03, 0.014, segs=4, r_top=0.008, material=roof_red, smooth=False)
        rf.data.transform(Matrix.Rotation(math.radians(45), 4, "Z"))
        fill.append(stand(rf, x, y, rot=10 * (ri % 3), extra=h))
        fill.append(stand(k.box(f"h-win-{ri}-{i}", (0.034, 0.038, 0.003), material=glow), x, y, rot=10 * (ri % 3), extra=h * 0.55))
for i in range(30):
    a, d = rnd.uniform(0, 2 * math.pi), rnd.uniform(0.2, LAND_R - 0.04)
    x, y = d * math.cos(a), d * math.sin(a)
    if water_depth(x, y) < 0.03:
        continue
    if any(math.hypot(x - cx, y - cy) < rr for cx, cy, rr in [(*BM, 0.3), (*HS, 0.24), (*GB, 0.2), (*GT, 0.08), (*ST, 0.08)]):
        continue
    h = rnd.uniform(0.05, 0.07)
    z = height(x, y)
    fill += [k.cylinder(f"tr-{i}", 0.004, h * 0.4, at=(x, y, z), segs=5, material=trunk),
             k.sphere(f"tc-{i}", h * 0.42, at=(x, y, z + h * 0.7), material=leaf, subdiv=2)]
k.join("DECO-city", fill)


# ---- cats, all around the place -------------------------------------------------
cats = k.empty("OBJ-cats")


def cat(tag, x, y, z, rot, col, pose):
    parts = []
    if pose == "sit":
        b = k.sphere(f"{tag}-body", 1.0, material=col, parent=cats, subdiv=2)
        b.data.transform(Matrix.Translation((0, 0, 0.007)) @ Matrix.Diagonal((0.006, 0.005, 0.008, 1)))
        parts.append(b)
        parts.append(k.sphere(f"{tag}-head", 0.0045, at=(0.002, 0, 0.017), material=col, parent=cats, subdiv=2))
        hz = 0.017
        parts.append(k.tube(f"{tag}-tail", [(-0.005, 0, 0.002), (-0.008, 0.004, 0.001), (-0.004, 0.008, 0.001)], 0.0012, material=col, segs=4, parent=cats))
    else:   # curled up asleep
        b = k.sphere(f"{tag}-body", 1.0, material=col, parent=cats, subdiv=2)
        b.data.transform(Matrix.Translation((0, 0, 0.004)) @ Matrix.Diagonal((0.009, 0.007, 0.005, 1)))
        parts.append(b)
        parts.append(k.sphere(f"{tag}-head", 0.004, at=(0.006, 0.003, 0.006), material=col, parent=cats, subdiv=2))
        hz = 0.006
        parts.append(k.tube(f"{tag}-tail", [(-0.008, 0, 0.003), (-0.004, -0.007, 0.003), (0.004, -0.007, 0.003)], 0.0014, material=col, segs=4, parent=cats))
    hx = 0.002 if pose == "sit" else 0.006
    hy = 0.0 if pose == "sit" else 0.003
    for sy in (-1, 1):
        parts.append(k.cylinder(f"{tag}-ear{sy}", 0.0018, 0.004, at=(hx, hy + sy * 0.0024, hz + 0.003), r_top=0.0, segs=4, material=col, parent=cats, smooth=False))
    for o in parts:
        o.data.transform(Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(rot), 4, "Z") @ Matrix.Scale(1.5, 4))


spots = [(BM[0] + 0.02, BM[1] - 0.26), (BM[0] + 0.1, BM[1] - 0.2), (HS[0] - 0.13, HS[1] - 0.04), (HS[0] + 0.02, HS[1] - 0.11),
         (GB[0] + 0.03, GB[1] - 0.1), (GB[0] - 0.08, GB[1] - 0.1), (GT[0] + 0.05, GT[1] - 0.03), (GT[0] - 0.04, GT[1] - 0.05),
         (ST[0] - 0.04, ST[1] - 0.03), (ST[0] + 0.02, ST[1] - 0.04), (ST[0] - 0.01, ST[1] + 0.04), (-0.06, -0.3),
         (0.58, -0.12), (0.62, 0.2), (-0.5, 0.2), (0.12, -0.42), (-0.62, -0.1), (0.24, -0.3), (-0.02, 0.4), (0.0, -0.05),
         (-0.3, 0.3), (0.5, -0.36), (-0.15, -0.5), (0.3, 0.05)]
for i, (x, y) in enumerate(spots):
    if math.hypot(x, y) > LAND_R - 0.02 or water_depth(x, y) < 0.01:
        continue
    cat(f"cat{i}", x, y, height(x, y), rnd.uniform(0, 360), cat_cols[i % 5], "sit" if i % 3 else "curl")
# Two on the Galata Bridge, waiting on the fishermen.
cat("cat-bridge0", GBX + 0.01, horn_y(GBX) - 0.02, G + 0.018, 90, cat_cols[0], "sit")
cat("cat-bridge1", GBX - 0.008, horn_y(GBX) + 0.03, G + 0.018, 270, cat_cols[2], "curl")


# ---- the Touristanbul bus, going round the ring road with its flag -----------
bus = k.empty("OBJ-touristanbul-bus")
bus["orbit"] = 52.0
R_ = 0.945
Lb, Wb, Hb = 0.15, 0.058, 0.05
bparts = [k.box("bus-body", (Wb, Lb, Hb), at=(R_, 0, 0.012), material=white, parent=bus),
          k.box("bus-red-band", (Wb + 0.002, Lb + 0.002, 0.012), at=(R_, 0, 0.014), material=red, parent=bus),
          k.box("bus-windows-l", (0.002, Lb * 0.85, 0.018), at=(R_ - Wb / 2 - 0.001, 0.004, 0.034), material=glow, parent=bus),
          k.box("bus-windows-r", (0.002, Lb * 0.85, 0.018), at=(R_ + Wb / 2 + 0.001, 0.004, 0.034), material=glow, parent=bus),
          k.box("bus-windscreen", (Wb * 0.85, 0.002, 0.022), at=(R_, Lb / 2 + 0.001, 0.032), material=glow, parent=bus),
          k.box("bus-roof", (Wb * 0.96, Lb * 0.97, 0.004), at=(R_, 0, 0.062), material=white, parent=bus)]
for wy in (-0.045, 0.045):
    for side in (-1, 1):
        w_ = k.cylinder(f"bus-wheel{wy}{side}", 0.012, 0.008, segs=12, material=dark, parent=bus)
        w_.data.transform(Matrix.Translation((R_ + side * (Wb / 2 - 0.003), wy, 0.012)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
        bparts.append(w_)
# The Touristanbul flag on a pole on the roof.
bparts.append(k.cylinder("bus-flagpole", 0.0012, 0.05, at=(R_, -0.03, 0.066), segs=5, material=dark, parent=bus))
flag = k.box("bus-flag", (0.002, 0.034, 0.022), at=(R_, -0.013, 0.094), material=red, parent=bus)
bparts.append(flag)
bparts.append(k.box("bus-flag-mark", (0.0025, 0.022, 0.006), at=(R_, -0.013, 0.102), material=white, parent=bus))
bparts.append(k.box("bus-side-logo", (0.003, 0.05, 0.008), at=(R_ - Wb / 2 - 0.0015, -0.03, 0.044), material=red, parent=bus))

k.export("istanbul")
