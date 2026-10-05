"""
taipei.py — the Taipei diorama. Nazym's brief: river all round, Taipei 101
in the middle, hills around (Taipei sits in a basin), NTU with its palms,
the Chiang Kai-shek Memorial Hall, Jiufen, Yehliu, a YouBike and night
market stalls, placed to look pretty.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python scripts/blender/taipei.py

        Yangmingshan hills          Elephant Mtn     Jiufen (on its hill)
   NTU palm boulevard           Taipei 101
     + YouBike dock           (flat basin)
   CKS Memorial Hall                                 Yehliu cape -> river
                       night market
   ~~~~~ river all round, a riverside bike path with a YouBike on it ~~~~~

Reference points (looked up): Taipei 101 is a podium then eight tiers of
eight floors, each flaring outward like a pagoda / bamboo stalk, blue-green
glass, ruyi ornaments, a pinnacle that glows yellow at night. CKS Memorial
Hall is white with a blue octagonal roof up stairs, the National Theater
and Concert Hall flank its square, entered through the Liberty Square gate.
Yehliu's hoodoos are top-heavy brown rocks on a cape; the Queen's Head has a
thin neck. Jiufen is steep stairs and teahouses hung with red lanterns.
NTU's Royal Palm Boulevard leads to the main library: arched windows and a
bell tower.
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

river = k.mat("river", (0.36, 0.58, 0.74))
river_side = k.mat("river-deep", (0.26, 0.44, 0.60))
grass = k.mat("grass", (0.52, 0.68, 0.44))
hill_m = k.mat("hill-green", (0.36, 0.56, 0.38))
path_m = k.mat("bike-path", (0.80, 0.50, 0.40))
shore = k.mat("riverbank", (0.82, 0.80, 0.70))
glass101 = k.mat("facade-101", (0.36, 0.62, 0.62))
glow = k.mat("lamp-yellow", (1.0, 0.82, 0.42))
gold = k.mat("gold", (0.96, 0.78, 0.30))
white = k.mat("white", (0.96, 0.96, 0.95))
cks_blue = k.mat("cks-blue", (0.16, 0.34, 0.66))
red_col = k.mat("pillar-red", (0.72, 0.16, 0.14))
yellow_tile = k.mat("tile-yellow", (0.94, 0.72, 0.24))
stone = k.mat("stone", (0.86, 0.84, 0.78))
paving = k.mat("paving", (0.80, 0.78, 0.72))
lib_brick = k.mat("ntu-brick", (0.80, 0.62, 0.48))
dark = k.mat("dark", (0.16, 0.16, 0.20))
palm_trunk = k.mat("palm-trunk", (0.62, 0.56, 0.48))
palm_leaf = k.mat("palm-leaf", (0.30, 0.58, 0.32))
leaf = k.mat("tree", (0.28, 0.50, 0.32))
trunk = k.mat("trunk", (0.36, 0.26, 0.22))
rock_lt = k.mat("yehliu-rock", (0.82, 0.66, 0.46))
rock_dk = k.mat("yehliu-rock-dark", (0.56, 0.42, 0.30))
teahouse = k.mat("teahouse-maroon", (0.48, 0.18, 0.16))
wood = k.mat("wood", (0.50, 0.34, 0.22))
lantern = k.mat("neon-lantern-red", (1.0, 0.22, 0.18))
tile_dark = k.mat("tile-grey", (0.28, 0.30, 0.34))
youbike = k.mat("youbike-yellow", (1.0, 0.82, 0.10))
neon = [k.mat(n, c) for n, c in [("neon-pink", (1.0, 0.42, 0.78)), ("neon-blue", (0.25, 0.62, 1.0)),
                                 ("neon-yellow", (1.0, 0.86, 0.25)), ("neon-green", (0.35, 0.95, 0.55)),
                                 ("neon-orange", (1.0, 0.55, 0.18))]]
people = [k.mat(f"person-{i}", c) for i, c in enumerate(
    [(0.86, 0.3, 0.3), (0.3, 0.45, 0.8), (0.95, 0.8, 0.3), (0.3, 0.6, 0.4), (0.9, 0.9, 0.9)])]

k.base(river, river_side)


# ---- the land: a flat basin in hills, a bike path round the shore ------------
def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


PATH_IN, PATH_OUT, EDGE, GZ = 0.66, 0.74, 0.78, 0.03
ELEPHANT = (0.2, 0.3)
JIUFEN = (0.44, 0.42)
HILLS = [(-0.26, 0.56, 0.22, 0.14), (0.02, 0.6, 0.15, 0.12), (ELEPHANT[0], ELEPHANT[1], 0.12, 0.08),
         (JIUFEN[0], JIUFEN[1], 0.2, 0.11), (0.58, 0.12, 0.12, 0.1), (-0.56, 0.32, 0.12, 0.1),
         (-0.58, -0.05, 0.06, 0.09), (0.6, -0.3, 0.05, 0.08)]


def height(x, y):
    r = math.hypot(x, y)
    if r >= PATH_IN:
        if r <= PATH_OUT:
            return 0.02
        return 0.02 + (-0.01 - 0.02) * smoothstep(PATH_OUT, EDGE, r)
    h = GZ + sum(hh * math.exp(-((x - hx) ** 2 + (y - hy) ** 2) / (2 * s * s)) for hx, hy, hh, s in HILLS)
    h += 0.006 * math.sin(21 * x) * math.sin(17 * y) * smoothstep(0.3, 0.5, r)
    return 0.02 + (h - 0.02) * (1 - smoothstep(0.6, PATH_IN, r))


RINGS, SEGS = 60, 176
bm = bmesh.new()
grid = [[bm.verts.new((0, 0, height(0, 0)))]]
radii = sorted(set([EDGE * j / RINGS for j in range(1, RINGS + 1)] + [PATH_IN, PATH_OUT]))
for r in radii:
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
for m in (grass, hill_m, path_m, shore):
    land.data.materials.append(m)
for p in land.data.polygons:
    c = p.center
    r = math.hypot(c.x, c.y)
    if PATH_IN + 0.01 < r < PATH_OUT - 0.01:
        p.material_index = 2
    elif r >= PATH_OUT - 0.01 or r >= PATH_IN - 0.01:
        p.material_index = 3
    else:
        p.material_index = 1 if c.z > 0.07 else 0
    p.use_smooth = True
k.smooth_by_angle(land, 30)


def stand(o, x, y, rot=0.0, extra=0.0):
    o.data.transform(Matrix.Translation((x, y, height(x, y) + extra)) @ Matrix.Rotation(math.radians(rot), 4, "Z"))
    return o


def frustum(name, r_bot, r_top, h, z0, x, y, material, parent, segs=4, rot=45):
    """A square frustum (r = half-diagonal), turned square-on by default."""
    o = k.cylinder(name, r_bot, h, at=(0, 0, 0), r_top=r_top, segs=segs, material=material, parent=parent, smooth=False)
    o.data.transform(Matrix.Translation((x, y, z0)) @ Matrix.Rotation(math.radians(rot), 4, "Z"))
    return o


# ---- Taipei 101 --------------------------------------------------------------
T1 = (0.0, 0.02)
t1 = k.empty("OBJ-taipei-101")
Z0 = height(*T1)
# Podium: a tapering pyramid base.
frustum("t101-podium", 0.085, 0.062, 0.13, Z0, *T1, glass101, t1)
z = Z0 + 0.13
# The ruyi: a round medallion on each face where the podium meets the tiers.
for i in range(4):
    ru = k.torus(f"t101-ruyi-{i}", 0.012, 0.0035, rot=(90, 0, 90 * i), segs=20, tube_segs=4, material=gold, parent=t1)
    ru.data.transform(Matrix.Translation((T1[0], T1[1], z - 0.015)) @ Matrix.Rotation(math.radians(90 * i), 4, "Z")
                      @ Matrix.Translation((0, -0.046, 0)))
# Eight tiers, each flaring outward toward its top.
TIER = 0.058
for i in range(8):
    frustum(f"t101-tier-{i}", 0.05, 0.066, TIER, z, *T1, glass101, t1)
    frustum(f"t101-tier-band-{i}", 0.067, 0.067, 0.004, z + TIER - 0.004, *T1, glow, t1)
    z += TIER
frustum("t101-crown", 0.046, 0.03, 0.04, z, *T1, glass101, t1)
z += 0.04
k.cylinder("t101-pinnacle-base", 0.012, 0.025, at=(T1[0], T1[1], z), segs=8, material=glass101, parent=t1)
k.cylinder("t101-pinnacle", 0.005, 0.09, at=(T1[0], T1[1], z + 0.025), r_top=0.0015, segs=8, material=gold, parent=t1)
k.sphere("t101-torch", 0.008, at=(T1[0], T1[1], z + 0.03), material=k.mat("lamp-pinnacle", (1.0, 0.86, 0.4)), parent=t1, subdiv=1)


# ---- Chiang Kai-shek Memorial Hall, its square, gate, theatre and concert hall
CK = (-0.32, -0.34)
CK_ROT = 35
ck = k.empty("OBJ-cks-memorial-hall")
cparts = [k.box("ck-plaza", (0.26, 0.3, 0.004), at=(0, 0, 0), material=paving, parent=ck)]
# The hall: three white terraces, the hall, a two-tier blue octagonal roof.
for i, (w, h) in enumerate([(0.11, 0.014), (0.095, 0.014), (0.08, 0.014)]):
    cparts.append(k.box(f"ck-terrace-{i}", (w, w, h), at=(0, 0.08, 0.004 + i * 0.014), material=white, parent=ck))
cparts.append(k.box("ck-stairs", (0.03, 0.04, 0.03), at=(0, 0.02, 0.004), material=stone, parent=ck))
cparts.append(k.box("ck-hall", (0.06, 0.06, 0.05), at=(0, 0.08, 0.046), material=white, parent=ck))
cparts.append(k.box("ck-door", (0.016, 0.002, 0.028), at=(0, 0.049, 0.046), material=glow, parent=ck))
roof1 = k.cylinder("ck-roof-lower", 0.058, 0.018, at=(0, 0, 0), r_top=0.036, segs=8, material=cks_blue, parent=ck, smooth=False)
roof1.data.transform(Matrix.Translation((0, 0.08, 0.096)) @ Matrix.Rotation(math.radians(22.5), 4, "Z"))
roof2 = k.cylinder("ck-roof-upper", 0.04, 0.03, at=(0, 0, 0), r_top=0.0, segs=8, material=cks_blue, parent=ck, smooth=False)
roof2.data.transform(Matrix.Translation((0, 0.08, 0.122)) @ Matrix.Rotation(math.radians(22.5), 4, "Z"))
cparts += [roof1, roof2,
           k.box("ck-roof-drum", (0.04, 0.04, 0.012), at=(0, 0.08, 0.112), material=white, parent=ck),
           k.sphere("ck-finial", 0.006, at=(0, 0.08, 0.154), material=gold, parent=ck, subdiv=1)]
# Liberty Square gate: white, five openings, blue roof.
cparts.append(k.box("ck-gate", (0.12, 0.022, 0.05), at=(0, -0.13, 0.004), material=white, parent=ck))
for i, x in enumerate((-0.044, -0.022, 0.0, 0.022, 0.044)):
    hh = 0.034 if i == 2 else 0.026
    cparts.append(k.box(f"ck-gate-arch-{i}", (0.014, 0.024, hh), at=(x, -0.13, 0.004), material=dark, parent=ck))
gr = k.cylinder("ck-gate-roof", 0.09, 0.02, segs=4, r_top=0.05, material=cks_blue, parent=ck, smooth=False)
gr.data.transform(Matrix.Translation((0, -0.13, 0.054)) @ Matrix.Diagonal((1.0, 0.22, 1, 1)) @ Matrix.Rotation(math.radians(45), 4, "Z"))
cparts.append(gr)
# The National Theater and Concert Hall: red columns, golden roofs.
for sx in (-1, 1):
    cparts.append(k.box(f"ck-hall-{sx}", (0.05, 0.08, 0.03), at=(sx * 0.1, -0.03, 0.004), material=stone, parent=ck))
    for c_ in range(5):
        cparts.append(k.cylinder(f"ck-col-{sx}-{c_}", 0.003, 0.03, at=(sx * 0.1 - sx * 0.027, -0.065 + c_ * 0.017, 0.004),
                                 segs=6, material=red_col, parent=ck))
    yr = k.cylinder(f"ck-hall-roof-{sx}", 0.07, 0.03, segs=4, r_top=0.03, material=yellow_tile, parent=ck, smooth=False)
    yr.data.transform(Matrix.Translation((sx * 0.1, -0.03, 0.034)) @ Matrix.Diagonal((0.62, 1.05, 1, 1)) @ Matrix.Rotation(math.radians(45), 4, "Z"))
    cparts.append(yr)
for o in cparts:
    stand(o, *CK, rot=CK_ROT)


# ---- NTU: the Royal Palm Boulevard and the main library ----------------------
NT = (-0.46, 0.12)
NT_ROT = -75          # the boulevard runs toward the centre
nt = k.empty("OBJ-ntu")


def palm(tag, x, y, h, parent, lean=0.0):
    """A royal palm: a tall pale trunk and a crown of arching fronds."""
    parts = [k.tube(f"{tag}-trunk", [(0, 0, 0), (lean * 0.3, 0, h * 0.5), (lean, 0, h)], 0.0045, material=palm_trunk, segs=6, parent=parent),
             k.cylinder(f"{tag}-crownshaft", 0.006, 0.014, at=(lean, 0, h - 0.004), segs=6, material=palm_leaf, parent=parent)]
    for i in range(8):
        a = 2 * math.pi * i / 8
        ca, sa = math.cos(a), math.sin(a)
        parts.append(k.tube(f"{tag}-frond-{i}", [(lean, 0, h + 0.008), (lean + 0.022 * ca, 0.022 * sa, h + 0.016), (lean + 0.042 * ca, 0.042 * sa, h - 0.006)],
                            0.0035, material=palm_leaf, segs=3, parent=parent))
    for o in parts:
        stand(o, x, y, extra=0) if False else o.data.transform(Matrix.Translation((x, y, height(x, y))))
    return parts


nparts = [k.box("ntu-boulevard", (0.05, 0.26, 0.003), at=(0, 0, 0), material=paving, parent=nt)]
lib = [k.box("ntu-library", (0.12, 0.05, 0.06), at=(0, 0.16, 0), material=lib_brick, parent=nt),
       k.box("ntu-library-roof", (0.124, 0.054, 0.006), at=(0, 0.16, 0.06), material=tile_dark, parent=nt),
       k.box("ntu-bell-tower", (0.028, 0.028, 0.1), at=(0.05, 0.17, 0), material=lib_brick, parent=nt),
       k.box("ntu-bell-roof", (0.032, 0.032, 0.012), at=(0.05, 0.17, 0.1), material=tile_dark, parent=nt)]
for i in range(5):
    lib.append(k.box(f"ntu-arch-win-{i}", (0.012, 0.002, 0.03), at=(-0.045 + i * 0.022, 0.134, 0.015), material=glow, parent=nt))
nparts += lib
for o in nparts:
    stand(o, *NT, rot=NT_ROT)
rot_m = Matrix.Rotation(math.radians(NT_ROT), 2)
for i in range(6):
    for sx in (-1, 1):
        local = Vector((sx * 0.04, -0.12 + i * 0.045))
        p = Vector(NT) + rot_m @ local
        palm(f"ntu-palm-{i}-{sx}", p.x, p.y, 0.12 + 0.01 * (i % 2), nt)
# A YouBike dock by the library, yellow bikes parked in a row.


def bike(tag, parent, colour=youbike):
    """A YouBike at the origin, facing +Y: two wheels, frame, basket."""
    p = [k.torus(f"{tag}-wheel-f", 0.008, 0.0016, rot=(0, 90, 0), at=(0, 0.012, 0.008), segs=14, tube_segs=4, material=dark, parent=parent),
         k.torus(f"{tag}-wheel-b", 0.008, 0.0016, rot=(0, 90, 0), at=(0, -0.012, 0.008), segs=14, tube_segs=4, material=dark, parent=parent),
         k.tube(f"{tag}-frame", [(0, -0.012, 0.008), (0, -0.003, 0.02), (0, 0.009, 0.02), (0, 0.012, 0.008)], 0.0018, material=colour, segs=4, parent=parent),
         k.tube(f"{tag}-down", [(0, -0.003, 0.02), (0, 0.004, 0.008)], 0.0018, material=colour, segs=4, parent=parent),
         k.box(f"{tag}-basket", (0.01, 0.008, 0.006), at=(0, 0.016, 0.018), material=colour, parent=parent),
         k.box(f"{tag}-seat", (0.004, 0.008, 0.002), at=(0, -0.004, 0.024), material=dark, parent=parent),
         k.tube(f"{tag}-bars", [(-0.007, 0.011, 0.027), (0.007, 0.011, 0.027)], 0.0013, material=dark, segs=4, parent=parent)]
    return p


dock = k.empty("OBJ-youbike-dock")
DK = Vector(NT) + rot_m @ Vector((0.085, 0.06))
for i in range(5):
    for o in bike(f"dock-bike-{i}", dock):
        o.data.transform(Matrix.Translation((DK.x, DK.y, height(DK.x, DK.y))) @ Matrix.Rotation(math.radians(NT_ROT), 4, "Z")
                         @ Matrix.Translation((i * 0.016 - 0.032, 0, 0)) @ Matrix.Rotation(math.radians(90), 4, "Z"))
stand(k.box("dock-rail", (0.09, 0.006, 0.014), material=k.mat("youbike-dock-grey", (0.6, 0.62, 0.66)), parent=dock), DK.x, DK.y, rot=NT_ROT + 90)


# ---- the YouBike riding the riverside path -----------------------------------
yb = k.empty("OBJ-youbike")
yb["orbit"] = 32.0
for o in bike("ride", yb):
    o.data.transform(Matrix.Translation((0.7, 0, 0.02)))


# ---- Jiufen: teahouses stacked up its hill, red lanterns, steep stairs ------
jf = k.empty("OBJ-jiufen")
JF_FACE = math.degrees(math.atan2(-JIUFEN[1], -JIUFEN[0])) + 90    # facing down toward the basin
dir_down = Vector((-JIUFEN[0], -JIUFEN[1])).normalized()
side = Vector((-dir_down.y, dir_down.x))
for i, (along, across) in enumerate([(0.12, -0.04), (0.12, 0.05), (0.07, -0.05), (0.06, 0.045), (0.02, -0.035), (0.0, 0.05), (-0.04, 0.0)]):
    p = Vector(JIUFEN) + dir_down * along + side * across
    w, h = 0.05, 0.035 + 0.01 * (i % 2)
    parts = [k.box(f"jf-house-{i}", (w, 0.04, h), material=teahouse, parent=jf),
             k.box(f"jf-balcony-{i}", (w + 0.004, 0.01, 0.004), at=(0, -0.025, h * 0.5), material=wood, parent=jf),
             k.box(f"jf-win-{i}", (w * 0.7, 0.002, 0.012), at=(0, -0.0205, h * 0.6), material=glow, parent=jf)]
    roof = k.cylinder(f"jf-roof-{i}", 0.04, 0.018, segs=4, r_top=0.012, material=tile_dark, parent=jf, smooth=False)
    roof.data.transform(Matrix.Translation((0, 0, h)) @ Matrix.Diagonal((1.0, 0.75, 1, 1)) @ Matrix.Rotation(math.radians(45), 4, "Z"))
    parts.append(roof)
    for j in range(4):
        parts.append(k.sphere(f"jf-lantern-{i}-{j}", 0.0045, at=(-w / 2 + 0.006 + j * (w - 0.012) / 3, -0.026, h - 0.004),
                              material=lantern, parent=jf, subdiv=1))
    for o in parts:
        stand(o, p.x, p.y, rot=JF_FACE)
# The stair street climbing between them, lantern posts beside it.
stairs = []
for j in range(14):
    t = j / 13
    p = Vector(JIUFEN) + dir_down * (0.16 - 0.22 * t)
    st = k.box(f"jf-step-{j}", (0.018, 0.016, 0.006), material=stone)
    stand(st, p.x, p.y, rot=JF_FACE)
    stairs.append(st)
    if j % 3 == 0:
        stairs.append(stand(k.cylinder(f"jf-post-{j}", 0.0012, 0.03, segs=4, material=dark), p.x + side.x * 0.014, p.y + side.y * 0.014))
        stairs.append(stand(k.sphere(f"jf-post-lantern-{j}", 0.005, material=lantern, subdiv=1), p.x + side.x * 0.014, p.y + side.y * 0.014, extra=0.032))
s_ = k.join("jf-stairs", stairs)
s_.parent = jf


# ---- Yehliu: a rocky cape into the river, hoodoos and the Queen's Head -------
YA = math.radians(-28)
YR0 = 0.74
yl = k.empty("OBJ-yehliu")
cape = [(math.cos(YA + da) * rr, math.sin(YA + da) * rr) for rr, da in
        [(0.72, -0.1), (0.78, -0.08), (0.84, -0.05), (0.88, 0.0), (0.84, 0.05), (0.78, 0.08), (0.72, 0.1)]]
pl = k.prism("yl-platform", cape, 0.014, z0=0.0, material=rock_lt)
pl.parent = yl
rnd = random.Random(9)
for i in range(9):
    rr = rnd.uniform(0.76, 0.85)
    da = rnd.uniform(-0.06, 0.06)
    x, y = math.cos(YA + da) * rr, math.sin(YA + da) * rr
    neck_h = rnd.uniform(0.014, 0.03)
    cap_r = rnd.uniform(0.012, 0.02)
    if i == 0:
        # The Queen's Head: a slender neck and an elongated, tilted head.
        k.cylinder("yl-queen-neck", 0.004, 0.03, at=(x, y, 0.014), r_top=0.0055, segs=10, material=rock_dk, parent=yl)
        head = k.sphere("yl-queen-head", 0.016, material=rock_lt, parent=yl, subdiv=2)
        head.data.transform(Matrix.Translation((x + 0.006, y, 0.054)) @ Matrix.Rotation(math.radians(20), 4, "Y")
                            @ Matrix.Diagonal((1.5, 0.9, 0.85, 1)))
        continue
    k.cylinder(f"yl-neck-{i}", cap_r * 0.45, neck_h, at=(x, y, 0.014), r_top=cap_r * 0.35, segs=10, material=rock_dk, parent=yl)
    cap = k.sphere(f"yl-cap-{i}", cap_r, material=rock_lt, parent=yl, subdiv=2)
    cap.data.transform(Matrix.Translation((x, y, 0.014 + neck_h + cap_r * 0.5)) @ Matrix.Diagonal((1.0, 1.0, 0.7, 1)))


# ---- the night market: a lane of stalls under a lit gate --------------------
NM = (0.1, -0.44)
NM_ROT = 10
nm = k.empty("OBJ-night-market")
mparts = [k.box("nm-lane", (0.06, 0.26, 0.003), material=paving, parent=nm)]
for side_ in (-1, 1):
    for i in range(6):
        y = -0.11 + i * 0.044
        x = side_ * 0.045
        mparts.append(k.box(f"nm-stall-{side_}-{i}", (0.028, 0.034, 0.02), at=(x, y, 0.003), material=wood, parent=nm))
        mparts.append(k.box(f"nm-awning-{side_}-{i}", (0.034, 0.04, 0.004), at=(x, y, 0.03), material=neon[(i + side_) % 5], parent=nm))
        mparts.append(k.box(f"nm-sign-{side_}-{i}", (0.003, 0.03, 0.01), at=(x - side_ * 0.016, y, 0.036), material=neon[(i * 2) % 5], parent=nm))
        mparts.append(k.box(f"nm-food-{side_}-{i}", (0.024, 0.008, 0.004), at=(x - side_ * 0.008, y, 0.023), material=glow, parent=nm))
# The gate at the lane's mouth: a lit arch with a red-lantern string.
mparts.append(k.box("nm-gate-left", (0.008, 0.008, 0.07), at=(-0.04, -0.14, 0.003), material=red_col, parent=nm))
mparts.append(k.box("nm-gate-right", (0.008, 0.008, 0.07), at=(0.04, -0.14, 0.003), material=red_col, parent=nm))
mparts.append(k.box("nm-gate-sign", (0.09, 0.008, 0.018), at=(0, -0.14, 0.072), material=neon[2], parent=nm))
gr2 = k.cylinder("nm-gate-roof", 0.07, 0.016, segs=4, r_top=0.03, material=yellow_tile, parent=nm, smooth=False)
gr2.data.transform(Matrix.Translation((0, -0.14, 0.09)) @ Matrix.Diagonal((1.0, 0.25, 1, 1)) @ Matrix.Rotation(math.radians(45), 4, "Z"))
mparts.append(gr2)
for i in range(9):
    y = -0.12 + i * 0.03
    mparts.append(k.sphere(f"nm-lantern-{i}", 0.0045, at=(0, y, 0.065), material=lantern, parent=nm, subdiv=1))
crowd = []
rp = random.Random(4)
for i in range(16):
    y = rp.uniform(-0.12, 0.12)
    x = rp.uniform(-0.018, 0.018)
    crowd.append(k.cylinder(f"nm-p-{i}", 0.0045, 0.016, at=(x, y, 0.003), segs=6, material=people[i % 5]))
    crowd.append(k.sphere(f"nm-ph-{i}", 0.004, at=(x, y, 0.023), material=dark, subdiv=1))
c_ = k.join("nm-crowd", crowd)
c_.parent = nm
mparts.append(c_)
for o in mparts:
    stand(o, *NM, rot=NM_ROT)


# ---- trees on the hills; low city blocks in the basin -----------------------
keep = [(T1[0], T1[1], 0.11), (CK[0], CK[1], 0.2), (NT[0], NT[1], 0.18), (JIUFEN[0], JIUFEN[1], 0.15), (NM[0], NM[1], 0.16)]
rnd = random.Random(21)
trees, blocks = [], []
spots = []
tries = 0
while len(spots) < 80 and tries < 9000:
    tries += 1
    a, d = rnd.uniform(0, 2 * math.pi), (PATH_IN - 0.03) * math.sqrt(rnd.random())
    x, y = d * math.cos(a), d * math.sin(a)
    if any((x - kx) ** 2 + (y - ky) ** 2 < kr ** 2 for kx, ky, kr in keep):
        continue
    if any((x - sx) ** 2 + (y - sy) ** 2 < 0.055 ** 2 for sx, sy in spots):
        continue
    spots.append((x, y))
for i, (x, y) in enumerate(spots):
    z = height(x, y)
    if z > 0.06 or math.hypot(x - T1[0], y - T1[1]) > 0.3:
        # Hills, and the open basin away from 101: trees, so the landmarks
        # are not lost among boxes.
        h = rnd.uniform(0.05, 0.08)
        trees += [k.cylinder(f"t-{i}", 0.005, h * 0.45, at=(x, y, z), segs=5, material=trunk),
                  k.sphere(f"c-{i}", h * 0.42, at=(x, y, z + h * 0.68), material=leaf, subdiv=2)]
    else:
        # Xinyi, round 101: a tight cluster of mid-rise blocks.
        w, h = rnd.uniform(0.035, 0.05), rnd.uniform(0.04, 0.1)
        blocks.append(stand(k.box(f"b-{i}", (w, w, h), material=[stone, white, lib_brick][i % 3]), x, y, rot=rnd.uniform(0, 90)))
        for b in range(int(h / 0.025)):
            blocks.append(stand(k.box(f"b-band-{i}-{b}", (w + 0.002, w + 0.002, 0.003), material=glow), x, y, extra=0.012 + b * 0.025))
k.join("DECO-hill-trees", trees)
k.join("DECO-city-blocks", blocks)

# ---- the island fills more of the river -------------------------------------
for o in list(bpy.data.objects):
    if o.parent is None and o.name != "DECO-base":
        k.grow(o, 1.08, (0, 0, 0))

k.export("taipei")
