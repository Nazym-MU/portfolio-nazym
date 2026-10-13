"""
ushuaia.py — the Ushuaia diorama: the mountains, the trail to Laguna
Esmeralda, the Beagle Channel, and the "fin del mundo" sign on the waterfront.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python scripts/blender/ushuaia.py

        Ojo del Albino glacier        Martial range + glacier
     cirque  ( Laguna Esmeralda )                         Monte Olivia
               \  outlet stream, beaver dams               Cinco Hermanos
                \     peat bog + boardwalk
                 \   lenga forest (some turned red)
                  \      trailhead
     ====== USHUAIA · fin del mundo ======     coloured tin-roofed houses, pier
     ~~~~~~~~~~~~~~ the Beagle Channel, a catamaran going to and fro ~~~~~~~~~~

The real trail: lenga beech forest first, then the open Carbajal valley peat
bog on log boardwalks past beaver dams, up a last rise to the emerald lake,
coloured by silt from the Ojo del Albino glacier hanging above it.
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
import diorama_kit as k  # noqa: E402

k.reset()

sea = k.mat("beagle-sea", (0.20, 0.40, 0.58))
sea_side = k.mat("sea-deep", (0.14, 0.30, 0.46))
grass = k.mat("fuegian-grass", (0.50, 0.62, 0.38))
bog = k.mat("peat-bog", (0.66, 0.58, 0.32))
rock = k.mat("slate-rock", (0.56, 0.53, 0.55))
scree = k.mat("scree", (0.60, 0.58, 0.58))
snow = k.mat("snow", (0.97, 0.97, 0.99))
glacier = k.mat("glacier-ice", (0.78, 0.92, 0.98))
shingle = k.mat("shingle", (0.66, 0.62, 0.56))
emerald = k.mat("laguna-emerald", (0.16, 0.70, 0.60))
stream = k.mat("stream", (0.36, 0.66, 0.74))
wood = k.mat("wood", (0.52, 0.36, 0.22))
wood_dark = k.mat("wood-dark", (0.36, 0.24, 0.15))
sticks = k.mat("beaver-sticks", (0.44, 0.32, 0.22))
snag = k.mat("dead-snag", (0.70, 0.68, 0.64))
trunk = k.mat("trunk", (0.36, 0.28, 0.22))
lenga = [k.mat("lenga-green", (0.32, 0.52, 0.26)), k.mat("lenga-dark", (0.24, 0.42, 0.22)),
         k.mat("lenga-red", (0.80, 0.26, 0.16)), k.mat("lenga-orange", (0.90, 0.54, 0.18))]
panel = k.mat("sign-cream", (0.96, 0.93, 0.84))
ink_blue = k.mat("sign-blue", (0.12, 0.30, 0.62))
ink_red = k.mat("sign-red", (0.80, 0.16, 0.14))
marker = k.mat("marker-yellow", (0.98, 0.80, 0.16))
road = k.mat("road", (0.40, 0.40, 0.42))
white = k.mat("white", (0.95, 0.95, 0.93))
concrete = k.mat("pier-concrete", (0.78, 0.77, 0.74))
hull_red = k.mat("hull-red", (0.80, 0.16, 0.14))
dark = k.mat("dark", (0.18, 0.18, 0.22))
win = k.mat("window-blue", (0.70, 0.84, 0.96))
walls = [k.mat(n, c) for n, c in [("wall-red", (0.84, 0.30, 0.24)), ("wall-yellow", (0.96, 0.80, 0.36)),
                                   ("wall-teal", (0.30, 0.64, 0.64)), ("wall-blue", (0.36, 0.52, 0.80)),
                                   ("wall-cream", (0.94, 0.90, 0.78)), ("wall-green", (0.44, 0.68, 0.42)),
                                   ("wall-orange", (0.94, 0.58, 0.28))]]
roofs = [k.mat(n, c) for n, c in [("tin-red", (0.72, 0.16, 0.14)), ("tin-green", (0.22, 0.48, 0.34)),
                                   ("tin-blue", (0.22, 0.36, 0.62)), ("tin-grey", (0.56, 0.58, 0.62))]]

# ---- the plinth is the channel; the land rises behind the shore ---------------
k.base(sea, sea_side)


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def lerp_pts(pts, y):
    if y <= pts[0][0]:
        return pts[0][1]
    for (y0, v0), (y1, v1) in zip(pts, pts[1:]):
        if y <= y1:
            return v0 + (v1 - v0) * (y - y0) / (y1 - y0)
    return pts[-1][1]


def shore_y(x):
    return -0.47 + 0.035 * math.sin(3.2 * x + 0.6)


def catmull(pts, n=10):
    P = [Vector(p) for p in pts]
    P = [P[0]] + P + [P[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for s in range(n):
            t = s / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return out


def seg_dist(p, pts):
    best = 9.0
    for a, b in zip(pts, pts[1:]):
        ab = b - a
        t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-12)))
        best = min(best, (p - (a + ab * t)).length)
    return best


LAKE = Vector((-0.40, 0.45))
LAKE_Z = 0.205
OLIVIA = Vector((0.52, 0.34))
TRAIL = catmull([(0.07, -0.21), (-0.01, -0.13), (-0.09, -0.05), (-0.15, 0.03), (-0.19, 0.11),
                 (-0.22, 0.19), (-0.27, 0.27), (-0.33, 0.335)], 10)
RIVER = catmull([(-0.43, 0.35), (-0.41, 0.25), (-0.37, 0.14), (-0.35, 0.02), (-0.33, -0.12),
                 (-0.31, -0.28), (-0.30, -0.44), (-0.30, -0.56)], 10)
FLOOR = [(-0.6, 0.0), (-0.45, 0.012), (-0.3, 0.04), (-0.1, 0.075), (0.05, 0.10), (0.22, 0.12),
         (0.30, 0.16), (0.36, 0.20)]
# Sharp faceted peaks (x, y, height, base radius, facet turn): the cirque round
# the lake, then the Martial range's crest behind town.
CONES = [(-0.67, 0.38, 0.34, 0.17, 0.3), (-0.58, 0.58, 0.46, 0.18, 0.9), (-0.42, 0.72, 0.52, 0.18, 0.2),
         (-0.22, 0.67, 0.44, 0.16, 0.7), (-0.03, 0.74, 0.42, 0.17, 0.4), (0.15, 0.71, 0.50, 0.18, 1.1),
         (0.31, 0.63, 0.40, 0.15, 0.6), (0.05, 0.58, 0.26, 0.12, 0.2)]
BODY = [(-0.5, 0.6, 0.30, 0.17), (-0.18, 0.72, 0.30, 0.13), (0.12, 0.68, 0.32, 0.17), (0.34, 0.56, 0.2, 0.1)]
HERMANOS = [(0.73, 0.16, 0.36), (0.78, 0.06, 0.30), (0.80, -0.04, 0.34), (0.79, -0.14, 0.28), (0.75, -0.23, 0.22)]


def facet(dx, dy, turn, p=1.3):
    c, s_ = math.cos(turn), math.sin(turn)
    u, v = c * dx + s_ * dy, -s_ * dx + c * dy
    return (abs(u) ** p + abs(v) ** p) ** (1 / p)


def peaks(x, y):
    m = sum(h * math.exp(-((x - px) ** 2 + (y - py) ** 2) / (2 * s * s)) for px, py, h, s in BODY)
    for px, py, h, R, turn in CONES:
        m = max(m, h * max(0.0, 1 - facet(x - px, y - py, turn) / (R + 0.04)) ** 1.3)
    # Rough rock: ridged ripples on the high ground only.
    m += 0.02 * (1 - abs(math.sin(29 * x + 7 * y))) * (1 - abs(math.sin(21 * y - 11 * x))) * smoothstep(0.12, 0.3, m)
    # Monte Olivia: a steep faceted horn, faces meeting in ridges at a sharp top.
    m = max(m, 0.62 * max(0.0, 1 - facet(x - OLIVIA.x, (y - OLIVIA.y) * 1.1, 0.35, 1.2) / 0.30) ** 1.55)
    # Cinco Hermanos: five sharp teeth in a row beside Olivia.
    for i, (px, py, h) in enumerate(HERMANOS):
        m = max(m, h * max(0.0, 1 - facet(x - px, y - py, 0.4 * i, 1.2) / 0.13) ** 1.5)
    return m


def height(x, y):
    r = math.hypot(x, y)
    p = Vector((x, y))
    ys = shore_y(x)
    if y < ys:
        return -0.006
    low = 0.012 + 0.12 * smoothstep(-0.45, 0.4, y)
    low *= smoothstep(0.0, 0.08, y - ys)
    h = max(low, peaks(x, y))
    # The valley: a flat floor down the stream, widening into the bog.
    dr = seg_dist(p, RIVER)
    fl = lerp_pts(FLOOR, y)
    width = 0.07 + 0.09 * smoothstep(-0.2, 0.05, y) * (1 - smoothstep(0.22, 0.32, y))
    h = fl + (h - fl) * smoothstep(width, width + 0.14, dr) if h > fl else h
    # Laguna Esmeralda sits in a bowl at the head of the valley.
    d = (p - LAKE).length
    h = h + (LAKE_Z - h) * (1 - smoothstep(0.11, 0.24, d)) ** 1.4
    return max(h, 0.0) * (1 - smoothstep(0.88, 0.99, r)) if y >= ys else -0.006


RINGS, SEGS = 96, 300
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
            bm.faces.new((a[i], b[i], b[(i + 1) % SEGS], a[(i + 1) % SEGS]))
land = k.obj_from_bm("DECO-land", bm)
MI = {}
for m in (grass, bog, rock, scree, snow, glacier, shingle, sea):
    MI[m.name] = len(land.data.materials)
    land.data.materials.append(m)

BOG = Vector((-0.29, 0.13))


def in_bog(x, y):
    """The open peat bog: a rounded valley meadow, edges wavering."""
    a = math.atan2(y - BOG.y, x - BOG.x)
    r = 0.14 * (1 + 0.12 * math.sin(3 * a + 1) + 0.07 * math.sin(7 * a))
    return ((x - BOG.x) / 1.0) ** 2 + ((y - BOG.y) / 1.25) ** 2 < r * r


ALBINO = Vector((-0.43, 0.60))      # the glacier hanging over the lake
MARTIAL = Vector((0.16, 0.60))      # Glaciar Martial, in its cirque above town
for f in land.data.polygons:
    c = f.center
    p = Vector((c.x, c.y))
    ys = shore_y(c.x)
    snow_line = 0.31 + 0.03 * math.sin(14 * c.x) + 0.02 * math.sin(33 * c.x + 1)
    steep = f.normal.z < 0.72
    if c.y < ys:
        f.material_index = MI[sea.name]
    elif c.y < ys + 0.03:
        f.material_index = MI[shingle.name]
    elif (p - ALBINO).length < 0.14 and c.z > 0.24:
        f.material_index = MI[glacier.name]
    elif (p - MARTIAL).length < 0.09 and c.z > 0.22:
        f.material_index = MI[glacier.name]
    elif c.z > snow_line and (f.normal.z > 0.45 or math.sin(60 * c.x + 40 * c.y) > 0.2):
        f.material_index = MI[snow.name]
    elif c.z > 0.17 and (p - LAKE).length > 0.1 and (steep or c.z > 0.22):
        f.material_index = MI[rock.name] if steep else MI[scree.name]
    elif in_bog(c.x, c.y) and c.z < 0.16:
        f.material_index = MI[bog.name]
    else:
        f.material_index = MI[grass.name]
k.smooth_by_angle(land, 40)


def split_faces(src, name, pred):
    """Move the faces matching pred out of src into a new object."""
    me = src.data.copy()
    me.name = name
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    for mesh, keep in ((me, True), (src.data, False)):
        b = bmesh.new()
        b.from_mesh(mesh)
        gone = [f for f in b.faces if pred(f) != keep]
        bmesh.ops.delete(b, geom=gone, context="FACES")
        b.to_mesh(mesh)
        b.free()
    return o


def in_cirque(f):
    c = f.calc_center_median()
    return (Vector((c.x, c.y)) - LAKE).length < 0.30 and c.z > LAKE_Z - 0.03 and c.y > 0.33


esmeralda = split_faces(land, "OBJ-laguna-esmeralda", in_cirque)
mountains = split_faces(land, "OBJ-mountains", lambda f: f.calc_center_median().z > 0.15)


def ground(x, y):
    return height(x, y)


def stand(o, x, y, rot=0.0, extra=0.0):
    o.data.transform(Matrix.Translation((x, y, ground(x, y) + extra)) @ Matrix.Rotation(math.radians(rot), 4, "Z"))
    return o


def resample(pts, step):
    out = [pts[0]]
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        L = (b - a).length
        t = step - acc
        while t <= L:
            out.append(a + (b - a) * (t / L))
            t += step
        acc = (acc + L) % step
    out.append(pts[-1])
    return out


def drape(name, pts, width, lift, material, parent=None):
    """A strip laid over the terrain (the trail, the stream)."""
    pts = resample(pts, 0.006)
    b = bmesh.new()
    L, R = [], []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        n = Vector((-t.y, t.x)) * width / 2
        for side, lst in ((n, L), (-n, R)):
            q = p + side
            lst.append(b.verts.new((q.x, q.y, ground(q.x, q.y) + lift)))
    for i in range(len(pts) - 1):
        b.faces.new((R[i], R[i + 1], L[i + 1], L[i]))
    return k.obj_from_bm(name, b, material, parent=parent)


def blob(cx, cy, r, n=28, sx=1.0, sy=1.0, wob=0.12, seed=0):
    rr = random.Random(seed)
    ph = [rr.uniform(0, 6.3) for _ in range(3)]
    return [(cx + r * sx * math.cos(2 * math.pi * i / n) * (1 + wob * math.sin(3 * 2 * math.pi * i / n + ph[0]) + wob * 0.5 * math.sin(5 * 2 * math.pi * i / n + ph[1])),
             cy + r * sy * math.sin(2 * math.pi * i / n) * (1 + wob * math.sin(3 * 2 * math.pi * i / n + ph[0]) + wob * 0.5 * math.sin(5 * 2 * math.pi * i / n + ph[1])))
            for i in range(n)]


def text_mesh(name, s, size, material, depth=0.0015, parent=None):
    """Raised letters, standing upright and facing the front (-Y)."""
    cu = bpy.data.curves.new(name + "-curve", "FONT")
    cu.body = s
    cu.size = size
    cu.extrude = depth
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    ob = bpy.data.objects.new(name + "-tmp", cu)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(ob)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(material)
    k.place(o, rot=(90, 0, 0))
    if parent:
        o.parent = parent
    return o


rnd = random.Random(7)

# ---- Laguna Esmeralda: the emerald lake, boulders on its shore ----------------
lake_pts = blob(LAKE.x, LAKE.y, 0.095, sx=1.25, sy=0.85, seed=3)
k.prism("lake-water", lake_pts, 0.004, z0=LAKE_Z - 0.002, material=emerald, parent=esmeralda)
for i in range(16):
    a = rnd.uniform(0, 2 * math.pi)
    x, y = LAKE.x + 0.135 * math.cos(a) * 1.15, LAKE.y + 0.11 * math.sin(a)
    if y < LAKE.y - 0.06 and abs(x - (-0.36)) < 0.05:
        continue    # keep the trail's arrival clear
    b = k.sphere(f"boulder{i}", rnd.uniform(0.008, 0.016), material=scree, parent=esmeralda, subdiv=1)
    for v in b.data.vertices:
        v.co.z *= 0.6
    stand(b, x, y, extra=0.002)

# ---- the trail: forest path, boardwalk over the bog, markers, a trailhead -----
trail = k.empty("OBJ-esmeralda-trail")
drape("trail-path", TRAIL, 0.028, 0.005, k.mat("trail-dirt", (0.86, 0.74, 0.54)), parent=trail)
walk = resample(TRAIL, 0.009)
planks = []
for i, p in enumerate(walk):
    if not (0.02 < p.y < 0.24):
        continue
    t = (walk[min(i + 1, len(walk) - 1)] - walk[max(i - 1, 0)]).normalized()
    ang = math.degrees(math.atan2(t.y, t.x)) + 90
    planks.append(stand(k.box(f"plank{i}", (0.03, 0.006, 0.003), material=wood), p.x, p.y, rot=ang, extra=0.004))
k.join("boardwalk", planks).parent = trail
posts = []
for i, p in enumerate(resample(TRAIL, 0.07)[1:-1]):
    posts.append(stand(k.cylinder(f"mpost{i}", 0.0025, 0.022, material=wood_dark, segs=6), p.x + 0.016, p.y, extra=0.0))
    posts.append(stand(k.cylinder(f"mtip{i}", 0.0028, 0.005, material=marker, segs=6), p.x + 0.016, p.y, extra=0.02))
k.join("trail-markers", posts).parent = trail
# Trailhead board.
th = TRAIL[0]
th_parts = [k.box("th-post-l", (0.004, 0.004, 0.04), at=(-0.028, 0, 0), material=wood_dark),
            k.box("th-post-r", (0.004, 0.004, 0.04), at=(0.028, 0, 0), material=wood_dark),
            k.box("th-board", (0.07, 0.004, 0.022), at=(0, 0, 0.022), material=wood)]
lbl = text_mesh("th-text", "Laguna Esmeralda", 0.0085, panel)
k.place(lbl, at=(0, -0.0025, 0.033))
th_parts.append(lbl)
board = k.join("trailhead", th_parts)
stand(board, th.x + 0.03, th.y - 0.02, rot=15)
board.parent = trail

# ---- the stream down the valley, beaver ponds and dams, drowned trees ---------
streamline = [p for p in RIVER if p.y < 0.36]
drape("DECO-stream", streamline, 0.018, 0.0035, stream)
beavers = k.empty("OBJ-beaver-dams")
for j, (cy, rad) in enumerate(((0.17, 0.05), (0.04, 0.045), (-0.09, 0.035))):
    # A pond backed up above each dam.
    cx = min(RIVER, key=lambda q: abs(q.y - cy)).x
    pz = ground(cx, cy) + 0.004
    k.prism(f"pond{j}", blob(cx, cy + rad * 0.3, rad, sx=1.1, sy=0.7, seed=20 + j), 0.003, z0=pz - 0.002,
            material=stream, parent=beavers)
    # The dam: a low curved bank of piled sticks across the stream below it.
    logs = []
    for i in range(22):
        t = i / 21
        a = math.pi * (1.15 + 0.7 * t)
        x = cx + rad * 1.15 * math.cos(a) * 0.9
        y = cy + rad * 0.3 + rad * 0.75 * math.sin(a)
        L = rnd.uniform(0.02, 0.032)
        o = k.cylinder(f"dam{j}-{i}", 0.0022, L, material=sticks, segs=5, smooth=False)
        k.place(o, rot=(rnd.uniform(70, 110), 0, math.degrees(a) + rnd.uniform(-35, 35)),
                at=(x, y, pz + rnd.uniform(-0.001, 0.004)))
        logs.append(o)
    k.join(f"dam{j}", logs).parent = beavers
    # Beaver lodge: a mound of sticks in the pond.
    lodge = k.sphere(f"lodge{j}", 0.014, material=sticks, parent=beavers, subdiv=2)
    for v in lodge.data.vertices:
        v.co.z *= 0.6
    k.place(lodge, at=(cx + rad * 0.45, cy + rad * 0.5, pz))
snags = []
for i in range(14):
    a = rnd.uniform(0, 2 * math.pi)
    p = RIVER[rnd.randrange(30, 52)] + Vector((math.cos(a), math.sin(a))) * rnd.uniform(0.05, 0.1)
    if seg_dist(p, TRAIL) < 0.025:
        continue
    h = rnd.uniform(0.03, 0.05)
    o = k.cylinder(f"snag{i}", 0.003, h, material=snag, segs=5, r_top=0.001)
    br = k.cylinder(f"snag{i}-br", 0.0015, h * 0.4, material=snag, segs=4, r_top=0.0006)
    k.place(br, rot=(0, 50, rnd.uniform(0, 360)), at=(0, 0, h * 0.55))
    snags.append(stand(k.join(f"snag{i}", [o, br]), p.x, p.y))
k.join("DECO-drowned-trees", snags)

# ---- lenga forest on the lower slopes, some trees already autumn red -----------
TOWN = (0.06, 0.78, -0.47, -0.17)    # x0, x1, y0, y1
crowns = [bmesh.new() for _ in lenga]
trunks = bmesh.new()
spots = []
tries = 0
while len(spots) < 230 and tries < 40000:
    tries += 1
    x, y = rnd.uniform(-0.9, 0.9), rnd.uniform(-0.5, 0.75)
    p = Vector((x, y))
    if p.length > 0.9:
        continue
    z = ground(x, y)
    if z > 0.175 or y < shore_y(x) + 0.05:
        continue
    if TOWN[0] < x < TOWN[1] and TOWN[2] < y < TOWN[3] + 0.04:
        continue
    if seg_dist(p, TRAIL) < 0.028 or seg_dist(p, RIVER) < 0.035 or (p - LAKE).length < 0.16:
        continue
    if in_bog(x, y):
        continue      # the open bog
    if -0.3 < x < 0.08 and y < -0.33:
        continue      # the waterfront by the sign
    if any((p - q).length < 0.034 for q in spots):
        continue
    spots.append(p)
for p in spots:
    z = ground(p.x, p.y)
    hh = rnd.uniform(0.045, 0.07)
    g = bmesh.ops.create_cone(trunks, cap_ends=True, cap_tris=False, segments=5, radius1=0.0035,
                              radius2=0.0025, depth=hh * 0.6)
    bmesh.ops.translate(trunks, verts=g["verts"], vec=(p.x, p.y, z + hh * 0.3))
    ci = rnd.choices(range(4), weights=(4, 3, 1.4, 1.2))[0]
    for layer in range(3):      # lenga crowns sit in flat layered tiers
        rr = hh * (0.34 - 0.07 * layer)
        g = bmesh.ops.create_icosphere(crowns[ci], subdivisions=1, radius=rr)
        bmesh.ops.scale(crowns[ci], verts=g["verts"], vec=(1, 1, 0.55))
        bmesh.ops.translate(crowns[ci], verts=g["verts"],
                            vec=(p.x + rnd.uniform(-0.004, 0.004), p.y + rnd.uniform(-0.004, 0.004), z + hh * (0.5 + 0.2 * layer)))
forest_parts = [k.obj_from_bm(f"lenga-{i}", b, m, smooth=True) for i, (b, m) in enumerate(zip(crowns, lenga))]
forest_parts.append(k.obj_from_bm("lenga-trunks", trunks, trunk))
k.join("DECO-lenga-forest", forest_parts)

# ---- the town: coloured houses with tin roofs, the avenue, the pier ------------
town = k.empty("OBJ-ushuaia")
drape("avenue", [Vector((x / 50, shore_y(x / 50) + 0.045)) for x in range(4, 42)], 0.024, 0.003, road, parent=town)
hs = []
for row in range(3):
    for i in range(9):
        x = 0.12 + i * 0.068 + (0.034 if row % 2 else 0) + rnd.uniform(-0.008, 0.008)
        y = shore_y(x) + 0.095 + row * 0.07
        if math.hypot(x, y) > 0.84 or x > 0.76:
            continue
        w, d = rnd.uniform(0.04, 0.05), rnd.uniform(0.032, 0.04)
        h = rnd.choice((0.028, 0.034, 0.046))
        wall = walls[rnd.randrange(len(walls))]
        roof = roofs[rnd.randrange(len(roofs))]
        parts = [k.box(f"h{row}{i}", (w, d, h), material=wall)]
        # Gable roof: a triangular prism along x.
        gb = bmesh.new()
        ridge = h + d * 0.45
        vs = [gb.verts.new(v) for v in [(-w / 2 - 0.003, -d / 2 - 0.004, h), (-w / 2 - 0.003, d / 2 + 0.004, h),
                                         (-w / 2 - 0.003, 0, ridge), (w / 2 + 0.003, -d / 2 - 0.004, h),
                                         (w / 2 + 0.003, d / 2 + 0.004, h), (w / 2 + 0.003, 0, ridge)]]
        for f in ((0, 2, 1), (3, 4, 5), (0, 3, 5, 2), (2, 5, 4, 1), (0, 1, 4, 3)):
            gb.faces.new([vs[q] for q in f])
        bmesh.ops.recalc_face_normals(gb, faces=gb.faces)
        parts.append(k.obj_from_bm(f"h{row}{i}-gable", gb, roof))
        for q, wx in enumerate((-w * 0.25, w * 0.25)):
            parts.append(k.box(f"h{row}{i}-w{q}", (0.009, 0.002, 0.01),
                               at=(wx, -d / 2 - 0.0005, h * 0.45), material=win))
        parts.append(k.box(f"h{row}{i}-door", (0.008, 0.002, 0.014), at=(0, -d / 2 - 0.0005, 0), material=wood_dark))
        o = k.join(f"house{row}-{i}", parts)
        hs.append(stand(o, x, y, rot=rnd.uniform(-4, 4)))
k.join("houses", hs).parent = town
PIER_X = 0.36
pier_parts = [k.box("pier-deck", (0.04, 0.17, 0.006), at=(PIER_X, shore_y(PIER_X) - 0.07, -0.002), material=concrete)]
for i in range(6):
    pier_parts.append(k.cylinder(f"pier-pile{i}", 0.003, 0.012, at=(PIER_X + (0.016 if i % 2 else -0.016), shore_y(PIER_X) - 0.02 - 0.03 * (i // 2), -0.008),
                                 material=dark, segs=6))
k.join("pier", pier_parts).parent = town
# An expedition ship alongside, red hull and white decks, bound for Antarctica.
ship = [k.box("ship-hull", (0.036, 0.17, 0.016), at=(0, 0, -0.004), material=hull_red),
        k.box("ship-deck1", (0.032, 0.12, 0.014), at=(0, -0.01, 0.012), material=white),
        k.box("ship-deck2", (0.026, 0.07, 0.012), at=(0, -0.02, 0.026), material=white),
        k.box("ship-bridge-win", (0.027, 0.002, 0.004), at=(0, -0.055, 0.032), material=dark),
        k.cylinder("ship-funnel", 0.006, 0.016, at=(0, 0.02, 0.026), material=hull_red, segs=10)]
for v in ship[0].data.vertices:
    if v.co.y < -0.05:
        v.co.x *= 1 - 0.75 * (-0.05 - v.co.y) / 0.035
hull = k.join("ship", ship)
k.place(hull, at=(PIER_X + 0.045, shore_y(PIER_X) - 0.13, 0))
hull.parent = town

# ---- the sign on the waterfront: USHUAIA · fin del mundo --------------------
sign = k.empty("OBJ-fin-del-mundo-sign")
SX, SY = -0.1, shore_y(-0.1) + 0.06
W, H, LIFT = 0.27, 0.115, 0.034
sp = [k.box("sign-post-l", (0.012, 0.012, LIFT + H + 0.012), at=(-W / 2 - 0.004, 0, 0), material=wood_dark),
      k.box("sign-post-r", (0.012, 0.012, LIFT + H + 0.012), at=(W / 2 + 0.004, 0, 0), material=wood_dark),
      k.box("sign-frame", (W + 0.02, 0.009, H + 0.012), at=(0, 0, LIFT - 0.006), material=wood),
      k.box("sign-panel", (W, 0.011, H), at=(0, 0, LIFT), material=panel),
      k.box("sign-cap", (W + 0.044, 0.024, 0.008), at=(0, 0, LIFT + H + 0.008), material=wood_dark)]
t1 = text_mesh("sign-ushuaia", "USHUAIA", 0.058, ink_blue)
k.place(t1, at=(0, -0.0065, LIFT + H * 0.64))
t2 = text_mesh("sign-fin", "fin del mundo", 0.036, ink_red)
k.place(t2, at=(0, -0.0065, LIFT + H * 0.26))
rule = k.box("sign-rule", (W * 0.7, 0.002, 0.0025), at=(0, -0.0055, LIFT + H * 0.43), material=ink_blue)
for o in sp + [t1, t2, rule]:
    stand(o, SX, SY, extra=0.0)
    o.parent = sign
# The waterfront plaza it stands on.
k.prism("sign-plaza", blob(SX, SY + 0.005, 0.1, sx=1.7, sy=0.45, wob=0.04, seed=9), 0.004,
        z0=ground(SX, SY) - 0.002, material=concrete, parent=sign)

# ---- the Beagle Channel: a catamaran going to and fro, rocky islets ------------
channel = k.empty("OBJ-beagle-channel")
islets = []
for i, (x, y, r) in enumerate(((-0.52, -0.66, 0.03), (-0.44, -0.72, 0.02), (0.14, -0.80, 0.025))):
    o = k.prism(f"islet{i}", blob(x, y, r, n=18, sx=1.6, wob=0.25, seed=30 + i), 0.008, z0=-0.004, material=rock)
    islets.append(o)
    islets.append(k.prism(f"islet{i}-top", blob(x, y, r * 0.75, n=18, sx=1.6, wob=0.2, seed=30 + i), 0.003, z0=0.004, material=grass))
k.join("islets", islets).parent = channel
a, b = Vector((-0.34, -0.66, 0.0)), Vector((0.24, -0.62, 0.0))
cat = k.empty("catamaran", parent=channel)
cat.location = a
d = b - a
cat.rotation_euler = (0, 0, math.atan2(d.y, d.x))
cat["shuttle"] = [d.x, d.y, d.z]
cat["period"] = 34.0
cat["phase"] = 0.0
cat["pingpong"] = 1
cat["bob"] = 0.0015
cat["bobHz"] = 0.7
for s in (-1, 1):
    hl = k.box(f"cat-hull{s}", (0.07, 0.01, 0.008), at=(0, s * 0.012, -0.003), material=white, parent=cat)
    for v in hl.data.vertices:
        if v.co.x > 0.02:
            v.co.y = s * 0.012 + (v.co.y - s * 0.012) * 0.3
k.box("cat-cabin", (0.046, 0.03, 0.012), at=(-0.004, 0, 0.005), material=white, parent=cat)
k.box("cat-stripe", (0.047, 0.031, 0.003), at=(-0.004, 0, 0.009), material=ink_red, parent=cat)
k.box("cat-win", (0.002, 0.026, 0.004), at=(0.019, 0, 0.011), material=dark, parent=cat)
k.box("cat-roof", (0.03, 0.026, 0.006), at=(-0.008, 0, 0.017), material=white, parent=cat)

k.export("ushuaia")
