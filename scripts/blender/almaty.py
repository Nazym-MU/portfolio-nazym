"""
almaty.py — the Almaty diorama, from Nazym's sketch.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python scripts/blender/almaty.py

          ~~~~~~~~~~~ the Alatau, snow on top ~~~~~~~~~~~
           Kolsay (on a terrace)
                              Koktobe hill: TV tower, Ferris wheel,
                              upper cable-car station
   Hotel Kazakhstan    cable car  ↗
      lower station                    Nurly Tau
                      Al-Farabi glass
   home + pool                         First President's Park gate
        apple trees everywhere in between

The cable car goes building to building (lower station -> upper station on
Koktobe), never touching the TV tower, which stands on its own on the hill.
Cabins carry a `shuttle` extra the viewer animates along the sagging cable.
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
import diorama_kit as k  # noqa: E402

k.reset()

grass = k.mat("grass", (0.56, 0.70, 0.42))
earth = k.mat("earth", (0.46, 0.38, 0.32))
rock = k.mat("mountain", (0.52, 0.62, 0.80))     # her sketch paints the range blue
snow = k.mat("snow", (0.97, 0.97, 0.99))
lake = k.mat("kolsay", (0.20, 0.42, 0.62))
spruce = k.mat("spruce", (0.16, 0.34, 0.26))
leaf = k.mat("apple-leaf", (0.38, 0.60, 0.32))
apple = k.mat("apple-red", (0.86, 0.14, 0.14))
trunk = k.mat("trunk", (0.38, 0.28, 0.22))
white = k.mat("white", (0.95, 0.95, 0.93))
steel = k.mat("steel", (0.62, 0.64, 0.68))
dark = k.mat("dark", (0.18, 0.18, 0.22))
glow = k.mat("lamp-yellow", (1.0, 0.82, 0.42))
gold = k.mat("hotel-gold", (0.88, 0.70, 0.36))
crown_m = k.mat("neon-hotel-crown", (1.0, 0.62, 0.22))
glass_blue = k.mat("facade-blue", (0.30, 0.44, 0.70))
glass_teal = k.mat("facade-teal", (0.34, 0.58, 0.70))
cream = k.mat("cream", (0.95, 0.90, 0.76))
gate_gold = k.mat("gate-gold", (0.92, 0.78, 0.42))
water = k.mat("pool", (0.40, 0.70, 0.90))
house_y = k.mat("house-yellow", (0.96, 0.84, 0.50))
roof_red = k.mat("roof-maroon", (0.56, 0.18, 0.18))
win_blue = k.mat("window-blue", (0.70, 0.84, 0.96))
cabin_red = k.mat("cabin-red", (0.82, 0.18, 0.16))
wheel_m = k.mat("wheel-white", (0.94, 0.94, 0.96))
paving = k.mat("paving", (0.82, 0.78, 0.70))

k.base(grass, earth)


# ---- the land: polar grid, heights from one function ------------------------
def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


PEAKS = [(-0.62, 0.52, 0.40, 0.17), (-0.32, 0.72, 0.52, 0.17), (0.02, 0.76, 0.5, 0.15),
         (0.34, 0.66, 0.46, 0.15), (0.6, 0.48, 0.36, 0.14), (-0.12, 0.6, 0.32, 0.12)]
KOK = (0.2, 0.27)          # Koktobe hill
LAKE = (-0.36, 0.48)       # Kolsay terrace
LAKE_Z = 0.24


def height(x, y):
    r = math.hypot(x, y)
    rng = sum(h * math.exp(-((x - px) ** 2 + (y - py) ** 2) / (2 * s * s)) for px, py, h, s in PEAKS)
    rng *= smoothstep(0.05, 0.42, y)                    # the range only at the back
    rng += 0.012 * math.sin(23 * x + 3 * y) * math.sin(17 * y) * smoothstep(0.1, 0.5, y)   # rough flanks
    kok = 0.27 * math.exp(-((x - KOK[0]) ** 2 + (y - KOK[1]) ** 2) / (2 * 0.11 ** 2))
    kok = min(kok, 0.19)                                # a flat top for the tower and the wheel
    h = max(rng, kok, 0.0)
    d = math.hypot(x - LAKE[0], y - LAKE[1])
    h = h + (LAKE_Z - h) * (1 - smoothstep(0.1, 0.3, d)) ** 1.5   # a gentle bowl, not a pit
    return h * (1 - smoothstep(0.86, 0.985, r))         # down to the plinth at the rim


RINGS, SEGS = 64, 192
bm = bmesh.new()
grid = [[bm.verts.new((0, 0, height(0, 0)))]]
for j in range(1, RINGS + 1):
    r = 0.995 * j / RINGS
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
for m in (grass, rock, snow):
    land.data.materials.append(m)
for p in land.data.polygons:
    c = p.center
    snow_line = 0.39 + 0.035 * math.sin(13 * c.x) + 0.025 * math.sin(29 * c.x + 1.0)
    near_kok = math.hypot(c.x - KOK[0], c.y - KOK[1]) < 0.2
    near_lake = math.hypot(c.x - LAKE[0], c.y - LAKE[1]) < 0.17
    if c.z > snow_line and not near_kok:
        p.material_index = 2
    elif c.z > 0.07 and not near_kok and not near_lake:
        p.material_index = 1
    else:
        p.material_index = 0
    p.use_smooth = True
k.smooth_by_angle(land, 30)


def ground(x, y):
    return height(x, y)


def stand(o, x, y, rot=0.0, extra=0.0):
    o.data.transform(Matrix.Translation((x, y, ground(x, y) + extra)) @ Matrix.Rotation(math.radians(rot), 4, "Z"))
    return o


# ---- Kolsay, on its terrace, ringed by Tian Shan spruces --------------------
pts = []
for i in range(36):
    a = 2 * math.pi * i / 36
    rr = 0.095 * (1 + 0.18 * math.sin(3 * a + 0.5) + 0.08 * math.sin(7 * a))
    pts.append((LAKE[0] + rr * math.cos(a) * 1.25, LAKE[1] + rr * math.sin(a) * 0.8))
k.prism("OBJ-kolsay", pts, 0.004, z0=LAKE_Z, material=lake)
rnd = random.Random(12)
spr = []
for i in range(40):
    a = rnd.uniform(0, 2 * math.pi)
    d = rnd.uniform(0.13, 0.22)
    x, y = LAKE[0] + d * math.cos(a) * 1.15, LAKE[1] + d * math.sin(a) * 0.9
    h = rnd.uniform(0.05, 0.08)
    c = k.cylinder(f"spruce-{i}", h * 0.24, h, segs=7, r_top=0.0, material=spruce)
    spr.append(stand(c, x, y))
k.join("DECO-spruces", spr)


# ---- Koktobe: TV tower, Ferris wheel, upper station --------------------------
TV = (0.24, 0.33)
tv = k.empty("OBJ-koktobe-tv-tower")
for i, (z0, h, r0, r1) in enumerate([(0.0, 0.16, 0.026, 0.016), (0.16, 0.14, 0.016, 0.011), (0.3, 0.1, 0.011, 0.007)]):
    seg = k.cylinder(f"tv-shaft-{i}", r0, h, segs=3, r_top=r1, material=white, parent=tv, smooth=False)
    stand(seg, *TV, extra=z0)
for i, (z, r) in enumerate([(0.14, 0.03), (0.2, 0.024), (0.29, 0.02)]):
    stand(k.cylinder(f"tv-deck-{i}", r, 0.016, segs=16, material=white, parent=tv), *TV, extra=z)
    stand(k.cylinder(f"tv-deck-win-{i}", r + 0.001, 0.006, segs=16, material=glow, parent=tv), *TV, extra=z + 0.005)
stand(k.cylinder("tv-antenna", 0.004, 0.09, segs=6, material=cabin_red, parent=tv), *TV, extra=0.4)
for leg in range(3):
    a = 2 * math.pi * leg / 3
    stand(k.tube(f"tv-strut-{leg}", [(0.06 * math.cos(a), 0.06 * math.sin(a), 0.0), (0.01 * math.cos(a), 0.01 * math.sin(a), 0.12)],
                 0.004, material=white, segs=4, parent=tv), *TV)

FW = (0.31, 0.21)
fw = k.empty("OBJ-ferris-wheel")
R_W = 0.07
ZW = ground(*FW) + R_W + 0.02
k.torus("fw-rim", R_W, 0.0035, rot=(90, 0, 25), at=(FW[0], FW[1], ZW), material=wheel_m, parent=fw)
spokes, gondolas = [], []
for i in range(12):
    a = 2 * math.pi * i / 12
    p = Vector((R_W * math.cos(a), 0, R_W * math.sin(a)))
    spokes.append(k.tube(f"fw-spoke-{i}", [(0, 0, 0), tuple(p)], 0.0012, material=wheel_m, segs=3))
    g = k.box(f"fw-gondola-{i}", (0.012, 0.012, 0.012), at=(p.x, p.y, p.z - 0.012), material=[cabin_red, glow, glass_teal][i % 3])
    gondolas.append(g)
for o in spokes + gondolas:
    o.data.transform(Matrix.Translation((FW[0], FW[1], ZW)) @ Matrix.Rotation(math.radians(25), 4, "Z"))
    o.parent = fw
for dx in (-0.03, 0.03):
    leg = k.tube(f"fw-leg-{dx}", [(dx, 0.02, -R_W - 0.02), (0, 0, 0)], 0.003, material=wheel_m, segs=4, parent=fw)
    leg.data.transform(Matrix.Translation((FW[0], FW[1], ZW)) @ Matrix.Rotation(math.radians(25), 4, "Z"))

UP = Vector((0.12, 0.22))      # upper station, beside (not on) the TV tower
LO = Vector((-0.4, -0.2))      # lower station, down in the city
station_h = 0.06
cc = k.empty("OBJ-cable-car")
axis = (UP - LO).normalized()
ang = math.degrees(math.atan2(axis.y, axis.x))
for name, P in (("upper", UP), ("lower", LO)):
    st = k.box(f"cc-{name}-station", (0.075, 0.06, station_h), material=cream, parent=cc)
    stand(st, P.x, P.y, rot=ang)
    rf = k.box(f"cc-{name}-roof", (0.085, 0.07, 0.01), material=cabin_red, parent=cc)
    stand(rf, P.x, P.y, rot=ang, extra=station_h)
    wn = k.box(f"cc-{name}-windows", (0.077, 0.062, 0.014), material=glow, parent=cc)
    stand(wn, P.x, P.y, rot=ang, extra=0.025)

# Two cables (up line, down line) with a gentle sag, on two pylons.
A = Vector((LO.x, LO.y, ground(*LO) + station_h - 0.006))
B = Vector((UP.x, UP.y, ground(*UP) + station_h - 0.006))
SAG = 0.035
side = Vector((-axis.y, axis.x, 0)) * 0.014


def cable_point(t, off):
    p = A.lerp(B, t) + off
    p.z -= SAG * 4 * t * (1 - t)
    return p


for li, off in enumerate((side, -side)):
    k.tube(f"cc-cable-{li}", [tuple(cable_point(i / 40, off)) for i in range(41)], 0.0012,
           material=dark, segs=3, parent=cc)
for pi_, t in enumerate((0.38, 0.7)):
    c = cable_point(t, Vector((0, 0, 0)))
    gz = ground(c.x, c.y)
    k.cylinder(f"cc-pylon-{pi_}", 0.006, c.z - gz + 0.004, at=(c.x, c.y, gz), segs=6, material=steel, parent=cc)
    arm = k.box(f"cc-pylon-arm-{pi_}", (0.008, 0.036, 0.006), material=steel, parent=cc)
    arm.data.transform(Matrix.Translation((c.x, c.y, c.z + 0.002)) @ Matrix.Rotation(math.radians(ang), 4, "Z"))

# Cabins: each is an empty the viewer slides along its line. Up line goes
# A->B, down line B->A; phases spread them out along the cable.
N_CABINS = 4
PERIOD = 28.0
for li, (off, frm, to) in enumerate(((side, A, B), (-side, B, A))):
    for n in range(N_CABINS):
        cab = k.empty(f"cc-cabin-{li}-{n}", parent=cc)
        start = frm + off
        cab.location = start
        delta = (to + off) - start
        cab["shuttle"] = [delta.x, delta.y, delta.z]   # Blender axes; the viewer converts
        cab["period"] = PERIOD
        cab["phase"] = n / N_CABINS
        cab["sag"] = SAG
        body = k.box(f"cabin-{li}-{n}", (0.016, 0.014, 0.016), at=(0, 0, -0.03), material=cabin_red, parent=cab)
        win = k.box(f"cabin-win-{li}-{n}", (0.017, 0.015, 0.006), at=(0, 0, -0.022), material=glow, parent=cab)
        hang = k.cylinder(f"cabin-hanger-{li}-{n}", 0.0012, 0.014, at=(0, 0, -0.014), segs=3, material=dark, parent=cab)
        for o in (body, win, hang):
            o.data.transform(Matrix.Rotation(math.radians(ang), 4, "Z"))


# ---- Hotel Kazakhstan --------------------------------------------------------
HK = (-0.52, 0.02)
hk = k.empty("OBJ-hotel-kazakhstan")
stand(k.box("hk-tower", (0.13, 0.09, 0.44), material=gold, parent=hk), *HK, rot=-15)
for b in range(14):
    stand(k.box(f"hk-floor-{b}", (0.132, 0.092, 0.006), material=glow, parent=hk), *HK, rot=-15, extra=0.03 + b * 0.029)
for rib in range(7):
    o = k.box(f"hk-rib-{rib}", (0.006, 0.094, 0.44), at=(-0.06 + rib * 0.02, 0, 0), material=cream, parent=hk)
    stand(o, *HK, rot=-15)
# The crown: a row of spikes along the top.
crown = []
for i in range(9):
    sp = k.cylinder(f"hk-spike-{i}", 0.008, 0.05, segs=4, r_top=0.0, material=crown_m, smooth=False)
    sp.data.transform(Matrix.Translation((-0.06 + i * 0.015, 0, 0.44)))
    crown.append(sp)
c = k.join("hk-crown", crown)
c.parent = hk
stand(c, *HK, rot=-15)


# ---- Al-Farabi glass: Esentai Tower and its neighbours -----------------------
glass = k.empty("OBJ-al-farabi")
for i, (x, y, w, d, h, m, slant) in enumerate([
        (0.0, -0.3, 0.09, 0.08, 0.5, glass_blue, 0.08),     # Esentai: tallest, slanted crown
        (0.12, -0.24, 0.08, 0.07, 0.32, glass_teal, 0.04),
        (-0.11, -0.38, 0.07, 0.07, 0.24, glass_blue, 0.03)]):
    t = k.box(f"af-tower-{i}", (w, d, h), material=m, parent=glass)
    # Slant the roof: lift the back edge.
    for v in t.data.vertices:
        if v.co.z > h - 1e-4:
            v.co.z += slant * (v.co.y / d + 0.5)
    stand(t, x, y, rot=20)
    for b in range(int(h / 0.05)):
        stand(k.box(f"af-band-{i}-{b}", (w + 0.002, d + 0.002, 0.004), material=glow, parent=glass), x, y, rot=20,
              extra=0.03 + b * 0.05)


# ---- Nurly Tau ---------------------------------------------------------------
nt = k.empty("OBJ-nurly-tau")
for i, (dx, dy, h) in enumerate([(0, 0, 0.36), (0.075, 0.03, 0.3), (-0.07, 0.035, 0.27), (0.02, 0.08, 0.22)]):
    t = k.box(f"nt-tower-{i}", (0.06, 0.06, h), material=glass_teal, parent=nt)
    for v in t.data.vertices:
        if v.co.z > h - 1e-4:
            v.co.z += 0.05 * (v.co.x / 0.06 + 0.5)        # the sloped tops it is known for
    stand(t, 0.4 + dx, -0.06 + dy, rot=-10)
    for b in range(int(h / 0.05)):
        stand(k.box(f"nt-band-{i}-{b}", (0.062, 0.062, 0.004), material=glow, parent=nt), 0.4 + dx, -0.06 + dy,
              rot=-10, extra=0.03 + b * 0.05)


# ---- First President's Park: the gate ---------------------------------------
PG = (0.5, -0.45)
gate = k.empty("OBJ-first-presidents-park")
gparts = []
for sx in (-1, 1):
    gparts.append(k.box(f"pg-pylon-{sx}", (0.035, 0.035, 0.2), at=(sx * 0.085, 0, 0), material=gate_gold, parent=gate))
gparts.append(k.box("pg-lintel", (0.21, 0.04, 0.03), at=(0, 0, 0.2), material=gate_gold, parent=gate))
for i in range(6):
    gparts.append(k.box(f"pg-grille-{i}", (0.006, 0.006, 0.17), at=(-0.05 + i * 0.02, 0, 0.03), material=gate_gold, parent=gate))
gparts.append(k.box("pg-grille-bar", (0.14, 0.006, 0.006), at=(0, 0, 0.12), material=gate_gold, parent=gate))
gparts.append(k.box("pg-plaza", (0.3, 0.22, 0.006), at=(0, -0.06, 0), material=paving, parent=gate))
gparts.append(k.cylinder("pg-fountain", 0.045, 0.014, at=(0, -0.11, 0.004), segs=24, material=paving, parent=gate))
gparts.append(k.cylinder("pg-fountain-water", 0.038, 0.004, at=(0, -0.11, 0.016), segs=24, material=water, parent=gate))
for o in gparts:
    stand(o, *PG, rot=30)


# ---- Home, in Kaskelen -------------------------------------------------------
HM = (-0.44, -0.56)
home = k.empty("OBJ-home")
hparts = [k.box("home-body", (0.16, 0.1, 0.1), material=house_y, parent=home),
          k.box("home-wing", (0.07, 0.07, 0.07), at=(0.105, -0.01, 0), material=house_y, parent=home),
          k.box("home-garage", (0.05, 0.003, 0.045), at=(0.105, -0.046, 0), material=win_blue, parent=home),
          k.box("home-door", (0.02, 0.003, 0.04), at=(-0.02, -0.0515, 0), material=dark, parent=home)]
for i, (x, z) in enumerate([(-0.055, 0.015), (0.03, 0.015), (-0.055, 0.06), (0.0, 0.06), (0.05, 0.06)]):
    hparts.append(k.box(f"home-win-{i}", (0.022, 0.003, 0.022), at=(x, -0.0515, z), material=win_blue, parent=home))
roof = k.cylinder("home-roof", 0.11, 0.045, segs=4, r_top=0.03, material=roof_red, parent=home, smooth=False)
roof.data.transform(Matrix.Translation((0, 0, 0.1)) @ Matrix.Diagonal((1.05, 0.66, 1, 1)) @ Matrix.Rotation(math.radians(45), 4, "Z"))
hparts.append(roof)
wroof = k.cylinder("home-wing-roof", 0.055, 0.03, segs=4, r_top=0.0, material=roof_red, parent=home, smooth=False)
wroof.data.transform(Matrix.Translation((0.105, -0.01, 0.07)) @ Matrix.Rotation(math.radians(45), 4, "Z"))
hparts.append(wroof)
# The pool: rectangular, beside the house, in a paved surround.
hparts.append(k.box("home-pool-deck", (0.12, 0.08, 0.004), at=(0.0, -0.13, 0), material=paving, parent=home))
hparts.append(k.box("home-pool", (0.09, 0.05, 0.005), at=(0.0, -0.13, 0.001), material=water, parent=home))
for o in hparts:
    stand(o, *HM, rot=-12)


# ---- apple trees, and apples, in the gaps ------------------------------------
keep = [(HK[0], HK[1], 0.11), (0.0, -0.3, 0.08), (0.12, -0.24, 0.07), (-0.11, -0.38, 0.07), (0.42, -0.04, 0.12),
        (PG[0], PG[1] - 0.04, 0.17), (HM[0], HM[1] - 0.05, 0.15), (LO.x, LO.y, 0.07)]
# Keep the cable car's corridor clear.
keep += [((LO + (UP - LO) * (i / 10)).x, (LO + (UP - LO) * (i / 10)).y, 0.05) for i in range(11)]
rnd = random.Random(31)
trees, fruit = [], []
spots = []
tries = 0
while len(spots) < 60 and tries < 8000:
    tries += 1
    a, d = rnd.uniform(0, 2 * math.pi), 0.93 * math.sqrt(rnd.random())
    x, y = d * math.cos(a), d * math.sin(a)
    if ground(x, y) > 0.03:          # orchards on the flat, not the mountain
        continue
    if any((x - kx) ** 2 + (y - ky) ** 2 < kr ** 2 for kx, ky, kr in keep):
        continue
    if any((x - sx) ** 2 + (y - sy) ** 2 < 0.075 ** 2 for sx, sy in spots):
        continue
    spots.append((x, y))
for i, (x, y) in enumerate(spots):
    h = rnd.uniform(0.07, 0.1)
    z = ground(x, y)
    trees.append(k.cylinder(f"at-trunk-{i}", 0.006, h * 0.5, at=(x, y, z), segs=6, material=trunk))
    trees.append(k.sphere(f"at-crown-{i}", h * 0.4, at=(x, y, z + h * 0.72), material=leaf, subdiv=2))
    for j in range(5):
        aa = rnd.uniform(0, 2 * math.pi)
        el = rnd.uniform(-0.3, 0.8)
        rr = h * 0.4
        fruit.append(k.sphere(f"at-apple-{i}-{j}", 0.0055, material=apple, subdiv=1,
                              at=(x + rr * math.cos(aa) * math.cos(el), y + rr * math.sin(aa) * math.cos(el),
                                  z + h * 0.72 + rr * math.sin(el))))
    if i % 3 == 0:   # a windfall or two on the grass
        fruit.append(k.sphere(f"at-fallen-{i}", 0.0055, at=(x + 0.03, y - 0.015, z + 0.005), material=apple, subdiv=1))
k.join("DECO-apple-trees", trees)
k.join("DECO-apples", fruit)

k.export("almaty")
