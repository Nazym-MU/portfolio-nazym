"""
san_francisco.py — the San Francisco diorama, from Nazym's sketch. Layers,
outside in:

  sea      the whole outer ring is the bay: the Golden Gate on one side, the
           Bay Bridge 180 degrees away, Alcatraz and the Ferry Building.
  skirt    green slopes rising from a sandy shore.
  road     a ring round the top of the hill, with cable-car tracks: the cable
           car (slow) and a Bay Wheels e-bike (faster) go round it.
  hills    the city on its hills: Transamerica, Salesforce Tower, downtown,
           the Painted Ladies on Alamo Square's slope, Coit Tower on
           Telegraph Hill.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python scripts/blender/san_francisco.py
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

sea = k.mat("bay", (0.30, 0.46, 0.66))
sea_side = k.mat("bay-deep", (0.22, 0.36, 0.56))
grass = k.mat("grass", (0.56, 0.68, 0.44))
sand = k.mat("sand", (0.90, 0.84, 0.68))
asphalt = k.mat("asphalt", (0.32, 0.32, 0.36))
rail = k.mat("rail", (0.55, 0.56, 0.60))
intl_orange = k.mat("golden-gate-orange", (0.86, 0.30, 0.16))
steel = k.mat("bay-bridge-steel", (0.62, 0.66, 0.72))
bay_lights = k.mat("neon-white", (0.95, 0.96, 1.0))
white = k.mat("white", (0.95, 0.95, 0.93))
concrete = k.mat("concrete", (0.70, 0.70, 0.72))
glassy = k.mat("tower-glass", (0.40, 0.50, 0.66))
stone = k.mat("stone", (0.86, 0.80, 0.68))
dark = k.mat("dark", (0.18, 0.18, 0.22))
glow = k.mat("lamp-yellow", (1.0, 0.82, 0.42))
crown = k.mat("neon-salesforce", (0.55, 0.85, 1.0))
maroon = k.mat("cable-car-maroon", (0.55, 0.12, 0.14))
cream = k.mat("cream", (0.95, 0.90, 0.76))
wood = k.mat("wood", (0.55, 0.38, 0.24))
lyft = k.mat("neon-lyft-pink", (1.0, 0.0, 0.75))
bike_frame = k.mat("bike-black", (0.12, 0.12, 0.14))
rock = k.mat("rock", (0.52, 0.48, 0.44))
leaf = k.mat("tree", (0.24, 0.44, 0.28))
trunk = k.mat("trunk", (0.36, 0.26, 0.20))
ladies = [k.mat(n, c) for n, c in [
    ("lady-pink", (0.96, 0.66, 0.72)), ("lady-mint", (0.62, 0.86, 0.74)), ("lady-lavender", (0.74, 0.66, 0.90)),
    ("lady-yellow", (0.98, 0.88, 0.56)), ("lady-blue", (0.60, 0.78, 0.94)), ("lady-peach", (0.98, 0.76, 0.58))]]

# The sea is the plinth itself: its top at z = 0 is the water.
k.base(sea, sea_side)

# ---- the land: one polar-grid mesh, heights from a function -----------------
HILL_R, ROAD_IN, ROAD_OUT, SHORE, EDGE = 0.42, 0.42, 0.53, 0.62, 0.68
ROAD_Z = 0.14
HILLS = [(-0.13, 0.12, 0.08, 0.13),     # Nob / Russian Hill
         (0.16, 0.25, 0.07, 0.07),      # Telegraph Hill (Coit Tower)
         (-0.22, -0.18, 0.05, 0.11),    # Alamo Square (Painted Ladies)
         (0.06, -0.3, 0.03, 0.08)]


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def height(x, y):
    r = math.hypot(x, y)
    if r <= ROAD_IN:
        h = sum(hh * math.exp(-((x - hx) ** 2 + (y - hy) ** 2) / (2 * s * s)) for hx, hy, hh, s in HILLS)
        return ROAD_Z + h * (1 - smoothstep(0.3, ROAD_IN, r))
    if r <= ROAD_OUT:
        return ROAD_Z
    if r <= SHORE:
        a = math.atan2(y, x)
        t = smoothstep(ROAD_OUT, SHORE, r)
        return ROAD_Z + (0.03 - ROAD_Z) * t + 0.008 * math.sin(5 * a) * math.sin(math.pi * t)
    return 0.03 + (-0.01 - 0.03) * smoothstep(SHORE, EDGE, r)


radii = sorted(set([0.0] + [i * 0.021 for i in range(1, 20)] + [ROAD_IN, 0.44, 0.47, 0.5, ROAD_OUT]
                   + [ROAD_OUT + (SHORE - ROAD_OUT) * i / 6 for i in range(1, 7)] + [0.65, EDGE]))
SEGS = 128
bm = bmesh.new()
grid = []
for r in radii:
    if r == 0:
        grid.append([bm.verts.new((0, 0, height(0, 0)))])
        continue
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
for m in (grass, asphalt, sand):
    land.data.materials.append(m)
for p in land.data.polygons:
    r = math.hypot(p.center.x, p.center.y)
    p.material_index = 1 if ROAD_IN < r < ROAD_OUT else (2 if r > SHORE - 0.01 else 0)
    p.use_smooth = True
k.smooth_by_angle(land, 25)

# Cable-car tracks: two rails and the slot between, all the way round.
for rr in (0.455, 0.485):
    k.torus(f"DECO-rail-{rr}", rr, 0.0022, at=(0, 0, ROAD_Z + 0.002), segs=128, tube_segs=4, material=rail)
k.torus("DECO-cable-slot", 0.47, 0.0012, at=(0, 0, ROAD_Z + 0.0015), segs=128, tube_segs=4, material=dark)


def on_ground(o, x, y, rot=0.0, extra=0.0):
    """Turn about the origin by `rot` degrees, then stand at (x, y) on the land."""
    o.data.transform(Matrix.Translation((x, y, height(x, y) + extra)) @ Matrix.Rotation(math.radians(rot), 4, "Z"))
    return o


# ---- downtown -----------------------------------------------------------------
TA = (0.10, 0.02)
ta = k.empty("OBJ-transamerica")
body = k.cylinder("ta-body", 0.055, 0.42, segs=4, r_top=0.004, material=white, parent=ta, smooth=False)
body.data.transform(Matrix.Rotation(math.radians(45), 4, "Z"))
on_ground(body, *TA)
for side in (-1, 1):
    wing = k.box(f"ta-wing-{side}", (0.03, 0.012, 0.11), material=white, parent=ta)
    wing.data.transform(Matrix.Translation((side * 0.03, 0, 0.27)) @ Matrix.Rotation(math.radians(side * -8), 4, "Y"))
    on_ground(wing, *TA)
spire = k.cylinder("ta-spire", 0.004, 0.06, segs=6, material=glow, parent=ta)
on_ground(spire, *TA, extra=0.42)

SF = (0.25, -0.12)
sf = k.empty("OBJ-salesforce-tower")
prof = [(0.05, 0.0), (0.05, 0.38), (0.046, 0.43), (0.036, 0.47), (0.02, 0.495), (0.0, 0.5)]
tower = k.lathe("sf-body", prof, segs=4, material=glassy, parent=sf, smooth=False)
# A rounded square in plan: a 4-sided lathe turned 45 degrees, then softened.
tower.data.transform(Matrix.Diagonal((0.9, 1.0, 1.0, 1.0)) @ Matrix.Rotation(math.radians(45), 4, "Z"))
on_ground(tower, *SF)
for b in range(7):
    band = k.box(f"sf-band-{b}", (0.074, 0.066, 0.005), material=glow, parent=sf)
    on_ground(band, *SF, extra=0.04 + b * 0.05)
crown_ring = k.cylinder("sf-crown", 0.036, 0.06, segs=16, r_top=0.018, material=crown, parent=sf)
on_ground(crown_ring, *SF, extra=0.42)

rnd = random.Random(8)
blocks = []
for i, (x, y) in enumerate([(0.0, -0.08), (0.14, -0.18), (0.32, 0.02), (0.2, 0.1), (-0.03, -0.2),
                            (0.34, -0.22), (0.05, 0.14), (0.26, -0.28)]):
    w, d, h = rnd.uniform(0.045, 0.07), rnd.uniform(0.045, 0.07), rnd.uniform(0.12, 0.26)
    bx = k.box(f"dt-{i}", (w, d, h), material=[concrete, glassy, stone][i % 3])
    blocks.append(on_ground(bx, x, y, rot=rnd.uniform(-10, 10)))
    for b in range(int(h / 0.045)):
        band = k.box(f"dt-band-{i}-{b}", (w + 0.002, d + 0.002, 0.004), material=glow)
        blocks.append(on_ground(band, x, y, extra=0.03 + b * 0.045))
k.join("DECO-downtown", blocks)


# ---- Coit Tower on Telegraph Hill --------------------------------------------
CT = (0.16, 0.25)
coit = k.empty("OBJ-coit-tower")
on_ground(k.cylinder("coit-base", 0.04, 0.02, segs=20, material=stone, parent=coit), *CT)
on_ground(k.cylinder("coit-shaft", 0.022, 0.13, segs=16, material=stone, parent=coit), *CT, extra=0.02)
on_ground(k.cylinder("coit-crown", 0.025, 0.018, segs=16, material=stone, parent=coit), *CT, extra=0.15)
for i in range(8):
    win = k.box(f"coit-win-{i}", (0.006, 0.002, 0.012), material=glow, parent=coit)
    win.data.transform(Matrix.Rotation(2 * math.pi * i / 8, 4, "Z") @ Matrix.Translation((0, -0.0255, 0.155)))
    on_ground(win, *CT)


# ---- Painted Ladies, stepping down Alamo Square's slope ----------------------
pl = k.empty("OBJ-painted-ladies")
PL0 = Vector((-0.34, -0.2))
along = Vector((0.96, -0.28)).normalized()      # the row runs down the slope
face = math.degrees(math.atan2(along.y, along.x))
for i in range(6):
    c = PL0 + along * (i * 0.05)
    m = ladies[i]
    parts = [k.box(f"pl-house-{i}", (0.046, 0.06, 0.075), material=m, parent=pl),
             k.box(f"pl-bay-{i}", (0.02, 0.012, 0.05), at=(-0.008, -0.034, 0.012), material=m, parent=pl),
             k.box(f"pl-win-{i}", (0.014, 0.002, 0.02), at=(-0.008, -0.041, 0.035), material=glow, parent=pl),
             k.box(f"pl-door-{i}", (0.01, 0.002, 0.025), at=(0.013, -0.031, 0.0), material=white, parent=pl),
             k.box(f"pl-trim-{i}", (0.05, 0.064, 0.005), at=(0, 0, 0.075), material=white, parent=pl)]
    gable = k.prism(f"pl-gable-{i}", [(-0.03, 0), (0.03, 0), (0, 0.04)], 0.064, material=m)
    gable.data.transform(Matrix.Translation((0, 0.032, 0.078)) @ Matrix.Rotation(math.radians(90), 4, "X"))
    gable.parent = pl
    parts.append(gable)
    for o in parts:
        o.data.transform(Matrix.Rotation(math.radians(face), 4, "Z"))
        on_ground(o, c.x, c.y)


# ---- trees on the hills ------------------------------------------------------
keep = [(TA[0], TA[1], 0.07), (SF[0], SF[1], 0.07), (CT[0], CT[1], 0.05), (0.17, -0.08, 0.2)]
keep += [((PL0 + along * (i * 0.05)).x, (PL0 + along * (i * 0.05)).y, 0.05) for i in range(6)]
trees = k.forest("DECO-trees-tmp", 46, leaf, keep, seed=21, r_max=ROAD_IN - 0.03, h=(0.06, 0.09),
                 round_crowns=True, trunk_mat=trunk)
# forest() puts trees at z=0; lift each vertex by the ground under its trunk.
for v in trees.data.vertices:
    v.co.z += height(v.co.x, v.co.y)
trees.name = "DECO-trees"
skirt_trees = k.forest("DECO-skirt-trees", 30, leaf, [], seed=4, r_max=SHORE - 0.02, h=(0.05, 0.07),
                       round_crowns=True, trunk_mat=trunk)
for v in list(skirt_trees.data.vertices):
    v.co.z += height(v.co.x, v.co.y)
# Keep only skirt trees that are actually on the skirt, not on the road.
bm = bmesh.new()
bm.from_mesh(skirt_trees.data)
islands, seen = [], set()
for v in bm.verts:
    if v.index in seen:
        continue
    stack, comp = [v], []
    while stack:
        x = stack.pop()
        if x.index in seen:
            continue
        seen.add(x.index)
        comp.append(x)
        stack.extend(e.other_vert(x) for e in x.link_edges)
    islands.append(comp)
doomed = []
for comp in islands:
    cx = sum(v.co.x for v in comp) / len(comp)
    cy = sum(v.co.y for v in comp) / len(comp)
    if not (ROAD_OUT + 0.02 < math.hypot(cx, cy) < SHORE - 0.02):
        doomed.extend(comp)
bmesh.ops.delete(bm, geom=list({v for v in doomed}), context="VERTS")
bm.to_mesh(skirt_trees.data)
bm.free()


# ---- bridges -----------------------------------------------------------------
def bridge(name, theta_deg, r, length, tower_u, tower_h, body_m, hanger_m, anchorage=False):
    """A suspension bridge on the water, tangent to the land at angle theta.
    Built in a local (u along the deck, v across, z up) frame."""
    root = k.empty(name)
    tag = name[4:]
    th = math.radians(theta_deg)
    P = Vector((r * math.cos(th), r * math.sin(th), 0))
    T = Vector((-math.sin(th), math.cos(th), 0))
    N = Vector((math.cos(th), math.sin(th), 0))
    M = Matrix(((T.x, N.x, 0, P.x), (T.y, N.y, 0, P.y), (0, 0, 1, 0), (0, 0, 0, 1)))
    parts = []
    DZ = 0.055
    parts.append(k.box(f"{tag}-deck", (length, 0.034, 0.01), at=(0, 0, DZ), material=body_m, parent=root))
    # Names use indices, never raw floats: Blender reads a trailing ".NNN" as
    # a duplicate counter, and 0.38 * 0.62 = 0.23559999999999998 overflows it
    # (the whole app aborts with "stoi: out of range").
    for ti, u in enumerate(tower_u):
        for vi, v in enumerate((-0.015, 0.015)):
            parts.append(k.box(f"{tag}-leg-{ti}-{vi}", (0.011, 0.009, tower_h), at=(u, v, 0), material=body_m, parent=root))
        for zi, zz in enumerate((DZ + 0.02, tower_h * 0.62, tower_h - 0.012)):
            parts.append(k.box(f"{tag}-beam-{ti}-{zi}", (0.01, 0.04, 0.01), at=(u, 0, zz), material=body_m, parent=root))
        parts.append(k.cylinder(f"{tag}-pier-{ti}", 0.02, DZ, segs=10, at=(u, 0, 0), material=concrete, parent=root))
    if anchorage:
        parts.append(k.box(f"{tag}-anchor", (0.04, 0.04, 0.08), at=(0, 0, 0), material=concrete, parent=root))
    # Main cables: sag between towers, fall to the deck at the ends (or anchorage).
    ends = sorted(tower_u)
    spans = []
    stops = [-length / 2] + ends + [length / 2]
    for a, b in zip(stops, stops[1:]):
        a_t, b_t = a in tower_u, b in tower_u
        if a_t and b_t and not (anchorage and a < 0 < b):
            spans.append((a, b, "sag"))
        elif a_t or b_t:
            spans.append((a, b, "fall"))
        else:
            spans.append((a, b, "fall"))
    hangers = []
    for vi, v in enumerate((-0.015, 0.015)):
        for si, (a, b, kind) in enumerate(spans):
            pts = []
            n = 16
            for i in range(n + 1):
                u = a + (b - a) * i / n
                t = (u - a) / (b - a)
                if kind == "sag":
                    z = DZ + 0.02 + (tower_h - DZ - 0.02) * (2 * t - 1) ** 2
                else:
                    hi_a = a in tower_u
                    z = DZ + 0.01 + (tower_h - DZ - 0.01) * ((1 - t) if hi_a else t) ** 1.6
                pts.append((u, v, z))
            parts.append(k.tube(f"{tag}-cable-{vi}-{si}", pts, 0.0028, material=body_m, segs=5, parent=root))
            for i in range(1, n):
                u, _, z = pts[i]
                if z - DZ > 0.012:
                    hangers.append(k.tube(f"{tag}-h", [(u, v, DZ + 0.01), (u, v, z)], 0.0011, material=hanger_m, segs=3))
    if hangers:
        h = k.join(f"{tag}-hangers", hangers)
        h.parent = root
        parts.append(h)
    for o in parts:
        o.data.transform(M)
    return root


bridge("OBJ-golden-gate", -140, 0.9, 0.78, (-0.21, 0.21), 0.38, intl_orange, intl_orange)
bridge("OBJ-bay-bridge", 40, 0.9, 0.74, (-0.18, 0.18), 0.27, steel, bay_lights, anchorage=True)


# ---- Alcatraz ----------------------------------------------------------------
AL = (0.9 * math.cos(math.radians(105)), 0.9 * math.sin(math.radians(105)))
alc = k.empty("OBJ-alcatraz")
k.lathe("alc-rock", [(0.075, -0.005), (0.07, 0.02), (0.05, 0.04), (0.0, 0.045)], segs=20,
        at=(AL[0], AL[1], 0), material=rock, parent=alc)
k.box("alc-cellhouse", (0.08, 0.035, 0.03), at=(AL[0], AL[1], 0.04), material=white, parent=alc)
k.cylinder("alc-lighthouse", 0.008, 0.07, at=(AL[0] + 0.045, AL[1] + 0.02, 0.035), segs=8, material=white, parent=alc)
k.sphere("alc-lamp", 0.009, at=(AL[0] + 0.045, AL[1] + 0.02, 0.11), material=glow, parent=alc, subdiv=1)


# ---- the Ferry Building, on the shore by the Bay Bridge ----------------------
fb = k.empty("OBJ-ferry-building")
FT = math.radians(15)
parts = [k.box("fb-hall", (0.16, 0.045, 0.035), material=stone, parent=fb),
         k.box("fb-roof", (0.164, 0.05, 0.008), at=(0, 0, 0.035), material=dark, parent=fb),
         k.box("fb-tower", (0.024, 0.024, 0.13), material=stone, parent=fb),
         k.box("fb-clock", (0.026, 0.026, 0.02), at=(0, 0, 0.1), material=glow, parent=fb)]
cap = k.cylinder("fb-cap", 0.019, 0.03, segs=4, r_top=0.0, material=dark, parent=fb, smooth=False)
cap.data.transform(Matrix.Translation((0, 0, 0.13)) @ Matrix.Rotation(math.radians(45), 4, "Z"))
parts.append(cap)
for o in parts:
    o.data.transform(Matrix.Translation((0.84 * math.cos(FT), 0.84 * math.sin(FT), 0.0))
                     @ Matrix.Rotation(FT + math.pi / 2, 4, "Z"))


# ---- the cable car and the e-bike, on the hill road --------------------------
def orbiting(name, orbit, start_deg):
    root = k.empty(name)
    root["orbit"] = orbit
    return root, Matrix.Rotation(math.radians(start_deg), 4, "Z")


cc, rot = orbiting("OBJ-cable-car", 80.0, 30)   # slow: cable cars crawl
L, W = 0.11, 0.042
Z0 = ROAD_Z + 0.012
cparts = [k.box("cc-body", (W, L * 0.62, 0.035), at=(0.47, 0, Z0), material=maroon, parent=cc),
          k.box("cc-ends", (W * 0.9, L, 0.012), at=(0.47, 0, Z0), material=maroon, parent=cc),
          k.box("cc-windows", (W + 0.002, L * 0.58, 0.016), at=(0.47, 0, Z0 + 0.016), material=glow, parent=cc),
          k.box("cc-cream", (W + 0.002, L * 0.64, 0.006), at=(0.47, 0, Z0 + 0.035), material=cream, parent=cc),
          k.box("cc-roof", (W * 1.12, L * 1.04, 0.008), at=(0.47, 0, Z0 + 0.046), material=cream, parent=cc),
          k.box("cc-clerestory", (W * 0.5, L * 0.8, 0.008), at=(0.47, 0, Z0 + 0.054), material=maroon, parent=cc)]
for u in (-0.4, 0.4):
    for v in (-1, 1):
        cparts.append(k.cylinder(f"cc-post-{u}-{v}", 0.0018, 0.034, at=(0.47 + v * W * 0.45, u * L, Z0 + 0.012),
                                 segs=4, material=wood, parent=cc))
for u in (-0.3, 0.3):
    for v in (-1, 1):
        wh = k.cylinder(f"cc-wheel-{u}-{v}", 0.008, 0.005, segs=10, material=dark, parent=cc)
        wh.data.transform(Matrix.Translation((0.47 + v * 0.015, u * L, ROAD_Z + 0.008)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
        cparts.append(wh)
for o in cparts:
    o.data.transform(rot)

bike, rot = orbiting("OBJ-bay-wheels", 34.0, 200)   # faster than the cable car
BR = 0.507
Z1 = ROAD_Z + 0.009
bparts = []
for u in (-0.012, 0.012):
    w = k.torus(f"bike-wheel-{u}", 0.008, 0.0016, rot=(0, 90, 0), at=(BR, u, Z1), segs=16, tube_segs=4,
                material=bike_frame, parent=bike)
    bparts.append(w)
bparts.append(k.tube("bike-frame", [(BR, -0.012, Z1), (BR, -0.002, Z1 + 0.012), (BR, 0.01, Z1 + 0.012),
                                     (BR, 0.012, Z1)], 0.0018, material=lyft, segs=4, parent=bike))
bparts.append(k.tube("bike-down", [(BR, -0.002, Z1 + 0.012), (BR, 0.004, Z1)], 0.0016, material=bike_frame, segs=4, parent=bike))
bparts.append(k.tube("bike-bars", [(BR - 0.007, 0.011, Z1 + 0.02), (BR + 0.007, 0.011, Z1 + 0.02)], 0.0013,
                     material=bike_frame, segs=4, parent=bike))
bparts.append(k.box("bike-basket", (0.01, 0.008, 0.006), at=(BR, 0.016, Z1 + 0.012), material=bike_frame, parent=bike))
bparts.append(k.box("bike-seat", (0.004, 0.008, 0.002), at=(BR, -0.004, Z1 + 0.016), material=bike_frame, parent=bike))
bparts.append(k.box("bike-battery", (0.004, 0.01, 0.004), at=(BR, 0.003, Z1 + 0.006), material=white, parent=bike))
for o in bparts:
    o.data.transform(rot)

# ---- the city fills more of the bay -------------------------------------------
# Everything was laid out on a 0.68 island; scale the island and all that
# stands on it up about the centre, leaving the sea things where they are.
SEA_THINGS = {"DECO-base", "OBJ-golden-gate", "OBJ-bay-bridge", "OBJ-alcatraz", "OBJ-ferry-building"}
for o in list(bpy.data.objects):
    if o.parent is None and o.name not in SEA_THINGS:
        k.grow(o, 1.15, (0, 0, 0))

k.export("san-francisco")
