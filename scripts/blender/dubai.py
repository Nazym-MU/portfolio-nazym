"""
dubai.py — the Dubai diorama: a round sandy island in the Gulf, the
landmarks big because there are only a few of them.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python scripts/blender/dubai.py

      Miracle Garden (A380, hearts)                 dunes
   Dubai Marina            Burj Khalifa
   (canal, Cayan,          lake + Dubai Fountain   Dubai Mall
    yachts)
                                           ~~ Burj Al Arab on its islet ~~

Reference points (looked up): Burj Khalifa has a Y-shaped tripartite plan
and rises in 27 setbacks arranged in a spiral, ending in a spire; the
Dubai Fountain sits in the lake at its foot beside the Dubai Mall; Burj Al
Arab is a dhow's sail, two wings in a V with the atrium between, a white
fabric facade, a braced exoskeleton, a cantilevered helipad, on an islet
joined to the beach by a curving bridge; the Miracle Garden's showpieces
are the Emirates A380 made of flowers and the heart-arch tunnel.
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

sea = k.mat("gulf", (0.30, 0.66, 0.78))
sea_side = k.mat("gulf-deep", (0.20, 0.48, 0.62))
sand = k.mat("sand", (0.94, 0.84, 0.64))
paving = k.mat("paving", (0.86, 0.82, 0.76))
lawn = k.mat("lawn", (0.50, 0.72, 0.40))
water = k.mat("lake", (0.26, 0.56, 0.74))
burj = k.mat("facade-burj", (0.74, 0.78, 0.84))
burj_band = k.mat("nightglow-burj-lights", (0.86, 0.92, 1.0))
spire = k.mat("steel", (0.82, 0.84, 0.88))
jet = k.mat("nightglow-fountain", (0.90, 0.96, 1.0))
sail = k.mat("sail-white", (0.97, 0.97, 0.98))
sail_glow = k.mat("nightglow-sail", (0.70, 0.80, 1.0))
helipad = k.mat("helipad", (0.28, 0.30, 0.34))
mall = k.mat("mall-stone", (0.90, 0.86, 0.78))
glass_m = k.mat("facade-marina", (0.36, 0.54, 0.70))
glass_d = k.mat("facade-marina-dark", (0.26, 0.36, 0.50))
windows = k.mat("nightglow-windows", (1.0, 0.86, 0.56))
white = k.mat("white", (0.96, 0.96, 0.96))
dark = k.mat("dark", (0.18, 0.18, 0.22))
palm_trunk = k.mat("palm-trunk", (0.62, 0.50, 0.36))
palm_leaf = k.mat("palm-leaf", (0.32, 0.58, 0.30))
flowers = [k.mat(n, c) for n, c in [("flower-pink", (0.98, 0.46, 0.66)), ("flower-yellow", (0.99, 0.84, 0.24)),
                                     ("flower-red", (0.92, 0.22, 0.24)), ("flower-violet", (0.62, 0.42, 0.88)),
                                     ("flower-orange", (0.98, 0.56, 0.20)), ("flower-white", (0.97, 0.96, 0.92))]]
emirates_red = k.mat("emirates-red", (0.84, 0.12, 0.14))

k.base(sea, sea_side)

SHORE, EDGE, GZ = 0.72, 0.78, 0.02


def height(x, y):
    r = math.hypot(x, y)
    if r <= SHORE:
        # A couple of soft dunes at the back right, flat everywhere else.
        return GZ + 0.05 * math.exp(-((x - 0.5) ** 2 + (y - 0.42) ** 2) / (2 * 0.1 ** 2)) \
               + 0.03 * math.exp(-((x - 0.3) ** 2 + (y - 0.58) ** 2) / (2 * 0.08 ** 2))
    return GZ + (-0.01 - GZ) * min(1.0, (r - SHORE) / (EDGE - SHORE))


RINGS, SEGS = 48, 160
bm = bmesh.new()
grid = [[bm.verts.new((0, 0, height(0, 0)))]]
for j in range(1, RINGS + 1):
    r = EDGE * j / RINGS
    grid.append([bm.verts.new((r * math.cos(2 * math.pi * i / SEGS), r * math.sin(2 * math.pi * i / SEGS),
                               height(r * math.cos(2 * math.pi * i / SEGS), r * math.sin(2 * math.pi * i / SEGS))))
                 for i in range(SEGS)])
for a, b in zip(grid, grid[1:]):
    for i in range(SEGS):
        if len(a) == 1:
            bm.faces.new((a[0], b[i], b[(i + 1) % SEGS]))
        else:
            bm.faces.new((a[i], a[(i + 1) % SEGS], b[(i + 1) % SEGS], b[i]))
land = k.obj_from_bm("DECO-island", bm, sand)
for p in land.data.polygons:
    p.use_smooth = True
k.smooth_by_angle(land, 30)


def stand(o, x, y, rot=0.0, extra=0.0):
    o.data.transform(Matrix.Translation((x, y, height(x, y) + extra)) @ Matrix.Rotation(math.radians(rot), 4, "Z"))
    return o


# ---- Burj Khalifa: a Y in plan, 27 setbacks spiralling up, then the spire ---
BK = (-0.04, 0.16)
bk = k.empty("OBJ-burj-khalifa")


def y_plan(lengths, w, core=0.03, rot=0.0):
    """Outline of a three-winged Y: wings 120 degrees apart, rounded tips."""
    pts = []
    for kk in range(3):
        th = rot + 2 * math.pi * kk / 3 + math.pi / 2
        d = Vector((math.cos(th), math.sin(th)))
        n = Vector((-d.y, d.x))
        notch = core * Vector((math.cos(th - math.pi / 3), math.sin(th - math.pi / 3)))
        pts.append(tuple(notch))
        pts.append(tuple(-n * w / 2 + d * core))
        L = lengths[kk]
        tip = d * L
        for i in range(9):
            a = -math.pi / 2 + math.pi * i / 8
            p = tip + (d * math.cos(a) + n * math.sin(a)) * (w / 2)
            pts.append(tuple(p))
        pts.append(tuple(n * w / 2 + d * core))
    return pts


Z = height(*BK)
H_BODY = 0.66
N_TIER = 27
lengths = [0.13, 0.13, 0.13]
w = 0.06
dz = H_BODY / N_TIER
z = Z
for j in range(N_TIER):
    # Each setback shortens one wing, turning round the building: the spiral.
    # Steeply: the tower ends a fraction of its base, the way it really does.
    lengths[j % 3] -= 0.0036 + 0.0024 * (j / N_TIER)
    t = j / N_TIER
    ww = w * (1 - 0.55 * t)
    tier = k.prism(f"bk-tier-{j}", y_plan(lengths, ww), dz * 0.94, z0=z, material=burj)
    tier.parent = bk
    tier.data.transform(Matrix.Translation((BK[0], BK[1], 0)))
    if j % 3 == 2:
        band = k.prism(f"bk-band-{j}", y_plan([l + 0.0012 for l in lengths], ww + 0.002), 0.003, z0=z + dz * 0.94 - 0.003, material=burj_band)
        band.parent = bk
        band.data.transform(Matrix.Translation((BK[0], BK[1], 0)))
    z += dz
# The core rising out of the last setbacks, then the spire.
k.cylinder("bk-core", 0.018, 0.06, at=(BK[0], BK[1], z), r_top=0.012, segs=12, material=burj, parent=bk)
k.cylinder("bk-spire", 0.011, 0.15, at=(BK[0], BK[1], z + 0.06), r_top=0.0015, segs=10, material=spire, parent=bk)
k.cylinder("bk-podium", 0.13, 0.012, at=(BK[0], BK[1], Z - 0.002), segs=36, material=paving, parent=bk)


# ---- the lake and the Dubai Fountain at its foot ----------------------------
LK = (0.02, -0.16)
lake_pts = []
for i in range(48):
    a = 2 * math.pi * i / 48
    lake_pts.append((LK[0] + 0.24 * math.cos(a) * (1 + 0.08 * math.sin(2 * a)), LK[1] + 0.1 * math.sin(a) * (1 + 0.15 * math.cos(3 * a))))
lk = k.prism("DECO-burj-lake", lake_pts, 0.004, z0=GZ, material=water)
fountain = k.empty("OBJ-dubai-fountain")
jets = []
for i in range(23):
    t = i / 22
    # The jets follow a long curve across the lake; tallest in the middle.
    x = LK[0] - 0.19 + 0.38 * t
    y = LK[1] + 0.03 * math.sin(math.pi * t * 2)
    h = 0.04 + 0.14 * math.sin(math.pi * t) ** 2 * (0.75 + 0.25 * math.cos(9 * t))
    jets.append(k.cylinder(f"jet-{i}", 0.006, h, at=(x, y, GZ + 0.004), r_top=0.0015, segs=6, material=jet))
    jets.append(k.sphere(f"jet-spray-{i}", 0.008 + 0.01 * h, at=(x, y, GZ + 0.004 + h), material=jet, subdiv=1))
jj = k.join("fountain-jets", jets)
jj.parent = fountain


# ---- Dubai Mall --------------------------------------------------------------
DM = (0.38, 0.02)
dm = k.empty("OBJ-dubai-mall")
mparts = []
# A long low block with a gently curved front facing the lake.
front = [(-0.13 + 0.26 * i / 20, -0.07 - 0.02 * math.sin(math.pi * i / 20)) for i in range(21)]
outline = front + [(0.13, 0.09), (-0.13, 0.09)]
body = k.prism("dm-body", outline, 0.07, material=mall, parent=dm)
mparts.append(body)
mparts.append(k.prism("dm-roof", outline, 0.008, z0=0.07, material=white, parent=dm))
for i in range(9):
    x = -0.11 + i * 0.0275
    mparts.append(k.box(f"dm-glass-{i}", (0.018, 0.004, 0.035), at=(x, -0.072 - 0.02 * math.sin(math.pi * (x + 0.13) / 0.26), 0.012), material=windows, parent=dm))
mparts.append(k.box("dm-sign", (0.09, 0.004, 0.012), at=(0, -0.093, 0.052), material=k.mat("neon-mall-sign", (0.95, 0.82, 0.45)), parent=dm))
for o in mparts:
    stand(o, *DM, rot=15)


# ---- Burj Al Arab on its islet, with the curving bridge ----------------------
BA = Vector((0.62, -0.58))
ba = k.empty("OBJ-burj-al-arab")
islet = k.cylinder("ba-islet", 0.075, 0.025, at=(BA.x, BA.y, -0.005), segs=32, material=sand, parent=ba)
H_S = 0.42
# The sail: in side view a tall curved blade, thick across.
side_pts = [(0.0, 0.0), (0.0, H_S)]
for i in range(1, 21):
    t = i / 20
    z_ = H_S * (1 - t)
    x_ = 0.15 * math.sin(math.pi * t * 0.92) ** 0.8 * (1 - 0.15 * t)
    side_pts.append((x_, z_))
sail_o = k.prism("ba-sail", [(-x, z) for x, z in side_pts], 0.075, material=sail, parent=ba)
sail_o.data.transform(Matrix.Rotation(math.radians(90), 4, "X") @ Matrix.Translation((0, 0, -0.0375)))
# The glowing fabric face, set just proud of the sail's curve.
face = k.prism("ba-sail-face", [(-x * 0.96, z) for x, z in side_pts[2:]] + [(0.0, 0.02)], 0.066, material=sail_glow, parent=ba)
face.data.transform(Matrix.Rotation(math.radians(90), 4, "X") @ Matrix.Translation((-0.004, 0, -0.033)))
# The mast at the back and the braced exoskeleton between the two wings.
k.cylinder("ba-mast", 0.008, H_S + 0.06, at=(0.008, 0, 0.0), r_top=0.003, segs=8, material=white, parent=ba)
for i in range(6):
    z0, z1 = H_S * i / 6, H_S * (i + 1) / 6
    for s in (-1, 1):
        k.tube(f"ba-brace-{i}-{s}", [(0.006, s * 0.04, z0), (0.006, -s * 0.04, z1)], 0.0025, material=white, segs=4, parent=ba)
# The helipad, cantilevered from near the top.
k.cylinder("ba-helipad", 0.03, 0.004, at=(-0.03, 0.04, H_S * 0.82), segs=24, material=helipad, parent=ba)
k.box("ba-helipad-arm", (0.03, 0.006, 0.004), at=(-0.012, 0.025, H_S * 0.82), material=white, parent=ba)
for o in ba.children:
    if o.name != "ba-islet":
        o.data.transform(Matrix.Translation((BA.x, BA.y, 0.015)) @ Matrix.Rotation(math.radians(-40), 4, "Z"))
# The curving bridge back to the beach.
shore_pt = Vector((0.5, -0.5)) * (SHORE / math.hypot(0.5, -0.5))
pts = []
for i in range(17):
    t = i / 16
    p = BA.lerp(shore_pt, t) + Vector((-(shore_pt - BA).y, (shore_pt - BA).x)).normalized() * 0.04 * math.sin(math.pi * t)
    pts.append((p.x, p.y, 0.022))
k.tube("ba-bridge", pts, 0.006, material=white, segs=5, parent=ba)


# ---- Dubai Marina: towers either side of a canal, Cayan twisting, yachts -----
MA = (-0.5, -0.12)
ma = k.empty("OBJ-dubai-marina")
canal = [(MA[0] - 0.04 + 0.06 * math.sin(3 * t), MA[1] - 0.28 + 0.56 * t) for t in [i / 30 for i in range(31)]]
k.ribbon("DECO-marina-canal", canal, 0.05, z=GZ + 0.002, material=water)
rnd = random.Random(12)
mparts = []
for i in range(10):
    t = (i // 2) / 4
    cx, cy = canal[int(t * 30)]
    side = -1 if i % 2 == 0 else 1
    x, y = cx + side * 0.07, cy
    h = rnd.uniform(0.26, 0.44)
    wv = rnd.uniform(0.045, 0.06)
    if i == 5:
        # Cayan Tower: each floor turned a little, 90 degrees in all.
        n = 24
        for f in range(n):
            fl = k.box(f"cayan-floor-{f}", (wv, wv, h / n * 0.96), material=glass_m, parent=ma)
            fl.data.transform(Matrix.Translation((x, y, height(x, y) + f * h / n)) @ Matrix.Rotation(math.radians(90 * f / n), 4, "Z"))
            mparts.append(fl)
            if f % 3 == 0:
                lit = k.box(f"cayan-lit-{f}", (wv + 0.002, wv + 0.002, 0.003), material=windows, parent=ma)
                lit.data.transform(Matrix.Translation((x, y, height(x, y) + f * h / n + 0.002)) @ Matrix.Rotation(math.radians(90 * f / n), 4, "Z"))
        continue
    stand(k.box(f"mt-{i}", (wv, wv, h), material=[glass_m, glass_d][i % 2], parent=ma), x, y, rot=rnd.uniform(-10, 10))
    for b in range(int(h / 0.04)):
        stand(k.box(f"mt-band-{i}-{b}", (wv + 0.002, wv + 0.002, 0.003), material=windows, parent=ma), x, y, extra=0.02 + b * 0.04)
    stand(k.box(f"mt-crown-{i}", (wv * 0.6, wv * 0.6, 0.03), material=white, parent=ma), x, y, extra=h)
# Yachts moored in the canal.
for i in range(5):
    cx, cy = canal[4 + i * 5]
    hull = k.box(f"yacht-{i}", (0.014, 0.04, 0.008), material=white, parent=ma)
    for v in hull.data.vertices:
        if v.co.y > 0.015:
            v.co.x *= 0.3
    hull.data.transform(Matrix.Translation((cx, cy, GZ + 0.004)))
    k.box(f"yacht-cabin-{i}", (0.01, 0.018, 0.006), at=(cx, cy - 0.004, GZ + 0.012), material=windows, parent=ma)


# ---- Miracle Garden: flower beds, heart arches, the flower A380 --------------
MG = (-0.36, 0.44)
mg = k.empty("OBJ-miracle-garden")
gparts = []
# Striped flower beds.
for i in range(7):
    gparts.append(k.box(f"mg-bed-{i}", (0.26, 0.022, 0.008), at=(0, -0.08 + i * 0.026, 0.0), material=flowers[i % 6], parent=mg))
# The heart tunnel: a row of heart-shaped arches.
for i in range(5):
    pts = []
    for j in range(25):
        a = 2 * math.pi * j / 24
        hx = 16 * math.sin(a) ** 3
        hz = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
        pts.append((-0.12 + hx * 0.0028, -0.1 + i * 0.022, 0.05 + hz * 0.0028))
    gparts.append(k.tube(f"mg-heart-{i}", pts, 0.004, material=flowers[0 if i % 2 == 0 else 2], segs=4, parent=mg))
# The Emirates A380, made of flowers.
PX, PY, PZ = 0.06, 0.02, 0.07
fus = k.cylinder("mg-a380-fuselage", 0.022, 0.2, segs=16, material=flowers[5], parent=mg)
fus.data.transform(Matrix.Translation((PX, PY, PZ)) @ Matrix.Rotation(math.radians(90), 4, "X") @ Matrix.Translation((0, 0, -0.1)))
gparts.append(fus)
nose = k.sphere("mg-a380-nose", 0.022, material=flowers[5], parent=mg, subdiv=2)
nose.data.transform(Matrix.Translation((PX, PY - 0.1, PZ)) @ Matrix.Diagonal((1, 1.6, 1, 1)))
gparts.append(nose)
gparts.append(k.box("mg-a380-wings", (0.22, 0.05, 0.006), at=(PX, PY + 0.01, PZ - 0.008), material=flowers[5], parent=mg))
gparts.append(k.box("mg-a380-tailplane", (0.08, 0.025, 0.005), at=(PX, PY + 0.09, PZ), material=flowers[5], parent=mg))
gparts.append(k.box("mg-a380-fin", (0.004, 0.035, 0.05), at=(PX, PY + 0.09, PZ), material=emirates_red, parent=mg))
gparts.append(k.box("mg-a380-stripe", (0.0005 + 0.045, 0.16, 0.006), at=(PX, PY, PZ + 0.004), material=emirates_red, parent=mg))
for i, x in enumerate((-0.06, -0.035, 0.035, 0.06)):
    gparts.append(k.cylinder(f"mg-a380-engine-{i}", 0.007, 0.022, at=(PX + x, PY - 0.01, PZ - 0.022), segs=10, material=flowers[1], parent=mg))
gparts.append(k.cylinder("mg-a380-stand", 0.006, PZ - 0.02, at=(PX, PY, 0), segs=8, material=lawn, parent=mg))
for o in gparts:
    stand(o, *MG, rot=-20)


# ---- big landmarks: there are only a few, so let them fill the island ------
k.grow(dm, 1.45, (DM[0], DM[1], GZ))
k.grow(fountain, 1.3, (LK[0], LK[1], GZ))
k.grow(bpy.data.objects["DECO-burj-lake"], 1.3, (LK[0], LK[1], GZ))
k.grow(mg, 1.35, (MG[0], MG[1], GZ))


# ---- date palms along the shore and round the landmarks ---------------------
def palm(tag, x, y, h):
    z = height(x, y)
    parts = [k.tube(f"{tag}-trunk", [(x, y, z), (x + 0.004, y, z + h * 0.5), (x + 0.006, y, z + h)], 0.004, material=palm_trunk, segs=6)]
    for i in range(7):
        a = 2 * math.pi * i / 7
        ca, sa = math.cos(a), math.sin(a)
        parts.append(k.tube(f"{tag}-frond-{i}", [(x + 0.006, y, z + h), (x + 0.006 + 0.018 * ca, y + 0.018 * sa, z + h + 0.008),
                                                (x + 0.006 + 0.034 * ca, y + 0.034 * sa, z + h - 0.008)], 0.0028, material=palm_leaf, segs=3))
    return parts


palms = []
for i in range(30):
    a = 2 * math.pi * i / 30 + 0.1
    if abs(math.degrees(a) % 360 - 318) < 14:   # leave the bridge's landing clear
        continue
    palms += palm(f"shore-palm-{i}", 0.67 * math.cos(a), 0.67 * math.sin(a), 0.08 + 0.02 * (i % 3))
for i, (x, y) in enumerate([(0.18, 0.3), (0.12, 0.38), (-0.22, 0.12), (0.26, -0.36), (-0.24, -0.36), (0.55, 0.22), (0.4, 0.32), (0.06, -0.4), (-0.1, -0.44), (0.18, -0.46)]):
    palms += palm(f"palm-{i}", x, y, 0.09)
k.join("DECO-palms", palms)

k.export("dubai")
