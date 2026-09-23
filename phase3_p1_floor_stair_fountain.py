"""3차 P1: 대각선 체크 바닥 + 쌍곡선 계단·곡선 발코니 + 층진 천사 분수 (레퍼런스 재구축).

COMPLETE 장면에 실행. 재실행하면 31~33 컬렉션을 비우고 다시 만든다.
교체된 원본(체크 바닥, 옛 계단·난간, 옛 분수)은 30x 숨김 컬렉션으로 옮기고 지우지 않는다.
"""
import bpy, bmesh, math
from math import sin, cos, pi, radians

sc = bpy.context.scene
M = bpy.data.materials
white = M['Ivory marble']; gold = M['Antique gilded bronze']; blue = M['Sapphire stone']
velvet = M['Royal blue velvet']; iron = M['Wrought iron']; tile = M['Blue grey marble']
water = M['Fountain water']; glass = M['Pale azure glazing']

HIDDEN = '30x | P3 replaced originals (hidden)'
C_FLOOR = '31 | P3 - Diagonal marble floor'
C_STAIR = '32 | P3 - Twin horseshoe stair'
C_FOUNT = '33 | P3 - Tiered angel fountain'


def ensure_coll(name, clear=True):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name); sc.collection.children.link(c)
    if clear:
        for o in list(c.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    return c


hidden = ensure_coll(HIDDEN, clear=False)
hidden.hide_render = True
for lc in bpy.context.view_layer.layer_collection.children:
    if lc.name == HIDDEN:
        lc.exclude = True
parked = []


def park(o):
    if hidden in o.users_collection:
        return
    o['p3_original_collections'] = ','.join(c.name for c in o.users_collection)
    for c in list(o.users_collection):
        c.objects.unlink(o)
    hidden.objects.link(o)
    parked.append(o.name)


colls = {k: ensure_coll(k) for k in (C_FLOOR, C_STAIR, C_FOUNT)}
coll = None
_mesh = {}


def unit_mesh(kind, mat):
    key = (kind, mat.name)
    if key in _mesh:
        return _mesh[key]
    name = 'P3_unit_%s_%s' % (kind, mat.name)
    me = bpy.data.meshes.get(name)
    if me is None:
        me = bpy.data.meshes.new(name); bm = bmesh.new()
        if kind == 'box':
            bmesh.ops.create_cube(bm, size=1)
        elif kind == 'cyl':
            bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=1, radius2=1, depth=1)
        else:
            bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=1)
        bm.to_mesh(me); bm.free()
        if kind != 'box':
            for p in me.polygons:
                p.use_smooth = True
        me.materials.append(mat)
    _mesh[key] = me
    return me


def add(name, kind, mat, loc, dims):
    o = bpy.data.objects.new(name, unit_mesh(kind, mat)); coll.objects.link(o)
    o.location = loc; o.scale = dims
    return o


def box(name, loc, dims, mat): return add(name, 'box', mat, loc, dims)
def cyl(name, loc, r, h, mat): return add(name, 'cyl', mat, loc, (r, r, h))
def ball(name, loc, dims, mat): return add(name, 'ball', mat, loc, dims)


def curves(name, splines, r, mat, closed=False):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 2 if r >= .02 else 1
    cu.resolution_u = 1; cu.use_fill_caps = True
    for pts in splines:
        sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
        for v, p in zip(sp.points, pts):
            v.co = (*p, 1)
        sp.use_cyclic_u = closed
    cu.materials.append(mat)
    o = bpy.data.objects.new(name, cu); coll.objects.link(o)
    return o


def mesh_obj(name, bm, mats):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in mats:
        me.materials.append(m)
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    return o


def lathe(name, profile, mat, center, segs=48, smooth=True):
    bm = bmesh.new()
    vs = [bm.verts.new((r, 0, z)) for r, z in profile]
    es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + es, angle=2 * pi, steps=segs, axis=(0, 0, 1), cent=(0, 0, 0))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    o = mesh_obj(name, bm, [mat])
    if smooth:
        for p in o.data.polygons:
            p.use_smooth = True
    o.location = (center[0], center[1], 0)
    return o


