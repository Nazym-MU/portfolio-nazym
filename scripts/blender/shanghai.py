"""
shanghai.py — the Shanghai diorama, at night, from Nazym's sketch.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python scripts/blender/shanghai.py

             Jin Mao   Shanghai Tower   SWFC          Disney castle
      the Bund           Oriental Pearl              Yu Garden
   (European row,        (Pudong lights)
    Custom House                                    Zootopia
    clock tower)
   ~~~~~~~~~~~~ the Huangpu all round, a cruise boat circling ~~~~~~~~~~~~

Reference points (looked up, not guessed): Shanghai Tower twists 120° as it
tapers; the SWFC is the "bottle opener" with a trapezoidal hole at the top;
Jin Mao is a stepped pagoda-like tower; the Oriental Pearl threads pink
spheres on columns; on the Bund the Custom House has a Big Ben-style clock
tower, HSBC a dome, the Peace Hotel a green pyramid roof, all floodlit at
night; Yu Garden has the Huxinting teahouse in a pond reached by the
zigzag Nine-turn Bridge, rockeries and grey "dragon walls"; the Enchanted
Storybook Castle is the tallest Disney castle with a peony on its top
spire; Zootopia land is Savanna Central with a station and tall towers,
one striped red like a tiger.
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

river = k.mat("huangpu-night", (0.16, 0.22, 0.38))
river_side = k.mat("river-deep", (0.12, 0.16, 0.28))
ground_m = k.mat("night-ground", (0.30, 0.30, 0.36))
promenade = k.mat("promenade", (0.50, 0.48, 0.50))
park = k.mat("park-green", (0.26, 0.40, 0.30))
glow = k.mat("lamp-yellow", (1.0, 0.82, 0.42))
bund_gold = k.mat("neon-bund-gold", (1.0, 0.70, 0.32))
bund_stone = k.mat("bund-stone", (0.80, 0.66, 0.46))
peace_green = k.mat("neon-peace-green", (0.30, 0.78, 0.55))
sht_glass = k.mat("facade-shanghai-tower", (0.30, 0.46, 0.62))
sht_light = k.mat("neon-cyan", (0.45, 0.92, 1.0))
swfc_glass = k.mat("facade-swfc", (0.34, 0.40, 0.56))
jinmao = k.mat("neon-jinmao-gold", (1.0, 0.78, 0.42))
pearl_pink = k.mat("neon-pearl-pink", (1.0, 0.36, 0.66))
pearl_col = k.mat("pearl-column", (0.70, 0.66, 0.74))
tower_dark = k.mat("facade-night", (0.22, 0.26, 0.38))
white = k.mat("white", (0.95, 0.95, 0.95))
dark = k.mat("dark", (0.14, 0.14, 0.18))
tile = k.mat("tile-grey", (0.32, 0.33, 0.38))
red_lantern = k.mat("neon-lantern-red", (1.0, 0.22, 0.18))
wood_red = k.mat("pillar-red", (0.66, 0.16, 0.14))
rock = k.mat("rock", (0.56, 0.52, 0.46))
pond = k.mat("pond-night", (0.20, 0.30, 0.44))
castle_wall = k.mat("castle-cream", (0.95, 0.92, 0.86))
castle_roof = k.mat("neon-castle-blue", (0.36, 0.56, 1.0))
castle_gold = k.mat("gold", (0.95, 0.75, 0.30))
zoo = [k.mat(n, c) for n, c in [("neon-zoo-orange", (1.0, 0.56, 0.2)), ("neon-zoo-teal", (0.25, 0.9, 0.8)),
                                 ("neon-zoo-pink", (1.0, 0.45, 0.75)), ("neon-zoo-yellow", (1.0, 0.88, 0.3))]]
tiger = k.mat("neon-tiger-red", (1.0, 0.24, 0.2))
zoo_wall = k.mat("zoo-sand", (0.90, 0.80, 0.62))
neon = [k.mat(n, c) for n, c in [("neon-blue", (0.25, 0.62, 1.0)), ("neon-pink", (1.0, 0.42, 0.78)),
                                 ("neon-white", (0.95, 0.96, 1.0)), ("neon-violet", (0.66, 0.45, 1.0))]]
leaf = k.mat("tree-night", (0.20, 0.34, 0.26))
trunk = k.mat("trunk", (0.30, 0.22, 0.18))

k.base(river, river_side)

SHORE, EDGE, GZ = 0.72, 0.76, 0.03


def ground(x, y):
    r = math.hypot(x, y)
    return GZ if r <= SHORE else GZ + (-0.01 - GZ) * min(1, (r - SHORE) / (EDGE - SHORE))


# The island: flat, dark, a lit promenade round its rim.
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=128, radius1=EDGE, radius2=SHORE, depth=GZ + 0.01)
bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, (GZ - 0.01) / 2))
isl = k.obj_from_bm("DECO-island", bm)
isl.data.materials.append(ground_m)
k.ribbon("DECO-promenade", [(0.68 * math.cos(math.radians(a)), 0.68 * math.sin(math.radians(a))) for a in range(0, 362, 4)],
         0.05, z=GZ + 0.001, material=promenade, clip=0.9)
lamps = []
for i in range(48):
    a = 2 * math.pi * i / 48
    lamps.append(k.sphere(f"prom-lamp-{i}", 0.005, at=(0.705 * math.cos(a), 0.705 * math.sin(a), GZ + 0.012), material=glow, subdiv=1))
k.join("DECO-promenade-lamps", lamps)


def stand(o, x, y, rot=0.0, extra=0.0):
    o.data.transform(Matrix.Translation((x, y, ground(x, y) + extra)) @ Matrix.Rotation(math.radians(rot), 4, "Z"))
    return o


# ---- Shanghai Tower: a rounded triangle that twists 120° as it tapers -------
ST = (-0.12, 0.24)
sht = k.empty("OBJ-shanghai-tower")
H, R0, N_Z, N_A = 0.8, 0.07, 40, 48
bm = bmesh.new()
rings = []
for j in range(N_Z + 1):
    t = j / N_Z
    rot = math.radians(120) * t
    R = R0 * (1 - 0.5 * t)
    ring = []
    for i in range(N_A):
        th = 2 * math.pi * i / N_A
        r = R * (1 + 0.13 * math.cos(3 * th))
        # The notch: one lobe pinched in, so the twist reads as a groove.
        r *= 1 - 0.18 * math.exp(-((math.atan2(math.sin(th), math.cos(th))) ** 2) / 0.02)
        ring.append(bm.verts.new((ST[0] + r * math.cos(th + rot), ST[1] + r * math.sin(th + rot), GZ + H * t)))
    rings.append(ring)
for a, b in zip(rings, rings[1:]):
    for i in range(N_A):
        bm.faces.new((a[i], a[(i + 1) % N_A], b[(i + 1) % N_A], b[i]))
bm.faces.new(list(reversed(rings[0])))
bm.faces.new(rings[-1])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
body = k.obj_from_bm("sht-body", bm, sht_glass, parent=sht)
k.smooth_by_angle(body, 50)
# Lit bands where its nine stacked zones meet, and the glowing notch.
for z in range(1, 9):
    t = z / 9
    rot = math.radians(120) * t
    R = R0 * (1 - 0.5 * t) * 1.02
    pts = [(ST[0] + R * (1 + 0.13 * math.cos(3 * th)) * math.cos(th + rot),
            ST[1] + R * (1 + 0.13 * math.cos(3 * th)) * math.sin(th + rot), GZ + H * t)
           for th in [2 * math.pi * i / 48 for i in range(49)]]
    k.tube(f"sht-band-{z}", pts, 0.0018, material=sht_light, segs=3, parent=sht)
notch = [(ST[0] + R0 * (1 - 0.5 * t) * 0.92 * math.cos(math.radians(120) * t),
          ST[1] + R0 * (1 - 0.5 * t) * 0.92 * math.sin(math.radians(120) * t), GZ + H * t) for t in [i / 30 for i in range(31)]]
k.tube("sht-notch", notch, 0.0025, material=sht_light, segs=4, parent=sht)


# ---- SWFC: the bottle opener -------------------------------------------------
SW = (0.18, 0.24)
swfc = k.empty("OBJ-swfc")
HW = 0.68
sb = k.box("swfc-body", (0.1, 0.1, HW), at=(0, 0, 0), material=swfc_glass, parent=swfc)
for v in sb.data.vertices:
    # Square at the base, a thin blade at the top: two faces slope inward.
    t = v.co.z / HW
    v.co.y *= 1 - 0.8 * t
sb.data.update()
cut = k.box("swfc-cutter", (0.12, 0.06, 0.065), at=(0, 0, HW - 0.1), material=dark)
cut.data.transform(Matrix.Diagonal((1, 1, 1, 1)))
for v in cut.data.vertices:       # trapezoid: wider at the top
    if v.co.z > HW - 0.07:
        pass
    v.co.x *= 0.62 if v.co.z < HW - 0.06 else 0.75
mod = sb.modifiers.new("hole", "BOOLEAN")
mod.operation = "DIFFERENCE"
mod.object = cut
bpy.context.view_layer.objects.active = sb
bpy.ops.object.modifier_apply(modifier="hole")
bpy.data.objects.remove(cut)
stand(sb, *SW, rot=-20)
for b in range(12):
    t = (b + 1) / 13
    band = k.box(f"swfc-band-{b}", (0.102, 0.102 * (1 - 0.8 * t), 0.004), at=(0, 0, HW * t), material=neon[2], parent=swfc)
    stand(band, *SW, rot=-20)
rim = k.box("swfc-rim", (0.102, 0.024, 0.006), at=(0, 0, HW - 0.003), material=neon[0], parent=swfc)
stand(rim, *SW, rot=-20)


# ---- Jin Mao: a stepped, pagoda-like tower ----------------------------------
JM = (0.03, 0.42)
jm = k.empty("OBJ-jin-mao")
z = 0.0
w = 0.075
for step in range(12):
    h = 0.075 - step * 0.004
    seg = k.cylinder(f"jm-tier-{step}", w, h, at=(JM[0], JM[1], GZ + z), r_top=w * 0.93, segs=8, material=tower_dark, parent=jm, smooth=False)
    k.cylinder(f"jm-ledge-{step}", w * 0.97, 0.005, at=(JM[0], JM[1], GZ + z + h - 0.003), segs=8, material=jinmao, parent=jm, smooth=False)
    z += h
    w *= 0.9
k.cylinder("jm-crown", w * 1.1, 0.04, at=(JM[0], JM[1], GZ + z), r_top=w * 0.4, segs=8, material=jinmao, parent=jm, smooth=False)
k.cylinder("jm-spire", 0.004, 0.07, at=(JM[0], JM[1], GZ + z + 0.04), segs=6, material=jinmao, parent=jm)


# ---- Oriental Pearl Tower ---------------------------------------------------
OP = (0.0, 0.0)
op = k.empty("OBJ-oriental-pearl")
for i in range(3):
    a = 2 * math.pi * i / 3 + 0.4
    # Three splayed legs at the foot, then three straight columns.
    k.tube(f"op-leg-{i}", [(OP[0] + 0.085 * math.cos(a), OP[1] + 0.085 * math.sin(a), GZ), (OP[0] + 0.025 * math.cos(a), OP[1] + 0.025 * math.sin(a), GZ + 0.12)],
           0.007, material=pearl_col, segs=6, parent=op)
    k.cylinder(f"op-col-{i}", 0.011, 0.3, at=(OP[0] + 0.022 * math.cos(a), OP[1] + 0.022 * math.sin(a), GZ + 0.08), segs=10, material=pearl_col, parent=op)
k.sphere("op-sphere-low", 0.06, at=(OP[0], OP[1], GZ + 0.14), material=pearl_pink, parent=op, subdiv=3)
k.sphere("op-sphere-high", 0.045, at=(OP[0], OP[1], GZ + 0.4), material=pearl_pink, parent=op, subdiv=3)
k.cylinder("op-neck", 0.012, 0.1, at=(OP[0], OP[1], GZ + 0.44), segs=10, material=pearl_col, parent=op)
k.sphere("op-sphere-top", 0.018, at=(OP[0], OP[1], GZ + 0.55), material=pearl_pink, parent=op, subdiv=2)
k.cylinder("op-spire", 0.005, 0.11, at=(OP[0], OP[1], GZ + 0.565), r_top=0.0015, segs=6, material=pearl_col, parent=op)
for i in range(5):
    k.sphere(f"op-bead-{i}", 0.01, at=(OP[0] + 0.03 * math.cos(i * 1.3), OP[1] + 0.03 * math.sin(i * 1.3), GZ + 0.2 + i * 0.035),
             material=pearl_pink, parent=op, subdiv=1)


# ---- the rest of Pudong: lit towers filling the gaps -------------------------
rnd = random.Random(3)
pud = []
for i, (x, y) in enumerate([(-0.25, 0.08), (-0.22, 0.4), (0.3, 0.06), (0.32, 0.36), (-0.06, 0.55), (0.18, 0.52),
                            (-0.3, 0.26), (0.12, -0.12), (-0.14, -0.08), (0.24, -0.2)]):
    w_, h_ = rnd.uniform(0.05, 0.075), rnd.uniform(0.18, 0.38)
    pud.append(stand(k.box(f"pd-{i}", (w_, w_, h_), material=tower_dark), x, y, rot=rnd.uniform(-20, 20)))
    for b in range(int(h_ / 0.035)):
        pud.append(stand(k.box(f"pd-band-{i}-{b}", (w_ + 0.002, w_ + 0.002, 0.004), material=glow), x, y, extra=0.02 + b * 0.035))
    pud.append(stand(k.box(f"pd-crown-{i}", (w_ + 0.003, w_ + 0.003, 0.006), material=neon[i % 4]), x, y, extra=h_ - 0.01))
k.join("DECO-pudong", pud)


# ---- the Bund: a European row along the river, floodlit gold ----------------
bund = k.empty("OBJ-the-bund")
BR = 0.58


def along(deg):
    a = math.radians(deg)
    return Vector((BR * math.cos(a), BR * math.sin(a))), deg - 90 - 180   # facing out to the river


bparts = []
for i, deg in enumerate(range(150, 252, 13)):
    P, face = along(deg)
    kind = ["plain", "custom", "hsbc", "plain", "peace", "plain", "plain", "dome2"][i % 8]
    w_, d_, h_ = 0.085, 0.06, 0.1 + 0.02 * (i % 3)
    parts = [k.box(f"bd-{i}-body", (w_, d_, h_), material=bund_stone, parent=bund)]
    for c_ in range(6):
        parts.append(k.cylinder(f"bd-{i}-col-{c_}", 0.0035, h_ * 0.45, at=(-w_ / 2 + 0.01 + c_ * (w_ - 0.02) / 5, -d_ / 2 - 0.003, h_ * 0.3),
                                segs=6, material=bund_gold, parent=bund))
    for r_ in range(3):
        parts.append(k.box(f"bd-{i}-win-{r_}", (w_ * 0.86, 0.002, 0.01), at=(0, -d_ / 2 - 0.001, 0.02 + r_ * h_ * 0.28), material=bund_gold, parent=bund))
    parts.append(k.box(f"bd-{i}-cornice", (w_ + 0.006, d_ + 0.006, 0.008), at=(0, 0, h_), material=bund_gold, parent=bund))
    if kind == "custom":
        # The Custom House clock tower, after Big Ben.
        parts.append(k.box(f"bd-{i}-clocktower", (0.034, 0.034, 0.1), at=(0, 0, h_), material=bund_stone, parent=bund))
        parts.append(k.box(f"bd-{i}-clock", (0.036, 0.036, 0.024), at=(0, 0, h_ + 0.07), material=bund_gold, parent=bund))
        sp = k.cylinder(f"bd-{i}-clock-roof", 0.026, 0.05, segs=4, r_top=0.0, material=bund_stone, parent=bund, smooth=False)
        sp.data.transform(Matrix.Translation((0, 0, h_ + 0.1)) @ Matrix.Rotation(math.radians(45), 4, "Z"))
        parts.append(sp)
    elif kind == "hsbc":
        parts.append(k.cylinder(f"bd-{i}-drum", 0.028, 0.02, at=(0, 0, h_), segs=20, material=bund_stone, parent=bund))
        dome = k.sphere(f"bd-{i}-dome", 0.028, material=bund_gold, parent=bund, subdiv=3)
        dome.data.transform(Matrix.Translation((0, 0, h_ + 0.02)))
        parts.append(dome)
    elif kind == "peace":
        roof = k.cylinder(f"bd-{i}-pyramid", 0.03, 0.06, segs=4, r_top=0.0, material=peace_green, parent=bund, smooth=False)
        roof.data.transform(Matrix.Translation((0, 0, h_ + 0.008)) @ Matrix.Rotation(math.radians(45), 4, "Z"))
        parts.append(roof)
    elif kind == "dome2":
        parts.append(k.cylinder(f"bd-{i}-cupola", 0.015, 0.03, at=(0, 0, h_), r_top=0.004, segs=12, material=bund_gold, parent=bund))
    for o in parts:
        stand(o, P.x, P.y, rot=face)


# ---- Yu Garden ----------------------------------------------------------------
YG = (0.46, -0.12)
yg = k.empty("OBJ-yu-garden")


def chinese_roof(name, w, d, h, eave=0.012, lift=0.016, material=tile, parent=None):
    """Hip roof with steeply upswept corners, as on Huxinting."""
    bm_ = bmesh.new()
    W, D = w / 2 + eave, d / 2 + eave
    c = [bm_.verts.new((sx * W, sy * D, lift)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    m = [bm_.verts.new(((c[i].co.x + c[(i + 1) % 4].co.x) / 2, (c[i].co.y + c[(i + 1) % 4].co.y) / 2, 0.0)) for i in range(4)]
    rx = max(w / 2 - min(w, d) * 0.35, 0.002)
    r0, r1 = bm_.verts.new((-rx, 0, h)), bm_.verts.new((rx, 0, h))
    for f in ((c[0], m[0], c[1], r1, r0), (c[1], m[1], c[2], r1), (c[2], m[2], c[3], r0, r1), (c[3], m[3], c[0], r0)):
        bm_.faces.new(f)
    bm_.faces.new((c[0], m[3], c[3], m[2], c[2], m[1], c[1], m[0]))
    bmesh.ops.recalc_face_normals(bm_, faces=bm_.faces)
    return k.obj_from_bm(name, bm_, material, parent=parent)


yparts = []
pond_pts = [(0.15 * math.cos(a) * (1 + 0.1 * math.sin(3 * a)), 0.11 * math.sin(a) * (1 + 0.08 * math.cos(2 * a)))
            for a in [2 * math.pi * i / 40 for i in range(40)]]
pd_ = k.prism("yg-pond", pond_pts, 0.003, material=pond)
pd_.parent = yg
yparts.append(pd_)
# Huxinting: two storeys, two upswept roofs, in the middle of the pond.
yparts.append(k.box("yg-hux-1", (0.05, 0.04, 0.028), at=(0.02, 0.01, 0.003), material=wood_red, parent=yg))
r1 = chinese_roof("yg-hux-roof-1", 0.05, 0.04, 0.018, parent=yg)
r1.data.transform(Matrix.Translation((0.02, 0.01, 0.031)))
yparts.append(r1)
yparts.append(k.box("yg-hux-2", (0.036, 0.028, 0.022), at=(0.02, 0.01, 0.045), material=wood_red, parent=yg))
r2 = chinese_roof("yg-hux-roof-2", 0.036, 0.028, 0.02, parent=yg)
r2.data.transform(Matrix.Translation((0.02, 0.01, 0.067)))
yparts.append(r2)
yparts.append(k.box("yg-hux-glow", (0.052, 0.042, 0.01), at=(0.02, 0.01, 0.012), material=glow, parent=yg))
# The Nine-turn Bridge: zigzagging across the water.
zig = [(-0.15, -0.06), (-0.11, -0.03), (-0.08, -0.06), (-0.05, -0.02), (-0.02, -0.05), (0.0, -0.01)]
for i, (a, b) in enumerate(zip(zig, zig[1:])):
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    ln = math.hypot(b[0] - a[0], b[1] - a[1])
    seg = k.box(f"yg-bridge-{i}", (ln + 0.006, 0.012, 0.006), material=rock, parent=yg)
    seg.data.transform(Matrix.Translation((mid[0], mid[1], 0.004)) @ Matrix.Rotation(math.atan2(b[1] - a[1], b[0] - a[0]), 4, "Z"))
    yparts.append(seg)
# Red lanterns strung around, a rockery, and a grey dragon wall.
for i in range(10):
    a = 2 * math.pi * i / 10
    yparts.append(k.cylinder(f"yg-post-{i}", 0.0015, 0.04, at=(0.17 * math.cos(a), 0.13 * math.sin(a), 0), segs=4, material=dark, parent=yg))
    yparts.append(k.sphere(f"yg-lantern-{i}", 0.007, at=(0.17 * math.cos(a), 0.13 * math.sin(a), 0.045), material=red_lantern, parent=yg, subdiv=1))
for i in range(6):
    yparts.append(k.sphere(f"yg-rock-{i}", 0.018 + 0.006 * (i % 3), at=(0.1 + 0.02 * i, 0.09 + 0.01 * (i % 2), 0.01 + 0.008 * (i % 3)),
                           material=rock, parent=yg, subdiv=1))
wall_pts = [(-0.18 + 0.36 * t, 0.16 + 0.01 * math.sin(6 * t), 0.022 + 0.008 * math.sin(math.pi * 4 * t)) for t in [i / 30 for i in range(31)]]
for i, (x, y, zz) in enumerate(wall_pts[:-1]):
    yparts.append(k.box(f"yg-wall-{i}", (0.0125, 0.01, zz), at=(x, y, 0), material=castle_wall, parent=yg))
yparts.append(k.tube("yg-dragon-ridge", [(x, y, zz + 0.004) for x, y, zz in wall_pts], 0.005, material=tile, segs=5, parent=yg))
for o in yparts:
    stand(o, *YG, rot=-25)


# ---- Shanghai Disneyland: the Enchanted Storybook Castle --------------------
DC = (0.44, 0.36)
castle = k.empty("OBJ-disney-castle")
cparts = [k.box("dc-base", (0.14, 0.08, 0.06), material=castle_wall, parent=castle),
          k.box("dc-gate", (0.03, 0.004, 0.035), at=(0, -0.042, 0), material=glow, parent=castle)]


def turret(tag, x, y, r, h, roof_h, z0=0.0):
    cparts.append(k.cylinder(f"dc-{tag}", r, h, at=(x, y, z0), segs=14, material=castle_wall, parent=castle))
    cparts.append(k.cylinder(f"dc-{tag}-roof", r * 1.25, roof_h, at=(x, y, z0 + h), r_top=0.0, segs=14, material=castle_roof, parent=castle, smooth=False))
    cparts.append(k.sphere(f"dc-{tag}-finial", r * 0.25, at=(x, y, z0 + h + roof_h + 0.002), material=castle_gold, parent=castle, subdiv=1))
    cparts.append(k.box(f"dc-{tag}-win", (r * 0.8, 0.003, r * 0.9), at=(x, y - r - 0.001, z0 + h * 0.55), material=glow, parent=castle))


turret("keep", 0, 0.005, 0.03, 0.17, 0.08, z0=0.0)
for sx in (-1, 1):
    turret(f"side-{sx}", sx * 0.055, -0.015, 0.016, 0.11, 0.05)
    turret(f"corner-{sx}", sx * 0.07, 0.03, 0.013, 0.08, 0.04)
    turret(f"small-{sx}", sx * 0.03, -0.035, 0.01, 0.075, 0.035)
# The peony on top of the tallest spire.
for i in range(6):
    a = 2 * math.pi * i / 6
    cparts.append(k.sphere(f"dc-peony-{i}", 0.006, at=(0.006 * math.cos(a), 0.005 + 0.006 * math.sin(a), 0.26), material=castle_gold, parent=castle, subdiv=1))
for o in cparts:
    stand(o, *DC, rot=-40)


# ---- Zootopia: Savanna Central -----------------------------------------------
ZT = (0.44, -0.46)
zt = k.empty("OBJ-zootopia")
zparts = [k.box("zt-show", (0.18, 0.12, 0.05), material=zoo_wall, parent=zt)]
# Two high-rises on top of the show building; one striped red like a tiger.
zparts.append(k.box("zt-tower-a", (0.04, 0.04, 0.2), at=(-0.04, 0.02, 0.05), material=tower_dark, parent=zt))
for b in range(8):
    zparts.append(k.box(f"zt-stripe-{b}", (0.042, 0.042, 0.008), at=(-0.04, 0.02, 0.06 + b * 0.024), material=tiger, parent=zt))
zparts.append(k.box("zt-tower-b", (0.035, 0.035, 0.16), at=(0.045, 0.03, 0.05), material=zoo[1], parent=zt))
# Zootopia Central Station: an arched glass front.
zparts.append(k.box("zt-station", (0.08, 0.03, 0.035), at=(0.0, -0.075, 0.0), material=zoo_wall, parent=zt))
zparts.append(k.tube("zt-station-arch", [(0.035 * math.cos(math.pi * i / 12), -0.091, 0.035 + 0.03 * math.sin(math.pi * i / 12)) for i in range(13)],
                     0.004, material=zoo[3], segs=5, parent=zt))
zparts.append(k.box("zt-station-glass", (0.06, 0.003, 0.03), at=(0, -0.091, 0.005), material=glow, parent=zt))
# Mane Street shopfronts: bright and mismatched.
for i in range(5):
    zparts.append(k.box(f"zt-shop-{i}", (0.03, 0.03, 0.04 + 0.01 * (i % 2)), at=(-0.08 + i * 0.035, -0.12, 0), material=zoo[i % 4], parent=zt))
for o in zparts:
    stand(o, *ZT, rot=30)


# ---- the cruise boat, circling on the river ---------------------------------
boat = k.empty("OBJ-river-cruise")
boat["orbit"] = 60.0
BRD = 0.88
bparts = [k.box("boat-hull", (0.05, 0.16, 0.022), at=(BRD, 0, -0.004), material=white, parent=boat)]
for v in bparts[0].data.vertices:
    if abs(v.co.y) > 0.07:        # a pointed bow and a rounded stern
        v.co.x = BRD + (v.co.x - BRD) * 0.4
bparts.append(k.box("boat-deck-1", (0.042, 0.12, 0.018), at=(BRD, -0.005, 0.018), material=white, parent=boat))
bparts.append(k.box("boat-windows-1", (0.044, 0.112, 0.008), at=(BRD, -0.005, 0.023), material=neon[0], parent=boat))
bparts.append(k.box("boat-deck-2", (0.034, 0.08, 0.014), at=(BRD, -0.01, 0.036), material=white, parent=boat))
bparts.append(k.box("boat-windows-2", (0.036, 0.072, 0.006), at=(BRD, -0.01, 0.04), material=neon[1], parent=boat))
lights = [k.sphere(f"boat-light-{i}", 0.003, at=(BRD + (0.026 if i % 2 else -0.026), -0.07 + (i // 2) * 0.014, 0.019), material=glow, subdiv=1)
          for i in range(20)]
bl = k.join("boat-lights", lights)
bl.parent = boat
bparts.append(bl)


# ---- the Lujiazui skywalk: the lit ring footbridge in front of the Pearl -----
SK = (0.0, -0.24)
sk = k.empty("OBJ-lujiazui-skywalk")
k.torus("sk-ring", 0.075, 0.006, at=(SK[0], SK[1], GZ + 0.05), segs=48, tube_segs=5, material=neon[2], parent=sk)
k.torus("sk-deck", 0.075, 0.011, at=(SK[0], SK[1], GZ + 0.045), segs=48, tube_segs=4, material=promenade, parent=sk)
for i in range(8):
    a = 2 * math.pi * i / 8
    k.cylinder(f"sk-post-{i}", 0.003, 0.045, at=(SK[0] + 0.075 * math.cos(a), SK[1] + 0.075 * math.sin(a), GZ), segs=5, material=pearl_col, parent=sk)
low = []
for i, (x, y) in enumerate([(-0.2, -0.32), (0.17, -0.36), (-0.12, -0.46), (0.08, -0.5), (-0.3, -0.18), (0.27, -0.06)]):
    w_, h_ = rnd.uniform(0.05, 0.07), rnd.uniform(0.07, 0.13)
    low.append(stand(k.box(f"low-{i}", (w_, w_ * 0.8, h_), material=tower_dark), x, y, rot=rnd.uniform(-25, 25)))
    for b in range(int(h_ / 0.03)):
        low.append(stand(k.box(f"low-band-{i}-{b}", (w_ + 0.002, w_ * 0.8 + 0.002, 0.004), material=glow), x, y, extra=0.015 + b * 0.03))
    low.append(stand(k.box(f"low-sign-{i}", (w_ * 0.7, 0.003, 0.02), at=(0, -w_ * 0.4 - 0.002, 0.03), material=neon[(i + 1) % 4]), x, y))
k.join("DECO-low-rise", low)


# ---- a few dark trees on the island -----------------------------------------
trees = k.forest("DECO-trees", 30, leaf, [(ST[0], ST[1], 0.1), (SW[0], SW[1], 0.09), (JM[0], JM[1], 0.08), (OP[0], OP[1], 0.1),
                                          (YG[0], YG[1], 0.2), (DC[0], DC[1], 0.12), (ZT[0], ZT[1], 0.15)]
                 + [(0.58 * math.cos(math.radians(a)), 0.58 * math.sin(math.radians(a)), 0.07) for a in range(150, 252, 13)]
                 + [(SK[0], SK[1], 0.1)],
                 seed=6, r_max=0.62, h=(0.05, 0.07), z=GZ, round_crowns=True, trunk_mat=trunk)

# ---- the island fills more of the river (the boat stays on the water) -------
for o in list(bpy.data.objects):
    if o.parent is None and o.name not in ("DECO-base", "OBJ-river-cruise"):
        k.grow(o, 1.1, (0, 0, 0))

k.export("shanghai")
