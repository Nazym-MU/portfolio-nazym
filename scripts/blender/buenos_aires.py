"""
buenos_aires.py — the Buenos Aires diorama, from Nazym's sketch. The
jacarandas are violet on purpose.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python scripts/blender/buenos_aires.py

            Caminito      |avenue|      Teatro Colón
                      jacarandas
                         Obelisco
                      jacarandas
          La Bombonera    |      |   empanadas
                          ~~~~ dock ~~~~ Puente de la Mujer
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Matrix  # noqa: E402
import diorama_kit as k  # noqa: E402

k.reset()

paving = k.mat("paving", (0.88, 0.85, 0.78))
side = k.mat("base-dark", (0.24, 0.22, 0.28))
asphalt = k.mat("asphalt", (0.32, 0.32, 0.36))
paint = k.mat("road-white", (0.95, 0.95, 0.92))
grass = k.mat("grass", (0.58, 0.70, 0.44))
white = k.mat("white", (0.96, 0.95, 0.92))
violet = k.mat("jacaranda", (0.62, 0.45, 0.86))
trunk = k.mat("trunk", (0.38, 0.28, 0.22))
water = k.mat("river", (0.22, 0.34, 0.50))
boca_blue = k.mat("boca-blue", (0.08, 0.22, 0.55))
boca_gold = k.mat("boca-gold", (0.98, 0.78, 0.18))
pitch = k.mat("pitch", (0.36, 0.60, 0.30))
cream = k.mat("cream", (0.94, 0.88, 0.74))
slate = k.mat("slate", (0.36, 0.40, 0.46))
lamp = k.mat("lamp-yellow", (1.0, 0.82, 0.42))
dark = k.mat("dark", (0.18, 0.18, 0.22))
pastry = k.mat("empanada", (0.90, 0.66, 0.34))
caminito = [k.mat(n, c) for n, c in [
    ("caminito-red", (0.86, 0.26, 0.22)), ("caminito-yellow", (0.98, 0.80, 0.25)),
    ("caminito-blue", (0.22, 0.48, 0.80)), ("caminito-green", (0.30, 0.66, 0.46)),
    ("caminito-orange", (0.95, 0.52, 0.22)), ("caminito-pink", (0.92, 0.50, 0.62)),
]]

k.base(paving, side)

# ---- Avenida 9 de Julio, front to back through the Obelisco -----------------
k.ribbon("DECO-avenue", [(0, y / 100) for y in range(-100, 101, 5)], 0.2, z=0.002, material=asphalt)
marks = []
for i, y in enumerate(range(-90, 91, 9)):
    if abs(y) < 16:
        continue
    for x in (-0.033, 0.033):
        d = k.box(f"mark-{i}-{x}", (0.006, 0.04, 0.002), at=(x, y / 100, 0.003), material=paint)
        marks.append(d)
k.join("DECO-road-marks", marks)
k.cylinder("DECO-obelisco-plaza", 0.15, 0.006, segs=48, material=grass)

obelisco = k.empty("OBJ-obelisco")
k.box("obelisco-step", (0.1, 0.1, 0.02), at=(0, 0, 0.006), material=white, parent=obelisco)
shaft = k.cylinder("obelisco-shaft", 0.045, 0.58, at=(0, 0, 0.026), r_top=0.032, segs=4,
                   material=white, parent=obelisco, smooth=False)
k.place(shaft, rot=(0, 0, 45))
tip = k.cylinder("obelisco-tip", 0.032, 0.05, at=(0, 0, 0.606), r_top=0.0, segs=4,
                 material=white, parent=obelisco, smooth=False)
k.place(tip, rot=(0, 0, 45))
k.box("obelisco-window", (0.012, 0.002, 0.016), at=(0, -0.0235, 0.57), material=lamp, parent=obelisco)


# ---- Jacarandas, lining the avenue ------------------------------------------
def jacaranda(x, y, h, i):
    """Cartoon jacaranda: a trunk and a stack of violet puffs."""
    t = k.cylinder(f"jac-trunk-{i}", 0.008, h * 0.35, at=(x, y, 0), segs=6, material=trunk)
    parts = [t]
    for j, (dz, r) in enumerate([(0.42, 0.05), (0.62, 0.044), (0.8, 0.034)]):
        s = k.sphere(f"jac-puff-{i}-{j}", r * h / 0.2, at=(x + 0.006 * (j % 2), y, h * dz),
                     material=violet, subdiv=2)
        parts.append(s)
    return parts


trees = []
i = 0
for x in (-0.15, 0.15):
    for y in (-0.78, -0.62, -0.46, -0.3, 0.3, 0.46, 0.62, 0.78):
        if math.hypot(x, y) > 0.9:
            continue
        trees += jacaranda(x, y, 0.19 + 0.02 * ((i * 7) % 3), i)
        i += 1
k.join("DECO-jacarandas", trees)


# ---- El Caminito ------------------------------------------------------------
cam = k.empty("OBJ-caminito")
CX, CY, ang = -0.52, 0.42, math.radians(-35)
rot = Matrix.Rotation(ang, 4, "Z")
for n in range(6):
    h = 0.09 + 0.035 * ((n * 5) % 3)
    w = 0.075
    lx = (n - 2.5) * (w + 0.004)
    body = k.box(f"cam-house-{n}", (w, 0.08, h), at=(lx, 0, 0), material=caminito[n % 6], parent=cam)
    trim = k.box(f"cam-trim-{n}", (w + 0.004, 0.084, 0.008), at=(lx, 0, h), material=caminito[(n + 3) % 6], parent=cam)
    win = k.box(f"cam-window-{n}", (0.022, 0.003, 0.028), at=(lx - 0.015, -0.041, h * 0.55), material=lamp, parent=cam)
    door = k.box(f"cam-door-{n}", (0.018, 0.003, 0.04), at=(lx + 0.018, -0.041, 0), material=caminito[(n + 2) % 6], parent=cam)
    bal = k.box(f"cam-balcony-{n}", (0.04, 0.016, 0.004), at=(lx - 0.015, -0.048, h * 0.48), material=dark, parent=cam)
    for o in (body, trim, win, door, bal):
        k.place(o, at=(0, 0, 0))
        o.data.transform(Matrix.Translation((CX, CY, 0)) @ rot)


# ---- La Bombonera -----------------------------------------------------------
BX, BY = -0.50, -0.36
bom = k.empty("OBJ-la-bombonera")


def rrect(w, d, r, n=6):
    pts = []
    for cx, cy, a0 in [(w / 2 - r, d / 2 - r, 0), (-w / 2 + r, d / 2 - r, 90),
                       (-w / 2 + r, -d / 2 + r, 180), (w / 2 - r, -d / 2 + r, 270)]:
        for j in range(n + 1):
            a = math.radians(a0 + 90 * j / n)
            pts.append((BX + cx + r * math.cos(a), BY + cy + r * math.sin(a)))
    return pts


inner = [(BX - 0.09, BY - 0.065), (BX + 0.09, BY - 0.065), (BX + 0.09, BY + 0.065), (BX - 0.09, BY + 0.065)]
k.prism("bom-stands", rrect(0.3, 0.24, 0.05), 0.07, holes=[inner], material=boca_blue).parent = bom
k.prism("bom-band", rrect(0.304, 0.244, 0.052), 0.016, z0=0.07, holes=[rrect(0.27, 0.21, 0.04)],
        material=boca_gold).parent = bom
k.box("bom-pitch", (0.18, 0.13, 0.004), at=(BX, BY, 0), material=pitch, parent=bom)
# The famous flat side: a tall straight block of boxes instead of a stand.
k.box("bom-flat-side", (0.3, 0.035, 0.14), at=(BX, BY + 0.1, 0), material=boca_gold, parent=bom)
for j in range(5):
    k.box(f"bom-box-{j}", (0.045, 0.003, 0.02), at=(BX - 0.1 + j * 0.05, BY + 0.0815, 0.09),
          material=lamp, parent=bom)
k.box("bom-stripe", (0.304, 0.038, 0.02), at=(BX, BY + 0.1, 0.05), material=boca_blue, parent=bom)


# ---- Teatro Colón -----------------------------------------------------------
TX, TY = 0.50, 0.40
colon = k.empty("OBJ-teatro-colon")
k.box("colon-body", (0.26, 0.18, 0.12), at=(TX, TY, 0), material=cream, parent=colon)
k.box("colon-cornice", (0.27, 0.19, 0.012), at=(TX, TY, 0.12), material=white, parent=colon)
roof = k.cylinder("colon-roof", 0.15, 0.05, at=(0, 0, 0), r_top=0.07, segs=4, material=slate, parent=colon, smooth=False)
roof.data.transform(Matrix.Diagonal((1.25, 0.85, 1, 1)) @ Matrix.Rotation(math.radians(45), 4, "Z"))
k.place(roof, at=(TX, TY, 0.132))
k.cylinder("colon-dome", 0.035, 0.03, at=(TX, TY, 0.18), r_top=0.012, segs=16, material=slate, parent=colon)
# Portico on the side facing the avenue (-X).
k.box("colon-portico-floor", (0.04, 0.14, 0.012), at=(TX - 0.15, TY, 0), material=white, parent=colon)
for j in range(6):
    k.cylinder(f"colon-column-{j}", 0.007, 0.09, at=(TX - 0.155, TY - 0.06 + j * 0.024, 0.012),
               segs=8, material=white, parent=colon)
k.box("colon-entablature", (0.04, 0.15, 0.016), at=(TX - 0.15, TY, 0.102), material=white, parent=colon)
ped = k.prism("colon-pediment", [(0, -0.075), (0, 0.075), (0.035, 0)], 0.03, material=white)
ped.data.transform(Matrix.Rotation(math.radians(-90), 4, "Y"))
k.place(ped, at=(TX - 0.13, TY, 0.118))
ped.parent = colon
for j in range(4):
    k.box(f"colon-window-{j}", (0.003, 0.025, 0.035), at=(TX - 0.1315, TY - 0.06 + j * 0.04, 0.03),
          material=lamp, parent=colon)


# ---- The empanada place -----------------------------------------------------
EX, EY = 0.40, -0.24
emp = k.empty("OBJ-empanadas")
k.box("emp-body", (0.13, 0.1, 0.09), at=(EX, EY, 0), material=caminito[4], parent=emp)
k.box("emp-roof", (0.14, 0.11, 0.01), at=(EX, EY, 0.09), material=white, parent=emp)
k.box("emp-window", (0.003, 0.06, 0.035), at=(EX - 0.0665, EY + 0.012, 0.03), material=lamp, parent=emp)
k.box("emp-door", (0.003, 0.022, 0.05), at=(EX - 0.0665, EY - 0.032, 0), material=dark, parent=emp)
for j in range(6):
    st = k.box(f"emp-awning-{j}", (0.035, 0.0183, 0.004), material=white if j % 2 else caminito[0], parent=emp)
    st.data.transform(Matrix.Rotation(math.radians(25), 4, "Y"))
    k.place(st, at=(EX - 0.08, EY - 0.046 + j * 0.0183, 0.068))
# A giant cartoon empanada on the roof: a half-disc with a crimped edge.
emp_pts = []
for j in range(25):
    a = math.pi * j / 24
    rr = 0.05 + (0.004 if j % 2 else 0.0)
    emp_pts.append((rr * math.cos(a), rr * math.sin(a)))
pie = k.prism("emp-sign", emp_pts, 0.022, material=pastry)
pie.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
pie.data.transform(Matrix.Rotation(math.radians(90), 4, "Z"))
k.place(pie, at=(EX, EY - 0.011 + 0.022 / 2 + 0.0, 0.1))
pie.parent = emp


# ---- Puerto Madero dock and Puente de la Mujer ------------------------------
dock = [(0.78 * math.cos(math.radians(a)), 0.78 * math.sin(math.radians(a))) for a in range(-78, -6, 3)]
k.ribbon("DECO-dock", dock, 0.11, z=0.003, material=water)
BA = math.radians(-50)
bx, by = 0.78 * math.cos(BA), 0.78 * math.sin(BA)
radial = (math.cos(BA), math.sin(BA))
tang = (-math.sin(BA), math.cos(BA))
puente = k.empty("OBJ-puente-de-la-mujer")
deck = k.box("puente-deck", (0.2, 0.026, 0.008), material=white, parent=puente)
deck.data.transform(Matrix.Rotation(BA, 4, "Z"))
k.place(deck, at=(bx, by, 0.008))
# The leaning mast over the deck, and the cables fanning down to it.
def on_deck(t, z):
    return (bx + radial[0] * t, by + radial[1] * t, z)


foot = on_deck(-0.075, 0.016)
top = (foot[0] + radial[0] * 0.07 + tang[0] * 0.012, foot[1] + radial[1] * 0.07 + tang[1] * 0.012, 0.19)
k.tube("puente-mast", [foot, top], 0.007, material=white, segs=6, parent=puente)
for j in range(5):
    k.tube(f"puente-cable-{j}", [top, on_deck(0.0 + 0.024 * j, 0.016)], 0.0018,
           material=white, segs=4, parent=puente)


# ---- bigger landmarks (scaled about their footprints) ----------------------
k.grow(obelisco, 1.1, (0, 0, 0))
k.grow(cam, 1.3, (CX, CY, 0))
k.grow(bom, 1.25, (BX, BY, 0))
k.grow(colon, 1.3, (TX, TY, 0))
k.grow(emp, 1.5, (EX, EY, 0))
k.grow(puente, 1.25, (bx, by, 0))


k.export("buenos-aires")