def ring_pts(cx, cy, r, z, n=64):
    return [(cx + r * cos(i * 2 * pi / n), cy + r * sin(i * 2 * pi / n), z) for i in range(n)]


def scroll_splines(pos_fn, w):
    """Paired acanthus scroll; pos_fn(t_offset, z_offset) -> xyz on the host surface."""
    out = []
    for sign in (-1, 1):
        pts = []
        for i in range(30):
            t = i / 29 * 2.5 * pi; rr = w * (1 - i / 36)
            pts.append(pos_fn(sign * (w * .8 + rr * cos(t)), rr * sin(t) * .45))
        out.append(pts)
    return out


def balustrade(name, pos, L, zbase, zfoot=None):
    """Iron heart-scroll balustrade with a gilt handrail along a path.
    pos(u)->(x,y) for arc length u in [0, L]; zbase(u) = walking line; zfoot(u) = post foot."""
    zfoot = zfoot or zbase
    n = max(2, round(L / .5)); du = L / n
    posts, hearts = [], []
    for k in range(n + 1):
        u = k * du; x, y = pos(u)
        posts.append([(x, y, zfoot(u)), (x, y, zbase(u) + .95)])
    for k in range(n):
        um = (k + .5) * du; w = du * .78; h = .52; zc = zbase(um) + .5
        pts = []
        for q in range(28):
            th = q / 28 * 2 * pi
            hx = (sin(th) ** 3) * (w / 2)
            hz = (13 * cos(th) - 5 * cos(2 * th) - 2 * cos(3 * th) - cos(4 * th)) / 17 * (h / 2)
            x, y = pos(um + hx)
            pts.append((x, y, zc + hz + zbase(um + hx) - zbase(um)))
        hearts.append(pts)
    m = max(8, int(L / .15))
    rail = [(*pos(L * i / m), zbase(L * i / m) + .95) for i in range(m + 1)]
    bottom = [(*pos(L * i / m), zbase(L * i / m) + .13) for i in range(m + 1)]
    curves(name + ' iron posts', posts, .02, iron)
    curves(name + ' iron heart scrolls', hearts, .012, iron, closed=True)
    curves(name + ' gilt handrail', [rail], .045, gold)
    curves(name + ' iron bottom rail', [bottom], .025, iron)


# ------------------------------------------------------------------ park originals
for o in list(sc.objects):
    n = o.name
    if n.startswith(('Polished checkerboard', 'Forehall | Polished checkerboard',
                     'Marble stair tread', 'Gilt tread nosing', 'Curving stair balustrade',
                     'Stair newel pedestal', 'Newel finial', 'Stair to landing bridge',
                     'Landing gilt safety rail', 'Landing iron upright')):
        park(o)
fountain_old = bpy.data.collections.get('04 | Fountain and winged sculpture')
if fountain_old:
    for o in list(fountain_old.objects):
        park(o)

# ------------------------------------------------------------------ A01 diagonal floor
coll = colls[C_FLOOR]


def diagonal_floor(name, xmin, xmax, ymin, ymax, t=1.0):
    s2 = 2 ** .5
    corners = [(xmin, ymin), (xmin, ymax), (xmax, ymin), (xmax, ymax)]
    us = [(x + y) / s2 for x, y in corners]; vs = [(y - x) / s2 for x, y in corners]
    bm = bmesh.new()
    for i in range(math.floor(min(us) / t) - 1, math.ceil(max(us) / t) + 1):
        for j in range(math.floor(min(vs) / t) - 1, math.ceil(max(vs) / t) + 1):
            q = [bm.verts.new((((a - b) * t) / s2, ((a + b) * t) / s2, 0)) for a, b in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))]
            bm.faces.new(q).material_index = (i + j) % 2
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    for co, no in (((xmin, 0, 0), (-1, 0, 0)), ((xmax, 0, 0), (1, 0, 0)), ((0, ymin, 0), (0, -1, 0)), ((0, ymax, 0), (0, 1, 0))):
        geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=co, plane_no=no, clear_outer=True)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(white); me.materials.append(tile)
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    return o


floor = diagonal_floor('P3 diagonal checker floor', -16, 16, -42, 14)

