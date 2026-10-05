"""
bukhara.py — the Bukhara diorama, made to be seen by day AND by night: the
viewer has a switch, and every `nightglow-*` material (the floodlit Kalan
minaret, lanterns, domes, windows, stall bulbs) lights up after dark.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python scripts/blender/bukhara.py

          Ark (fortress, ramp)     Kalyan Mosque  Kalan minaret  Mir-i-Arab
                                        (Po-i-Kalyan square)
     Ulugbek Madrasah      trading domes + chapan stalls        Chor Minor

Reference points (looked up): the Ark is a massive earthen fortress with
sloping walls, entered up a rising ramp between two towers joined by a
gallery; the Kalan minaret is a tapering baked-brick column with ornamental
brick bands and a lantern rotunda of sixteen arches under a stalactite
cornice, linked by an arched bridge to the Kalyan Mosque, opposite the
Mir-i-Arab madrasah; Chor Minor is a gatehouse with four towers each capped
by a blue-tiled dome; the trading domes (toki) are clusters of domes over
crossroads, where chapans hang for sale.
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
import silk_road as sr  # noqa: E402

k.reset()

paving = k.mat("paving-sand", (0.86, 0.78, 0.62))
earth = k.mat("earth", (0.60, 0.46, 0.32))
grass = k.mat("grass", (0.56, 0.68, 0.44))
# Day colours; the `nightglow-` prefix makes them light up at night.
brick = k.mat("nightglow-brick", (0.80, 0.64, 0.44))
clay = k.mat("nightglow-ark-clay", (0.78, 0.62, 0.44))
tile = k.mat("nightglow-tile", (0.18, 0.60, 0.70))
dome_m = k.mat("nightglow-dome", (0.16, 0.54, 0.78))
lantern = k.mat("nightglow-lantern", (1.0, 0.84, 0.50))
window = k.mat("nightglow-window", (0.98, 0.78, 0.44))
inner = k.mat("niche-blue", (0.16, 0.38, 0.62))
white = k.mat("stucco-white", (0.94, 0.93, 0.88))
dark = k.mat("dark", (0.18, 0.18, 0.22))
wood = k.mat("wood", (0.50, 0.34, 0.22))
leaf = k.mat("mulberry", (0.32, 0.52, 0.30))
trunk = k.mat("trunk", (0.40, 0.30, 0.22))
pool = k.mat("pool", (0.30, 0.56, 0.66))
ikat = [k.mat(n, c) for n, c in [("ikat-purple", (0.50, 0.24, 0.62)), ("ikat-gold", (0.94, 0.72, 0.22)),
                                  ("ikat-teal", (0.12, 0.58, 0.58)), ("ikat-red", (0.82, 0.18, 0.20)),
                                  ("ikat-green", (0.28, 0.58, 0.30)), ("ikat-blue", (0.20, 0.34, 0.72))]]

MAT = dict(body=brick, tile=tile, inner=inner, dome=dome_m, lantern=lantern, window=window)

k.base(paving, earth)


def ground(x, y):
    return 0.0


def at(parts, x, y, rot):
    return sr.place_all(parts, x, y, 0.0, rot)


# Grass round the rim, paving in the old town.
rim = k.prism("DECO-rim-grass", [(0.98 * math.cos(2 * math.pi * i / 96), 0.98 * math.sin(2 * math.pi * i / 96)) for i in range(96)], 0.002,
              holes=[[(0.8 * math.cos(2 * math.pi * i / 96), 0.8 * math.sin(2 * math.pi * i / 96)) for i in range(96)]], material=grass)


# ---- the Kalan minaret ---------------------------------------------------------
KM = (0.02, 0.24)
km = k.empty("OBJ-kalan-minaret")
H = 0.56
kparts = [k.cylinder("km-shaft", 0.05, H, r_top=0.033, segs=24, material=brick, parent=km)]
# Ornamental brick belts all the way up, a blue frieze near the top.
for i in range(10):
    z = H * (0.06 + 0.09 * i)
    r = 0.05 + (0.033 - 0.05) * z / H
    kparts.append(k.cylinder(f"km-belt-{i}", r * 1.03, 0.006, at=(0, 0, z), segs=24,
                             material=tile if i in (8,) else k.mat("nightglow-brick-dark", (0.66, 0.50, 0.34)), parent=km))
# The lantern rotunda: sixteen open arches, a stalactite cornice, a cap.
kparts.append(k.cylinder("km-rotunda", 0.04, 0.05, at=(0, 0, H), segs=24, material=brick, parent=km))
for i in range(16):
    a = 2 * math.pi * i / 16
    n = sr.niche(f"km-arch-{i}", 0.01, 0.034, 0.003, lantern, parent=km)
    n.data.transform(Matrix.Rotation(a, 4, "Z") @ Matrix.Translation((0, -0.0405, H + 0.008)))
    kparts.append(n)
kparts.append(k.cylinder("km-cornice", 0.046, 0.016, at=(0, 0, H + 0.05), r_top=0.04, segs=24, material=brick, parent=km))
kparts.append(k.cylinder("km-cap", 0.036, 0.022, at=(0, 0, H + 0.066), r_top=0.012, segs=24, material=brick, parent=km))
at(kparts, *KM, 0)


# ---- Kalyan Mosque (west) and Mir-i-Arab Madrasah (east) round the square -----
kalyan = k.empty("OBJ-kalyan-mosque")
kparts = [k.box("kal-wall", (0.08, 0.3, 0.07), material=brick, parent=kalyan)]
for o in sr.pishtaq("kal-portal", 0.1, 0.14, 0.03, brick, tile, inner, parent=kalyan):
    o.data.transform(Matrix.Translation((0, -0.16, 0)))
    kparts.append(o)
for o in sr.ribbed_dome("kal", 0.05, 0.06, dome_m, ribs=24, depth=0.04, drum_h=0.04, drum_mat=brick, parent=kalyan):
    o.data.transform(Matrix.Translation((0, 0.06, 0.07)))
    kparts.append(o)
for i in range(6):
    kparts.append(k.box(f"kal-win-{i}", (0.004, 0.022, 0.024), at=(0.041, -0.11 + i * 0.044, 0.02), material=window, parent=kalyan))
at(kparts, KM[0] - 0.24, KM[1] + 0.02, -90)
# The arched footbridge from the minaret to the mosque roof.
bridge = []
for i in range(13):
    t = i / 12
    bridge.append((KM[0] - 0.03 - 0.17 * t, KM[1] + 0.02, 0.07 + 0.02 * math.sin(math.pi * t)))
br = k.tube("kal-bridge", bridge, 0.006, material=brick, segs=5, parent=kalyan)

mir = k.empty("OBJ-mir-i-arab")
at(sr.madrasah("mir", 0.3, 0.06, 0.08, MAT, parent=mir, minarets=False, domes=2), KM[0] + 0.25, KM[1] + 0.02, 90)


# ---- the Ark -------------------------------------------------------------------
AK = (-0.54, -0.02)
ark = k.empty("OBJ-ark")
aparts = []
# Sloping earthen walls: a frustum on a rounded rectangle.
bm = bmesh.new()
outline = []
for cx, cy, a0 in [(0.12, 0.09, 0), (-0.12, 0.09, 90), (-0.12, -0.09, 180), (0.12, -0.09, 270)]:
    for j in range(7):
        a = math.radians(a0 + 90 * j / 6)
        outline.append((cx, cy, a))
bot = [bm.verts.new((cx + 0.06 * math.cos(a), cy + 0.06 * math.sin(a), 0.0)) for cx, cy, a in outline]
top = [bm.verts.new((cx * 0.92 + 0.045 * math.cos(a), cy * 0.92 + 0.045 * math.sin(a), 0.13)) for cx, cy, a in outline]
n = len(outline)
for i in range(n):
    bm.faces.new((bot[i], bot[(i + 1) % n], top[(i + 1) % n], top[i]))
bm.faces.new(top)
bm.faces.new(list(reversed(bot)))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
aparts.append(k.obj_from_bm("ark-walls", bm, clay, parent=ark))
# Crenellations along the top edge.
for i in range(0, n, 1):
    cx, cy, a = outline[i]
    aparts.append(k.box(f"ark-merlon-{i}", (0.012, 0.012, 0.014), at=(cx * 0.92 + 0.045 * math.cos(a), cy * 0.92 + 0.045 * math.sin(a), 0.13),
                        material=clay, parent=ark))
# The entrance on the east face: two great round towers, a gallery between,
# and the ramp rising to the gate.
for side in (-1, 1):
    aparts.append(k.cylinder(f"ark-gate-tower-{side}", 0.034, 0.17, r_top=0.026, at=(0.18, side * 0.045, 0.0), segs=20, material=clay, parent=ark))
aparts.append(k.box("ark-gallery", (0.04, 0.07, 0.035), at=(0.19, 0.0, 0.12), material=brick, parent=ark))
for i in range(4):
    aparts.append(k.box(f"ark-gallery-win-{i}", (0.003, 0.01, 0.016), at=(0.211, -0.022 + i * 0.015, 0.128), material=window, parent=ark))
aparts.append(k.box("ark-gate", (0.004, 0.03, 0.05), at=(0.17, 0.0, 0.06), material=dark, parent=ark))
ramp = k.box("ark-ramp", (0.16, 0.04, 0.006), material=clay, parent=ark)
for v in ramp.data.vertices:
    v.co.z += 0.06 * (0.5 - v.co.x / 0.16)          # rising toward the gate
ramp.data.transform(Matrix.Translation((0.26, 0.0, 0.0)))
aparts.append(ramp)
at(aparts, *AK, 0)


# ---- Ulugbek Madrasah ----------------------------------------------------------
ub = k.empty("OBJ-ulugbek-madrasah")
at(sr.madrasah("ub", 0.28, 0.06, 0.08, MAT, parent=ub, minarets=True, domes=0), -0.34, -0.44, 20)


# ---- Chor Minor ----------------------------------------------------------------
CM = (0.5, -0.32)
cm = k.empty("OBJ-chor-minor")
cparts = [k.box("cm-block", (0.1, 0.1, 0.08), material=brick, parent=cm),
          k.box("cm-door", (0.03, 0.003, 0.05), at=(0, -0.0515, 0), material=dark, parent=cm),
          k.box("cm-window", (0.05, 0.003, 0.012), at=(0, -0.0515, 0.058), material=window, parent=cm)]
cd = k.sphere("cm-centre-dome", 0.03, material=white, parent=cm, subdiv=3)
cd.data.transform(Matrix.Translation((0, 0, 0.08)) @ Matrix.Diagonal((1, 1, 0.7, 1)))
cparts.append(cd)
# Four towers, each decorated differently, each with a blue dome.
for i, (sx, sy) in enumerate([(-1, -1), (1, -1), (1, 1), (-1, 1)]):
    x, y = sx * 0.05, sy * 0.05
    cparts.append(k.cylinder(f"cm-tower-{i}", 0.02, 0.12, at=(x, y, 0), segs=16, material=brick, parent=cm))
    for b in range(i + 1):
        cparts.append(k.cylinder(f"cm-tower-{i}-band-{b}", 0.0205, 0.006, at=(x, y, 0.04 + b * 0.022), segs=16,
                                 material=[tile, white, window, tile][i], parent=cm))
    tdome = k.sphere(f"cm-tower-{i}-dome", 0.022, material=dome_m, parent=cm, subdiv=3)
    tdome.data.transform(Matrix.Translation((x, y, 0.12)) @ Matrix.Diagonal((1, 1, 1.15, 1)))
    cparts.append(tdome)
at(cparts, *CM, -25)


# ---- trading domes and the chapan stalls --------------------------------------
TD = (0.06, -0.36)
td = k.empty("OBJ-trading-domes")
tparts = [k.cylinder("td-octagon", 0.07, 0.06, segs=8, material=brick, parent=td, smooth=False)]
big = k.sphere("td-dome", 0.062, material=brick, parent=td, subdiv=3)
big.data.transform(Matrix.Translation((0, 0, 0.06)) @ Matrix.Diagonal((1, 1, 0.75, 1)))
tparts.append(big)
for i in range(6):
    a = 2 * math.pi * i / 6
    x, y = 0.1 * math.cos(a), 0.1 * math.sin(a)
    tparts.append(k.cylinder(f"td-small-base-{i}", 0.03, 0.04, at=(x, y, 0), segs=12, material=brick, parent=td))
    sd_ = k.sphere(f"td-small-dome-{i}", 0.03, material=brick, parent=td, subdiv=2)
    sd_.data.transform(Matrix.Translation((x, y, 0.04)) @ Matrix.Diagonal((1, 1, 0.7, 1)))
    tparts.append(sd_)
    n = sr.niche(f"td-arch-{i}", 0.022, 0.032, 0.003, window, parent=td)
    n.data.transform(Matrix.Rotation(a + math.pi / 2, 4, "Z") @ Matrix.Translation((0, -0.0705, 0.0)))
    tparts.append(n)
# Racks of chapans: striped ikat coats on rails in front of the domes.
rnd = random.Random(11)
for r_ in range(3):
    rx = -0.11 + r_ * 0.11
    ry = -0.16
    tparts.append(k.cylinder(f"td-rack-post-l-{r_}", 0.0015, 0.06, at=(rx - 0.04, ry, 0), segs=4, material=wood, parent=td))
    tparts.append(k.cylinder(f"td-rack-post-r-{r_}", 0.0015, 0.06, at=(rx + 0.04, ry, 0), segs=4, material=wood, parent=td))
    tparts.append(k.tube(f"td-rack-bar-{r_}", [(rx - 0.04, ry, 0.06), (rx + 0.04, ry, 0.06)], 0.0015, material=wood, segs=4, parent=td))
    tparts.append(k.sphere(f"td-bulb-{r_}", 0.004, at=(rx, ry, 0.066), material=lantern, parent=td, subdiv=1))
    for c_ in range(4):
        cx = rx - 0.03 + c_ * 0.02
        col = ikat[(r_ * 4 + c_) % len(ikat)]
        stripe = ikat[(r_ * 4 + c_ + 3) % len(ikat)]
        # A chapan: long body, sleeves out, a contrasting ikat stripe.
        tparts.append(k.box(f"chapan-{r_}-{c_}", (0.016, 0.003, 0.044), at=(cx, ry, 0.012), material=col, parent=td))
        tparts.append(k.box(f"chapan-sleeves-{r_}-{c_}", (0.026, 0.003, 0.007), at=(cx, ry, 0.048), material=col, parent=td))
        tparts.append(k.box(f"chapan-stripe-{r_}-{c_}", (0.005, 0.0035, 0.044), at=(cx, ry, 0.012), material=stripe, parent=td))
# Suzani on the ground and a couple of stall tables.
for i in range(2):
    tparts.append(k.box(f"td-suzani-{i}", (0.05, 0.035, 0.002), at=(-0.14 + i * 0.28, -0.08, 0), material=ikat[(i * 3) % 6], parent=td))
at(tparts, *TD, 0)


# ---- Lyabi-hauz style pool and mulberries --------------------------------------
pl = k.cylinder("DECO-pool", 0.07, 0.004, segs=32, material=pool)
pl.data.transform(Matrix.Translation((-0.06, -0.06, 0)) @ Matrix.Diagonal((1.4, 1, 1, 1)))
keep = [(KM[0], KM[1], 0.1), (KM[0] - 0.24, KM[1] + 0.02, 0.2), (KM[0] + 0.25, KM[1] + 0.02, 0.2), (AK[0] + 0.05, AK[1], 0.3),
        (-0.34, -0.44, 0.2), (CM[0], CM[1], 0.12), (TD[0], TD[1] - 0.04, 0.22), (-0.06, -0.06, 0.12)]
rnd = random.Random(23)
trees, spots = [], []
tries = 0
while len(spots) < 50 and tries < 9000:
    tries += 1
    a, d = rnd.uniform(0, 2 * math.pi), 0.92 * math.sqrt(rnd.random())
    x, y = d * math.cos(a), d * math.sin(a)
    if any((x - kx) ** 2 + (y - ky) ** 2 < kr ** 2 for kx, ky, kr in keep):
        continue
    if any((x - sx) ** 2 + (y - sy) ** 2 < 0.06 ** 2 for sx, sy in spots):
        continue
    spots.append((x, y))
for i, (x, y) in enumerate(spots):
    h = rnd.uniform(0.06, 0.09)
    trees += [k.cylinder(f"t-{i}", 0.005, h * 0.45, at=(x, y, 0), segs=5, material=trunk),
              k.sphere(f"c-{i}", h * 0.45, at=(x, y, h * 0.7), material=leaf, subdiv=2)]
    if i % 4 == 0:   # a street lamp here and there, for the night
        trees += [k.cylinder(f"lp-{i}", 0.0015, 0.05, at=(x + 0.03, y, 0), segs=4, material=dark),
                  k.sphere(f"lb-{i}", 0.005, at=(x + 0.03, y, 0.052), material=lantern, subdiv=1)]
k.join("DECO-trees", trees)


# ---- bigger landmarks: fill the base ------------------------------------------
for o, anchor, f in [(km, (KM[0], KM[1], 0), 1.15), (ark, (AK[0], AK[1], 0), 1.25), (cm, (CM[0], CM[1], 0), 1.35),
                     (td, (TD[0], TD[1], 0), 1.2), (ub, (-0.34, -0.44, 0), 1.15)]:
    k.grow(o, f, anchor)

k.export("bukhara")
