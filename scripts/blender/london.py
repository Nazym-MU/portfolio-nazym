"""
london.py — the London diorama, from Nazym's sketch ("May London always keep
its spark").

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python scripts/blender/london.py

The base is inset: a raised round of land with a road ring around it, and a
red double-decker on that road (OBJ-bus, orbit = seconds per lap).

        Shard        Big Ben          London Eye
   ~~~~~~~~~~~~~~~~~~~ Thames ~~~~~~~~~~~~~~~~~~~~
     bookshop     lamp    phone box    Underground
   (bus going round the outside)
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diorama_kit as k  # noqa: E402

k.reset()

G = 0.05            # land height above the road
ROAD_R = 0.945      # bus lane centre

grass = k.mat("grass", (0.55, 0.68, 0.42))
road = k.mat("asphalt", (0.30, 0.31, 0.34))
earth = k.mat("earth", (0.42, 0.36, 0.32))
paint = k.mat("road-white", (0.95, 0.95, 0.92))
water = k.mat("thames", (0.20, 0.30, 0.46))
stone = k.mat("stone", (0.86, 0.76, 0.56))
slate = k.mat("slate", (0.24, 0.34, 0.33))
clock = k.mat("clock-face", (0.97, 0.94, 0.84))
dark = k.mat("dark", (0.18, 0.18, 0.22))
shard_m = k.mat("shard", (0.70, 0.78, 0.86))
white = k.mat("white", (0.95, 0.95, 0.95))
red = k.mat("red", (0.80, 0.12, 0.12))
lamp = k.mat("lamp-yellow", (1.0, 0.82, 0.42))
blue = k.mat("blue", (0.10, 0.20, 0.55))
green = k.mat("shop-green", (0.12, 0.33, 0.27))
cream = k.mat("cream", (0.95, 0.90, 0.78))
brick = k.mat("brick", (0.62, 0.32, 0.24))
leaf = k.mat("tree", (0.26, 0.45, 0.26))
trunk = k.mat("trunk", (0.36, 0.26, 0.20))

k.inset_base(grass, road, earth)

# Dashed centre line, one mesh.
dashes = []
for i in range(56):
    a = 360 * i / 56
    d = k.box(f"dash-{i}", (0.035, 0.008, 0.002), material=paint)
    k.place(d, rot=(0, 0, a + 90), at=(0.91 * math.cos(math.radians(a)), 0.91 * math.sin(math.radians(a)), 0))
    dashes.append(d)
k.join("DECO-road-marks", dashes)


# ---- the Thames -------------------------------------------------------------
def thames_y(x):
    return -0.02 + 0.09 * math.sin(2.4 * x + 0.3)


thames = [(x / 100, thames_y(x / 100)) for x in range(-82, 83, 2)]
k.ribbon("DECO-thames", thames, 0.17, z=G + 0.002, material=water, clip=0.79)


# ---- Big Ben ----------------------------------------------------------------
BX, BY = -0.02, 0.32
bigben = k.empty("OBJ-big-ben")
k.box("bb-shaft", (0.085, 0.085, 0.42), at=(BX, BY, G), material=stone, parent=bigben)
k.box("bb-clock", (0.105, 0.105, 0.11), at=(BX, BY, G + 0.42), material=stone, parent=bigben)
for i, (dx, dy, rz) in enumerate([(0, -1, 0), (1, 0, 90), (0, 1, 180), (-1, 0, 270)]):
    f = k.cylinder(f"bb-face-{i}", 0.038, 0.004, segs=24, material=clock, parent=bigben, smooth=False)
    k.place(f, rot=(90, 0, rz), at=(BX + dx * 0.0545, BY + dy * 0.0545, G + 0.475))
    h = k.box(f"bb-hands-{i}", (0.004, 0.002, 0.03), material=dark, parent=bigben)
    k.place(h, rot=(0, 0, rz), at=(BX + dx * 0.058, BY + dy * 0.058, G + 0.47))
k.box("bb-belfry", (0.09, 0.09, 0.06), at=(BX, BY, G + 0.53), material=stone, parent=bigben)
spire = k.cylinder("bb-spire", 0.064, 0.13, segs=4, r_top=0.0, material=slate, parent=bigben, smooth=False)
k.place(spire, rot=(0, 0, 45), at=(BX, BY, G + 0.59))
k.cylinder("bb-finial", 0.004, 0.04, at=(BX, BY, G + 0.71), material=lamp, parent=bigben, segs=6)


# ---- The Shard --------------------------------------------------------------
SX, SY = -0.40, 0.30
shard = k.empty("OBJ-shard")
body = k.cylinder("shard-body", 0.12, 0.64, segs=4, r_top=0.014, material=shard_m, parent=shard, smooth=False)
k.place(body, rot=(0, 0, 45), at=(SX, SY, G))
# The broken-glass top: a few splinters that do not quite meet.
for i, (dx, dy, h) in enumerate([(0.008, 0.004, 0.09), (-0.007, 0.006, 0.07), (0.002, -0.008, 0.08)]):
    sp = k.cylinder(f"shard-splinter-{i}", 0.006, h, segs=3, r_top=0.0, material=shard_m, parent=shard, smooth=False)
    k.place(sp, rot=(0, 0, 30 * i), at=(SX + dx, SY + dy, G + 0.6))


# ---- London Eye -------------------------------------------------------------
EX, EY, ER = 0.44, 0.30, 0.26
EZ = G + ER + 0.06
eye = k.empty("OBJ-london-eye")
k.torus("eye-rim", ER, 0.006, rot=(90, 0, 0), at=(EX, EY, EZ), material=white, parent=eye)
k.torus("eye-rim-inner", ER - 0.02, 0.003, rot=(90, 0, 0), at=(EX, EY, EZ), material=white, parent=eye)
hub = k.cylinder("eye-hub", 0.018, 0.04, segs=16, material=white, parent=eye)
k.place(hub, rot=(90, 0, 0), at=(EX, EY + 0.02, EZ))
for i in range(16):
    a = 2 * math.pi * i / 16
    ca, sa = math.cos(a), math.sin(a)
    k.tube(f"eye-spoke-{i}", [(EX, EY, EZ), (EX + ER * ca, EY, EZ + ER * sa)], 0.0018,
           material=white, segs=4, parent=eye)
    pod = k.sphere(f"eye-pod-{i}", 0.014, material=cream, parent=eye, subdiv=2)
    pod.data.transform(__import__("mathutils").Matrix.Diagonal((1.6, 1.0, 1.0, 1.0)))
    k.place(pod, at=(EX + (ER + 0.014) * ca, EY, EZ + (ER + 0.014) * sa))
# The A-frame leaning in from behind.
for dx in (-0.06, 0.06):
    k.tube(f"eye-leg-{dx}", [(EX + dx, EY + 0.12, G), (EX, EY + 0.02, EZ)], 0.006,
           material=white, segs=6, parent=eye)


# ---- Phone box --------------------------------------------------------------
PX, PY = 0.06, -0.38
phone = k.empty("OBJ-phone-box")
k.box("phone-body", (0.07, 0.07, 0.16), at=(PX, PY, G), material=red, parent=phone)
k.box("phone-crown", (0.078, 0.078, 0.022), at=(PX, PY, G + 0.16), material=red, parent=phone)
k.box("phone-sign", (0.074, 0.074, 0.01), at=(PX, PY, G + 0.164), material=cream, parent=phone)
k.cylinder("phone-dome", 0.034, 0.014, at=(PX, PY, G + 0.182), r_top=0.012, material=red, parent=phone, segs=16)
for i, (dx, dy, rz) in enumerate([(0, -1, 0), (1, 0, 90), (-1, 0, 270)]):
    for row in range(3):
        w = k.box(f"phone-pane-{i}-{row}", (0.046, 0.002, 0.026), material=lamp, parent=phone)
        k.place(w, rot=(0, 0, rz), at=(PX + dx * 0.0355, PY + dy * 0.0355, G + 0.05 + row * 0.033))


# ---- Lamp (фонарь) ----------------------------------------------------------
LX, LY = -0.16, -0.30
lamppost = k.empty("OBJ-lamp")
k.cylinder("lamp-foot", 0.016, 0.03, at=(LX, LY, G), r_top=0.009, material=dark, parent=lamppost, segs=10)
k.cylinder("lamp-post", 0.0065, 0.2, at=(LX, LY, G + 0.03), material=dark, parent=lamppost, segs=8)
lantern = k.cylinder("lamp-glass", 0.018, 0.05, segs=4, r_top=0.026, material=lamp, parent=lamppost, smooth=False)
k.place(lantern, rot=(0, 0, 45), at=(LX, LY, G + 0.23))
roof = k.cylinder("lamp-roof", 0.03, 0.025, segs=4, r_top=0.0, material=dark, parent=lamppost, smooth=False)
k.place(roof, rot=(0, 0, 45), at=(LX, LY, G + 0.28))
k.sphere("lamp-knob", 0.006, at=(LX, LY, G + 0.31), material=dark, parent=lamppost, subdiv=1)


# ---- Underground, peeking up out of the ground ------------------------------
UX, UY = 0.42, -0.34
tube_ = k.empty("OBJ-underground")
k.box("tube-stairwell", (0.12, 0.07, 0.003), at=(UX, UY, G), material=dark, parent=tube_)
for i in range(4):
    st = k.box(f"tube-step-{i}", (0.11, 0.012, 0.002), material=stone, parent=tube_)
    k.place(st, at=(UX, UY + 0.022 - i * 0.015, G + 0.0035))
for dy in (-0.035, 0.035):
    k.tube(f"tube-rail-{dy}", [(UX - 0.06, UY + dy, G + 0.035), (UX + 0.06, UY + dy, G + 0.035)], 0.003,
           material=dark, segs=5, parent=tube_)
    for dx in (-0.06, 0.0, 0.06):
        k.cylinder(f"tube-baluster-{dy}-{dx}", 0.0025, 0.035, at=(UX + dx, UY + dy, G),
                   material=dark, parent=tube_, segs=5)
k.tube("tube-rail-back", [(UX - 0.06, UY + 0.035, G + 0.035), (UX - 0.06, UY - 0.035, G + 0.035)], 0.003,
       material=dark, segs=5, parent=tube_)
k.cylinder("tube-sign-post", 0.004, 0.13, at=(UX + 0.075, UY - 0.04, G), material=dark, parent=tube_, segs=6)
ring = k.torus("tube-roundel", 0.03, 0.008, rot=(90, 0, 0), at=(UX + 0.075, UY - 0.04, G + 0.15),
               material=red, parent=tube_, segs=32, tube_segs=6)
bar = k.box("tube-bar", (0.09, 0.012, 0.018), material=blue, parent=tube_)
k.place(bar, at=(UX + 0.075, UY - 0.042, G + 0.141))


# ---- A bookshop -------------------------------------------------------------
KX, KY = -0.46, -0.28
shop = k.empty("OBJ-bookshop")
k.box("shop-body", (0.2, 0.12, 0.17), at=(KX, KY, G), material=brick, parent=shop)
k.box("shop-front", (0.2, 0.006, 0.08), at=(KX, KY - 0.062, G), material=green, parent=shop)
k.box("shop-fascia", (0.2, 0.012, 0.022), at=(KX, KY - 0.065, G + 0.08), material=cream, parent=shop)
for dx in (-0.055, 0.055):
    k.box(f"shop-window-{dx}", (0.07, 0.004, 0.05), at=(KX + dx, KY - 0.066, G + 0.018), material=lamp, parent=shop)
k.box("shop-door", (0.03, 0.004, 0.065), at=(KX, KY - 0.066, G), material=dark, parent=shop)
for dx in (-0.06, 0.0, 0.06):
    k.box(f"shop-upper-{dx}", (0.035, 0.004, 0.04), at=(KX + dx, KY - 0.061, G + 0.115), material=cream, parent=shop)
awning = k.box("shop-awning", (0.2, 0.05, 0.005), material=green, parent=shop)
awning.data.transform(__import__("mathutils").Matrix.Rotation(math.radians(-20), 4, "X"))
k.place(awning, at=(KX, KY - 0.085, G + 0.07))
roof = k.prism("shop-roof", [(-0.105, -0.065), (0.105, -0.065), (0.105, 0.065), (-0.105, 0.065)], 0.001, material=slate)
roof.parent = shop
# A pitched roof: lift the ridge line.
for v in roof.data.vertices:
    v.co.x += KX
    v.co.y += KY
    v.co.z = G + 0.17 + (0.06 * (1 - abs(v.co.y - KY) / 0.065) if v.co.z > 0.0005 else 0)
k.box("shop-chimney", (0.025, 0.025, 0.06), at=(KX + 0.06, KY + 0.02, G + 0.17), material=brick, parent=shop)


# ---- The bus on its loop ----------------------------------------------------
bus = k.empty("OBJ-bus")
bus["orbit"] = 48.0     # seconds per lap: slow, a toy rather than traffic
# Built at angle 0 on the ring, facing along the road (+Y). The viewer turns
# the whole OBJ-bus node about the base's centre.
L, W, H = 0.17, 0.062, 0.1
k.box("bus-body", (W, L, H), at=(ROAD_R, 0, 0.018), material=red, parent=bus)
k.box("bus-roof", (W * 0.94, L * 0.97, 0.008), at=(ROAD_R, 0, 0.018 + H), material=red, parent=bus)
for deck_z in (0.04, 0.083):
    for side in (-1, 1):
        k.box(f"bus-windows-{deck_z}-{side}", (0.002, L * 0.86, 0.026),
              at=(ROAD_R + side * (W / 2 + 0.001), 0.004, deck_z), material=lamp, parent=bus)
k.box("bus-windscreen", (W * 0.8, 0.002, 0.03), at=(ROAD_R, L / 2 + 0.001, 0.04), material=lamp, parent=bus)
k.box("bus-windscreen-top", (W * 0.8, 0.002, 0.026), at=(ROAD_R, L / 2 + 0.001, 0.083), material=lamp, parent=bus)
k.box("bus-stripe", (W + 0.003, L + 0.003, 0.006), at=(ROAD_R, 0, 0.074), material=cream, parent=bus)
for wy in (-0.05, 0.05):
    for side in (-1, 1):
        wh = k.cylinder(f"bus-wheel-{wy}-{side}", 0.017, 0.012, segs=12, material=dark, parent=bus)
        k.place(wh, rot=(0, 90, 0), at=(ROAD_R + side * (W / 2 - 0.004) - 0.006, wy, 0.017))


# ---- bigger landmarks (scaled about their footprints) ----------------------
k.grow(bigben, 1.1, (BX, BY, G))
k.grow(phone, 1.45, (PX, PY, G))
k.grow(lamppost, 1.45, (LX, LY, G))
k.grow(tube_, 1.35, (UX, UY, G))
k.grow(shop, 1.35, (KX, KY, G))
k.grow(bus, 1.15, (ROAD_R, 0, 0))


# ---- plane trees along the embankments --------------------------------------
keep = [(BX, BY, 0.09), (SX, SY, 0.13), (EX, EY + 0.06, 0.12), (EX - 0.2, EY, 0.06), (EX + 0.2, EY, 0.06),
        (PX, PY, 0.09), (LX, LY, 0.07), (UX + 0.03, UY, 0.13), (KX, KY, 0.2)]
keep += [(x, y, 0.12) for x, y in thames]
k.forest("DECO-trees", 40, leaf, keep, seed=9, r_max=0.74, h=(0.09, 0.13), z=G,
         round_crowns=True, trunk_mat=trunk)

k.export("london")