# ------------------------------------------------------------------ A02/A03 twin horseshoe stair
coll = colls[C_STAIR]
CY = 4.0
R_IN, R_OUT = 3.4, 5.6
PHI0, PHI1 = radians(30), radians(150)
N, H = 30, 5.12
DPHI = (PHI1 - PHI0) / N
OUTER_END = radians(137)   # outer edge meets the rear landing slab here


def P(s, r, phi, z):
    return (s * r * sin(phi), CY - r * cos(phi), z)


def z_line(phi):
    return H * (phi - PHI0) / (PHI1 - PHI0)


def z_step(phi):
    return min(H, (math.floor((phi - PHI0) / DPHI + 1e-6) + 1) * H / N)


for s, tag in ((1, 'R'), (-1, 'L')):
    # Solid marble treads.
    bm = bmesh.new()
    for i in range(N):
        a = PHI0 + i * DPHI; z = (i + 1) * H / N
        outer = [P(s, R_OUT, a + DPHI * k / 3, 0) for k in range(4)]
        inner = [P(s, R_IN, a + DPHI * k / 3, 0) for k in range(4)]
        poly = outer + inner[::-1]
        bot = [bm.verts.new(p) for p in poly]
        top = [bm.verts.new((p[0], p[1], z)) for p in poly]
        bm.faces.new(top); bm.faces.new(bot[::-1])
        for k in range(len(poly)):
            bm.faces.new((bot[k], bot[(k + 1) % len(poly)], top[(k + 1) % len(poly)], top[k]))
    mesh_obj('P3 stair marble treads %s' % tag, bm, [white])
    curves('P3 stair gilt nosing %s' % tag,
           [[P(s, R_IN + .06, PHI0 + i * DPHI, (i + 1) * H / N + .006), P(s, R_OUT - .06, PHI0 + i * DPHI, (i + 1) * H / N + .006)] for i in range(N)],
           .018, gold)

    # Marble stringers (curb walls) with gilt frieze.
    for side, r_face, r_back, phi_end in (('outer', R_OUT + .12, R_OUT, OUTER_END), ('inner', R_IN - .12, R_IN, PHI1)):
        bm = bmesh.new(); rings = []
        K = 72
        for k in range(K + 1):
            phi = PHI0 + (phi_end - PHI0) * k / K
            zt = z_line(phi) + H / N + .22
            rings.append([bm.verts.new(P(s, r_face, phi, 0)), bm.verts.new(P(s, r_face, phi, zt)),
                          bm.verts.new(P(s, r_back, phi, zt)), bm.verts.new(P(s, r_back, phi, 0))])
        for a_, b_ in zip(rings, rings[1:]):
            for m in range(4):
                bm.faces.new((a_[m], a_[(m + 1) % 4], b_[(m + 1) % 4], b_[m]))
        bm.faces.new(rings[0]); bm.faces.new(rings[-1][::-1])
        mesh_obj('P3 stair %s stringer marble %s' % (side, tag), bm, [white])

        rf = r_face + (.012 if side == 'outer' else -.012)
        phis = [radians(42) + (phi_end - radians(42)) * k / 60 for k in range(61)]
        curves('P3 stair %s frieze gilt lines %s' % (side, tag),
               [[P(s, rf, ph, z_line(ph) + .06) for ph in phis], [P(s, rf, ph, z_line(ph) - .36) for ph in phis],
                [P(s, rf, ph, .3) for ph in [PHI0 + (phi_end - PHI0) * k / 60 for k in range(61)]]],
               .022, gold)
        slope = H / ((PHI1 - PHI0) * rf)
        scr = []
        ph = radians(47)
        while ph < phi_end - radians(4):
            scr += scroll_splines(lambda dt, dz, ph=ph: P(s, rf, ph + dt / rf, z_line(ph) - .15 + dz + slope * dt), .15)
            ph += radians(8)
        curves('P3 stair %s frieze gilt scrolls %s' % (side, tag), scr, .014, gold)

    # Balustrades.
    for side, r, phi_end in (('outer', R_OUT - .1, OUTER_END), ('inner', R_IN + .1, PHI1)):
        L = r * (phi_end - PHI0)
        balustrade('P3 stair %s balustrade %s' % (side, tag),
                   lambda u, r=r: P(s, r, PHI0 + u / r, 0)[:2], L,
                   lambda u, r=r: z_line(PHI0 + u / r) + .5 * H / N,
                   lambda u, r=r: z_step(PHI0 + u / r))

    # Sapphire urn newels at the foot.
    for r in (R_IN + .1, R_OUT - .1):
        x, y, _ = P(s, r, PHI0 - radians(2.5), 0)
        box('P3 newel sapphire pedestal', (x, y, .5), (.5, .5, 1.0), blue)
        box('P3 newel gilt cap', (x, y, 1.04), (.6, .6, .08), gold)
        box('P3 newel marble base', (x, y, .08), (.62, .62, .16), white)
        cyl('P3 newel urn gilt foot', (x, y, 1.14), .13, .1, gold)
        ball('P3 newel urn sapphire body', (x, y, 1.42), (.21, .21, .25), blue)
        cyl('P3 newel urn gilt rim', (x, y, 1.64), .16, .05, gold)
        ball('P3 newel urn gilt finial', (x, y, 1.76), (.07, .07, .1), gold)

