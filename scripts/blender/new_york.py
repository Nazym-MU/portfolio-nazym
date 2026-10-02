"""
new_york.py — the New York diorama, from Nazym's sketch. Same inset base as
London: Central Park in the middle, a road ring outside with a hop-on hop-off
bus and a yellow cab going round at different speeds.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python scripts/blender/new_york.py

          Times Square towers          Empire State
   Liberty      park trees
   subway       Strawberry Fields    the pond
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Matrix  # noqa: E402
import diorama_kit as k  # noqa: E402

k.reset()
G = 0.05

grass = k.mat("grass", (0.52, 0.70, 0.40))
road = k.mat("asphalt", (0.30, 0.31, 0.34))
earth = k.mat("earth", (0.40, 0.36, 0.34))
paint = k.mat("road-white", (0.95, 0.95, 0.92))
path_m = k.mat("path", (0.86, 0.80, 0.68))
water = k.mat("pond", (0.24, 0.40, 0.55))
tower_a = k.mat("tower-steel", (0.55, 0.62, 0.72))
tower_b = k.mat("tower-dark", (0.30, 0.36, 0.48))
tower_c = k.mat("tower-stone", (0.78, 0.72, 0.62))
glow = k.mat("lamp-yellow", (1.0, 0.82, 0.42))
board_r = k.mat("billboard-red", (0.95, 0.32, 0.30))
board_b = k.mat("billboard-blue", (0.30, 0.62, 0.98))
board_p = k.mat("billboard-pink", (0.98, 0.50, 0.75))
stone = k.mat("stone", (0.86, 0.80, 0.68))
copper = k.mat("liberty-copper", (0.48, 0.74, 0.64))
gold = k.mat("gold", (0.98, 0.72, 0.28))
dark = k.mat("dark", (0.16, 0.17, 0.20))
subway_g = k.mat("subway-green", (0.18, 0.42, 0.30))
white = k.mat("white", (0.95, 0.95, 0.93))
red = k.mat("red", (0.82, 0.14, 0.14))
cab = k.mat("cab-yellow", (0.98, 0.78, 0.12))
leaf = k.mat("tree", (0.26, 0.48, 0.28))
trunk = k.mat("trunk", (0.36, 0.26, 0.20))
bench = k.mat("bench", (0.45, 0.32, 0.22))

k.inset_base(grass, road, earth)
dashes = []
for i in range(56):
    a = 360 * i / 56
    d = k.box(f"dash-{i}", (0.035, 0.008, 0.002), material=paint)
    k.place(d, rot=(0, 0, a + 90), at=(0.91 * math.cos(math.radians(a)), 0.91 * math.sin(math.radians(a)), 0))
    dashes.append(d)
k.join("DECO-road-marks", dashes)

# ---- park paths and the pond ------------------------------------------------
k.ribbon("DECO-path-loop", [(0.62 * math.cos(math.radians(a)), 0.62 * math.sin(math.radians(a)) - 0.05)
                            for a in range(0, 362, 6)], 0.035, z=G + 0.002, material=path_m, clip=0.78)
k.ribbon("DECO-path-cross", [(x / 100, -0.1 + 0.05 * math.sin(x / 20)) for x in range(-70, 71, 5)],
         0.03, z=G + 0.002, material=path_m, clip=0.78)
pond = [(0.24 + 0.2 * math.cos(a) * (1 + 0.12 * math.sin(3 * a)), -0.42 + 0.12 * math.sin(a) * (1 + 0.1 * math.cos(2 * a)))
        for a in [2 * math.pi * i / 40 for i in range(40)]]
k.prism("OBJ-the-pond", pond, 0.004, z0=G, material=water)


# ---- Times Square, at the back ----------------------------------------------
ts = k.empty("OBJ-times-square")
towers = [(-0.16, 0.42, 0.12, 0.1, 0.62, tower_a), (-0.03, 0.36, 0.11, 0.1, 0.5, tower_b),
          (0.1, 0.44, 0.1, 0.1, 0.58, tower_a), (-0.28, 0.32, 0.09, 0.09, 0.36, tower_c),
          (0.0, 0.54, 0.12, 0.08, 0.42, tower_c)]
boards = [board_r, board_b, board_p, glow]
for n, (x, y, w, d, h, m) in enumerate(towers):
    k.box(f"ts-tower-{n}", (w, d, h), at=(x, y, G), material=m, parent=ts)
    k.box(f"ts-cap-{n}", (w * 0.7, d * 0.7, 0.025), at=(x, y, G + h), material=m, parent=ts)
    # window bands that glow at night
    for b in range(int(h / 0.07)):
        k.box(f"ts-band-{n}-{b}", (w + 0.002, d + 0.002, 0.008), at=(x, y, G + 0.05 + b * 0.07),
              material=glow, parent=ts)
    # billboards on the front faces, lower floors
    for b in range(2):
        k.box(f"ts-board-{n}-{b}", (w * 0.8, 0.004, 0.04), at=(x, y - d / 2 - 0.002, G + 0.03 + b * 0.05),
              material=boards[(n + b) % 4], parent=ts)


# ---- Empire State -----------------------------------------------------------
ES = (0.42, 0.30)
es = k.empty("OBJ-empire-state")
for z0, w, h in [(0, 0.15, 0.1), (0.1, 0.11, 0.32), (0.42, 0.08, 0.05), (0.47, 0.06, 0.04), (0.51, 0.04, 0.03)]:
    k.box(f"es-tier-{z0}", (w, w, h), at=(ES[0], ES[1], G + z0), material=tower_c, parent=es)
k.cylinder("es-mast", 0.012, 0.06, at=(ES[0], ES[1], G + 0.54), r_top=0.007, segs=8, material=tower_c, parent=es)
k.cylinder("es-needle", 0.003, 0.06, at=(ES[0], ES[1], G + 0.6), segs=5, material=white, parent=es)
for side in range(4):
    for col in range(3):
        o = k.box(f"es-win-{side}-{col}", (0.012, 0.002, 0.26), material=glow, parent=es)
        off = Matrix.Rotation(math.radians(90 * side), 4, "Z") @ Matrix.Translation(((col - 1) * 0.03, -0.0555, 0))
        o.data.transform(Matrix.Translation((ES[0], ES[1], G + 0.13)) @ off)
k.box("es-crown-glow", (0.062, 0.062, 0.012), at=(ES[0], ES[1], G + 0.49), material=gold, parent=es)


# ---- Statue of Liberty (cartoon) --------------------------------------------
LX, LY = -0.52, 0.10
lib = k.empty("OBJ-statue-of-liberty")
k.box("lib-pedestal", (0.1, 0.1, 0.1), at=(LX, LY, G), material=stone, parent=lib)
k.box("lib-pedestal-top", (0.08, 0.08, 0.03), at=(LX, LY, G + 0.1), material=stone, parent=lib)
k.lathe("lib-robe", [(0.038, 0), (0.034, 0.08), (0.024, 0.15), (0.0, 0.16)], segs=16,
        at=(LX, LY, G + 0.13), material=copper, parent=lib)
k.sphere("lib-head", 0.018, at=(LX, LY, G + 0.3), material=copper, parent=lib, subdiv=2)
for i in range(7):
    a = math.radians(-60 + 120 * i / 6 - 90)
    k.tube(f"lib-ray-{i}", [(LX, LY, G + 0.31), (LX + 0.03 * math.cos(a), LY + 0.03 * math.sin(a), G + 0.33)],
           0.003, material=copper, segs=4, parent=lib)
k.tube("lib-arm", [(LX + 0.02, LY, G + 0.26), (LX + 0.035, LY, G + 0.33), (LX + 0.04, LY, G + 0.37)], 0.007,
       material=copper, segs=6, parent=lib)
k.cylinder("lib-torch", 0.008, 0.02, at=(LX + 0.04, LY, G + 0.37), r_top=0.013, segs=8, material=copper, parent=lib)
k.sphere("lib-flame", 0.011, at=(LX + 0.04, LY, G + 0.4), material=gold, parent=lib, subdiv=2)
k.box("lib-tablet", (0.02, 0.012, 0.035), at=(LX - 0.03, LY - 0.012, G + 0.2), material=copper, parent=lib)


# ---- Subway station, peeking up ---------------------------------------------
SX, SY = -0.45, -0.32
sub = k.empty("OBJ-subway")
k.box("sub-stairwell", (0.12, 0.07, 0.003), at=(SX, SY, G), material=dark, parent=sub)
for i in range(4):
    st = k.box(f"sub-step-{i}", (0.11, 0.012, 0.002), material=stone, parent=sub)
    k.place(st, at=(SX, SY + 0.022 - i * 0.015, G + 0.0035))
for dy in (-0.035, 0.035):
    k.tube(f"sub-rail-{dy}", [(SX - 0.06, SY + dy, G + 0.035), (SX + 0.06, SY + dy, G + 0.035)], 0.003,
           material=subway_g, segs=5, parent=sub)
    for dx in (-0.06, 0.0, 0.06):
        k.cylinder(f"sub-baluster-{dy}-{dx}", 0.0025, 0.035, at=(SX + dx, SY + dy, G),
                   material=subway_g, parent=sub, segs=5)
k.tube("sub-rail-back", [(SX - 0.06, SY + 0.035, G + 0.035), (SX - 0.06, SY - 0.035, G + 0.035)], 0.003,
       material=subway_g, segs=5, parent=sub)
# The two green globe lamps either side of the steps.
for dy in (-0.035, 0.035):
    k.cylinder(f"sub-lamp-post-{dy}", 0.004, 0.09, at=(SX + 0.06, SY + dy, G), material=subway_g, parent=sub, segs=6)
    k.sphere(f"sub-globe-{dy}", 0.011, at=(SX + 0.06, SY + dy, G + 0.1), material=glow, parent=sub, subdiv=2)
k.box("sub-sign", (0.004, 0.06, 0.016), at=(SX + 0.064, SY, G + 0.07), material=dark, parent=sub)


# ---- Strawberry Fields: the Imagine mosaic and its benches -------------------
FX, FY = -0.12, -0.36
sf = k.empty("OBJ-strawberry-fields")
k.cylinder("sf-mosaic", 0.075, 0.004, at=(FX, FY, G), segs=40, material=white, parent=sf)
k.cylinder("sf-mosaic-ring", 0.05, 0.005, at=(FX, FY, G), segs=40, material=dark, parent=sf)
k.cylinder("sf-mosaic-centre", 0.022, 0.006, at=(FX, FY, G), segs=24, material=white, parent=sf)
for i in range(8):
    a = 2 * math.pi * i / 8
    ray = k.cylinder(f"sf-ray-{i}", 0.006, 0.0055, segs=3, material=white, parent=sf, smooth=False)
    ray.data.transform(Matrix.Diagonal((4.5, 1, 1, 1)))
    k.place(ray, rot=(0, 0, math.degrees(a)), at=(FX + 0.036 * math.cos(a), FY + 0.036 * math.sin(a), G))
for i in range(5):
    a = math.radians(30 + 30 * i)
    b = k.box(f"sf-bench-{i}", (0.045, 0.014, 0.012), material=bench, parent=sf)
    k.place(b, rot=(0, 0, math.degrees(a) - 90), at=(FX + 0.11 * math.cos(a), FY + 0.11 * math.sin(a), G + 0.008))
    back = k.box(f"sf-bench-back-{i}", (0.045, 0.004, 0.018), material=bench, parent=sf)
    k.place(back, rot=(0, 0, math.degrees(a) - 90),
            at=(FX + 0.118 * math.cos(a), FY + 0.118 * math.sin(a), G + 0.012))


# ---- Traffic on the ring ----------------------------------------------------
def vehicle(name, lane, length, width, height, body, decks, orbit, start_deg, extras=()):
    """A box vehicle on the ring at `lane`, facing along the road. `extras` are
    (size, at, material) boxes for roofs, rails and lights."""
    root = k.empty(name)
    tag = name[4:]   # parts must not start with OBJ- or each becomes its own object
    root["orbit"] = orbit
    parts = [k.box(f"{tag}-body", (width, length, height), at=(lane, 0, 0.016), material=body, parent=root)]
    for z in decks:
        for side in (-1, 1):
            parts.append(k.box(f"{tag}-win-{z}-{side}", (0.002, length * 0.8, 0.022),
                               at=(lane + side * (width / 2 + 0.001), 0.006, z), material=glow, parent=root))
    for wy in (-length * 0.3, length * 0.3):
        for side in (-1, 1):
            wh = k.cylinder(f"{tag}-wheel-{wy}-{side}", 0.015, 0.01, segs=12, material=dark, parent=root)
            k.place(wh, rot=(0, 90, 0), at=(lane + side * (width / 2 - 0.004) - 0.005, wy, 0.015))
            parts.append(wh)
    for j, (size, at, m) in enumerate(extras):
        parts.append(k.box(f"{tag}-part-{j}", size, at=at, material=m, parent=root))
    for o in parts:
        o.data.transform(Matrix.Rotation(math.radians(start_deg), 4, "Z"))
    return root


# The hop-on hop-off: an open-top red double-decker.
vehicle("OBJ-hop-on-hop-off", 0.945, 0.17, 0.062, 0.075, red, (0.04,), 52.0, 0, extras=[
    ((0.004, 0.16, 0.02), (0.945 - 0.029, 0, 0.091), red),
    ((0.004, 0.16, 0.02), (0.945 + 0.029, 0, 0.091), red),
    ((0.04, 0.13, 0.008), (0.945, 0, 0.091), dark),
])
vehicle("OBJ-yellow-cab", 0.875, 0.09, 0.045, 0.03, cab, (), 30.0, 180, extras=[
    ((0.04, 0.05, 0.02), (0.875, -0.005, 0.046), cab),
    ((0.02, 0.008, 0.008), (0.875, -0.005, 0.066), glow),
])


# ---- bigger landmarks (scaled about their footprints) ----------------------
k.grow(lib, 1.35, (LX, LY, G))
k.grow(sub, 1.3, (SX, SY, G))
k.grow(sf, 1.25, (FX, FY, G))
k.grow(es, 1.12, (ES[0], ES[1], G))


# ---- park trees -------------------------------------------------------------
keep = [(x, y, max(w, d) * 0.8) for x, y, w, d, _h, _m in towers] + [(ES[0], ES[1], 0.13), (LX, LY, 0.11),
        (SX, SY, 0.13), (FX, FY, 0.19), (0.24, -0.42, 0.24)]
k.forest("DECO-trees", 50, leaf, keep, seed=4, r_max=0.74, h=(0.09, 0.14), z=G,
         round_crowns=True, trunk_mat=trunk)

k.export("new-york")
