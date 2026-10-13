"""
pattaya.py — the Pattaya diorama. The Gulf of Thailand on the west, Pattaya
Beach along it, Koh Lan offshore with ferries and speedboats running out,
and a loop road round the city with tuk-tuks driving it. Inside the loop:
Terminal 21 (its runway forecourt and the airliner taking off) and the
Runway night market round its Boeing 747. Outside: Ramayana water park
and Khao Kheow Open Zoo with Moo Deng.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python scripts/blender/pattaya.py

Reference points (looked up): Runway Street Food is a night market on
Second Road round a retired Orient Thai Boeing 747, tables under its wings;
Terminal 21 Pattaya is airport-themed, its forecourt a runway with an
airliner taking off over a made-up beach; Ramayana is Thailand's largest
water park, its centrepiece Hanuman's Splash, a water fortress of slides
with a giant tipping bucket, plus a lazy river and a wave pool; Khao
Kheow's star is Moo Deng, the baby pygmy hippo, with giraffes, zebras and
flamingos; Koh Lan's Tawaen Beach is reached by ferry or speedboat from
Bali Hai Pier.

Day/night: `nightglow-*` materials (market lights, hotel windows, the
loop's street lamps) light up when the viewer switches to night.
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

sea = k.mat("gulf-sea", (0.24, 0.58, 0.74))
sea_side = k.mat("sea-deep", (0.18, 0.44, 0.60))
sand = k.mat("beach-sand", (0.96, 0.88, 0.68))
ground_m = k.mat("city-ground", (0.80, 0.78, 0.72))
grass = k.mat("grass", (0.48, 0.68, 0.40))
road_m = k.mat("asphalt", (0.34, 0.34, 0.38))
paint = k.mat("road-white", (0.95, 0.95, 0.92))
pool = k.mat("pool-blue", (0.30, 0.74, 0.92))
white = k.mat("white", (0.96, 0.96, 0.96))
dark = k.mat("dark", (0.16, 0.16, 0.20))
glow = k.mat("nightglow-windows", (1.0, 0.86, 0.56))
market_lights = [k.mat(n, c) for n, c in [("nightglow-bulb-warm", (1.0, 0.82, 0.4)), ("nightglow-bulb-pink", (1.0, 0.5, 0.7)),
                                           ("nightglow-bulb-cyan", (0.4, 0.9, 1.0))]]
awn = [k.mat(n, c) for n, c in [("awning-red", (0.84, 0.22, 0.20)), ("awning-blue", (0.22, 0.42, 0.80)),
                                 ("awning-yellow", (0.98, 0.80, 0.22)), ("awning-green", (0.22, 0.62, 0.40))]]
umbr = [k.mat(n, c) for n, c in [("umbrella-blue", (0.20, 0.50, 0.90)), ("umbrella-orange", (1.0, 0.56, 0.16)),
                                  ("umbrella-pink", (0.98, 0.46, 0.68)), ("umbrella-green", (0.30, 0.74, 0.46))]]
palm_trunk = k.mat("palm-trunk", (0.60, 0.48, 0.34))
palm_leaf = k.mat("palm-leaf", (0.28, 0.60, 0.30))
coconut = k.mat("coconut", (0.42, 0.32, 0.18))
hotel = [k.mat(n, c) for n, c in [("hotel-white", (0.94, 0.94, 0.92)), ("hotel-sand", (0.90, 0.84, 0.72)), ("hotel-blue", (0.64, 0.76, 0.88))]]
jungle = k.mat("island-jungle", (0.30, 0.54, 0.32))
orient_red = k.mat("orient-red", (0.86, 0.20, 0.16))
orient_gold = k.mat("orient-gold", (0.98, 0.70, 0.20))
t21_blue = k.mat("t21-blue", (0.16, 0.36, 0.72))
slides = [k.mat(n, c) for n, c in [("slide-yellow", (0.99, 0.82, 0.18)), ("slide-red", (0.92, 0.24, 0.22)),
                                    ("slide-blue", (0.20, 0.50, 0.92)), ("slide-green", (0.24, 0.74, 0.40)),
                                    ("slide-purple", (0.60, 0.36, 0.84))]]
fortress = k.mat("fortress-stone", (0.86, 0.68, 0.40))
tuk_cols = [k.mat("tuktuk-blue", (0.12, 0.36, 0.82)), k.mat("tuktuk-red", (0.86, 0.14, 0.14)), k.mat("tuktuk-green", (0.14, 0.62, 0.32))]

# ---- the plinth is the sea; the land sits on it to the east -------------------
k.base(sea, sea_side)


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def shore_x(y):
    """Pattaya Bay: a crescent shore down the west of the land."""
    return -0.3 + 0.1 * (y / 0.8) ** 2 + 0.02 * math.sin(4 * y)


ZOO = (0.5, 0.52)
G = 0.02


def height(x, y):
    r = math.hypot(x, y)
    d = x - shore_x(y)
    if d < 0:
        return -0.006
    h = G * smoothstep(0.0, 0.06, d)
    return h * (1 - smoothstep(0.9, 0.99, r))


RINGS, SEGS = 56, 200
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
for m in (ground_m, sand, sea, grass):
    land.data.materials.append(m)
for p in land.data.polygons:
    c = p.center
    d = c.x - shore_x(c.y)
    if d < 0:
        p.material_index = 2
    elif d < 0.08:
        p.material_index = 1
    elif math.hypot(c.x - ZOO[0], c.y - ZOO[1]) < 0.26 or math.hypot(c.x, c.y) > 0.86:
        p.material_index = 3
    else:
        p.material_index = 0
    p.use_smooth = True
k.smooth_by_angle(land, 40)


def stand(o, x, y, rot=0.0, extra=0.0):
    o.data.transform(Matrix.Translation((x, y, height(x, y) + extra)) @ Matrix.Rotation(math.radians(rot), 4, "Z"))
    return o


def place(parts, x, y, rot=0.0, extra=0.0):
    for o in parts:
        stand(o, x, y, rot=rot, extra=extra)
    return parts


def mover(name, start, end, period, phase=0.0, bob=0.0, bob_hz=1.5, parent=None):
    e = k.empty(name, parent=parent)
    e.location = start
    d = Vector(end) - Vector(start)
    e.rotation_euler = (0, 0, math.atan2(d.y, d.x))
    e["shuttle"] = [d.x, d.y, d.z]
    e["period"] = period
    e["phase"] = phase
    e["pingpong"] = 1
    if bob:
        e["bob"] = bob
        e["bobHz"] = bob_hz
    return e


# ---- airliners -------------------------------------------------------------------
def airliner(tag, parent, L, body, stripe, tail, hump=False, four_engines=False):
    """An airliner at the origin, nose toward +X: fuselage, nose and tail
    cone, swept wings, tailplane and fin, engines, cockpit and windows."""
    r = L * 0.06
    p = []
    fus = k.cylinder(f"{tag}-fuselage", r, L * 0.72, segs=20, material=body, parent=parent)
    fus.data.transform(Matrix.Rotation(math.radians(90), 4, "Y") @ Matrix.Translation((0, 0, -L * 0.36)))
    p.append(fus)
    nose = k.sphere(f"{tag}-nose", 1.0, material=body, parent=parent, subdiv=3)
    nose.data.transform(Matrix.Translation((L * 0.36, 0, 0)) @ Matrix.Diagonal((r * 2.0, r, r, 1)))
    for v in nose.data.vertices:
        v.co.x = max(v.co.x, L * 0.36)
    p.append(nose)
    tc = k.cylinder(f"{tag}-tailcone", r, L * 0.2, r_top=r * 0.25, segs=20, material=body, parent=parent)
    tc.data.transform(Matrix.Translation((-L * 0.36, 0, r * 0.25)) @ Matrix.Rotation(math.radians(-90), 4, "Y"))
    p.append(tc)
    if hump:   # the 747's upper deck
        hm = k.sphere(f"{tag}-hump", 1.0, material=body, parent=parent, subdiv=3)
        hm.data.transform(Matrix.Translation((L * 0.2, 0, r * 0.55)) @ Matrix.Diagonal((L * 0.2, r * 0.8, r * 0.8, 1)))
        p.append(hm)
    p.append(k.box(f"{tag}-stripe", (L * 0.72, r * 2.02, r * 0.25), at=(0, 0, -r * 0.2), material=stripe, parent=parent))
    p.append(k.box(f"{tag}-windows", (L * 0.6, r * 2.04, r * 0.16), at=(0, 0, r * 0.25), material=glow, parent=parent))
    p.append(k.box(f"{tag}-cockpit", (r * 0.6, r * 1.4, r * 0.35), at=(L * 0.45, 0, r * 0.3), material=dark, parent=parent))
    for s in (-1, 1):
        wing = k.prism(f"{tag}-wing{s}", [(L * 0.14, 0), (-L * 0.06, 0), (-L * 0.2, s * L * 0.46), (-L * 0.12, s * L * 0.46)], r * 0.18, material=body, parent=parent)
        wing.data.transform(Matrix.Translation((0, 0, -r * 0.4)))
        p.append(wing)
        tp = k.prism(f"{tag}-tailplane{s}", [(-L * 0.4, 0), (-L * 0.48, 0), (-L * 0.56, s * L * 0.16), (-L * 0.5, s * L * 0.16)], r * 0.12, material=body, parent=parent)
        tp.data.transform(Matrix.Translation((0, 0, r * 0.2)))
        p.append(tp)
        for e in ((0.18, 0.32) if four_engines else (0.22,)):
            eng = k.cylinder(f"{tag}-engine{s}{e}", r * 0.38, L * 0.12, segs=14, material=body, parent=parent)
            eng.data.transform(Matrix.Translation((L * 0.02 - e * L * 0.18, s * e * L, -r * 0.85)) @ Matrix.Rotation(math.radians(90), 4, "Y")
                               @ Matrix.Translation((0, 0, -L * 0.06)))
            p.append(eng)
    fin = k.prism(f"{tag}-fin", [(-L * 0.36, 0), (-L * 0.5, 0), (-L * 0.56, L * 0.2), (-L * 0.48, L * 0.2)], r * 0.14, material=tail, parent=parent)
    fin.data.transform(Matrix.Translation((0, r * 0.07, r * 0.6)) @ Matrix.Rotation(math.radians(90), 4, "X"))
    p.append(fin)
    return p


# ---- the loop road, and the tuk-tuks driving it --------------------------------
LOOP_C, LOOP_R = Vector((0.25, -0.02)), 0.42
loop = [(LOOP_C.x + LOOP_R * math.cos(2 * math.pi * i / 96), LOOP_C.y + LOOP_R * math.sin(2 * math.pi * i / 96)) for i in range(97)]
road = k.ribbon("DECO-loop-road", loop, 0.06, z=G + 0.002, material=road_m, clip=0.99)
for v in road.data.vertices:
    v.co.z = height(v.co.x, v.co.y) + 0.002
marks, lamps = [], []
for i in range(48):
    a = 2 * math.pi * i / 48
    x, y = LOOP_C.x + LOOP_R * math.cos(a), LOOP_C.y + LOOP_R * math.sin(a)
    mk = k.box(f"mark-{i}", (0.02, 0.004, 0.001), material=paint)
    mk.data.transform(Matrix.Translation((x, y, height(x, y) + 0.003)) @ Matrix.Rotation(a + math.pi / 2, 4, "Z"))
    marks.append(mk)
    if i % 4 == 0:   # street lamps along the outside of the loop
        lx, ly = LOOP_C.x + (LOOP_R + 0.04) * math.cos(a), LOOP_C.y + (LOOP_R + 0.04) * math.sin(a)
        lamps.append(k.cylinder(f"lamp-post-{i}", 0.0015, 0.04, at=(lx, ly, height(lx, ly)), segs=4, material=dark))
        lamps.append(k.sphere(f"lamp-{i}", 0.004, at=(lx, ly, height(lx, ly) + 0.042), material=market_lights[0], subdiv=1))
k.join("DECO-road-marks", marks)
k.join("DECO-street-lamps", lamps)

tuks = k.empty("OBJ-tuk-tuks")
for i, (start, orbit) in enumerate([(0, 26.0), (120, 30.0), (230, 23.0)]):
    t = k.empty(f"tuktuk-{i}", parent=tuks)
    t.location = (LOOP_C.x, LOOP_C.y, G)
    t["orbit"] = orbit
    col = tuk_cols[i % 3]
    a = math.radians(start)
    # Built at the loop's edge, facing along the road (anticlockwise), then turned to its start angle.
    R = LOOP_R - 0.012 * (i % 2)
    parts = [k.box(f"tuk{i}-cab", (0.018, 0.03, 0.016), at=(R, -0.004, 0.006), material=col, parent=t),
             k.box(f"tuk{i}-roof", (0.022, 0.036, 0.003), at=(R, -0.002, 0.026), material=col, parent=t),
             k.box(f"tuk{i}-seat", (0.016, 0.012, 0.008), at=(R, -0.012, 0.008), material=k.mat("tuk-seat", (0.9, 0.85, 0.6)), parent=t),
             k.box(f"tuk{i}-nose", (0.01, 0.012, 0.012), at=(R, 0.016, 0.006), material=col, parent=t),
             k.box(f"tuk{i}-light", (0.006, 0.002, 0.004), at=(R, 0.0225, 0.012), material=market_lights[0], parent=t)]
    for px in (-0.009, 0.009):
        parts.append(k.cylinder(f"tuk{i}-post{px}", 0.001, 0.014, at=(R + px, -0.016, 0.012), segs=4, material=dark, parent=t))
    for wx, wy in ((-0.009, -0.012), (0.009, -0.012), (0.0, 0.018)):
        w_ = k.cylinder(f"tuk{i}-wheel{wx}{wy}", 0.0045, 0.003, segs=10, material=dark, parent=t)
        w_.data.transform(Matrix.Translation((R + wx, wy, 0.0045)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
        parts.append(w_)
    for o in parts:
        # Local to the empty: shift so the empty sits at the loop's centre.
        o.data.transform(Matrix.Rotation(a, 4, "Z"))


# ---- Pattaya Beach: umbrellas, deckchairs, palms; beach-road hotels -----------
beach = k.empty("OBJ-pattaya-beach")
bparts = []
rnd = random.Random(3)
for i in range(22):
    y = -0.64 + i * 0.06
    x = shore_x(y) + 0.035
    if math.hypot(x, y) > 0.9:
        continue
    z = height(x, y)
    bparts.append(k.cylinder(f"umb-pole{i}", 0.0012, 0.03, at=(x, y, z), segs=4, material=white, parent=beach))
    bparts.append(k.cylinder(f"umb{i}", 0.018, 0.008, at=(x, y, z + 0.028), r_top=0.0, segs=8, material=umbr[i % 4], parent=beach, smooth=False))
    for s in (-1, 1):
        ch = k.box(f"chair{i}{s}", (0.012, 0.006, 0.003), at=(x - 0.006, y + s * 0.012, z + 0.002), material=white, parent=beach)
        bparts.append(ch)
for i in range(16):
    y = -0.66 + i * 0.085
    x = shore_x(y) + 0.07
    if math.hypot(x, y) > 0.9:
        continue
    for o in k.palm(f"beach-palm{i}", x, y, height(x, y), rnd.uniform(0.08, 0.1), palm_trunk, palm_leaf, fruit_mat=coconut, seed=i, parent=beach):
        bparts.append(o)
# Beach Road hotels, a tidy row just inland, windows that light at night.
hotels = []
for i in range(9):
    y = -0.5 + i * 0.12
    x = shore_x(y) + 0.14
    if math.hypot(x, y) > 0.86 or math.hypot(x - LOOP_C.x, y - LOOP_C.y) < LOOP_R + 0.05:
        continue
    h = rnd.uniform(0.1, 0.2)
    hotels.append(stand(k.box(f"hotel{i}", (0.04, 0.05, h), material=hotel[i % 3]), x, y))
    for b in range(int(h / 0.022)):
        hotels.append(stand(k.box(f"hotel{i}-win{b}", (0.042, 0.052, 0.004), material=glow), x, y, extra=0.012 + b * 0.022))
if hotels:
    k.join("DECO-beach-road-hotels", hotels)


# ---- Koh Lan offshore, Tawaen beach, and the boats out to it -------------------
KL = Vector((-0.62, 0.34))
koh = k.empty("OBJ-koh-lan")
isl = k.lathe("koh-lan-hill", [(0.17, -0.006), (0.15, 0.012), (0.1, 0.05), (0.04, 0.08), (0.0, 0.085)], segs=36,
              at=(KL.x, KL.y, 0.0), material=jungle, parent=koh)
for v in isl.data.vertices:
    a = math.atan2(v.co.y - KL.y, v.co.x - KL.x)
    rr = 1 + 0.12 * math.sin(3 * a + 1) + 0.06 * math.sin(7 * a)
    v.co.x = KL.x + (v.co.x - KL.x) * rr
    v.co.y = KL.y + (v.co.y - KL.y) * rr * 0.8
k.smooth_by_angle(isl, 50)
# Tawaen beach: a sandy crescent on the side facing Pattaya.
tw = k.lathe("koh-lan-tawaen", [(0.07, -0.006), (0.065, 0.004), (0.0, 0.004)], segs=24, at=(KL.x + 0.13, KL.y - 0.05, 0.0), material=sand, parent=koh)
tw.data.transform(Matrix.Translation((KL.x + 0.13, KL.y - 0.05, 0)) @ Matrix.Diagonal((0.5, 1.0, 1, 1)) @ Matrix.Translation((-(KL.x + 0.13), -(KL.y - 0.05), 0)))
for i in range(5):
    x, y = KL.x + 0.14, KL.y - 0.1 + i * 0.024
    k.cylinder(f"tw-umb-pole{i}", 0.0012, 0.022, at=(x, y, 0.002), segs=4, material=white, parent=koh)
    k.cylinder(f"tw-umb{i}", 0.012, 0.006, at=(x, y, 0.022), r_top=0.0, segs=8, material=umbr[i % 4], parent=koh, smooth=False)
for i in range(6):
    a = 2 * math.pi * i / 6 + 0.4
    x, y = KL.x + 0.07 * math.cos(a), KL.y + 0.05 * math.sin(a)
    for o in k.palm(f"kl-palm{i}", x, y, 0.05, 0.06, palm_trunk, palm_leaf, seed=40 + i, parent=koh):
        pass
# Bali Hai Pier at the south end of the bay.
PIER = Vector((shore_x(-0.5) - 0.02, -0.5))
k.box("DECO-bali-hai-pier", (0.16, 0.022, 0.006), at=(PIER.x - 0.06, PIER.y, -0.004), material=k.mat("pier-concrete", (0.80, 0.80, 0.80)))
boats = k.empty("OBJ-ferries-to-koh-lan")
dest = Vector((KL.x + 0.15, KL.y - 0.05))
for i, (kind, ph, off) in enumerate([("ferry", 0.0, 0.0), ("speed", 0.3, 0.03), ("speed", 0.75, -0.03)]):
    a = Vector((PIER.x - 0.13, PIER.y + off, 0.0))
    b = Vector((dest.x + 0.02, dest.y + off, 0.0))
    bt = mover(f"{kind}-{i}", a, b, 26.0 if kind == "ferry" else 12.0, phase=ph, bob=0.002, bob_hz=0.8, parent=boats)
    if kind == "ferry":
        h = k.box(f"ferry{i}-hull", (0.06, 0.022, 0.01), at=(0, 0, -0.002), material=white, parent=bt)
        k.box(f"ferry{i}-deck", (0.04, 0.018, 0.012), at=(-0.004, 0, 0.008), material=k.mat("ferry-blue", (0.2, 0.42, 0.78)), parent=bt)
        k.box(f"ferry{i}-roof", (0.044, 0.02, 0.002), at=(-0.004, 0, 0.02), material=white, parent=bt)
    else:
        h = k.box(f"speed{i}-hull", (0.034, 0.012, 0.006), at=(0, 0, -0.001), material=white, parent=bt)
        k.box(f"speed{i}-stripe", (0.034, 0.0125, 0.002), at=(0, 0, 0.0), material=orient_red, parent=bt)
        k.box(f"speed{i}-canopy", (0.012, 0.01, 0.002), at=(-0.004, 0, 0.012), material=umbr[i % 4], parent=bt)
    for v in h.data.vertices:
        if v.co.x > 0.012:
            v.co.y *= 0.35


# ---- Terminal 21: a terminal building, a runway forecourt, an airliner climbing
T21 = (0.18, 0.16)
t21 = k.empty("OBJ-terminal-21")
tparts = [k.box("t21-building", (0.24, 0.1, 0.07), at=(0, 0.04, 0), material=white, parent=t21),
          k.box("t21-glass", (0.22, 0.003, 0.05), at=(0, -0.0115, 0.01), material=k.mat("terminal-glass", (0.55, 0.75, 0.92)), parent=t21),
          k.box("t21-sign", (0.12, 0.004, 0.012), at=(0, -0.013, 0.058), material=t21_blue, parent=t21),
          k.box("t21-control-tower", (0.02, 0.02, 0.13), at=(0.1, 0.06, 0), material=white, parent=t21),
          k.cylinder("t21-tower-cab", 0.018, 0.016, at=(0.1, 0.06, 0.13), r_top=0.022, segs=8, material=k.mat("tower-cab-glass", (0.5, 0.75, 0.95)), parent=t21, smooth=False),
          k.box("t21-runway", (0.26, 0.06, 0.002), at=(0, -0.05, 0), material=road_m, parent=t21),
          k.box("t21-beach", (0.26, 0.03, 0.002), at=(0, -0.095, 0), material=sand, parent=t21)]
for i in range(10):
    tparts.append(k.box(f"t21-runway-mark{i}", (0.014, 0.004, 0.001), at=(-0.11 + i * 0.024, -0.05, 0.002), material=paint, parent=t21))
for i in range(6):
    tparts.append(k.box(f"t21-windows{i}", (0.242, 0.102, 0.004), at=(0, 0.04, 0.012 + i * 0.01), material=glow, parent=t21))
plane = airliner("t21-plane", t21, 0.16, white, t21_blue, t21_blue)
for o in plane:
    # Climbing out over the forecourt's beach, nose up.
    o.data.transform(Matrix.Translation((0.0, -0.06, 0.09)) @ Matrix.Rotation(math.radians(-12), 4, "Y"))
tparts += plane
tparts.append(k.cylinder("t21-plane-pylon", 0.004, 0.075, at=(0.0, -0.06, 0.0), segs=6, material=white, parent=t21))
place(tparts, *T21)


# ---- the Runway night market round its Boeing 747 ----------------------------
NM = (0.32, -0.24)
nm = k.empty("OBJ-runway-night-market")
mparts = [k.box("nm-ground", (0.3, 0.2, 0.002), material=k.mat("market-ground", (0.62, 0.62, 0.64)), parent=nm)]
b747 = airliner("nm-747", nm, 0.24, white, orient_red, orient_gold, hump=True, four_engines=True)
for o in b747:
    o.data.transform(Matrix.Translation((0.0, 0.0, 0.034)))
mparts += b747
for sx in (-1, 1):   # it stands on its gear, wheels on the ground
    mparts.append(k.cylinder(f"nm-gear{sx}", 0.003, 0.02, at=(-0.01, sx * 0.03, 0.0), segs=6, material=dark, parent=nm))
mparts.append(k.cylinder("nm-gear-nose", 0.003, 0.022, at=(0.1, 0.0, 0.0), segs=6, material=dark, parent=nm))
# Stalls round it, tables under the wings, strings of bulbs.
for i in range(10):
    side = -1 if i < 5 else 1
    x = -0.12 + (i % 5) * 0.06
    y = side * 0.085
    mparts.append(k.box(f"nm-stall{i}", (0.03, 0.024, 0.018), at=(x, y, 0.002), material=k.mat("stall-wood", (0.58, 0.40, 0.26)), parent=nm))
    mparts.append(k.box(f"nm-awning{i}", (0.036, 0.03, 0.003), at=(x, y, 0.026), material=awn[i % 4], parent=nm))
    mparts.append(k.box(f"nm-food{i}", (0.026, 0.008, 0.003), at=(x, y - side * 0.012, 0.02), material=market_lights[i % 3], parent=nm))
for i in range(8):
    x = -0.06 + i * 0.018
    for sy in (-1, 1):
        mparts.append(k.box(f"nm-table{i}{sy}", (0.012, 0.008, 0.002), at=(x, sy * 0.045, 0.01), material=white, parent=nm))
for sy in (-1, 1):
    for i in range(16):
        mparts.append(k.sphere(f"nm-bulb{sy}{i}", 0.0025, at=(-0.14 + i * 0.019, sy * 0.098, 0.034 + 0.004 * math.sin(i)), material=market_lights[i % 3], parent=nm, subdiv=1))
place(mparts, *NM, rot=-10)


# ---- Ramayana water park: Hanuman's Splash, slides, the lazy river ----------
RW = (0.2, -0.68)
rw = k.empty("OBJ-ramayana-water-park")
rparts = []
rparts.append(k.prism("rw-wave-pool", [(-0.1 + 0.06 * math.cos(a), -0.02 + 0.045 * math.sin(a)) for a in [2 * math.pi * i / 24 for i in range(24)]], 0.003, material=pool, parent=rw))
lazy = [(0.12 * math.cos(2 * math.pi * i / 40), 0.08 * math.sin(2 * math.pi * i / 40)) for i in range(41)]
lr = k.ribbon("rw-lazy-river", lazy, 0.022, z=0.002, material=pool)
lr.parent = rw
rparts.append(lr)
# Hanuman's Splash: a stepped water fortress, slides spiralling off it, the giant bucket on top.
rparts.append(k.box("rw-fortress", (0.07, 0.06, 0.05), at=(0.02, 0.0, 0.0), material=fortress, parent=rw))
rparts.append(k.box("rw-fortress-top", (0.05, 0.045, 0.03), at=(0.02, 0.0, 0.05), material=fortress, parent=rw))
for i in range(4):
    rparts.append(k.box(f"rw-flag{i}", (0.003, 0.003, 0.02), at=(0.02 + (-1) ** i * 0.022, 0.018 * (1 if i < 2 else -1), 0.08), material=slides[i], parent=rw))
rparts.append(k.cylinder("rw-bucket-post", 0.003, 0.04, at=(0.02, 0.0, 0.08), segs=6, material=dark, parent=rw))
bk = k.cylinder("rw-bucket", 0.016, 0.022, at=(0.0, 0.0, 0.0), r_top=0.021, segs=16, material=slides[0], parent=rw)
bk.data.transform(Matrix.Translation((0.03, 0.0, 0.115)) @ Matrix.Rotation(math.radians(25), 4, "Y"))
rparts.append(bk)
for i in range(4):
    rparts.append(k.sphere(f"rw-splash{i}", 0.006, at=(0.045 + i * 0.004, 0.0, 0.11 - i * 0.02), material=pool, parent=rw, subdiv=1))
for s in range(5):
    pts = []
    a0 = 2 * math.pi * s / 5
    for i in range(30):
        t = i / 29
        a = a0 + t * (2.4 + 0.4 * s)
        rr = 0.03 + 0.07 * t
        pts.append((0.02 + rr * math.cos(a), rr * math.sin(a), 0.07 - 0.068 * t + 0.01 * math.sin(6 * t)))
    rparts.append(k.tube(f"rw-slide{s}", pts, 0.0045, material=slides[s % 5], segs=8, parent=rw))
# A towering freefall slide off a tall platform.
rparts.append(k.box("rw-freefall-tower", (0.02, 0.02, 0.12), at=(0.1, 0.05, 0.0), material=slides[2], parent=rw))
rparts.append(k.tube("rw-freefall", [(0.1, 0.04, 0.12), (0.1, 0.01, 0.1), (0.1, -0.02, 0.03), (0.1, -0.05, 0.004)], 0.005, material=slides[1], segs=8, parent=rw))
place(rparts, *RW, rot=15)


# ---- Khao Kheow Open Zoo: Moo Deng, giraffes, zebras, flamingos -------------
zoo = k.empty("OBJ-khao-kheow-zoo")
zp = []
zz = height(*ZOO)
zp.append(k.box("zoo-sign", (0.06, 0.004, 0.016), at=(ZOO[0] - 0.12, ZOO[1] - 0.14, height(ZOO[0] - 0.12, ZOO[1] - 0.14) + 0.02),
                material=k.mat("zoo-sign-green", (0.20, 0.52, 0.30)), parent=zoo))
for sx in (-1, 1):
    zp.append(k.cylinder(f"zoo-sign-post{sx}", 0.0015, 0.026, at=(ZOO[0] - 0.12 + sx * 0.025, ZOO[1] - 0.14, height(ZOO[0] - 0.12, ZOO[1] - 0.14)), segs=4, material=dark, parent=zoo))
# Moo Deng's pool, Moo Deng and her mother Jonah.
MD = Vector((ZOO[0] - 0.06, ZOO[1] - 0.04))
mz = height(*MD)
zp.append(k.cylinder("zoo-hippo-pool", 0.04, 0.004, at=(MD.x, MD.y, mz), segs=24, material=pool, parent=zoo))
hippo = k.mat("pygmy-hippo", (0.42, 0.36, 0.38))
pink = k.mat("hippo-pink", (0.86, 0.56, 0.56))
for name, (dx, sc) in (("jonah", (0.012, 1.0)), ("moo-deng", (-0.03, 0.58))):
    c = Vector((MD.x + dx, MD.y - 0.002, mz + 0.008 * sc))
    body = k.sphere(f"zoo-{name}-body", 1.0, material=hippo, parent=zoo, subdiv=2)
    body.data.transform(Matrix.Translation(c) @ Matrix.Diagonal((0.016 * sc, 0.01 * sc, 0.009 * sc, 1)))
    zp.append(body)
    head = k.sphere(f"zoo-{name}-head", 1.0, material=hippo, parent=zoo, subdiv=2)
    head.data.transform(Matrix.Translation(c + Vector((0.016 * sc, 0, 0.003 * sc))) @ Matrix.Diagonal((0.008 * sc, 0.007 * sc, 0.006 * sc, 1)))
    zp.append(head)
    zp.append(k.sphere(f"zoo-{name}-snout", 0.004 * sc, at=tuple(c + Vector((0.023 * sc, 0, 0.001 * sc))), material=pink, parent=zoo, subdiv=1))
    for ex in (-1, 1):
        zp.append(k.sphere(f"zoo-{name}-ear{ex}", 0.0018 * sc, at=tuple(c + Vector((0.013 * sc, ex * 0.004 * sc, 0.009 * sc))), material=hippo, parent=zoo, subdiv=1))
    for lx in (-0.009, 0.009):
        for ly in (-0.005, 0.005):
            zp.append(k.cylinder(f"zoo-{name}-leg{lx}{ly}", 0.0028 * sc, 0.008 * sc, at=(c.x + lx * sc, c.y + ly * sc, c.z - 0.008 * sc), segs=6, material=hippo, parent=zoo))
# Giraffes.
gir = k.mat("giraffe", (0.94, 0.72, 0.32))
spot = k.mat("giraffe-spots", (0.56, 0.32, 0.16))
for i, (dx, dy) in enumerate(((0.06, 0.04), (0.1, 0.0))):
    x, y = ZOO[0] + dx, ZOO[1] + dy
    z = height(x, y)
    zp.append(k.sphere(f"zoo-giraffe{i}-body", 1.0, material=gir, parent=zoo, subdiv=2))
    zp[-1].data.transform(Matrix.Translation((x, y, z + 0.032)) @ Matrix.Diagonal((0.014, 0.008, 0.009, 1)))
    for lx in (-0.009, 0.009):
        for ly in (-0.004, 0.004):
            zp.append(k.cylinder(f"zoo-giraffe{i}-leg{lx}{ly}", 0.0015, 0.028, at=(x + lx, y + ly, z), segs=5, material=gir, parent=zoo))
    zp.append(k.tube(f"zoo-giraffe{i}-neck", [(x + 0.01, y, z + 0.036), (x + 0.016, y, z + 0.06), (x + 0.02, y, z + 0.075)], 0.003, material=gir, segs=6, parent=zoo))
    zp.append(k.sphere(f"zoo-giraffe{i}-head", 0.005, at=(x + 0.024, y, z + 0.077), material=gir, parent=zoo, subdiv=2))
    for j in range(6):
        zp.append(k.sphere(f"zoo-giraffe{i}-spot{j}", 0.0028, at=(x - 0.008 + j * 0.003, y + (0.0075 if j % 2 else -0.0075), z + 0.032 + 0.002 * (j % 3)), material=spot, parent=zoo, subdiv=1))
# Zebras.
zeb = k.mat("zebra-white", (0.95, 0.95, 0.94))
for i, (dx, dy) in enumerate(((0.0, 0.1), (0.04, 0.12))):
    x, y = ZOO[0] + dx, ZOO[1] + dy
    z = height(x, y)
    b = k.sphere(f"zoo-zebra{i}-body", 1.0, material=zeb, parent=zoo, subdiv=2)
    b.data.transform(Matrix.Translation((x, y, z + 0.016)) @ Matrix.Diagonal((0.013, 0.0065, 0.007, 1)))
    zp.append(b)
    for j in range(5):
        st = k.box(f"zoo-zebra{i}-stripe{j}", (0.002, 0.0135, 0.0145), at=(x - 0.009 + j * 0.0045, y, z + 0.009), material=dark, parent=zoo)
        zp.append(st)
    zp.append(k.sphere(f"zoo-zebra{i}-head", 0.004, at=(x + 0.016, y, z + 0.024), material=zeb, parent=zoo, subdiv=2))
    for lx in (-0.008, 0.008):
        for ly in (-0.003, 0.003):
            zp.append(k.cylinder(f"zoo-zebra{i}-leg{lx}{ly}", 0.0013, 0.012, at=(x + lx, y + ly, z), segs=5, material=zeb, parent=zoo))
# Flamingos in their pond.
FL = Vector((ZOO[0] - 0.14, ZOO[1] + 0.06))
fz = height(*FL)
zp.append(k.cylinder("zoo-flamingo-pond", 0.04, 0.003, at=(FL.x, FL.y, fz), segs=24, material=pool, parent=zoo))
flam = k.mat("flamingo-pink", (0.98, 0.52, 0.62))
for i in range(6):
    a = 2 * math.pi * i / 6
    x, y = FL.x + 0.022 * math.cos(a), FL.y + 0.022 * math.sin(a)
    zp.append(k.cylinder(f"zoo-flamingo{i}-leg", 0.0007, 0.018, at=(x, y, fz), segs=4, material=flam, parent=zoo))
    b = k.sphere(f"zoo-flamingo{i}-body", 1.0, material=flam, parent=zoo, subdiv=1)
    b.data.transform(Matrix.Translation((x, y, fz + 0.021)) @ Matrix.Diagonal((0.006, 0.004, 0.004, 1)))
    zp.append(b)
    zp.append(k.tube(f"zoo-flamingo{i}-neck", [(x + 0.004, y, fz + 0.022), (x + 0.006, y, fz + 0.03), (x + 0.004, y, fz + 0.036)], 0.0012, material=flam, segs=4, parent=zoo))
    zp.append(k.sphere(f"zoo-flamingo{i}-head", 0.0022, at=(x + 0.006, y, fz + 0.037), material=flam, parent=zoo, subdiv=1))
# Zoo trees on the hills.
for i in range(18):
    a, d = rnd.uniform(0, 2 * math.pi), rnd.uniform(0.1, 0.2)
    x, y = ZOO[0] + d * math.cos(a), ZOO[1] + d * math.sin(a)
    if math.hypot(x, y) > 0.9:
        continue
    h = rnd.uniform(0.05, 0.07)
    zp.append(k.cylinder(f"zoo-trunk{i}", 0.004, h * 0.4, at=(x, y, height(x, y)), segs=5, material=k.mat("trunk", (0.38, 0.28, 0.22)), parent=zoo))
    zp.append(k.sphere(f"zoo-crown{i}", h * 0.42, at=(x, y, height(x, y) + h * 0.7), material=k.mat("tree", (0.30, 0.52, 0.32)), parent=zoo, subdiv=2))


# ---- bigger landmarks, each grown about its own footprint --------------------
def grow_in_place(o, f):
    pts = []
    stack = [o]
    while stack:
        x_ = stack.pop()
        if x_.type == "MESH":
            pts += [x_.matrix_world @ v.co for v in x_.data.vertices]
        stack.extend(x_.children)
    cx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2
    cy = (min(p.y for p in pts) + max(p.y for p in pts)) / 2
    k.grow(o, f, (cx, cy, height(cx, cy)))


for o, f in [(rw, 1.6), (zoo, 1.45), (t21, 1.25), (nm, 1.15)]:
    grow_in_place(o, f)


# ---- a few city blocks and palms inside the loop -----------------------------
fill = []
for i in range(20):
    a, d = rnd.uniform(0, 2 * math.pi), rnd.uniform(0.05, LOOP_R - 0.06)
    x, y = LOOP_C.x + d * math.cos(a), LOOP_C.y + d * math.sin(a)
    if math.hypot(x - T21[0], y - T21[1]) < 0.17 or math.hypot(x - NM[0], y - NM[1]) < 0.19:
        continue
    w, h = rnd.uniform(0.026, 0.04), rnd.uniform(0.04, 0.09)
    fill.append(stand(k.box(f"blk{i}", (w, w, h), material=hotel[i % 3]), x, y, rot=rnd.uniform(0, 90)))
    fill.append(stand(k.box(f"blk{i}-win", (w + 0.002, w + 0.002, 0.003), material=glow), x, y, extra=h * 0.6))
if fill:
    k.join("DECO-city-blocks", fill)

k.export("pattaya")