# Curved balcony bridge joining both stair tops over the back of the fountain.
BR0, BR1 = PHI1, 2 * pi - PHI1
bm = bmesh.new(); rings = []
for k in range(41):
    phi = BR0 + (BR1 - BR0) * k / 40
    rings.append([bm.verts.new(P(1, R_IN - .1, phi, 4.55)), bm.verts.new(P(1, R_IN - .1, phi, H)),
                  bm.verts.new(P(1, R_OUT, phi, H)), bm.verts.new(P(1, R_OUT, phi, 4.82))])
for a_, b_ in zip(rings, rings[1:]):
    for m in range(4):
        bm.faces.new((a_[m], a_[(m + 1) % 4], b_[(m + 1) % 4], b_[m]))
bm.faces.new(rings[0]); bm.faces.new(rings[-1][::-1])
mesh_obj('P3 balcony bridge marble', bm, [white])
bm = bmesh.new(); rings = []
for k in range(41):
    phi = BR0 + (BR1 - BR0) * k / 40
    rings.append([bm.verts.new(P(1, 3.75, phi, H + .005)), bm.verts.new(P(1, 5.25, phi, H + .005)),
                  bm.verts.new(P(1, 5.25, phi, H + .02)), bm.verts.new(P(1, 3.75, phi, H + .02))])
for a_, b_ in zip(rings, rings[1:]):
    for m in range(4):
        bm.faces.new((a_[m], a_[(m + 1) % 4], b_[(m + 1) % 4], b_[m]))
mesh_obj('P3 balcony bridge sapphire carpet', bm, [velvet])
rb = R_IN - .112
bphis = [BR0 + (BR1 - BR0) * k / 60 for k in range(61)]
curves('P3 balcony bridge frieze gilt lines', [[P(1, rb, ph, z) for ph in bphis] for z in (4.62, 5.0)], .022, gold)
scr = []
ph = BR0 + radians(5)
while ph < BR1 - radians(3):
    scr += scroll_splines(lambda dt, dz, ph=ph: P(1, rb, ph + dt / rb, 4.81 + dz), .14)
    ph += radians(10)
curves('P3 balcony bridge frieze gilt scrolls', scr, .014, gold)
r = R_IN + .1
balustrade('P3 balcony bridge balustrade', lambda u: P(1, r, BR0 + u / r, 0)[:2], r * (BR1 - BR0), lambda u: H)

# Rear landing edge balustrade, left and right of the bridge.
for s, tag in ((1, 'R'), (-1, 'L')):
    x0, x1 = 3.85 * s, 11.3 * s
    L = abs(x1 - x0)
    balustrade('P3 landing edge balustrade %s' % tag, lambda u, x0=x0, s=s: (x0 + s * u, 8.12), L, lambda u: H)
    curves('P3 landing fascia gilt line %s' % tag, [[(x0, 8.18, 4.9), (x1, 8.18, 4.9)]], .02, gold)

