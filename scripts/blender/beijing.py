"""
beijing.py — the Beijing diorama, from Nazym's sketch: the Forbidden City in
the middle, Tiananmen Square, the Temple of Heaven, the Lama Temple, a
mountain with the Great Wall on the side, and Qianmen Street's food.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python scripts/blender/beijing.py

      Lama Temple (Wanfu Pavilion)                        Great Wall on
                        Forbidden City (moat, corner towers,   its mountain
   Temple of Heaven      Meridian Gate, Supreme Harmony)          ridge
                        Tiananmen Gate
                        Tiananmen Square (monument, flag)   Qianmen Street
                        Zhengyangmen                         (archway, food)

Reference points (looked up): the Hall of Prayer for Good Harvests is
round, three tiers of dark-blue roof on a three-level white marble base;
the Forbidden City has red walls in a wide moat, yellow-tiled roofs, corner
towers with many-ridged roofs, the Meridian Gate with two forward wings and
five gateways, the Hall of Supreme Harmony on a three-tier white marble
terrace, and its axis runs south through Tiananmen to the square; the Lama
Temple is yellow-roofed halls on an axis behind memorial archways, ending
in the tall Wanfu Pavilion.
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

paving = k.mat("paving", (0.84, 0.80, 0.72))
earth = k.mat("earth", (0.56, 0.44, 0.34))
grass = k.mat("grass", (0.54, 0.66, 0.44))
mountain = k.mat("mountain-green", (0.38, 0.56, 0.36))
red_wall = k.mat("palace-red", (0.72, 0.20, 0.16))
yellow = k.mat("roof-yellow", (0.96, 0.74, 0.22))
blue_roof = k.mat("roof-heaven-blue", (0.16, 0.26, 0.58))
marble = k.mat("marble", (0.95, 0.94, 0.90))
moat = k.mat("moat", (0.30, 0.50, 0.58))
glow = k.mat("lamp-yellow", (1.0, 0.82, 0.42))
gold = k.mat("gold", (0.96, 0.76, 0.30))
green_paint = k.mat("dancheong-green", (0.24, 0.52, 0.46))
wall_stone = k.mat("great-wall-stone", (0.70, 0.64, 0.54))
grey_tile = k.mat("tile-grey", (0.38, 0.40, 0.44))
hutong = k.mat("hutong-brick", (0.62, 0.62, 0.62))
lantern = k.mat("neon-lantern-red", (1.0, 0.22, 0.18))
dark = k.mat("dark", (0.18, 0.18, 0.22))
leaf = k.mat("tree", (0.30, 0.50, 0.32))
pine = k.mat("pine", (0.20, 0.40, 0.28))
trunk = k.mat("trunk", (0.38, 0.28, 0.22))
people = [k.mat(f"person-{i}", c) for i, c in enumerate(
    [(0.86, 0.3, 0.3), (0.3, 0.45, 0.8), (0.95, 0.8, 0.3), (0.3, 0.6, 0.4), (0.9, 0.9, 0.9)])]

k.base(paving, earth)


# ---- ground: flat city, a mountain ridge along the right for the Great Wall --
def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


RIDGE = [Vector(p) for p in [(0.36, 0.72), (0.52, 0.56), (0.64, 0.36), (0.74, 0.14), (0.78, -0.08)]]


def ridge_dist(x, y):
    p = Vector((x, y))
    best = 9.0
    for a, b in zip(RIDGE, RIDGE[1:]):
        ab = b - a
        t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
        best = min(best, (p - (a + ab * t)).length)
    return best


def height(x, y):
    r = math.hypot(x, y)
    d = ridge_dist(x, y)
    h = 0.24 * math.exp(-d * d / (2 * 0.1 ** 2)) * (0.85 + 0.15 * math.sin(14 * x + 9 * y))
    return h * (1 - smoothstep(0.88, 0.99, r))


RINGS, SEGS = 56, 176
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
for m in (paving, grass, mountain):
    land.data.materials.append(m)
for p in land.data.polygons:
    c = p.center
    p.material_index = 2 if c.z > 0.03 else (1 if math.hypot(c.x, c.y) > 0.82 else 0)
    p.use_smooth = True
k.smooth_by_angle(land, 30)


def stand(o, x, y, rot=0.0, extra=0.0):
    o.data.transform(Matrix.Translation((x, y, height(x, y) + extra)) @ Matrix.Rotation(math.radians(rot), 4, "Z"))
    return o


# ---- roofs -------------------------------------------------------------------
def chinese_roof(name, w, d, h, eave=0.01, lift=0.012, material=yellow, parent=None):
    """Hip roof with upswept corners, ridge along X. Built at z = 0."""
    bm_ = bmesh.new()
    W, D = w / 2 + eave, d / 2 + eave
    c = [bm_.verts.new((sx * W, sy * D, lift)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    m = [bm_.verts.new(((c[i].co.x + c[(i + 1) % 4].co.x) / 2, (c[i].co.y + c[(i + 1) % 4].co.y) / 2, 0.0)) for i in range(4)]
    rx = max(w / 2 - min(w, d) * 0.4, 0.002)
    r0, r1 = bm_.verts.new((-rx, 0, h)), bm_.verts.new((rx, 0, h))
    for f in ((c[0], m[0], c[1], r1, r0), (c[1], m[1], c[2], r1), (c[2], m[2], c[3], r0, r1), (c[3], m[3], c[0], r0)):
        bm_.faces.new(f)
    bm_.faces.new((c[0], m[3], c[3], m[2], c[2], m[1], c[1], m[0]))
    bmesh.ops.recalc_face_normals(bm_, faces=bm_.faces)
    o = k.obj_from_bm(name, bm_, material, parent=parent)
    ridge = k.box(name + "-ridge", (2 * rx + 0.006, 0.005, 0.005), at=(0, 0, h - 0.002), material=material, parent=parent)
    return [o, ridge]


def hall(tag, w, d, h, roof_h, parent, double=False, roof=yellow, walls=red_wall):
    """A palace hall: red columned walls, a painted bracket band, a yellow
    hip roof (two eaves if `double`). Built at the origin facing -Y."""
    parts = [k.box(f"{tag}-walls", (w, d, h), material=walls, parent=parent),
             k.box(f"{tag}-band", (w + 0.002, d + 0.002, h * 0.12), at=(0, 0, h * 0.88), material=green_paint, parent=parent),
             k.box(f"{tag}-doors", (w * 0.7, 0.002, h * 0.5), at=(0, -d / 2 - 0.001, 0), material=glow, parent=parent)]
    z = h
    if double:
        for o in chinese_roof(f"{tag}-roof-lower", w, d, roof_h * 0.45, material=roof, parent=parent):
            o.data.transform(Matrix.Translation((0, 0, z)))
            parts.append(o)
        parts.append(k.box(f"{tag}-upper", (w * 0.8, d * 0.7, roof_h * 0.35), at=(0, 0, z + roof_h * 0.3), material=walls, parent=parent))
        z += roof_h * 0.62
        w, d = w * 0.82, d * 0.74
    for o in chinese_roof(f"{tag}-roof", w, d, roof_h, material=roof, parent=parent):
        o.data.transform(Matrix.Translation((0, 0, z)))
        parts.append(o)
    return parts


def place(parts, x, y, rot=0.0, extra=0.0):
    for o in parts:
        stand(o, x, y, rot=rot, extra=extra)
    return parts


# ---- the Forbidden City --------------------------------------------------------
FC = (0.0, 0.1)
FW, FD = 0.42, 0.44
fc = k.empty("OBJ-forbidden-city")
fparts = []
# The moat round the walls.
outer = [(-FW / 2 - 0.04, -FD / 2 - 0.04), (FW / 2 + 0.04, -FD / 2 - 0.04), (FW / 2 + 0.04, FD / 2 + 0.04), (-FW / 2 - 0.04, FD / 2 + 0.04)]
inner = [(-FW / 2 - 0.012, -FD / 2 - 0.012), (FW / 2 + 0.012, -FD / 2 - 0.012), (FW / 2 + 0.012, FD / 2 + 0.012), (-FW / 2 - 0.012, FD / 2 + 0.012)]
fparts.append(k.prism("fc-moat", outer, 0.003, holes=[inner], material=moat, parent=fc))
fparts.append(k.box("fc-ground", (FW, FD, 0.003), material=k.mat("courtyard", (0.86, 0.82, 0.74)), parent=fc))
# Red walls with yellow-tiled caps.
for sx, sy, w, d in ((0, FD / 2, FW, 0.014), (0, -FD / 2, FW, 0.014), (-FW / 2, 0, 0.014, FD), (FW / 2, 0, 0.014, FD)):
    fparts.append(k.box(f"fc-wall-{sx}-{sy}", (w, d, 0.04), at=(sx, sy, 0), material=red_wall, parent=fc))
    fparts.append(k.box(f"fc-wall-cap-{sx}-{sy}", (w + 0.006, d + 0.006, 0.006), at=(sx, sy, 0.04), material=yellow, parent=fc))
# Corner towers: many-ridged roofs, here as crossed hip roofs and a crown.
for cx, cy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
    x, y = cx * FW / 2, cy * FD / 2
    fparts.append(k.box(f"fc-ct-{cx}-{cy}", (0.04, 0.04, 0.03), at=(x, y, 0.04), material=red_wall, parent=fc))
    for rot in (0, 90):
        for o in chinese_roof(f"fc-ct-roof-{cx}-{cy}-{rot}", 0.05, 0.03, 0.022, parent=fc):
            o.data.transform(Matrix.Translation((x, y, 0.07)) @ Matrix.Rotation(math.radians(rot), 4, "Z"))
            fparts.append(o)
    for o in chinese_roof(f"fc-ct-crown-{cx}-{cy}", 0.02, 0.02, 0.02, parent=fc):
        o.data.transform(Matrix.Translation((x, y, 0.09)))
        fparts.append(o)
# The Meridian Gate: a U of walls with five pavilions, the main one double-eaved.
MZ = -FD / 2
fparts.append(k.box("fc-meridian-base", (0.16, 0.03, 0.05), at=(0, MZ, 0), material=red_wall, parent=fc))
for sx in (-1, 1):
    fparts.append(k.box(f"fc-meridian-wing-{sx}", (0.03, 0.08, 0.05), at=(sx * 0.065, MZ - 0.04, 0), material=red_wall, parent=fc))
    for o in hall(f"fc-meridian-pav-{sx}", 0.03, 0.03, 0.02, 0.02, fc):
        o.data.transform(Matrix.Translation((sx * 0.065, MZ - 0.07, 0.05)))
        fparts.append(o)
for i, x in enumerate((-0.04, -0.02, 0.0, 0.02, 0.04)):
    fparts.append(k.box(f"fc-meridian-door-{i}", (0.008, 0.032, 0.022), at=(x, MZ, 0), material=dark, parent=fc))
for o in hall("fc-meridian-main", 0.1, 0.03, 0.025, 0.035, fc, double=True):
    o.data.transform(Matrix.Translation((0, MZ, 0.05)))
    fparts.append(o)
# The Hall of Supreme Harmony on its three-tier marble terrace, more halls
# behind it on the axis.
for i, (w, d) in enumerate([(0.2, 0.15), (0.17, 0.125), (0.14, 0.1)]):
    fparts.append(k.box(f"fc-terrace-{i}", (w, d, 0.012), at=(0, 0.02, 0.003 + i * 0.012), material=marble, parent=fc))
for o in hall("fc-supreme-harmony", 0.12, 0.06, 0.045, 0.06, fc, double=True):
    o.data.transform(Matrix.Translation((0, 0.02, 0.039)))
    fparts.append(o)
for i, (y, w) in enumerate([(0.12, 0.08), (0.18, 0.1)]):
    for o in hall(f"fc-rear-{i}", w, 0.04, 0.03, 0.035, fc):
        o.data.transform(Matrix.Translation((0, y, 0.003)))
        fparts.append(o)
# Side courts: rows of smaller yellow-roofed halls.
for sx in (-1, 1):
    for j in range(3):
        for o in hall(f"fc-side-{sx}-{j}", 0.05, 0.035, 0.022, 0.022, fc):
            o.data.transform(Matrix.Translation((sx * 0.15, -0.08 + j * 0.11, 0.003)))
            fparts.append(o)
place(fparts, *FC)


# ---- Tiananmen Gate and the Square -------------------------------------------
TG = (0.0, -0.3)
tg = k.empty("OBJ-tiananmen")
tparts = [k.box("tg-wall", (0.26, 0.05, 0.05), material=red_wall, parent=tg)]
for i, x in enumerate((-0.08, -0.04, 0.0, 0.04, 0.08)):
    tparts.append(k.box(f"tg-arch-{i}", (0.014 if i != 2 else 0.018, 0.052, 0.03 if i != 2 else 0.034), at=(x, 0, 0), material=dark, parent=tg))
tparts.append(k.box("tg-portrait", (0.016, 0.002, 0.02), at=(0, -0.026, 0.033), material=k.mat("portrait", (0.32, 0.34, 0.38)), parent=tg))
tparts.append(k.box("tg-terrace", (0.24, 0.045, 0.004), at=(0, 0, 0.05), material=marble, parent=tg))
for o in hall("tg-tower", 0.18, 0.04, 0.03, 0.045, tg, double=True):
    o.data.transform(Matrix.Translation((0, 0, 0.054)))
    tparts.append(o)
for i in range(5):   # the Golden Water Bridges in front
    tparts.append(k.box(f"tg-bridge-{i}", (0.014, 0.03, 0.004), at=(-0.06 + i * 0.03, -0.05, 0), material=marble, parent=tg))
place(tparts, *TG)

sq = k.empty("OBJ-tiananmen-square")
SQ = (0.0, -0.5)
sparts = [k.box("sq-square", (0.3, 0.32, 0.003), material=k.mat("square-stone", (0.80, 0.78, 0.74)), parent=sq)]
sparts.append(k.box("sq-monument-base", (0.04, 0.04, 0.01), at=(0, -0.02, 0.003), material=marble, parent=sq))
sparts.append(k.box("sq-monument", (0.016, 0.016, 0.13), at=(0, -0.02, 0.013), material=marble, parent=sq))
sparts.append(k.box("sq-monument-cap", (0.02, 0.02, 0.008), at=(0, -0.02, 0.143), material=marble, parent=sq))
sparts.append(k.cylinder("sq-flagpole", 0.0015, 0.1, at=(0, 0.12, 0.003), segs=4, material=k.mat("steel", (0.8, 0.8, 0.84)), parent=sq))
sparts.append(k.box("sq-flag", (0.028, 0.002, 0.018), at=(0.015, 0.12, 0.085), material=k.mat("flag-red", (0.9, 0.12, 0.12)), parent=sq))
for i in range(14):   # visitors
    x, y = -0.12 + (i * 37 % 24) / 100, -0.13 + (i * 53 % 26) / 100
    sparts.append(k.cylinder(f"sq-p-{i}", 0.004, 0.014, at=(x, y, 0.003), segs=6, material=people[i % 5], parent=sq))
# Zhengyangmen (Qianmen gate) closing the square to the south.
for o in [k.box("sq-zym-base", (0.12, 0.04, 0.04), at=(0, -0.2, 0), material=hutong, parent=sq)]:
    sparts.append(o)
sparts.append(k.box("sq-zym-door", (0.02, 0.042, 0.026), at=(0, -0.2, 0), material=dark, parent=sq))
for o in hall("sq-zym-tower", 0.1, 0.035, 0.03, 0.04, sq, double=True, walls=red_wall, roof=grey_tile):
    o.data.transform(Matrix.Translation((0, -0.2, 0.04)))
    sparts.append(o)
place(sparts, *SQ)


# ---- the Temple of Heaven -----------------------------------------------------
TH = (-0.52, -0.08)
th = k.empty("OBJ-temple-of-heaven")
hparts = []
for i, r in enumerate((0.12, 0.1, 0.08)):    # three levels of white marble
    hparts.append(k.cylinder(f"th-terrace-{i}", r, 0.016, at=(0, 0, i * 0.016), segs=40, material=marble, parent=th))
    hparts.append(k.torus(f"th-balustrade-{i}", r - 0.002, 0.002, at=(0, 0, i * 0.016 + 0.02), segs=48, tube_segs=3, material=marble, parent=th))
for i in range(3):   # stairs on the axis
    hparts.append(k.box(f"th-stairs-{i}", (0.02, 0.04, 0.016 * (i + 1)), at=(0, -0.1 + i * 0.02, 0), material=marble, parent=th))
Z0 = 0.048
for i, (r_wall, h_wall, r_roof, h_roof) in enumerate([(0.05, 0.04, 0.072, 0.025), (0.042, 0.03, 0.06, 0.022), (0.034, 0.026, 0.05, 0.04)]):
    hparts.append(k.cylinder(f"th-wall-{i}", r_wall, h_wall, at=(0, 0, Z0), segs=24, material=red_wall, parent=th))
    hparts.append(k.cylinder(f"th-lattice-{i}", r_wall + 0.001, h_wall * 0.5, at=(0, 0, Z0 + h_wall * 0.2), segs=24, material=glow, parent=th))
    hparts.append(k.cylinder(f"th-bracket-{i}", r_wall + 0.002, 0.006, at=(0, 0, Z0 + h_wall - 0.006), segs=24, material=green_paint, parent=th))
    hparts.append(k.cylinder(f"th-roof-{i}", r_roof, h_roof, at=(0, 0, Z0 + h_wall), r_top=r_wall * (0.75 if i < 2 else 0.0), segs=24, material=blue_roof, parent=th))
    Z0 += h_wall + h_roof * (0.6 if i < 2 else 1.0)
hparts.append(k.sphere("th-finial", 0.01, at=(0, 0, Z0 + 0.005), material=gold, parent=th, subdiv=2))
hparts.append(k.cylinder("th-finial-spike", 0.002, 0.02, at=(0, 0, Z0 + 0.012), segs=6, material=gold, parent=th))
place(hparts, *TH)


# ---- the Lama Temple: archway, halls on the axis, the Wanfu Pavilion -----------
LT = (-0.4, 0.44)
lt = k.empty("OBJ-lama-temple")
lparts = []
for i, y in enumerate((-0.08, 0.0)):
    for o in hall(f"lt-hall-{i}", 0.09, 0.045, 0.032, 0.035, lt):
        o.data.transform(Matrix.Translation((0, y, 0)))
        lparts.append(o)
# Wanfu Pavilion: three storeys of eaves, the tallest thing in the temple.
z = 0.0
for i, (w, h) in enumerate([(0.08, 0.05), (0.066, 0.04), (0.052, 0.035)]):
    lparts.append(k.box(f"lt-wanfu-{i}", (w, w * 0.8, h), at=(0, 0.1, z), material=red_wall, parent=lt))
    lparts.append(k.box(f"lt-wanfu-band-{i}", (w + 0.002, w * 0.8 + 0.002, 0.006), at=(0, 0.1, z + h - 0.006), material=green_paint, parent=lt))
    for o in chinese_roof(f"lt-wanfu-roof-{i}", w, w * 0.8, 0.022 if i < 2 else 0.04, parent=lt):
        o.data.transform(Matrix.Translation((0, 0.1, z + h)))
        lparts.append(o)
    z += h + 0.016
# The memorial archway (paifang) at the front.
for sx in (-1, 1):
    lparts.append(k.box(f"lt-paifang-post-{sx}", (0.008, 0.008, 0.07), at=(sx * 0.045, -0.16, 0), material=red_wall, parent=lt))
lparts.append(k.box("lt-paifang-beam", (0.1, 0.01, 0.014), at=(0, -0.16, 0.06), material=green_paint, parent=lt))
for o in chinese_roof("lt-paifang-roof", 0.1, 0.014, 0.014, parent=lt):
    o.data.transform(Matrix.Translation((0, -0.16, 0.074)))
    lparts.append(o)
place(lparts, *LT, rot=-25)


# ---- the Great Wall, snaking along the ridge -----------------------------------
gw = k.empty("OBJ-great-wall")
wall_pts = []
for a, b in zip(RIDGE, RIDGE[1:]):
    for i in range(10):
        t = i / 10
        p = a.lerp(b, t)
        # A little wander either side of the crest, the way the wall follows it.
        side = Vector((-(b - a).y, (b - a).x)).normalized() * 0.018 * math.sin(i * 1.3)
        wall_pts.append(p + side)
wall_pts.append(RIDGE[-1])
gparts = []
for i, (a, b) in enumerate(zip(wall_pts, wall_pts[1:])):
    mid = (a + b) / 2
    ln = (b - a).length
    ang = math.atan2(b.y - a.y, b.x - a.x)
    seg = k.box(f"gw-seg-{i}", (ln + 0.004, 0.02, 0.026), material=wall_stone)
    seg.data.transform(Matrix.Translation((mid.x, mid.y, height(mid.x, mid.y) - 0.008)) @ Matrix.Rotation(ang, 4, "Z"))
    gparts.append(seg)
    for c_ in range(3):   # crenellations
        u = -ln / 2 + (c_ + 0.5) * ln / 3
        mer = k.box(f"gw-merlon-{i}-{c_}", (0.006, 0.004, 0.008), at=(u, 0.009, 0.018), material=wall_stone)
        mer.data.transform(Matrix.Translation((mid.x, mid.y, height(mid.x, mid.y) - 0.008)) @ Matrix.Rotation(ang, 4, "Z"))
        gparts.append(mer)
    if i % 8 == 0:   # watchtowers
        tw = k.box(f"gw-tower-{i}", (0.036, 0.036, 0.05), material=wall_stone)
        stand(tw, a.x, a.y, rot=math.degrees(ang), extra=-0.01)
        gparts.append(tw)
        for o in chinese_roof(f"gw-tower-roof-{i}", 0.03, 0.03, 0.016, material=grey_tile):
            stand(o, a.x, a.y, rot=math.degrees(ang), extra=0.04)
            gparts.append(o)
g_ = k.join("gw-wall", gparts)
g_.parent = gw


# ---- Qianmen Street: a painted archway, old shopfronts, lanterns and food ------
QM = (0.4, -0.5)
qm = k.empty("OBJ-qianmen-street")
qparts = [k.box("qm-street", (0.06, 0.26, 0.003), material=k.mat("street-stone", (0.70, 0.68, 0.64)), parent=qm)]
for sx in (-1, 1):
    for i in range(5):
        y = -0.1 + i * 0.05
        for o in hall(f"qm-shop-{sx}-{i}", 0.04, 0.045, 0.04, 0.02, qm, roof=grey_tile):
            o.data.transform(Matrix.Translation((sx * 0.055, y, 0)) @ Matrix.Rotation(math.radians(-90 * sx), 4, "Z"))
            qparts.append(o)
        qparts.append(k.sphere(f"qm-lantern-{sx}-{i}", 0.006, at=(sx * 0.032, y, 0.045), material=lantern, parent=qm, subdiv=1))
for i in range(4):   # street-food carts down the middle
    y = -0.08 + i * 0.05
    qparts.append(k.box(f"qm-cart-{i}", (0.018, 0.016, 0.014), at=(0, y, 0.003), material=k.mat("wood", (0.55, 0.38, 0.24)), parent=qm))
    qparts.append(k.box(f"qm-cart-awning-{i}", (0.024, 0.02, 0.003), at=(0, y, 0.03), material=lantern, parent=qm))
    qparts.append(k.box(f"qm-cart-food-{i}", (0.014, 0.01, 0.003), at=(0, y, 0.017), material=glow, parent=qm))
# The five-bay painted archway at the street's mouth.
for x in (-0.05, -0.025, 0.025, 0.05):
    qparts.append(k.box(f"qm-pf-post-{x}", (0.006, 0.006, 0.07 if abs(x) < 0.03 else 0.055), at=(x, -0.14, 0), material=red_wall, parent=qm))
qparts.append(k.box("qm-pf-beam", (0.11, 0.008, 0.012), at=(0, -0.14, 0.05), material=green_paint, parent=qm))
qparts.append(k.box("qm-pf-sign", (0.03, 0.009, 0.012), at=(0, -0.14, 0.062), material=gold, parent=qm))
for o in chinese_roof("qm-pf-roof", 0.06, 0.012, 0.016, parent=qm):
    o.data.transform(Matrix.Translation((0, -0.14, 0.075)))
    qparts.append(o)
place(qparts, *QM, rot=20)


# ---- bigger landmarks, so the city fills the base ---------------------------
for o, c, f in [(fc, FC, 1.3), (tg, TG, 1.2), (sq, SQ, 1.1), (th, TH, 1.5), (lt, LT, 1.4), (qm, QM, 1.3)]:
    k.grow(o, f, (c[0], c[1], height(*c)))


# ---- hutong courtyard houses and trees to fill the gaps ------------------------
keep = [(FC[0], FC[1], 0.42), (TG[0], TG[1], 0.18), (SQ[0], SQ[1], 0.26), (TH[0], TH[1], 0.22), (LT[0], LT[1], 0.26), (QM[0], QM[1], 0.23)]
rnd = random.Random(8)
fill, spots = [], []
tries = 0
while len(spots) < 44 and tries < 9000:
    tries += 1
    a, d = rnd.uniform(0, 2 * math.pi), 0.9 * math.sqrt(rnd.random())
    x, y = d * math.cos(a), d * math.sin(a)
    if ridge_dist(x, y) < 0.08:
        continue
    if any((x - kx) ** 2 + (y - ky) ** 2 < kr ** 2 for kx, ky, kr in keep):
        continue
    if any((x - sx) ** 2 + (y - sy) ** 2 < 0.06 ** 2 for sx, sy in spots):
        continue
    spots.append((x, y))
for i, (x, y) in enumerate(spots):
    z = height(x, y)
    if i % 2 == 0 and z < 0.02:
        # A siheyuan: grey walls round a court, grey roofs.
        rot = rnd.choice((0, 90))
        for j, (dx, dy, w, d) in enumerate([(0, 0.016, 0.044, 0.012), (0, -0.016, 0.044, 0.012), (-0.016, 0, 0.012, 0.02), (0.016, 0, 0.012, 0.02)]):
            fill.append(stand(k.box(f"hu-{i}-{j}", (w, d, 0.016), at=(dx, dy, 0), material=hutong), x, y, rot=rot))
            for o in chinese_roof(f"hu-roof-{i}-{j}", w, d, 0.01, eave=0.004, lift=0.004, material=grey_tile):
                o.data.transform(Matrix.Translation((dx, dy, 0.016)) @ Matrix.Rotation(0 if w > d else math.pi / 2, 4, "Z"))
                fill.append(stand(o, x, y, rot=rot))
    else:
        h = rnd.uniform(0.06, 0.09)
        m = pine if z > 0.03 else leaf
        fill += [k.cylinder(f"tr-{i}", 0.005, h * 0.4, at=(x, y, z), segs=5, material=trunk),
                 k.sphere(f"tc-{i}", h * 0.42, at=(x, y, z + h * 0.7), material=m, subdiv=2)]
k.join("DECO-hutongs-and-trees", fill)
# Pines up the Great Wall's mountain.
pines = []
for i in range(30):
    t = rnd.random()
    seg = rnd.randrange(len(RIDGE) - 1)
    p = RIDGE[seg].lerp(RIDGE[seg + 1], t)
    off = Vector((rnd.uniform(-0.12, 0.12), rnd.uniform(-0.12, 0.12)))
    q = p + off
    if math.hypot(q.x, q.y) > 0.9 or ridge_dist(q.x, q.y) < 0.04:
        continue
    h = rnd.uniform(0.05, 0.07)
    pines.append(k.cylinder(f"pine-{i}", h * 0.25, h, at=(q.x, q.y, height(q.x, q.y)), r_top=0.0, segs=7, material=pine))
if pines:
    k.join("DECO-pines", pines)

k.export("beijing")
