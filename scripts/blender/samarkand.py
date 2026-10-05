"""
samarkand.py — the Samarkand diorama: Registan, Gur-e-Amir, Siyob Bazaar
and the Ulugh Beg Observatory on its hill.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python scripts/blender/samarkand.py

     Gur-e-Amir                       Ulugh Beg Observatory (on Kohak hill)
                    Tilya-Kori
         Ulugh Beg  [Registan]  Sher-Dor
                                         Siyob Bazaar
          poplars and mulberries round the edges

Reference points (looked up): the Registan's three madrasahs face the
square, Ulugh Beg on the west, Tilya-Kori (gilded) on the north, Sher-Dor
on the east with tigers carrying a rising sun on its portal; Gur-e-Amir is a
deeply ribbed bright-blue dome on a tall drum, two minarets at its portal;
the observatory was a three-storey arcaded cylinder with the Fakhri
sextant, a giant marble arc sunk in a trench; Siyob Bazaar has a two-tiered
roof over its pavilions and a triple arch lined with blue majolica.
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

sand = k.mat("paving-sand", (0.88, 0.80, 0.64))
earth = k.mat("earth", (0.62, 0.48, 0.34))
grass = k.mat("grass", (0.58, 0.70, 0.44))
brick = k.mat("brick-tan", (0.84, 0.70, 0.50))
tile = k.mat("tile-turquoise", (0.18, 0.62, 0.72))
tile_blue = k.mat("tile-blue", (0.14, 0.34, 0.68))
inner = k.mat("niche-blue", (0.16, 0.40, 0.66))
dome_m = k.mat("dome-azure", (0.16, 0.56, 0.82))
gold = k.mat("gold", (0.96, 0.76, 0.30))
glow = k.mat("lamp-yellow", (1.0, 0.82, 0.42))
window = k.mat("cell-shadow", (0.30, 0.34, 0.44))
marble = k.mat("marble", (0.94, 0.93, 0.90))
tiger = k.mat("tiger-orange", (0.96, 0.58, 0.18))
roof_green = k.mat("bazaar-roof", (0.30, 0.60, 0.62))
canvas = [k.mat(n, c) for n, c in [("parasol-red", (0.86, 0.26, 0.22)), ("parasol-white", (0.95, 0.94, 0.9)),
                                    ("parasol-blue", (0.24, 0.48, 0.80))]]
melon = k.mat("melon", (0.88, 0.76, 0.32))
leaf = k.mat("tree", (0.32, 0.52, 0.30))
poplar = k.mat("poplar", (0.36, 0.58, 0.32))
trunk = k.mat("trunk", (0.40, 0.30, 0.22))
dark = k.mat("dark", (0.18, 0.18, 0.22))

MAT = dict(body=brick, tile=tile, inner=inner, dome=dome_m, lantern=glow, window=window)

k.base(sand, earth)


# ---- ground: flat, with Kohak hill at the back right for the observatory ----
def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


OBS = (0.46, 0.44)


def height(x, y):
    r = math.hypot(x, y)
    h = 0.11 * math.exp(-((x - OBS[0]) ** 2 + (y - OBS[1]) ** 2) / (2 * 0.17 ** 2))
    h = min(h, 0.09)                         # a flat top for the observatory
    return h * (1 - smoothstep(0.86, 0.98, r))


RINGS, SEGS = 50, 160
bm = bmesh.new()
grid = [[bm.verts.new((0, 0, height(0, 0) + 0.001))]]
for j in range(1, RINGS + 1):
    r = 0.995 * j / RINGS
    grid.append([bm.verts.new((r * math.cos(2 * math.pi * i / SEGS), r * math.sin(2 * math.pi * i / SEGS),
                               height(r * math.cos(2 * math.pi * i / SEGS), r * math.sin(2 * math.pi * i / SEGS)) + 0.001))
                 for i in range(SEGS)])
for a, b in zip(grid, grid[1:]):
    for i in range(SEGS):
        if len(a) == 1:
            bm.faces.new((a[0], b[i], b[(i + 1) % SEGS]))
        else:
            bm.faces.new((a[i], a[(i + 1) % SEGS], b[(i + 1) % SEGS], b[i]))
land = k.obj_from_bm("DECO-land", bm)
for m in (sand, grass):
    land.data.materials.append(m)
for p in land.data.polygons:
    c = p.center
    # Grass on the hill and round the rim; paved in the city.
    p.material_index = 1 if (c.z > 0.02 or math.hypot(c.x, c.y) > 0.78) else 0
    p.use_smooth = True
k.smooth_by_angle(land, 30)


def at_ground(parts, x, y, rot):
    return sr.place_all(parts, x, y, height(x, y), rot)


# ---- Registan ----------------------------------------------------------------
RG = (0.0, -0.06)
reg = k.empty("OBJ-registan")
sq = k.box("rg-square", (0.52, 0.46, 0.004), material=marble, parent=reg)
sq.data.transform(Matrix.Translation((RG[0], RG[1], 0.001)))
W, D, H = 0.26, 0.05, 0.085
# Ulugh Beg madrasah, west side, facing east (+X).
at_ground(sr.madrasah("rg-ulughbeg", W, D, H, MAT, parent=reg, domes=2), RG[0] - 0.2, RG[1], -90)
# Tilya-Kori, north side, facing south: one big turquoise dome, gilded inside.
tk = sr.madrasah("rg-tilyakori", W * 1.1, D, H, dict(MAT, inner=gold), parent=reg, minarets=False, domes=0)
tk += sr.ribbed_dome("rg-tilyakori-big", 0.045, 0.055, dome_m, drum_h=0.05, drum_mat=brick, finial=gold, parent=reg)
tk[-2].data.transform(Matrix.Translation((-0.075, 0.03, H)))
tk[-1].data.transform(Matrix.Translation((-0.075, 0.03, H)))
tk[-3].data.transform(Matrix.Translation((-0.075, 0.03, H)))
at_ground(tk, RG[0], RG[1] + 0.2, 0)
# Sher-Dor, east side, facing west: the tigers and the sun on its portal.
sd = sr.madrasah("rg-sherdor", W, D, H, MAT, parent=reg, domes=2)
pw, ph = W * 0.36, H * 1.75
for side in (-1, 1):
    t_ = k.box(f"rg-tiger-{side}", (0.024, 0.003, 0.012), at=(side * pw * 0.33, -D * 0.1 - D * 0.58 - 0.004, ph * 0.8), material=tiger, parent=reg)
    sd.append(t_)
    sun = k.cylinder(f"rg-sun-{side}", 0.006, 0.003, segs=12, material=gold, parent=reg)
    sun.data.transform(Matrix.Translation((side * pw * 0.33 + side * 0.012, -D * 0.1 - D * 0.58 - 0.006, ph * 0.86)) @ Matrix.Rotation(math.radians(90), 4, "X"))
    sd.append(sun)
at_ground(sd, RG[0] + 0.2, RG[1], 90)


# ---- Gur-e-Amir --------------------------------------------------------------
GA = (-0.48, 0.38)
ga = k.empty("OBJ-gur-e-amir")
gparts = [k.cylinder("ga-octagon", 0.07, 0.08, segs=8, material=brick, parent=ga, smooth=False)]
gparts.append(k.cylinder("ga-octagon-band", 0.072, 0.012, at=(0, 0, 0.06), segs=8, material=tile, parent=ga, smooth=False))
gparts += sr.ribbed_dome("ga", 0.06, 0.1, dome_m, ribs=32, depth=0.14, drum_h=0.1, drum_mat=tile_blue, finial=gold, parent=ga)
for o in gparts[2:]:
    o.data.transform(Matrix.Translation((0, 0, 0.08)))
for o in sr.pishtaq("ga-portal", 0.08, 0.13, 0.03, brick, tile, inner, parent=ga):
    o.data.transform(Matrix.Translation((0, -0.12, 0)))
    gparts.append(o)
for side in (-1, 1):
    for o in sr.minaret(f"ga-minaret-{side}", 0.014, 0.011, 0.24, brick, tile, glow, dome_m, parent=ga):
        o.data.transform(Matrix.Translation((side * 0.07, -0.13, 0)))
        gparts.append(o)
at_ground(gparts, *GA, -20)


# ---- Ulugh Beg Observatory on Kohak hill ------------------------------------
ob = k.empty("OBJ-ulugh-beg-observatory")
oparts = [k.cylinder("ob-drum", 0.09, 0.09, segs=32, material=brick, parent=ob)]
for row in range(3):
    for i in range(14):
        a = 2 * math.pi * (i + 0.5 * row) / 14
        n = sr.niche(f"ob-arch-{row}-{i}", 0.018, 0.024, 0.003, window if row == 0 else inner, parent=ob)
        n.data.transform(Matrix.Rotation(a, 4, "Z") @ Matrix.Translation((0, -0.0905, 0.006 + row * 0.028)))
        oparts.append(n)
oparts.append(k.cylinder("ob-parapet", 0.092, 0.006, at=(0, 0, 0.09), segs=32, material=tile, parent=ob))
# The Fakhri sextant: a great marble arc in a trench, cutting through the drum.
arc = []
for i in range(25):
    t = i / 24
    a = math.radians(-60 + 120 * t)
    arc.append((0.13 * math.sin(a), 0.0, 0.13 * (1 - math.cos(a)) - 0.004))
oparts.append(k.tube("ob-sextant", [(x, y, 0.1 - z * 0.6) for x, y, z in arc], 0.008, material=marble, segs=6, parent=ob))
oparts.append(k.box("ob-trench", (0.27, 0.025, 0.004), at=(0, 0, 0.0), material=dark, parent=ob))
at_ground(oparts, *OBS, 30)


# ---- Siyob Bazaar ------------------------------------------------------------
SB = (0.55, -0.46)
sb = k.empty("OBJ-siyob-bazaar")
bparts = [k.box("sb-hall", (0.22, 0.14, 0.05), material=marble, parent=sb)]
# The two-tiered roof.
for i, (w, d, z, h) in enumerate([(0.24, 0.16, 0.05, 0.02), (0.15, 0.09, 0.07, 0.025)]):
    r_ = k.cylinder(f"sb-roof-{i}", 1.0, h, segs=4, r_top=0.75, material=roof_green, parent=sb, smooth=False)
    r_.data.transform(Matrix.Translation((0, 0, z)) @ Matrix.Diagonal((w * 0.71, d * 0.71, 1, 1)) @ Matrix.Rotation(math.radians(45), 4, "Z"))
    bparts.append(r_)
bparts.append(k.box("sb-clerestory", (0.15, 0.09, 0.02), at=(0, 0, 0.05), material=glow, parent=sb))
# Triple arch entrance, lined with blue majolica.
bparts.append(k.box("sb-gate", (0.12, 0.02, 0.07), at=(0, -0.08, 0), material=tile_blue, parent=sb))
for i, x in enumerate((-0.035, 0.0, 0.035)):
    n = sr.niche(f"sb-arch-{i}", 0.026, 0.05 if i == 1 else 0.042, 0.004, window, parent=sb)
    n.data.transform(Matrix.Translation((x, -0.091, 0.0)))
    bparts.append(n)
# Stalls under parasols, melons piled high.
rnd = random.Random(7)
for i in range(8):
    x, y = -0.1 + (i % 4) * 0.065, -0.13 - (i // 4) * 0.055
    bparts.append(k.box(f"sb-table-{i}", (0.03, 0.02, 0.012), at=(x, y, 0), material=k.mat("wood", (0.55, 0.38, 0.24)), parent=sb))
    bparts.append(k.cylinder(f"sb-pole-{i}", 0.0015, 0.04, at=(x, y, 0), segs=4, material=dark, parent=sb))
    bparts.append(k.cylinder(f"sb-parasol-{i}", 0.026, 0.012, at=(x, y, 0.038), r_top=0.0, segs=8, material=canvas[i % 3], parent=sb, smooth=False))
    for j in range(3):
        bparts.append(k.sphere(f"sb-melon-{i}-{j}", 0.006, at=(x - 0.008 + j * 0.008, y, 0.017), material=melon, parent=sb, subdiv=1))
at_ground(bparts, *SB, 25)


# ---- bigger landmarks, so the base is full of city rather than ground -------
k.grow(reg, 1.45, (RG[0], RG[1], 0))
k.grow(ga, 1.6, (GA[0], GA[1], height(*GA)))
k.grow(ob, 1.5, (OBS[0], OBS[1], height(*OBS)))
k.grow(sb, 1.35, (SB[0], SB[1], height(*SB)))


# ---- trees: poplars in rows and round mulberries ---------------------------
keep = [(RG[0], RG[1], 0.48), (GA[0], GA[1], 0.26), (OBS[0], OBS[1], 0.22), (SB[0] - 0.02, SB[1] - 0.04, 0.26)]
rnd = random.Random(19)
trees, spots = [], []
tries = 0
while len(spots) < 55 and tries < 9000:
    tries += 1
    a, d = rnd.uniform(0, 2 * math.pi), 0.9 * math.sqrt(rnd.random())
    x, y = d * math.cos(a), d * math.sin(a)
    if any((x - kx) ** 2 + (y - ky) ** 2 < kr ** 2 for kx, ky, kr in keep):
        continue
    if any((x - sx) ** 2 + (y - sy) ** 2 < 0.06 ** 2 for sx, sy in spots):
        continue
    spots.append((x, y))
for i, (x, y) in enumerate(spots):
    z = height(x, y)
    if i % 3 == 0:
        h = rnd.uniform(0.07, 0.1)
        trees += [k.cylinder(f"t-{i}", 0.005, h * 0.45, at=(x, y, z), segs=5, material=trunk),
                  k.sphere(f"c-{i}", h * 0.42, at=(x, y, z + h * 0.7), material=leaf, subdiv=2)]
    else:
        # Poplars: tall thin flames, the Central Asian roadside tree.
        h = rnd.uniform(0.12, 0.17)
        trees += [k.cylinder(f"pt-{i}", 0.004, h * 0.2, at=(x, y, z), segs=5, material=trunk)]
        p = k.sphere(f"pc-{i}", 1.0, material=poplar, subdiv=2)
        p.data.transform(Matrix.Translation((x, y, z + h * 0.55)) @ Matrix.Diagonal((0.018, 0.018, h * 0.5, 1)))
        trees.append(p)
k.join("DECO-trees", trees)

k.export("samarkand")