# ------------------------------------------------------------------ A04 tiered angel fountain
coll = colls[C_FOUNT]
FX, FY = 0.0, 4.0
cyl('P3 fountain plinth step marble', (FX, FY, .05), 2.55, .1, white)
curves('P3 fountain plinth gilt edge', [ring_pts(FX, FY, 2.55, .1)], .025, gold, True)
lathe('P3 fountain basin marble wall', [(2.1, .1), (2.3, .1), (2.3, .56), (2.37, .6), (2.37, .67), (2.08, .67), (2.08, .1)], white, (FX, FY), 64, False)
lathe('P3 fountain basin sapphire frieze band', [(2.3, .19), (2.315, .19), (2.315, .47), (2.3, .47)], blue, (FX, FY), 64, False)
curves('P3 fountain basin gilt bands', [ring_pts(FX, FY, 2.322, .19), ring_pts(FX, FY, 2.322, .47), ring_pts(FX, FY, 2.37, .675)], .02, gold, True)
scr = []
for k in range(12):
    a0 = k * 2 * pi / 12
    scr += scroll_splines(lambda dt, dz, a0=a0: (FX + 2.33 * cos(a0 + dt / 2.33), FY + 2.33 * sin(a0 + dt / 2.33), .33 + dz), .16)
curves('P3 fountain basin gilt scrolls', scr, .013, gold)
cyl('P3 fountain basin water', (FX, FY, .5), 2.08, .03, water)
lathe('P3 fountain baluster pedestal', [(0, .45), (.5, .45), (.5, .55), (.32, .62), (.28, .9), (.42, 1.12), (.3, 1.38), (.22, 1.5), (0, 1.5)], white, (FX, FY))
lathe('P3 fountain lower bowl', [(0, 1.74), (1.05, 1.78), (1.3, 1.9), (1.42, 1.9), (1.42, 1.84), (1.1, 1.66), (.4, 1.5), (0, 1.48)], white, (FX, FY), 64)
curves('P3 fountain lower bowl gilt rim', [ring_pts(FX, FY, 1.43, 1.9)], .03, gold, True)
cyl('P3 fountain lower bowl water', (FX, FY, 1.83), 1.28, .02, water)
lathe('P3 fountain upper stem', [(0, 1.74), (.2, 1.74), (.16, 1.95), (.26, 2.2), (.14, 2.45), (.1, 2.55), (0, 2.55)], white, (FX, FY))
lathe('P3 fountain upper bowl', [(0, 2.76), (.5, 2.8), (.72, 2.92), (.82, 2.92), (.82, 2.86), (.62, 2.7), (.25, 2.55), (0, 2.52)], white, (FX, FY))
curves('P3 fountain upper bowl gilt rim', [ring_pts(FX, FY, .83, 2.92, 48)], .025, gold, True)
cyl('P3 fountain upper bowl water', (FX, FY, 2.85), .7, .02, water)
lathe('P3 angel plinth', [(0, 2.76), (.3, 2.76), (.3, 2.84), (.24, 2.9), (.22, 3.18), (.3, 3.24), (.3, 3.3), (0, 3.3)], white, (FX, FY))
curves('P3 angel plinth gilt ring', [ring_pts(FX, FY, .31, 3.3, 32)], .02, gold, True)

# Angel: robed figure, arms raised, layered wings behind (+Y, away from the entrance).
lathe('P3 angel robe', [(0, 3.3), (.36, 3.3), (.34, 3.4), (.27, 3.8), (.21, 4.2), (.19, 4.45), (.15, 4.6), (0, 4.62)], white, (FX, FY))
folds = []
for k in range(9):
    a0 = pi + (k - 4) * .28
    folds.append([(FX + .19 * sin(a0), FY + .19 * cos(a0) * .9, 4.42), (FX + .27 * sin(a0 * 1.02), FY + .27 * cos(a0) * .9, 3.85), (FX + .35 * sin(a0 * 1.04), FY + .35 * cos(a0) * .9, 3.34)])
