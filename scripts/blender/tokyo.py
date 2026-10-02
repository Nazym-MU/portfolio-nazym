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
FX, FY, FR, FH = 0.0, 0.1, 0.5, 0.56
# Concave sides, a flat crater on top.
prof = [(FR * (1 - t) ** 1.6 + 0.07 * t, FH * t) for t in [i / 20 for i in range(21)]]
prof.append((0.0, FH))
fuji = k.lathe("OBJ-mt-fuji", prof, segs=48, at=(FX, FY, 0), material=fuji_m)
# The snow cap, a skin over the top fifth, with a ragged lower edge.
cap_prof = [(FR * (1 - t) ** 1.6 + 0.07 * t + 0.003, FH * t + 0.002) for t in [0.7 + 0.3 * i / 10 for i in range(11)]]
cap_prof.append((0.0, FH + 0.002))
cap = k.lathe("fuji-snow", cap_prof, segs=48, at=(FX, FY, 0), material=snow)
for v in cap.data.vertices:
    if v.co.z < FH * 0.72 + 0.003:
        a = math.atan2(v.co.y - FY, v.co.x - FX)
        v.co.z -= 0.025 * (0.5 + 0.5 * math.sin(7 * a))
cap.parent = fuji


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
VX, VY = -0.5, -0.5
vend = k.empty("OBJ-seventeen-ice")
parts = [k.box("vend-body", (0.12, 0.075, 0.21), at=(0, 0, 0), material=white, parent=vend),
         k.box("vend-top", (0.124, 0.079, 0.03), at=(0, 0, 0.18), material=pink, parent=vend),
         k.box("vend-base", (0.124, 0.079, 0.025), at=(0, 0, 0), material=sky, parent=vend),
         k.box("vend-slot", (0.06, 0.004, 0.018), at=(0, -0.039, 0.03), material=black, parent=vend)]
ice = [pink, sky, glow, s_orange, f_green]
for r in range(3):
    for col in range(4):
        parts.append(k.box(f"vend-ice-{r}-{col}", (0.02, 0.004, 0.026),
                           at=(-0.039 + col * 0.026, -0.039, 0.065 + r * 0.035),
                           material=ice[(r * 4 + col) % len(ice)], parent=vend))
for o in parts:
    o.data.transform(Matrix.Translation((VX, VY, 0)) @ Matrix.Rotation(math.radians(-40), 4, "Z"))


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
