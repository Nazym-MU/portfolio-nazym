"""
seoul.py — the Seoul diorama, from Nazym's sketch: Namsan in the middle with
N Seoul Tower on top and a path winding up it, the Han River all round.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python scripts/blender/seoul.py

                 Gyeongbokgung (hall + Gwanghwamun)
     Bukchon hanoks                         DDP + LED roses
                        Namsan + tower
     Myeongdong          (path, cable car)
        cherry blossoms                   Gangnam
   ~~~~~~~~~~~~~~~~~~~~ Han River all round ~~~~~~~~~~~~~~~~~~~~

Reference points (checked, not guessed): N Seoul Tower is a tapered white
concrete shaft with a bulbous stack of observation levels and an antenna
spire; the Namsan cable car runs up to it; DDP is a long, low, undulating
silver-aluminium form with a walkable roof; Geunjeongjeon sits on a
two-tier stone platform under a double hipped-and-gabled tiled roof.
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

river = k.mat("han-river", (0.42, 0.66, 0.86))
river_side = k.mat("river-deep", (0.30, 0.50, 0.70))
grass = k.mat("grass", (0.54, 0.66, 0.50))
hill = k.mat("namsan-green", (0.46, 0.60, 0.46))
sand = k.mat("riverbank", (0.86, 0.82, 0.70))
path_m = k.mat("path-sand", (0.92, 0.82, 0.52))
white = k.mat("white", (0.96, 0.96, 0.95))
dark = k.mat("dark", (0.18, 0.18, 0.22))
glow = k.mat("lamp-yellow", (1.0, 0.82, 0.42))
red = k.mat("red", (0.80, 0.16, 0.16))
tile = k.mat("hanok-tile", (0.30, 0.32, 0.36))
hanok_wall = k.mat("hanok-wall", (0.95, 0.93, 0.86))
timber = k.mat("timber", (0.50, 0.30, 0.20))
dancheong = k.mat("dancheong-green", (0.28, 0.58, 0.50))
pillar_red = k.mat("pillar-red", (0.70, 0.16, 0.14))
stone = k.mat("stone", (0.82, 0.80, 0.74))
silver = k.mat("ddp-silver", (0.80, 0.82, 0.86))
rose = k.mat("neon-led-rose", (1.0, 0.95, 0.9))
blossom = k.mat("cherry-blossom", (0.98, 0.72, 0.84))
leaf = k.mat("tree", (0.28, 0.48, 0.32))
trunk = k.mat("trunk", (0.36, 0.26, 0.22))
glass_m = k.mat("facade-blue", (0.32, 0.46, 0.68))
glass_d = k.mat("facade-night", (0.22, 0.30, 0.46))
paving = k.mat("paving", (0.80, 0.78, 0.72))
neon = [k.mat(n, c) for n, c in [
    ("neon-pink", (1.0, 0.42, 0.78)), ("neon-blue", (0.25, 0.62, 1.0)), ("neon-yellow", (1.0, 0.86, 0.25)),
    ("neon-red", (1.0, 0.25, 0.28)), ("neon-green", (0.35, 0.95, 0.55)), ("neon-white", (0.95, 0.96, 1.0))]]

k.base(river, river_side)


# ---- the island and Namsan ---------------------------------------------------
def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


NAM = (0.0, 0.04)
SHORE, EDGE = 0.68, 0.74
BUKCHON = (-0.42, 0.36)


def height(x, y):
    r = math.hypot(x, y)
    d = math.hypot(x - NAM[0], y - NAM[1])
    h = 0.03 + min(0.26 * math.exp(-d * d / (2 * 0.17 ** 2)), 0.22)
    h += 0.04 * math.exp(-((x - BUKCHON[0]) ** 2 + (y - BUKCHON[1]) ** 2) / (2 * 0.12 ** 2))   # Bukchon's slope
    h += 0.006 * math.sin(19 * x) * math.sin(15 * y) * smoothstep(0.08, 0.25, d) * (1 - smoothstep(0.3, 0.4, d))
    return h if r <= SHORE else h + (-0.01 - h) * smoothstep(SHORE, EDGE, r)


RINGS, SEGS = 52, 160
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
land = k.obj_from_bm("DECO-land", bm)
for m in (grass, hill, sand):
    land.data.materials.append(m)
for p in land.data.polygons:
    c = p.center
    r = math.hypot(c.x, c.y)
    p.material_index = 2 if r > SHORE - 0.03 else (1 if c.z > 0.07 else 0)
    p.use_smooth = True
k.smooth_by_angle(land, 30)


def stand(o, x, y, rot=0.0, extra=0.0):
    o.data.transform(Matrix.Translation((x, y, height(x, y) + extra)) @ Matrix.Rotation(math.radians(rot), 4, "Z"))
    return o


# ---- the path up Namsan: a sandy ribbon spiralling up the hill ---------------
path_pts = []
for i in range(90):
    t = i / 89
    # Up the front face in an S, the way the trail climbs, not round and round.
    a = math.radians(-95 + 70 * t + 28 * math.sin(3 * math.pi * t))
    rr = 0.36 * (1 - t) + 0.055 * t
    path_pts.append(Vector((NAM[0] + rr * math.cos(a), NAM[1] + rr * math.sin(a))))
bm = bmesh.new()
L, R = [], []
for i, p in enumerate(path_pts):
    tg = (path_pts[min(i + 1, 89)] - path_pts[max(i - 1, 0)]).normalized()
    n = Vector((-tg.y, tg.x)) * 0.012
    for side, lst in ((n, L), (-n, R)):
        q = p + side
        lst.append(bm.verts.new((q.x, q.y, height(q.x, q.y) + 0.003)))
for i in range(89):
    bm.faces.new((R[i], R[i + 1], L[i + 1], L[i]))
k.obj_from_bm("DECO-namsan-path", bm, path_m)


# ---- N Seoul Tower -----------------------------------------------------------
tower = k.empty("OBJ-n-seoul-tower")
TZ = height(*NAM)
k.box("tower-plaza", (0.14, 0.1, 0.02), at=(NAM[0], NAM[1], TZ - 0.005), material=paving, parent=tower)
k.box("tower-base-hall", (0.08, 0.05, 0.04), at=(NAM[0], NAM[1] - 0.02, TZ), material=white, parent=tower)
k.cylinder("tower-shaft", 0.022, 0.32, at=(NAM[0], NAM[1], TZ), r_top=0.015, segs=20, material=white, parent=tower)
# The observatory: a bulbous stack of rings, glazed between.
obs = [(0.0, 0.032), (0.012, 0.05), (0.028, 0.054), (0.044, 0.052), (0.058, 0.044), (0.07, 0.03), (0.078, 0.018)]
k.lathe("tower-observatory", [(r, z) for z, r in obs], segs=28, at=(NAM[0], NAM[1], TZ + 0.3), material=white, parent=tower)
for i, (z, r) in enumerate([(0.016, 0.051), (0.034, 0.055), (0.05, 0.05)]):
    k.cylinder(f"tower-glazing-{i}", r + 0.001, 0.008, at=(NAM[0], NAM[1], TZ + 0.3 + z), segs=28, material=glow, parent=tower)
k.cylinder("tower-mast", 0.008, 0.08, at=(NAM[0], NAM[1], TZ + 0.378), r_top=0.006, segs=10, material=white, parent=tower)
for j in range(5):
    k.cylinder(f"tower-antenna-{j}", 0.0045 - j * 0.0006, 0.022, at=(NAM[0], NAM[1], TZ + 0.458 + j * 0.022),
               segs=6, material=red if j % 2 == 0 else white, parent=tower)
# Palgakjeong, the octagonal pavilion by the tower.
pav = k.cylinder("palgakjeong-floor", 0.026, 0.008, segs=8, material=stone, parent=tower)
stand(pav, NAM[0] + 0.07, NAM[1] + 0.03)
pr = k.cylinder("palgakjeong-roof", 0.034, 0.02, segs=8, r_top=0.004, material=tile, parent=tower, smooth=False)
stand(pr, NAM[0] + 0.07, NAM[1] + 0.03, extra=0.032)
for i in range(8):
    a = 2 * math.pi * i / 8
    stand(k.cylinder(f"palgakjeong-post-{i}", 0.0025, 0.026, segs=5, material=pillar_red, parent=tower),
          NAM[0] + 0.07 + 0.02 * math.cos(a), NAM[1] + 0.03 + 0.02 * math.sin(a), extra=0.006)


# ---- Namsan cable car (cabins shuttle along the cable) -----------------------
cc = k.empty("OBJ-namsan-cable-car")
LO, UP = Vector((0.2, -0.44)), Vector((0.06, -0.1))
ang = math.degrees(math.atan2(UP.y - LO.y, UP.x - LO.x))
for name, P in (("lower", LO), ("upper", UP)):
    stand(k.box(f"ncc-{name}-station", (0.06, 0.05, 0.045), material=white, parent=cc), P.x, P.y, rot=ang)
    stand(k.box(f"ncc-{name}-roof", (0.068, 0.058, 0.008), material=red, parent=cc), P.x, P.y, rot=ang, extra=0.045)
A = Vector((LO.x, LO.y, height(*LO) + 0.04))
B = Vector((UP.x, UP.y, height(*UP) + 0.04))
SAG = 0.02
side = Vector((-(UP - LO).normalized().y, (UP - LO).normalized().x, 0)) * 0.01
for li, off in enumerate((side, -side)):
    pts = []
    for i in range(31):
        t = i / 30
        p = A.lerp(B, t) + off
        p.z -= SAG * 4 * t * (1 - t)
        pts.append(tuple(p))
    k.tube(f"ncc-cable-{li}", pts, 0.001, material=dark, segs=3, parent=cc)
for li, (off, frm, to) in enumerate(((side, A, B), (-side, B, A))):
    cab = k.empty(f"ncc-cabin-{li}", parent=cc)
    cab.location = frm + off
    delta = (to + off) - (frm + off)
    cab["shuttle"] = [delta.x, delta.y, delta.z]
    cab["period"] = 22.0
    cab["phase"] = 0.5 * li
    cab["sag"] = SAG
    for o in (k.box(f"ncc-cabin-body-{li}", (0.02, 0.016, 0.018), at=(0, 0, -0.028), material=red, parent=cab),
              k.box(f"ncc-cabin-win-{li}", (0.021, 0.017, 0.007), at=(0, 0, -0.02), material=glow, parent=cab),
              k.cylinder(f"ncc-cabin-hanger-{li}", 0.001, 0.012, at=(0, 0, -0.012), segs=3, material=dark, parent=cab)):
        o.data.transform(Matrix.Rotation(math.radians(ang), 4, "Z"))


# ---- hanok roofs: tiles with upturned corners --------------------------------
def hanok_roof(name, w, d, h, eave=0.012, lift=0.012, material=tile, parent=None):
    """A hipped-and-gabled tile roof over a w x d footprint at z = 0, its
    eave corners swept up the way Korean roofs are. Built at the origin."""
    bm_ = bmesh.new()
    W, D = w / 2 + eave, d / 2 + eave
    c = [bm_.verts.new((sx * W, sy * D, lift)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    m = [bm_.verts.new(((c[i].co.x + c[(i + 1) % 4].co.x) / 2, (c[i].co.y + c[(i + 1) % 4].co.y) / 2, 0.0)) for i in range(4)]
    rx = w / 2 - min(w, d) * 0.3
    r0 = bm_.verts.new((-rx, 0, h))
    r1 = bm_.verts.new((rx, 0, h))
    for f in ((c[0], m[0], c[1], r1, r0), (c[1], m[1], c[2], r1), (c[2], m[2], c[3], r0, r1), (c[3], m[3], c[0], r0)):
        bm_.faces.new(f)
    bm_.faces.new((c[0], m[3], c[3], m[2], c[2], m[1], c[1], m[0]))
    bmesh.ops.recalc_face_normals(bm_, faces=bm_.faces)
    o = k.obj_from_bm(name, bm_, material, parent=parent)
    ridge = k.box(name + "-ridge", (2 * rx + 0.01, 0.006, 0.006), at=(0, 0, h - 0.002), material=material, parent=parent)
    return [o, ridge]


def hanok(tag, x, y, rot, w=0.07, d=0.045, h=0.035, parent=None):
    parts = [k.box(f"{tag}-wall", (w, d, h), material=hanok_wall, parent=parent)]
    for i in range(4):
        parts.append(k.box(f"{tag}-beam-{i}", (0.004, d + 0.002, h), at=(-w / 2 + w * i / 3, 0, 0), material=timber, parent=parent))
    parts.append(k.box(f"{tag}-door", (0.014, 0.002, 0.022), at=(0, -d / 2 - 0.001, 0), material=timber, parent=parent))
    for o in hanok_roof(f"{tag}-roof", w, d, 0.03, parent=parent):
        o.data.transform(Matrix.Translation((0, 0, h)))
        parts.append(o)
    for o in parts:
        stand(o, x, y, rot=rot)


# ---- Gyeongbokgung: Geunjeongjeon on its platform, Gwanghwamun in front -------
GB = (-0.02, 0.52)
gb = k.empty("OBJ-gyeongbokgung")
gparts = []
gparts.append(k.box("gb-court", (0.32, 0.22, 0.004), material=paving, parent=gb))
for sx, sy, w, d in ((0, 0.11, 0.32, 0.008), (-0.16, 0, 0.008, 0.22), (0.16, 0, 0.008, 0.22)):
    gparts.append(k.box(f"gb-wall-{sx}-{sy}", (w, d, 0.03), at=(sx, sy, 0), material=pillar_red, parent=gb))
    gparts.append(k.box(f"gb-wall-cap-{sx}-{sy}", (w + 0.006, d + 0.006, 0.006), at=(sx, sy, 0.03), material=tile, parent=gb))
# Two-tier stone platform.
gparts.append(k.box("gb-platform-1", (0.16, 0.1, 0.014), at=(0, 0.04, 0), material=stone, parent=gb))
gparts.append(k.box("gb-platform-2", (0.13, 0.08, 0.014), at=(0, 0.045, 0.014), material=stone, parent=gb))
gparts.append(k.box("gb-stairs", (0.03, 0.03, 0.02), at=(0, -0.02, 0), material=stone, parent=gb))
# Throne hall body: red columns, green-painted bracket band, two roofs.
HZ = 0.028
gparts.append(k.box("gb-hall", (0.1, 0.055, 0.045), at=(0, 0.045, HZ), material=hanok_wall, parent=gb))
for i in range(6):
    gparts.append(k.cylinder(f"gb-col-{i}", 0.0035, 0.045, at=(-0.045 + i * 0.018, 0.016, HZ), segs=6, material=pillar_red, parent=gb))
gparts.append(k.box("gb-bracket", (0.104, 0.059, 0.008), at=(0, 0.045, HZ + 0.045), material=dancheong, parent=gb))
for o in hanok_roof("gb-roof-lower", 0.1, 0.055, 0.02, eave=0.016, lift=0.01, parent=gb):
    o.data.transform(Matrix.Translation((0, 0.045, HZ + 0.053)))
    gparts.append(o)
gparts.append(k.box("gb-upper", (0.07, 0.035, 0.02), at=(0, 0.045, HZ + 0.066), material=dancheong, parent=gb))
for o in hanok_roof("gb-roof-upper", 0.072, 0.038, 0.035, eave=0.016, lift=0.012, parent=gb):
    o.data.transform(Matrix.Translation((0, 0.045, HZ + 0.086)))
    gparts.append(o)
# Gwanghwamun: stone base with three arches, a two-tier pavilion on top.
gparts.append(k.box("gwm-base", (0.1, 0.035, 0.04), at=(0, -0.11, 0), material=stone, parent=gb))
for i, x in enumerate((-0.03, 0.0, 0.03)):
    gparts.append(k.box(f"gwm-arch-{i}", (0.016, 0.037, 0.024), at=(x, -0.11, 0), material=dark, parent=gb))
gparts.append(k.box("gwm-pavilion", (0.06, 0.026, 0.018), at=(0, -0.11, 0.04), material=pillar_red, parent=gb))
for o in hanok_roof("gwm-roof-lower", 0.06, 0.026, 0.014, eave=0.012, lift=0.008, parent=gb):
    o.data.transform(Matrix.Translation((0, -0.11, 0.058)))
    gparts.append(o)
for o in hanok_roof("gwm-roof-upper", 0.044, 0.02, 0.024, eave=0.012, lift=0.008, parent=gb):
    o.data.transform(Matrix.Translation((0, -0.11, 0.072)))
    gparts.append(o)
for o in gparts:
    stand(o, *GB)


# ---- Bukchon Hanok Village ---------------------------------------------------
bk = k.empty("OBJ-bukchon")
for i, (dx, dy, rot) in enumerate([(-0.07, -0.05, -10), (0.02, -0.06, 5), (-0.1, 0.04, 15), (-0.01, 0.03, -5),
                                   (0.08, 0.0, 10), (-0.05, 0.12, 0), (0.05, 0.1, -15)]):
    hanok(f"bk-{i}", BUKCHON[0] + dx, BUKCHON[1] + dy, rot, parent=bk)


# ---- Myeongdong: a narrow street crammed with signs and stalls ---------------
MD = (-0.5, -0.12)
md = k.empty("OBJ-myeongdong")
rnd = random.Random(5)
mparts = [k.box("md-street", (0.06, 0.26, 0.003), material=paving, parent=md)]
for side in (-1, 1):
    for i in range(5):
        h = rnd.uniform(0.07, 0.13)
        y = -0.1 + i * 0.05
        x = side * 0.06
        mparts.append(k.box(f"md-shop-{side}-{i}", (0.05, 0.045, h), at=(x, y, 0), material=[stone, hanok_wall, glass_m][i % 3], parent=md))
        # Signs facing the street: a lit fascia and a vertical blade.
        mparts.append(k.box(f"md-fascia-{side}-{i}", (0.003, 0.04, 0.02), at=(x - side * 0.0265, y, 0.025), material=neon[(i + side) % 6], parent=md))
        mparts.append(k.box(f"md-blade-{side}-{i}", (0.012, 0.003, 0.05), at=(x - side * 0.033, y + 0.015, 0.05), material=neon[(i * 2 + 1) % 6], parent=md))
for i in range(4):
    y = -0.09 + i * 0.06
    mparts.append(k.box(f"md-stall-{i}", (0.022, 0.018, 0.016), at=(0, y, 0.003), material=timber, parent=md))
    mparts.append(k.box(f"md-stall-tent-{i}", (0.028, 0.024, 0.005), at=(0, y, 0.026), material=red, parent=md))
for o in mparts:
    stand(o, *MD, rot=8)


# ---- Dongdaemun Design Plaza: the long silver wave, and the LED roses --------
DD = (0.46, 0.22)
ddp = k.empty("OBJ-ddp")
blob = k.sphere("ddp-body", 1.0, material=silver, parent=ddp, subdiv=4)
for v in blob.data.vertices:
    x, y, z = v.co
    z = max(z, 0.0)                       # flat underside
    wave = 1 + 0.18 * math.sin(3 * math.atan2(y, x))   # the undulating plan
    v.co = Vector((x * 0.17 * wave, y * 0.075 * wave, z * 0.055 * (1 + 0.25 * math.sin(4 * x))))
blob.data.update()
k.smooth_by_angle(blob, 60)
stand(blob, *DD, rot=-35)
# Its panels catch the light in long seams.
for i in range(5):
    seam = k.torus(f"ddp-seam-{i}", 1.0, 0.004, segs=48, tube_segs=3, material=k.mat("neon-ddp", (0.75, 0.88, 1.0)), parent=ddp)
    seam.data.transform(Matrix.Diagonal((0.172 * (1 - i * 0.12), 0.077 * (1 - i * 0.12), 1, 1)))
    stand(seam, *DD, rot=-35, extra=0.008 + i * 0.01)
roses = []
for i in range(36):
    x = DD[0] - 0.02 + (i % 9) * 0.017
    y = DD[1] - 0.14 + (i // 9) * 0.017
    roses.append(stand(k.cylinder(f"ddp-rose-stem-{i}", 0.001, 0.012, segs=3, material=leaf), x, y))
    roses.append(stand(k.sphere(f"ddp-rose-{i}", 0.0045, material=rose, subdiv=1), x, y, extra=0.014))
r_ = k.join("ddp-roses", roses)
r_.parent = ddp


# ---- Gangnam -----------------------------------------------------------------
GN = (0.4, -0.36)
gn = k.empty("OBJ-gangnam")
for i, (dx, dy, w, h) in enumerate([(0, 0, 0.06, 0.34), (0.07, 0.03, 0.05, 0.27), (-0.07, 0.02, 0.05, 0.24),
                                    (0.03, -0.07, 0.05, 0.2), (-0.04, -0.07, 0.045, 0.16)]):
    stand(k.box(f"gn-tower-{i}", (w, w, h), material=[glass_m, glass_d][i % 2], parent=gn), GN[0] + dx, GN[1] + dy)
    for c_ in range(4):
        for s_ in (-1, 1):
            stand(k.box(f"gn-mull-{i}-{c_}-{s_}", (0.0015, 0.0025, h - 0.01), at=(-w / 2 + (c_ + 0.5) * w / 4, s_ * (w / 2 + 0.001), 0.005),
                        material=white, parent=gn), GN[0] + dx, GN[1] + dy)
    stand(k.box(f"gn-sign-{i}", (w * 0.8, 0.003, 0.03), at=(0, -w / 2 - 0.002, 0.02), material=neon[i % 6], parent=gn), GN[0] + dx, GN[1] + dy)
    stand(k.box(f"gn-crown-{i}", (w + 0.002, w + 0.002, 0.006), material=neon[(i + 2) % 6], parent=gn), GN[0] + dx, GN[1] + dy, extra=h - 0.012)


# ---- cherry blossoms, and green on Namsan -----------------------------------
keep = [(GB[0], GB[1] - 0.02, 0.2), (BUKCHON[0], BUKCHON[1] + 0.03, 0.15), (MD[0], MD[1], 0.15), (DD[0], DD[1] - 0.04, 0.2),
        (GN[0], GN[1], 0.13), (NAM[0], NAM[1], 0.09), (LO.x, LO.y, 0.05)]
keep += [((LO + (UP - LO) * (i / 8)).x, (LO + (UP - LO) * (i / 8)).y, 0.035) for i in range(9)]
keep += [(p.x, p.y, 0.03) for p in path_pts[::3]]
rnd = random.Random(14)
spots = []
tries = 0
while len(spots) < 62 and tries < 9000:
    tries += 1
    a, d = rnd.uniform(0, 2 * math.pi), (SHORE - 0.03) * math.sqrt(rnd.random())
    x, y = d * math.cos(a), d * math.sin(a)
    if any((x - kx) ** 2 + (y - ky) ** 2 < kr ** 2 for kx, ky, kr in keep):
        continue
    if any((x - sx) ** 2 + (y - sy) ** 2 < 0.06 ** 2 for sx, sy in spots):
        continue
    spots.append((x, y))
pink, green = [], []
for i, (x, y) in enumerate(spots):
    # Blossom along the river and the lower path; pine-green up on Namsan.
    on_hill = height(x, y) > 0.09
    h = rnd.uniform(0.06, 0.09)
    z = height(x, y)
    tr = k.cylinder(f"tr-{i}", 0.005, h * 0.5, at=(x, y, z), segs=5, material=trunk)
    if on_hill:
        green += [tr, k.sphere(f"cr-{i}", h * 0.4, at=(x, y, z + h * 0.7), material=leaf, subdiv=2)]
    else:
        pink += [tr]
        for j, (dx, dy, dz, r) in enumerate([(0, 0, 0.7, 0.42), (0.02, 0.01, 0.8, 0.3), (-0.018, -0.01, 0.78, 0.3)]):
            pink.append(k.sphere(f"bl-{i}-{j}", h * r, at=(x + dx, y + dy, z + h * dz), material=blossom, subdiv=2))
k.join("DECO-cherry-blossoms", pink)
k.join("DECO-namsan-trees", green)

# ---- the island fills more of the river -------------------------------------
for o in list(bpy.data.objects):
    if o.parent is None and o.name != "DECO-base":
        k.grow(o, 1.12, (0, 0, 0))

k.export("seoul")
