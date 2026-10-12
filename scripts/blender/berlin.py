"""
berlin.py — the Berlin diorama. Nazym asked for a lot of places and for it
to look organised, not messy. So it is laid out on Berlin's own spine:

  an east-west axis across the middle:
      Brandenburger Tor -> Unter den Linden -> Museumsinsel (in the Spree's
      fork) -> Alexanderplatz with the Fernsehturm
  north of the axis:  Bundestag on the Spree bend, Gärten der Welt on
                      Kienberg with its cable car and the Wolkenhain
  south of the axis:  the Zoo (Tiergarten side), Potsdamer Platz, the Mall
                      of Berlin, the Wall along the river, Lidl and Rewe
  Ampelmann lights at the boulevard's crossings; filler is neat rows of
  Berlin blocks along streets, not scatter.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python scripts/blender/berlin.py

Reference points (looked up / well known): the Brandenburg Gate is six
pairs of Doric columns (five passages) under an attic with the Quadriga;
the Reichstag has four corner towers, a columned portico and the glass
dome; the Fernsehturm is a concrete shaft with a steel sphere and a
red-and-white antenna; on Museum Island the Berliner Dom has a green
copper dome, the Altes Museum a long colonnade, the Bode Museum a dome at
the island's tip; the Sony Center's roof is an umbrella of steel, glass and
fabric with an opening in the middle; the Mall of Berlin has light stone
fronts and a barrel glass roof; the Zoo's Elephant Gate is two lying stone
elephants carrying a red pagoda roof with green tiles and gold ornaments;
Gärten der Welt has Europe's largest Chinese garden, a cable car, and the
cloud-shaped Wolkenhain platform on Kienberg.
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

paving = k.mat("paving", (0.82, 0.80, 0.76))
earth = k.mat("earth", (0.52, 0.44, 0.36))
park = k.mat("park-green", (0.50, 0.66, 0.42))
spree = k.mat("spree", (0.34, 0.54, 0.66))
street = k.mat("street", (0.46, 0.46, 0.50))
sandstone = k.mat("sandstone", (0.90, 0.84, 0.70))
copper = k.mat("copper-green", (0.42, 0.66, 0.58))
concrete = k.mat("concrete", (0.80, 0.80, 0.80))
steel = k.mat("steel", (0.78, 0.80, 0.84))
glass_m = k.mat("facade-blue", (0.40, 0.54, 0.68))
glass_d = k.mat("facade-dark", (0.28, 0.34, 0.44))
brick = k.mat("kollhoff-brick", (0.56, 0.30, 0.22))
glow = k.mat("lamp-yellow", (1.0, 0.82, 0.42))
red = k.mat("red", (0.84, 0.16, 0.16))
white = k.mat("white", (0.96, 0.96, 0.95))
dark = k.mat("dark", (0.18, 0.18, 0.22))
leaf = k.mat("linden", (0.40, 0.62, 0.34))
trunk = k.mat("trunk", (0.38, 0.28, 0.22))
pagoda_red = k.mat("pagoda-red", (0.72, 0.18, 0.14))
tile_green = k.mat("tile-green", (0.24, 0.58, 0.40))
gold = k.mat("gold", (0.96, 0.76, 0.30))
elephant = k.mat("sandstone-elephant", (0.82, 0.76, 0.64))
amp_red = k.mat("neon-ampel-red", (1.0, 0.18, 0.16))
amp_green = k.mat("neon-ampel-green", (0.25, 1.0, 0.45))
lidl_blue = k.mat("lidl-blue", (0.0, 0.30, 0.62))
lidl_yellow = k.mat("lidl-yellow", (1.0, 0.86, 0.0))
rewe_red = k.mat("rewe-red", (0.82, 0.06, 0.10))
cloud = k.mat("wolkenhain-white", (0.96, 0.97, 1.0))
pond = k.mat("pond", (0.36, 0.58, 0.70))
murals = [k.mat(n, c) for n, c in [("mural-red", (0.92, 0.28, 0.24)), ("mural-yellow", (0.98, 0.82, 0.24)),
                                    ("mural-blue", (0.24, 0.48, 0.86)), ("mural-green", (0.30, 0.72, 0.42)),
                                    ("mural-pink", (0.94, 0.50, 0.70)), ("mural-violet", (0.58, 0.40, 0.84))]]
blocks_c = [k.mat(n, c) for n, c in [("altbau-cream", (0.92, 0.88, 0.78)), ("altbau-ochre", (0.88, 0.74, 0.52)),
                                      ("altbau-grey", (0.74, 0.74, 0.76)), ("altbau-rose", (0.86, 0.70, 0.66))]]
roof_grey = k.mat("roof-grey", (0.40, 0.42, 0.46))

k.base(paving, earth)


# ---- ground: flat, with Kienberg (Gärten der Welt) at the back right -----------
def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


KB = (0.62, 0.5)


def height(x, y):
    r = math.hypot(x, y)
    h = 0.12 * math.exp(-((x - KB[0]) ** 2 + (y - KB[1]) ** 2) / (2 * 0.1 ** 2))
    return h * (1 - smoothstep(0.88, 0.98, r)) + 0.002


RINGS, SEGS = 50, 160
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
for m in (paving, park):
    land.data.materials.append(m)
for p in land.data.polygons:
    c = p.center
    # Green: the Tiergarten west of the gate, Kienberg, and the rim.
    tier = c.x < -0.52 and abs(c.y) < 0.36
    p.material_index = 1 if (tier or c.z > 0.02 or math.hypot(c.x, c.y) > 0.86) else 0
    p.use_smooth = True
k.smooth_by_angle(land, 30)


def stand(o, x, y, rot=0.0, extra=0.0):
    o.data.transform(Matrix.Translation((x, y, height(x, y) + extra)) @ Matrix.Rotation(math.radians(rot), 4, "Z"))
    return o


def place(parts, x, y, rot=0.0, extra=0.0):
    for o in parts:
        stand(o, x, y, rot=rot, extra=extra)
    return parts


# ---- the Spree: in from the east, round Museum Island in two arms, out west ---
main_east = [(0.98, -0.34), (0.8, -0.3), (0.62, -0.25), (0.46, -0.2), (0.3, -0.14)]
west_arm = [(0.3, -0.14), (0.16, -0.1), (0.1, 0.02), (0.1, 0.14), (0.16, 0.22)]
east_arm = [(0.3, -0.14), (0.36, -0.02), (0.37, 0.12), (0.3, 0.22), (0.16, 0.22)]
main_west = [(0.16, 0.22), (0.02, 0.3), (-0.18, 0.44), (-0.4, 0.5), (-0.62, 0.5), (-0.82, 0.46), (-0.98, 0.44)]


def smooth_path(pts, n=6):
    out = []
    for a, b in zip(pts, pts[1:]):
        for i in range(n):
            t = i / n
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    out.append(pts[-1])
    return out


for name, pts, w in (("east", main_east, 0.1), ("west-arm", west_arm, 0.055), ("east-arm", east_arm, 0.055), ("west", main_west, 0.1)):
    k.ribbon(f"DECO-spree-{name}", smooth_path(pts), w, z=0.004, material=spree, clip=0.985)
# Museum Island's ground between the arms.
k.prism("DECO-museum-island", [(0.16, -0.08), (0.28, -0.1), (0.33, 0.02), (0.33, 0.14), (0.26, 0.19), (0.16, 0.19), (0.13, 0.12), (0.13, 0.0)],
        0.004, material=park)


# ---- the axis: Unter den Linden ----------------------------------------------
AXIS_Y = -0.02
X_GATE, X_ISLAND = -0.5, 0.11
udl = k.empty("OBJ-unter-den-linden")
k.box("udl-road", (X_ISLAND - X_GATE, 0.1, 0.003), at=((X_GATE + X_ISLAND) / 2, AXIS_Y, 0.003), material=street, parent=udl)
k.box("udl-promenade", (X_ISLAND - X_GATE - 0.04, 0.03, 0.004), at=((X_GATE + X_ISLAND) / 2, AXIS_Y, 0.004), material=k.mat("gravel", (0.86, 0.82, 0.72)), parent=udl)
lindens = []
for i in range(11):
    x = X_GATE + 0.06 + i * (X_ISLAND - X_GATE - 0.1) / 10
    for y in (AXIS_Y - 0.008, AXIS_Y + 0.008):
        lindens += [k.cylinder(f"udl-trunk-{i}-{y}", 0.0025, 0.02, at=(x, y, 0.004), segs=5, material=trunk),
                    k.sphere(f"udl-crown-{i}-{y}", 0.011, at=(x, y, 0.032), material=leaf, subdiv=2)]
lt = k.join("udl-lindens", lindens)
lt.parent = udl
# Schlossbrücke over the west arm onto the island.
k.box("udl-bridge", (0.07, 0.09, 0.008), at=(0.12, AXIS_Y, 0.004), material=sandstone, parent=udl)


# ---- Brandenburger Tor ---------------------------------------------------------
bt = k.empty("OBJ-brandenburger-tor")
bparts = [k.box("bt-base", (0.05, 0.16, 0.008), material=sandstone, parent=bt)]
for i in range(6):
    y = -0.07 + i * 0.028
    for x in (-0.012, 0.012):
        bparts.append(k.cylinder(f"bt-col-{i}-{x}", 0.0045, 0.075, at=(x, y, 0.008), segs=10, material=sandstone, parent=bt))
bparts.append(k.box("bt-entablature", (0.044, 0.17, 0.016), at=(0, 0, 0.083), material=sandstone, parent=bt))
bparts.append(k.box("bt-attic", (0.036, 0.11, 0.02), at=(0, 0, 0.099), material=sandstone, parent=bt))
for sy in (-1, 1):
    bparts.append(k.box(f"bt-wing-{sy}", (0.03, 0.03, 0.06), at=(0, sy * 0.1, 0.008), material=sandstone, parent=bt))
# The Quadriga: a chariot and four horses, on top, facing the city.
bparts.append(k.box("bt-quadriga-car", (0.012, 0.014, 0.012), at=(0.004, 0, 0.119), material=copper, parent=bt))
for i in range(4):
    bparts.append(k.box(f"bt-horse-{i}", (0.014, 0.004, 0.01), at=(0.016, -0.009 + i * 0.006, 0.119), material=copper, parent=bt))
bparts.append(k.cylinder("bt-victoria", 0.0025, 0.02, at=(0.002, 0, 0.131), segs=5, material=copper, parent=bt))
bparts.append(k.box("bt-pariser-platz", (0.12, 0.2, 0.003), at=(0.06, 0, 0), material=paving, parent=bt))
place(bparts, X_GATE, AXIS_Y)


# ---- Museumsinsel ----------------------------------------------------------------
mi = k.empty("OBJ-museumsinsel")
mparts = []
# Berliner Dom: cream walls, a big green copper dome, four corner domes.
mparts.append(k.box("dom-body", (0.09, 0.08, 0.06), at=(0.25, -0.02, 0.006), material=sandstone, parent=mi))
mparts.append(k.cylinder("dom-drum", 0.028, 0.03, at=(0.25, -0.02, 0.066), segs=24, material=sandstone, parent=mi))
dd = k.sphere("dom-dome", 0.032, material=copper, parent=mi, subdiv=3)
dd.data.transform(Matrix.Translation((0.25, -0.02, 0.096)) @ Matrix.Diagonal((1, 1, 1.15, 1)))
mparts.append(dd)
mparts.append(k.cylinder("dom-lantern", 0.006, 0.03, at=(0.25, -0.02, 0.13), segs=8, r_top=0.0, material=gold, parent=mi))
for sx in (-1, 1):
    for sy in (-1, 1):
        cd = k.sphere(f"dom-corner-{sx}-{sy}", 0.012, material=copper, parent=mi, subdiv=2)
        cd.data.transform(Matrix.Translation((0.25 + sx * 0.04, -0.02 + sy * 0.035, 0.07)))
        mparts.append(cd)
# Altes Museum: the long colonnade facing the Lustgarten.
mparts.append(k.box("am-body", (0.1, 0.04, 0.04), at=(0.2, 0.08, 0.006), material=sandstone, parent=mi))
for i in range(12):
    mparts.append(k.cylinder(f"am-col-{i}", 0.003, 0.034, at=(0.155 + i * 0.0082, 0.058, 0.008), segs=8, material=white, parent=mi))
mparts.append(k.box("am-cornice", (0.104, 0.046, 0.006), at=(0.2, 0.08, 0.046), material=white, parent=mi))
# Bode Museum: a dome at the island's tip.
mparts.append(k.cylinder("bode-body", 0.035, 0.05, at=(0.24, 0.16, 0.006), segs=6, material=sandstone, parent=mi, smooth=False))
bd = k.sphere("bode-dome", 0.02, material=copper, parent=mi, subdiv=2)
bd.data.transform(Matrix.Translation((0.24, 0.16, 0.056)))
mparts.append(bd)


# ---- Alexanderplatz and the Fernsehturm -----------------------------------------
TV = (0.52, 0.08)
tv = k.empty("OBJ-fernsehturm")
k.cylinder("tv-base", 0.04, 0.03, at=(TV[0], TV[1], 0.002), r_top=0.03, segs=3, material=concrete, parent=tv, smooth=False)
k.cylinder("tv-shaft", 0.018, 0.44, at=(TV[0], TV[1], 0.002), r_top=0.011, segs=20, material=concrete, parent=tv)
k.sphere("tv-sphere", 0.05, at=(TV[0], TV[1], 0.47), material=steel, parent=tv, subdiv=3)
k.cylinder("tv-sphere-band", 0.051, 0.012, at=(TV[0], TV[1], 0.462), segs=32, material=glow, parent=tv)
k.cylinder("tv-mast", 0.009, 0.05, at=(TV[0], TV[1], 0.515), segs=10, material=concrete, parent=tv)
for j in range(5):
    k.cylinder(f"tv-antenna-{j}", 0.0045 - j * 0.0006, 0.026, at=(TV[0], TV[1], 0.565 + j * 0.026), segs=6,
               material=red if j % 2 == 0 else white, parent=tv)
alex = k.empty("OBJ-alexanderplatz")
k.box("alex-square", (0.22, 0.16, 0.003), at=(0.58, -0.06, 0.002), material=paving, parent=alex)
# The Weltzeituhr: a column carrying the world-time drum and the atom model.
k.cylinder("wzu-column", 0.004, 0.05, at=(0.6, -0.08, 0.005), segs=8, material=steel, parent=alex)
k.cylinder("wzu-drum", 0.016, 0.014, at=(0.6, -0.08, 0.055), segs=16, material=k.mat("neon-weltzeituhr", (0.98, 0.84, 0.4)), parent=alex)
k.sphere("wzu-atom", 0.008, at=(0.6, -0.08, 0.08), material=steel, parent=alex, subdiv=1)
k.torus("wzu-orbit", 0.012, 0.0012, at=(0.6, -0.08, 0.08), rot=(60, 0, 0), segs=20, tube_segs=3, material=steel, parent=alex)
# Galeria on the square, a big pale block.
k.box("alex-kaufhof", (0.1, 0.05, 0.06), at=(0.66, 0.0, 0.002), material=concrete, parent=alex)
k.box("alex-kaufhof-sign", (0.06, 0.003, 0.01), at=(0.66, -0.026, 0.045), material=k.mat("neon-galeria", (0.3, 0.7, 1.0)), parent=alex)


# ---- Bundestag (Reichstag), on the Spree bend ---------------------------------
RT = (-0.4, 0.3)
rt = k.empty("OBJ-bundestag")
rparts = [k.box("rt-body", (0.17, 0.12, 0.05), material=sandstone, parent=rt)]
for sx in (-1, 1):
    for sy in (-1, 1):
        rparts.append(k.box(f"rt-tower-{sx}-{sy}", (0.03, 0.03, 0.072), at=(sx * 0.07, sy * 0.045, 0), material=sandstone, parent=rt))
# The west portico, facing the gate's side (-Y here, turned below).
rparts.append(k.box("rt-portico", (0.07, 0.02, 0.06), at=(0, -0.07, 0), material=sandstone, parent=rt))
for i in range(6):
    rparts.append(k.cylinder(f"rt-col-{i}", 0.003, 0.05, at=(-0.03 + i * 0.012, -0.08, 0.002), segs=8, material=white, parent=rt))
pd_ = k.cylinder("rt-pediment", 0.04, 0.016, segs=3, material=sandstone, parent=rt, smooth=False)
pd_.data.transform(Matrix.Translation((0, -0.072, 0.06)) @ Matrix.Diagonal((1.0, 0.4, 1, 1)) @ Matrix.Rotation(math.radians(90), 4, "Z"))
rparts.append(pd_)
# The glass dome.
gd = k.sphere("rt-glass-dome", 0.034, material=k.mat("dome-glass", (0.74, 0.86, 0.92), alpha=0.5), parent=rt, subdiv=3)
gd.data.transform(Matrix.Translation((0, 0, 0.05)) @ Matrix.Diagonal((1, 1, 0.9, 1)))
for v in gd.data.vertices:
    v.co.z = max(v.co.z, 0.05)
rparts.append(gd)
for i in range(8):
    a = 2 * math.pi * i / 8
    rparts.append(k.tube(f"rt-dome-rib-{i}", [(0.034 * math.cos(a), 0.034 * math.sin(a), 0.05), (0.024 * math.cos(a), 0.024 * math.sin(a), 0.072), (0.0, 0.0, 0.08)],
                         0.0012, material=steel, segs=3, parent=rt))
rparts.append(k.cylinder("rt-dome-cone", 0.012, 0.03, at=(0, 0, 0.05), r_top=0.002, segs=12, material=steel, parent=rt))
place(rparts, *RT, rot=-90)


# ---- the Berlin Wall: a painted stretch along the river (East Side Gallery) ---
bw = k.empty("OBJ-berlin-wall")
wall_line = [(0.4, -0.31), (0.56, -0.36), (0.72, -0.41)]
idx = 0
for a, b in zip(wall_line, wall_line[1:]):
    a, b = Vector(a), Vector(b)
    n = 7
    for i in range(n):
        t = (i + 0.5) / n
        p = a.lerp(b, t)
        ang = math.degrees(math.atan2(b.y - a.y, b.x - a.x))
        seg = k.box(f"bw-panel-{idx}", ((b - a).length / n - 0.002, 0.008, 0.05), material=concrete, parent=bw)
        stand(seg, p.x, p.y, rot=ang)
        mur = k.box(f"bw-mural-{idx}", ((b - a).length / n - 0.004, 0.002, 0.038), at=(0, -0.005, 0.005), material=murals[idx % 6], parent=bw)
        stand(mur, p.x, p.y, rot=ang)
        cap = k.cylinder(f"bw-cap-{idx}", 0.005, (b - a).length / n - 0.002, segs=8, material=concrete, parent=bw)
        cap.data.transform(Matrix.Rotation(math.radians(90), 4, "Y"))
        stand(cap, p.x, p.y, rot=ang, extra=0.052)
        idx += 1


# ---- Potsdamer Platz: the Sony Center's umbrella roof and its towers ---------
PP = (-0.34, -0.42)
pp = k.empty("OBJ-potsdamer-platz")
pparts = [k.box("pp-plaza", (0.26, 0.2, 0.003), material=paving, parent=pp)]
# Kollhoff tower: dark brick, stepped; the DB tower: rounded glass.
pparts.append(k.box("pp-kollhoff", (0.045, 0.045, 0.2), at=(-0.06, -0.05, 0), material=brick, parent=pp))
pparts.append(k.box("pp-kollhoff-top", (0.03, 0.03, 0.03), at=(-0.06, -0.05, 0.2), material=brick, parent=pp))
for b in range(9):
    pparts.append(k.box(f"pp-kollhoff-win-{b}", (0.046, 0.046, 0.003), at=(-0.06, -0.05, 0.02 + b * 0.02), material=glow, parent=pp))
db = k.cylinder("pp-db-tower", 0.03, 0.22, at=(0.02, -0.06, 0), segs=24, material=glass_m, parent=pp)
db.data.transform(Matrix.Translation((0.02, -0.06, 0)) @ Matrix.Diagonal((1.0, 0.7, 1, 1)) @ Matrix.Translation((-0.02, 0.06, 0)))
pparts.append(db)
# Sony Center: a ring of buildings under the umbrella roof.
SC = (0.06, 0.04)
for i in range(7):
    a = 2 * math.pi * i / 7
    pparts.append(k.box(f"sc-block-{i}", (0.04, 0.025, 0.07), at=(SC[0] + 0.065 * math.cos(a), SC[1] + 0.065 * math.sin(a), 0), material=glass_d, parent=pp))
roof = k.lathe("sc-roof", [(0.095, 0.075), (0.07, 0.095), (0.04, 0.11), (0.018, 0.13), (0.012, 0.115)], segs=32,
               at=(SC[0], SC[1], 0), material=k.mat("sony-fabric", (0.92, 0.92, 0.94)), parent=pp)
pparts.append(roof)
pparts.append(k.cylinder("sc-mast", 0.003, 0.15, at=(SC[0], SC[1], 0), segs=6, material=steel, parent=pp))
place(pparts, *PP)


# ---- Mall of Berlin: light stone fronts, a barrel glass roof down the middle --
MB = (0.0, -0.46)
mb = k.empty("OBJ-mall-of-berlin")
mbp = []
for sy in (-1, 1):
    mbp.append(k.box(f"mb-wing-{sy}", (0.2, 0.05, 0.07), at=(0, sy * 0.045, 0), material=blocks_c[0], parent=mb))
    for i in range(8):
        mbp.append(k.box(f"mb-win-{sy}-{i}", (0.014, 0.002, 0.04), at=(-0.085 + i * 0.024, sy * 0.071, 0.015), material=glow, parent=mb))
vault = k.lathe("mb-vault", [(0.04, 0.0), (0.035, 0.02), (0.02, 0.034), (0.0, 0.04)], segs=24, material=k.mat("barrel-glass", (0.76, 0.88, 0.94)), parent=mb)
vault.data.transform(Matrix.Translation((0, 0, 0.065)) @ Matrix.Diagonal((1, 0.9, 1, 1)) @ Matrix.Rotation(math.radians(90), 4, "Y")
                     @ Matrix.Diagonal((1, 1, 1, 1)))
mbp.append(vault)
mbp.append(k.box("mb-arcade-floor", (0.2, 0.04, 0.004), material=paving, parent=mb))
mbp.append(k.box("mb-sign", (0.05, 0.003, 0.012), at=(0, -0.071, 0.05), material=k.mat("neon-mall-sign", (0.95, 0.8, 0.4)), parent=mb))
place(mbp, *MB)


# ---- the Zoo: the Elephant Gate, enclosures, the elephants ---------------------
ZO = (-0.72, -0.12)
zoo = k.empty("OBJ-berlin-zoo")
zparts = []
# Two lying stone elephants carry the red pagoda roof.
for sy in (-1, 1):
    body = k.sphere(f"zoo-elephant-{sy}", 1.0, material=elephant, parent=zoo, subdiv=2)
    body.data.transform(Matrix.Translation((0, sy * 0.032, 0.016)) @ Matrix.Diagonal((0.026, 0.014, 0.016, 1)))
    head = k.sphere(f"zoo-elephant-head-{sy}", 0.011, at=(0.024, sy * 0.032, 0.026), material=elephant, parent=zoo, subdiv=2)
    trunk_ = k.tube(f"zoo-elephant-trunk-{sy}", [(0.032, sy * 0.032, 0.024), (0.04, sy * 0.032, 0.012), (0.043, sy * 0.032, 0.004)], 0.003,
                    material=elephant, segs=5, parent=zoo)
    post = k.box(f"zoo-gate-post-{sy}", (0.01, 0.01, 0.06), at=(0, sy * 0.032, 0.028), material=pagoda_red, parent=zoo)
    zparts += [body, head, trunk_, post]
zparts.append(k.box("zoo-gate-beam", (0.014, 0.08, 0.012), at=(0, 0, 0.082), material=pagoda_red, parent=zoo))
pr = k.cylinder("zoo-gate-roof", 0.07, 0.03, segs=4, r_top=0.02, material=tile_green, parent=zoo, smooth=False)
pr.data.transform(Matrix.Translation((0, 0, 0.094)) @ Matrix.Diagonal((0.45, 1.0, 1, 1)) @ Matrix.Rotation(math.radians(45), 4, "Z"))
zparts.append(pr)
zparts.append(k.cylinder("zoo-gate-finial", 0.004, 0.024, at=(0, 0, 0.124), segs=6, r_top=0.0, material=gold, parent=zoo))
# Behind the gate: an elephant enclosure and a pond.
zparts.append(k.prism("zoo-pond", [(-0.08 + 0.04 * math.cos(a), 0.02 + 0.03 * math.sin(a)) for a in [2 * math.pi * i / 20 for i in range(20)]],
                      0.003, material=pond, parent=zoo))
for i, (x, y) in enumerate([(-0.12, -0.04), (-0.15, 0.02)]):
    e = k.sphere(f"zoo-ele-{i}", 1.0, material=k.mat("elephant-grey", (0.58, 0.58, 0.6)), parent=zoo, subdiv=2)
    e.data.transform(Matrix.Translation((x, y, 0.022)) @ Matrix.Diagonal((0.02, 0.012, 0.014, 1)))
    zparts.append(e)
    for lx in (-0.01, 0.01):
        for ly in (-0.006, 0.006):
            zparts.append(k.cylinder(f"zoo-ele-leg-{i}-{lx}-{ly}", 0.003, 0.012, at=(x + lx, y + ly, 0.002), segs=5,
                                     material=k.mat("elephant-grey", (0.58, 0.58, 0.6)), parent=zoo))
place(zparts, *ZO, rot=0)


# ---- Gärten der Welt: Kienberg, the Wolkenhain, the Chinese garden, a cable car
gw = k.empty("OBJ-gaerten-der-welt")
# The Wolkenhain on Kienberg's top: a light, cloud-shaped platform.
top_z = height(*KB)
for i in range(6):
    a = 2 * math.pi * i / 6
    k.cylinder(f"wh-leg-{i}", 0.002, 0.05, at=(KB[0] + 0.025 * math.cos(a), KB[1] + 0.025 * math.sin(a), top_z), segs=4, material=white, parent=gw)
for i, (dx, dy, r) in enumerate([(0, 0, 0.03), (0.024, 0.01, 0.02), (-0.022, 0.012, 0.02), (0.006, -0.022, 0.018)]):
    c = k.sphere(f"wh-cloud-{i}", r, material=cloud, parent=gw, subdiv=2)
    c.data.transform(Matrix.Translation((KB[0] + dx, KB[1] + dy, top_z + 0.055)) @ Matrix.Diagonal((1, 1, 0.45, 1)))
# The Chinese garden: a pavilion on a lake, a zigzag bridge, below the hill.
CG = (0.38, 0.5)
k.prism("cg-lake", [(CG[0] + 0.07 * math.cos(a), CG[1] + 0.045 * math.sin(a)) for a in [2 * math.pi * i / 24 for i in range(24)]], 0.004,
        z0=height(*CG), material=pond, parent=gw)
pav = k.cylinder("cg-pavilion", 0.018, 0.022, at=(CG[0] + 0.02, CG[1] + 0.005, height(*CG) + 0.004), segs=8, material=pagoda_red, parent=gw)
pr2 = k.cylinder("cg-pavilion-roof", 0.03, 0.018, at=(CG[0] + 0.02, CG[1] + 0.005, height(*CG) + 0.026), r_top=0.0, segs=8, material=tile_green, parent=gw, smooth=False)
for i in range(4):
    k.box(f"cg-bridge-{i}", (0.022, 0.008, 0.004), at=(CG[0] - 0.06 + i * 0.02, CG[1] - 0.012 + (i % 2) * 0.01, height(*CG) + 0.004),
          material=k.mat("bridge-stone", (0.84, 0.82, 0.76)), parent=gw)
# The cable car, over the gardens and up the hill.
LO, UP = Vector((0.3, 0.68)), Vector((KB[0] - 0.04, KB[1] + 0.04))
ang = math.degrees(math.atan2(UP.y - LO.y, UP.x - LO.x))
for nm, P in (("lower", LO), ("upper", UP)):
    stand(k.box(f"gw-cc-{nm}", (0.03, 0.026, 0.03), material=white, parent=gw), P.x, P.y, rot=ang)
A = Vector((LO.x, LO.y, height(*LO) + 0.026))
B = Vector((UP.x, UP.y, height(*UP) + 0.026))
SAG = 0.015
side = Vector((-(UP - LO).normalized().y, (UP - LO).normalized().x, 0)) * 0.007
for li, off in enumerate((side, -side)):
    pts = []
    for i in range(21):
        t = i / 20
        p = A.lerp(B, t) + off
        p.z -= SAG * 4 * t * (1 - t)
        pts.append(tuple(p))
    k.tube(f"gw-cable-{li}", pts, 0.0008, material=dark, segs=3, parent=gw)
for li, (off, frm, to) in enumerate(((side, A, B), (-side, B, A))):
    for n in range(2):
        cab = k.empty(f"gw-cabin-{li}-{n}", parent=gw)
        cab.location = frm + off
        delta = (to + off) - (frm + off)
        cab["shuttle"] = [delta.x, delta.y, delta.z]
        cab["period"] = 18.0
        cab["phase"] = 0.5 * n + 0.25 * li
        cab["sag"] = SAG
        for o in (k.box(f"gw-cab-{li}-{n}", (0.012, 0.01, 0.011), at=(0, 0, -0.017), material=k.mat("cabin-blue", (0.2, 0.5, 0.86)), parent=cab),
                  k.cylinder(f"gw-hang-{li}-{n}", 0.0008, 0.008, at=(0, 0, -0.008), segs=3, material=dark, parent=cab)):
            o.data.transform(Matrix.Rotation(math.radians(ang), 4, "Z"))


# ---- Ampelmann: the East German traffic-light men at the boulevard's crossings -
amp = k.empty("OBJ-ampelmann")
for i, x in enumerate((-0.2, 0.0)):
    for sy in (-1, 1):
        y = AXIS_Y + sy * 0.06
        k.cylinder(f"amp-pole-{i}-{sy}", 0.0025, 0.06, at=(x, y, 0.004), segs=6, material=dark, parent=amp)
        k.box(f"amp-box-{i}-{sy}", (0.012, 0.01, 0.03), at=(x, y, 0.064), material=dark, parent=amp)
        # Red man (arms out) above, green man (walking, hat) below, lit.
        k.box(f"amp-red-{i}-{sy}", (0.008, 0.002, 0.009), at=(x, y - sy * 0.0052, 0.08), material=amp_red, parent=amp)
        k.box(f"amp-red-arms-{i}-{sy}", (0.011, 0.002, 0.002), at=(x, y - sy * 0.0052, 0.085), material=amp_red, parent=amp)
        k.box(f"amp-green-{i}-{sy}", (0.005, 0.002, 0.009), at=(x, y - sy * 0.0052, 0.067), material=amp_green, parent=amp)
        k.box(f"amp-green-hat-{i}-{sy}", (0.008, 0.002, 0.0015), at=(x, y - sy * 0.0052, 0.0765), material=amp_green, parent=amp)
# Zebra crossings at the two lights.
for i, x in enumerate((-0.2, 0.0)):
    for j in range(6):
        k.box(f"amp-zebra-{i}-{j}", (0.024, 0.006, 0.001), at=(x - 0.02, AXIS_Y - 0.04 + j * 0.016, 0.006), material=white, parent=amp)


# ---- Lidl and Rewe, in a neighbourhood corner ------------------------------------
lidl = k.empty("OBJ-lidl")
LP = (0.24, -0.62)
lparts = [k.box("lidl-store", (0.12, 0.08, 0.04), material=white, parent=lidl),
          k.box("lidl-front", (0.11, 0.002, 0.025), at=(0, -0.041, 0.004), material=glow, parent=lidl),
          k.box("lidl-roof-band", (0.122, 0.082, 0.008), at=(0, 0, 0.04), material=lidl_blue, parent=lidl)]
# The logo: a blue square with a yellow circle and a red ring.
lparts.append(k.box("lidl-sign-board", (0.024, 0.004, 0.024), at=(0.04, -0.044, 0.04), material=lidl_blue, parent=lidl))
lg = k.cylinder("lidl-sign-circle", 0.0095, 0.002, segs=20, material=lidl_yellow, parent=lidl)
lg.data.transform(Matrix.Translation((0.04, -0.047, 0.052)) @ Matrix.Rotation(math.radians(90), 4, "X"))
lparts.append(lg)
lr = k.torus("lidl-sign-ring", 0.0085, 0.0012, rot=(90, 0, 0), segs=20, tube_segs=3, material=red, parent=lidl)
lr.data.transform(Matrix.Translation((0.04, -0.049, 0.052)))
lparts.append(lr)
lparts.append(k.box("lidl-car-park", (0.12, 0.05, 0.002), at=(0, -0.07, 0), material=street, parent=lidl))
place(lparts, *LP, rot=10)

rewe = k.empty("OBJ-rewe")
RP = (0.46, -0.56)
wparts = [k.box("rewe-store", (0.11, 0.08, 0.042), material=k.mat("rewe-grey", (0.86, 0.86, 0.86)), parent=rewe),
          k.box("rewe-front", (0.1, 0.002, 0.026), at=(0, -0.041, 0.004), material=glow, parent=rewe),
          k.box("rewe-sign", (0.07, 0.004, 0.014), at=(0, -0.043, 0.032), material=rewe_red, parent=rewe),
          k.box("rewe-sign-letters", (0.054, 0.005, 0.005), at=(0, -0.044, 0.0365), material=white, parent=rewe),
          k.box("rewe-car-park", (0.11, 0.05, 0.002), at=(0, -0.07, 0), material=street, parent=rewe)]
place(wparts, *RP, rot=20)


# ---- bigger landmarks, each grown about its own footprint ----------------------
def grow_in_place(o, f):
    pts = []
    stack = [o]
    while stack:
        x = stack.pop()
        if x.type == "MESH":
            pts += [x.matrix_world @ v.co for v in x.data.vertices]
        stack.extend(x.children)
    cx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2
    cy = (min(p.y for p in pts) + max(p.y for p in pts)) / 2
    k.grow(o, f, (cx, cy, height(cx, cy)))


for o, f in [(bt, 1.8), (mi, 1.3), (alex, 1.4), (rt, 1.6), (pp, 1.45), (mb, 1.4), (zoo, 1.6), (lidl, 1.5), (rewe, 1.5)]:
    grow_in_place(o, f)
for o in bw.children:          # the Wall: taller panels, same line
    o.data.transform(Matrix.Translation((0, 0, 0)) @ Matrix.Diagonal((1, 1, 1.4, 1)))


# ---- filler: neat rows of Berlin blocks along streets, and park trees --------
rnd = random.Random(4)
blocks = []
# Blocks along streets parallel to the axis, south of it (between the axis and
# Potsdamer Platz) and north of it toward the river: tidy rows, not scatter.
rows = [(-0.36, 0.12, -0.22, 0.12), (-0.12, 0.12, 0.0, 0.12), (-0.28, -0.14, -0.06, -0.14),
        (-0.04, -0.14, 0.08, -0.14), (-0.02, -0.26, 0.12, -0.26), (0.18, -0.36, 0.34, -0.36),
        (0.62, 0.2, 0.74, 0.2), (0.62, -0.18, 0.78, -0.18), (-0.2, 0.26, -0.06, 0.26),
        # East of the river round Alexanderplatz, and north of the river bend.
        (0.42, 0.3, 0.56, 0.34), (0.68, -0.02, 0.8, 0.04), (0.44, -0.12, 0.44, 0.02),
        (-0.26, 0.58, 0.0, 0.44), (-0.62, 0.62, -0.36, 0.66), (0.02, 0.56, 0.16, 0.48),
        # The south edge, behind Potsdamer Platz and the supermarkets.
        (-0.44, -0.7, -0.24, -0.74), (0.02, -0.7, 0.14, -0.74)]
for ri, (x0, y0, x1, y1) in enumerate(rows):
    n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 0.04))
    for i in range(n):
        t = (i + 0.5) / n
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        h = 0.045 + 0.01 * ((ri + i) % 3)
        col = blocks_c[(ri + i) % 4]
        blocks.append(stand(k.box(f"blk-{ri}-{i}", (0.034, 0.04, h), material=col), x, y))
        blocks.append(stand(k.box(f"blk-roof-{ri}-{i}", (0.036, 0.042, 0.006), material=roof_grey), x, y, extra=h))
        for f in range(2):
            blocks.append(stand(k.box(f"blk-win-{ri}-{i}-{f}", (0.028, 0.042, 0.003), material=glow), x, y, extra=0.014 + f * 0.016))
k.join("DECO-blocks", blocks)
# Tiergarten trees between the zoo and the gate, and some along the river.
trees = []
for i in range(40):
    x, y = rnd.uniform(-0.62, -0.54), rnd.uniform(-0.32, 0.3)
    if i % 2:
        x = rnd.uniform(-0.64, -0.55)
    if abs(y - AXIS_Y) < 0.06:
        continue
    h = rnd.uniform(0.05, 0.07)
    trees += [k.cylinder(f"tg-t-{i}", 0.004, h * 0.4, at=(x, y, 0.002), segs=5, material=trunk),
              k.sphere(f"tg-c-{i}", h * 0.42, at=(x, y, 0.002 + h * 0.7), material=leaf, subdiv=2)]
for i in range(26):
    a = rnd.uniform(0, 2 * math.pi)
    d = rnd.uniform(0.8, 0.88)
    x, y = d * math.cos(a), d * math.sin(a)
    if any((x - qx) ** 2 + (y - qy) ** 2 < 0.12 ** 2 for qx, qy in [ZO, LP, RP, KB, (0.3, 0.68)]):
        continue
    h = rnd.uniform(0.05, 0.07)
    trees += [k.cylinder(f"rim-t-{i}", 0.004, h * 0.4, at=(x, y, height(x, y)), segs=5, material=trunk),
              k.sphere(f"rim-c-{i}", h * 0.42, at=(x, y, height(x, y) + h * 0.7), material=leaf, subdiv=2)]
for i in range(16):   # Kienberg's slopes
    a = rnd.uniform(0, 2 * math.pi)
    x, y = KB[0] + 0.09 * math.cos(a), KB[1] + 0.09 * math.sin(a)
    h = rnd.uniform(0.04, 0.06)
    trees += [k.sphere(f"kb-c-{i}", h * 0.45, at=(x, y, height(x, y) + h * 0.5), material=leaf, subdiv=2)]
k.join("DECO-trees", trees)

k.export("berlin")
