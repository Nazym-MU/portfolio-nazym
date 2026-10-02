"""
tokyo.py — the Tokyo diorama, from Nazym's sketch: Mt. Fuji in the middle and
the city packed in around its foot.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python scripts/blender/tokyo.py

                 houses        houses
     Tokyo Tower                       sakura
  FamilyMart         Mt. Fuji          torii
     Seventeen Ice                  7-Eleven
                Shibuya crossing
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh  # noqa: E402
from mathutils import Matrix  # noqa: E402
import diorama_kit as k  # noqa: E402

k.reset()

paving = k.mat("paving", (0.84, 0.82, 0.76))
side = k.mat("base-cream", (0.93, 0.91, 0.86))
fuji_m = k.mat("fuji", (0.56, 0.68, 0.86))
snow = k.mat("snow", (0.97, 0.97, 0.98))
orange = k.mat("tower-orange", (0.95, 0.42, 0.16))
white = k.mat("white", (0.96, 0.96, 0.94))
deck = k.mat("lamp-deck", (1.0, 0.84, 0.45))
glow = k.mat("lamp-yellow", (1.0, 0.82, 0.42))
asphalt = k.mat("asphalt", (0.30, 0.31, 0.34))
torii_red = k.mat("torii-red", (0.78, 0.16, 0.12))
black = k.mat("dark", (0.16, 0.16, 0.20))
sakura = k.mat("sakura", (0.96, 0.66, 0.82))
trunk = k.mat("trunk", (0.36, 0.26, 0.22))
roof_m = k.mat("roof-slate", (0.28, 0.30, 0.38))
wall_m = k.mat("wall", (0.90, 0.86, 0.78))
s_orange = k.mat("seven-orange", (0.98, 0.52, 0.12))
s_green = k.mat("seven-green", (0.10, 0.55, 0.36))
s_red = k.mat("seven-red", (0.86, 0.12, 0.14))
f_green = k.mat("famima-green", (0.10, 0.62, 0.32))
f_blue = k.mat("famima-blue", (0.12, 0.40, 0.78))
pink = k.mat("seventeen-pink", (0.98, 0.55, 0.72))
sky = k.mat("seventeen-blue", (0.45, 0.72, 0.96))
people = [k.mat(f"person-{i}", c) for i, c in enumerate(
    [(0.86, 0.3, 0.3), (0.3, 0.45, 0.8), (0.95, 0.8, 0.3), (0.3, 0.6, 0.4), (0.9, 0.9, 0.9), (0.5, 0.35, 0.65)])]

k.base(paving, side)


def rotate_about(o, deg, cx, cy):
    o.data.transform(Matrix.Translation((cx, cy, 0)) @ Matrix.Rotation(math.radians(deg), 4, "Z")
                     @ Matrix.Translation((-cx, -cy, 0)))


# ---- Mt. Fuji ---------------------------------------------------------------
# The real silhouette: long gentle feet sweeping up into steeper upper slopes,
# and a wide, flat, slightly dented summit, not a point. Snow comes down the
# ridges in streaks rather than stopping at a clean line.
FX, FY, FR, FH, FT = 0.0, 0.1, 0.52, 0.44, 0.13      # base radius, height, summit radius
SEGS, RINGS = 120, 36
bm = bmesh.new()
rings = []
for j in range(RINGS + 1):
    t = j / RINGS                                     # 0 at the foot, 1 at the summit rim
    r = FR + (FT - FR) * t
    z = FH * t ** 1.7                                 # concave: flat feet, steep top
    ring = []
    for i in range(SEGS):
        a_ = 2 * math.pi * i / SEGS
        # Ridges and gullies, strongest mid-slope, gone at the rim and the foot.
        wob = (0.035 * math.sin(5 * a_ + 0.7) + 0.02 * math.sin(11 * a_ + 2.1) + 0.012 * math.sin(23 * a_)) * math.sin(math.pi * t)
        rr = r * (1 + wob)
        ring.append(bm.verts.new((FX + rr * math.cos(a_), FY + rr * math.sin(a_), z)))
    rings.append(ring)
# The crater: a shallow dent inside the summit rim.
dent = [bm.verts.new((FX + FT * 0.6 * math.cos(2 * math.pi * i / SEGS), FY + FT * 0.6 * math.sin(2 * math.pi * i / SEGS), FH - 0.012))
        for i in range(SEGS)]
centre = bm.verts.new((FX, FY, FH - 0.018))
for ra, rb in zip(rings, rings[1:]):
    for i in range(SEGS):
        bm.faces.new((ra[i], ra[(i + 1) % SEGS], rb[(i + 1) % SEGS], rb[i]))
for i in range(SEGS):
    bm.faces.new((rings[-1][i], rings[-1][(i + 1) % SEGS], dent[(i + 1) % SEGS], dent[i]))
    bm.faces.new((dent[i], dent[(i + 1) % SEGS], centre))
bm.faces.new(list(reversed(rings[0])))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
fuji = k.obj_from_bm("OBJ-mt-fuji", bm)
fuji.data.materials.append(fuji_m)
fuji.data.materials.append(snow)
for poly in fuji.data.polygons:
    c = poly.center
    a_ = math.atan2(c.y - FY, c.x - FX)
    streak = max(0.0, math.sin(9 * a_ + 0.4)) ** 3 * 0.16 + max(0.0, math.sin(17 * a_ + 1.3)) ** 4 * 0.08
    snow_line = FH * (0.66 - streak)
    poly.material_index = 1 if c.z > snow_line else 0
k.smooth_by_angle(fuji, 50)


# ---- Tokyo Tower ------------------------------------------------------------
TX, TY = -0.52, 0.40
tower = k.empty("OBJ-tokyo-tower")
bands = [(0.0, 0.11, 0.09, orange), (0.11, 0.09, 0.075, white), (0.2, 0.075, 0.06, orange),
         (0.29, 0.06, 0.048, white), (0.38, 0.048, 0.036, orange), (0.47, 0.036, 0.026, white),
         (0.56, 0.026, 0.016, orange), (0.65, 0.016, 0.006, white)]
for z0, r0, r1, m in bands:
    seg = k.cylinder(f"tower-{z0}", r0, 0.09, at=(TX, TY, z0), r_top=r1, segs=4, material=m,
                     parent=tower, smooth=False)
    rotate_about(seg, 45, TX, TY)
# Arch cut-outs at the foot read as dark panels on each side.
for i in range(4):
    a = k.box(f"tower-arch-{i}", (0.07, 0.004, 0.06), material=black, parent=tower)
    a.data.transform(Matrix.Translation((TX, TY, 0)) @ Matrix.Rotation(math.radians(90 * i), 4, "Z")
                     @ Matrix.Translation((0, -0.1, 0)))
k.box("tower-deck-main", (0.11, 0.11, 0.035), at=(TX, TY, 0.2), material=deck, parent=tower)
k.box("tower-deck-top", (0.06, 0.06, 0.02), at=(TX, TY, 0.47), material=deck, parent=tower)
k.cylinder("tower-antenna", 0.004, 0.08, at=(TX, TY, 0.74), segs=5, material=white, parent=tower)
# Squash to clear the dome (its glass is lower out here than at the centre).
for ch in tower.children:
    ch.data.transform(Matrix.Translation((TX, TY, 0)) @ Matrix.Diagonal((1, 1, 0.84, 1)) @ Matrix.Translation((-TX, -TY, 0)))


# ---- Shibuya crossing -------------------------------------------------------
CX, CY, CW, CD = 0.0, -0.66, 0.5, 0.34
cross = k.empty("OBJ-shibuya-crossing")
k.box("crossing-road", (CW, CD, 0.004), at=(CX, CY, 0), material=asphalt, parent=cross)
stripes = []


def zebra(x0, y0, x1, y1, n, w=0.008):
    """n stripes along the segment (x0,y0)-(x1,y1), each across it."""
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    for i in range(n):
        t = (i + 0.5) / n
        s = k.box("z", (w, 0.06, 0.002), material=white)
        k.place(s, rot=(0, 0, ang), at=(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 0.004))
        stripes.append(s)


hx, hy = CW / 2 - 0.05, CD / 2 - 0.045
zebra(CX - hx, CY + hy, CX + hx, CY + hy, 12)
zebra(CX - hx, CY - hy, CX + hx, CY - hy, 12)
zebra(CX - hx - 0.0, CY - hy + 0.03, CX - hx, CY + hy - 0.03, 7)
zebra(CX + hx, CY - hy + 0.03, CX + hx, CY + hy - 0.03, 7)
zebra(CX - hx + 0.05, CY - hy + 0.05, CX + hx - 0.05, CY + hy - 0.05, 11)
zebra(CX - hx + 0.05, CY + hy - 0.05, CX + hx - 0.05, CY - hy + 0.05, 11)
st = k.join("crossing-stripes", stripes)
st.parent = cross
rnd = random.Random(17)
crowd = []
for i in range(22):
    x, y = CX + rnd.uniform(-CW / 2 + 0.03, CW / 2 - 0.03), CY + rnd.uniform(-CD / 2 + 0.03, CD / 2 - 0.03)
    m = people[i % len(people)]
    crowd.append(k.cylinder(f"p-{i}", 0.008, 0.026, at=(x, y, 0.004), segs=6, material=m))
    crowd.append(k.sphere(f"ph-{i}", 0.007, at=(x, y, 0.038), material=black, subdiv=1))
c = k.join("crossing-people", crowd)
c.parent = cross


# ---- Shibuya: the buildings that make the crossing ---------------------------
neon = [k.mat(n, c) for n, c in [
    ("neon-blue", (0.25, 0.62, 1.0)), ("neon-pink", (1.0, 0.42, 0.78)), ("neon-yellow", (1.0, 0.86, 0.25)),
    ("neon-green", (0.35, 0.95, 0.55)), ("neon-red", (1.0, 0.25, 0.28)), ("neon-white", (0.95, 0.96, 1.0))]]
silver = k.mat("silver", (0.80, 0.82, 0.86))
concrete = k.mat("concrete", (0.62, 0.62, 0.66))
glassy = k.mat("tower-dark", (0.30, 0.36, 0.48))


def block(name_, x, y, w, d, h, body, face_deg, screens):
    """A building facing the crossing: body, lit window bands, and screens
    [(width, height, z, material)] on its front."""
    parts = [k.box(f"{name_}-body", (w, d, h), material=body, parent=cross)]
    for b_ in range(int(h / 0.05)):
        parts.append(k.box(f"{name_}-band-{b_}", (w + 0.002, d + 0.002, 0.005), at=(0, 0, 0.03 + b_ * 0.05),
                           material=glow, parent=cross))
    for j, (sw, sh, sz, m) in enumerate(screens):
        parts.append(k.box(f"{name_}-screen-{j}", (sw, 0.006, sh), at=(0, -d / 2 - 0.003, sz), material=m, parent=cross))
    for o in parts:
        o.data.transform(Matrix.Translation((x, y, 0)) @ Matrix.Rotation(math.radians(face_deg), 4, "Z"))


# Shibuya 109: the silver cylinder on the fork, with its tall sign.
S9X, S9Y = -0.36, -0.46
k.cylinder("s109-drum", 0.065, 0.42, at=(S9X, S9Y, 0), segs=28, material=silver, parent=cross)
k.cylinder("s109-cap", 0.068, 0.02, at=(S9X, S9Y, 0.42), segs=28, material=concrete, parent=cross)
k.box("s109-sign", (0.03, 0.006, 0.22), at=(S9X + 0.02, S9Y - 0.066, 0.17), material=neon[4], parent=cross)
for b_ in range(7):
    k.cylinder(f"s109-band-{b_}", 0.066, 0.005, at=(S9X, S9Y, 0.04 + b_ * 0.055), segs=28, material=glow, parent=cross)
block("s109-wing", -0.44, -0.6, 0.1, 0.14, 0.26, concrete, -70, [(0.12, 0.06, 0.12, neon[1])])
# QFRONT: the glass corner with the giant screen, Starbucks on its ground floor.
block("qfront", 0.36, -0.47, 0.16, 0.12, 0.38, glassy, 35,
      [(0.15, 0.16, 0.17, neon[0]), (0.15, 0.04, 0.02, neon[3])])
# The two flanking blocks at the front corners, screens stacked up their faces.
block("tsutaya-east", 0.37, -0.76, 0.12, 0.1, 0.3, concrete, 60,
      [(0.11, 0.08, 0.16, neon[2]), (0.11, 0.05, 0.06, neon[5])])
block("shibuya-west", -0.33, -0.8, 0.12, 0.1, 0.28, glassy, -55,
      [(0.11, 0.09, 0.14, neon[1]), (0.11, 0.04, 0.04, neon[0])])


# ---- Convenience stores -----------------------------------------------------
def konbini(name, x, y, face_deg, bands, w=0.2, d=0.13, h=0.12):
    """A white corner shop with coloured fascia bands and a lit window, built
    facing -Y then turned to face `face_deg`."""
    root = k.empty(name)
    tag = name[4:]   # parts must not start with OBJ- or each becomes its own object
    parts = [k.box(f"{tag}-body", (w, d, h), at=(0, 0, 0), material=white, parent=root),
             k.box(f"{tag}-roof", (w + 0.006, d + 0.006, 0.01), at=(0, 0, h), material=white, parent=root),
             k.box(f"{tag}-window", (w * 0.8, 0.004, 0.055), at=(0, -d / 2 - 0.002, 0.012), material=glow, parent=root),
             k.box(f"{tag}-door", (0.03, 0.005, 0.06), at=(w * 0.32, -d / 2 - 0.003, 0.0), material=black, parent=root)]
    bh = 0.03 / len(bands)
    for j, m in enumerate(bands):
        parts.append(k.box(f"{tag}-band-{j}", (w + 0.004, d + 0.004, bh), at=(0, 0, h - 0.04 + j * bh),
                           material=m, parent=root))
    for o in parts:
        o.data.transform(Matrix.Translation((x, y, 0)) @ Matrix.Rotation(math.radians(face_deg), 4, "Z"))
    return root


konbini("OBJ-7-eleven", 0.6, -0.48, 40, [s_red, s_green, s_orange])
konbini("OBJ-familymart", -0.76, -0.06, -80, [f_blue, white, f_green], w=0.19)


# ---- Seventeen Ice vending machine ------------------------------------------
# Just the machine, small: roughly a person and a half tall next to the crowd.
# White cabinet, the round pink-and-blue top, a lit window of cones.
VX, VY = -0.56, -0.4
vend = k.empty("OBJ-seventeen-ice")
vw, vd, vh = 0.05, 0.035, 0.075
parts = [k.box("vend-body", (vw, vd, vh), material=white, parent=vend),
         k.box("vend-base", (vw + 0.002, vd + 0.002, 0.008), material=sky, parent=vend),
         k.box("vend-window", (vw * 0.8, 0.003, 0.032), at=(0, -vd / 2 - 0.0015, 0.03), material=glow, parent=vend),
         k.box("vend-slot", (vw * 0.5, 0.003, 0.008), at=(0, -vd / 2 - 0.0015, 0.012), material=black, parent=vend)]
top = k.cylinder("vend-top", vd / 2 + 0.001, vw + 0.002, segs=16, material=pink, parent=vend)
top.data.transform(Matrix.Translation((0, 0, vh)) @ Matrix.Rotation(math.radians(90), 4, "Y")
                   @ Matrix.Translation((0, 0, -(vw + 0.002) / 2)))
parts.append(top)
for col in range(3):
    cone = k.cylinder(f"vend-cone-{col}", 0.004, 0.012, segs=6, r_top=0.0, material=s_orange, parent=vend)
    cone.data.transform(Matrix.Translation((-0.013 + col * 0.013, -vd / 2 - 0.004, 0.037)) @ Matrix.Rotation(math.pi, 4, "X"))
    scoop = k.sphere(f"vend-scoop-{col}", 0.004, at=(-0.013 + col * 0.013, -vd / 2 - 0.004, 0.039),
                     material=[pink, sky, white][col], parent=vend, subdiv=1)
    parts += [cone, scoop]
for o in parts:
    o.data.transform(Matrix.Translation((VX, VY, 0)) @ Matrix.Rotation(math.radians(-30), 4, "Z"))


# ---- Torii and sakura -------------------------------------------------------
GX, GY = 0.66, -0.06
torii = k.empty("OBJ-torii")
tp = []
for dx in (-0.075, 0.075):
    tp.append(k.cylinder(f"torii-post-{dx}", 0.011, 0.2, at=(dx, 0, 0), segs=10, material=torii_red, parent=torii))
    tp.append(k.cylinder(f"torii-foot-{dx}", 0.015, 0.018, at=(dx, 0, 0), segs=10, material=black, parent=torii))
tp.append(k.box("torii-nuki", (0.19, 0.016, 0.016), at=(0, 0, 0.15), material=torii_red, parent=torii))
kasagi = k.box("torii-kasagi", (0.25, 0.024, 0.02), at=(0, 0, 0.2), material=black, parent=torii)
# Upturned ends: bend the beam up toward its tips.
for v in kasagi.data.vertices:
    v.co.z += 0.12 * (v.co.x / 0.125) ** 2 * 0.1
tp.append(kasagi)
tp.append(k.box("torii-shimaki", (0.22, 0.02, 0.012), at=(0, 0, 0.188), material=torii_red, parent=torii))
for o in tp:
    o.data.transform(Matrix.Translation((GX, GY, 0)) @ Matrix.Rotation(math.radians(90), 4, "Z"))

blossoms = []
for i, (x, y, h) in enumerate([(0.56, 0.2, 0.2), (0.72, 0.12, 0.17), (0.44, 0.38, 0.19), (0.74, -0.26, 0.16),
                               (0.3, 0.56, 0.17), (0.62, 0.36, 0.15), (0.84, -0.05, 0.14), (0.5, -0.3, 0.13)]):
    blossoms.append(k.cylinder(f"sak-trunk-{i}", 0.01, h * 0.45, at=(x, y, 0), segs=6, material=trunk))
    for j, (dx, dy, dz, r) in enumerate([(0, 0, 0.6, 0.06), (0.035, 0.02, 0.72, 0.045), (-0.03, -0.02, 0.7, 0.045),
                                         (0.0, 0.03, 0.85, 0.04)]):
        blossoms.append(k.sphere(f"sak-{i}-{j}", r * h / 0.17, at=(x + dx, y + dy, h * dz), material=sakura, subdiv=2))
k.join("DECO-sakura", blossoms)


# ---- Houses filling the back ------------------------------------------------
houses = []
for i, a in enumerate([100, 115, 130, 160, 75, 60]):
    r = 0.8 if i % 2 else 0.72
    x, y = r * math.cos(math.radians(a)), r * math.sin(math.radians(a))
    w, h = 0.1 + 0.02 * (i % 3), 0.07 + 0.025 * (i % 2)
    body = k.box(f"house-{i}", (w, 0.09, h), material=wall_m)
    roof = k.cylinder(f"house-roof-{i}", 0.08, 0.04, segs=4, r_top=0.02, material=roof_m, smooth=False)
    roof.data.transform(Matrix.Translation((0, 0, h)) @ Matrix.Diagonal((w / 0.11, 0.09 / 0.11, 1, 1))
                        @ Matrix.Rotation(math.radians(45), 4, "Z"))
    win = k.box(f"house-win-{i}", (0.03, 0.004, 0.025), at=(0, -0.047, h * 0.4), material=glow)
    for o in (body, roof, win):
        o.data.transform(Matrix.Translation((x, y, 0)) @ Matrix.Rotation(math.radians(a - 90 + 180), 4, "Z"))
        houses.append(o)
k.join("DECO-houses", houses)

k.export("tokyo")