curves('P3 angel robe folds', folds, .02, white)
ball('P3 angel torso', (FX, FY, 4.66), (.19, .14, .24), white)
cyl('P3 angel neck', (FX, FY, 4.88), .05, .12, white)
ball('P3 angel head', (FX, FY - .01, 5.0), (.105, .11, .13), white)
ball('P3 angel hair', (FX, FY + .05, 5.06), (.1, .09, .09), white)
for sx in (-1, 1):
    curves('P3 angel raised arm', [[(FX + sx * .15, FY, 4.8), (FX + sx * .26, FY - .02, 5.05), (FX + sx * .25, FY - .03, 5.32), (FX + sx * .17, FY - .02, 5.48)]], .042, white)
    ball('P3 angel hand', (FX + sx * .16, FY - .02, 5.53), (.045, .045, .06), white)
    # Wing = lofted sheet hanging from an arched leading edge, scalloped feather tips, solidified.
    base = (FX + sx * .1, FY + .16, 4.78); peak = (FX + sx * .62, FY + .38, 5.6); tipp = (FX + sx * .86, FY + .52, 4.05)
    U, V = 28, 6
    bm = bmesh.new(); grid = []; ridges = []
    for iu in range(U + 1):
        t = iu / U
        B = [(1 - t) ** 2 * base[i] + 2 * (1 - t) * t * peak[i] + t * t * tipp[i] for i in range(3)]
        Lv = .62 * (1 - t) + .12
        scal = 1 + .16 * abs(sin(t * pi * 8))
        wing_pt = lambda v, dy=0.0: (B[0] + sx * .06 * v, B[1] + .05 * v + .05 * sin(pi * min(v, 1)) + dy, B[2] - Lv * v)
        grid.append([bm.verts.new(wing_pt(iv / V * scal)) for iv in range(V + 1)])
        if iu % 2 == 1:
            ridges.append([wing_pt(j / 8 * scal, -.03) for j in range(9)])
    for iu in range(U):
        for iv in range(V):
            bm.faces.new((grid[iu][iv], grid[iu + 1][iv], grid[iu + 1][iv + 1], grid[iu][iv + 1]))
    wtag = 'R' if sx > 0 else 'L'
    wing = mesh_obj('P3 angel wing ' + wtag, bm, [white])
    for p in wing.data.polygons:
        p.use_smooth = True
    mod = wing.modifiers.new('Wing thickness', 'SOLIDIFY'); mod.thickness = .05; mod.offset = 0
    curves('P3 angel wing feather ridges ' + wtag, ridges, .013, white)

# Water jets.
jets = []
for k in range(8):
    a0 = k * 2 * pi / 8
    jets.append([(FX + (.82 + .43 * t) * cos(a0), FY + (.82 + .43 * t) * sin(a0), 2.92 - 1.06 * t + .22 * (1 - (2 * t - 1) ** 2)) for t in [i / 14 for i in range(15)]])
for k in range(12):
    a0 = (k + .5) * 2 * pi / 12
    jets.append([(FX + (1.43 + .6 * t) * cos(a0), FY + (1.43 + .6 * t) * sin(a0), 1.9 - 1.38 * t + .2 * (1 - (2 * t - 1) ** 2)) for t in [i / 14 for i in range(15)]])
for k in range(8):
    a0 = (k + .5) * 2 * pi / 8
    jets.append([(FX + (2.12 - 1.55 * t) * cos(a0), FY + (2.12 - 1.55 * t) * sin(a0), .62 + .9 * t + 1.1 * (1 - (2 * t - 1) ** 2)) for t in [i / 18 for i in range(19)]])
curves('P3 fountain water jets', jets, .014, glass)

# ------------------------------------------------------------------ camera
coll = colls[C_STAIR]
from mathutils import Vector
cd = bpy.data.cameras.new('CAM 11 | P3 - Reference front view')
cam = bpy.data.objects.new(cd.name, cd); coll.objects.link(cam)
cam.location = (0, -12.0, 3.2)
cam.rotation_euler = (Vector((0, 8, 6.2)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
cd.lens = 16; cd.clip_end = 400

result = {k: len(c.objects) for k, c in colls.items()}
result['parked'] = len(parked)
result['floor_faces'] = len(floor.data.polygons)
result['scene_objects'] = len(sc.objects)
print('P3_P1_RESULT', result)
