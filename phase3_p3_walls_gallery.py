"""3차 P3: 벽 패널 시스템 + 갤러리 난간·대리석 띠 + 기둥 위 가로보 (레퍼런스 재구축).

- 옆벽(x=±16, 앞·뒤 절반)과 뒤벽(y=14): 위층 5.7~10.4m, 아래층 0.55~4.4m 두 단.
  넓은 대리석 패널(금장 이중 틀 + 위아래 스크롤) 사이에 파란 좁은 패널과 랜턴 벽등.
- 뒤 창: 청색 테두리 + 양옆 금장 S자 스크롤.
- 갤러리 가장자리·계단참·정문 발코니: 대리석 띠(금장 선 + 스크롤) + 철제 하트 난간(옛 O자 난간 교체).
- 갤러리 기둥 줄(x=±11.8) 위 12m까지 가로보, 청색 인방 패널, 기둥마다 금장 소용돌이.
반복 부재는 재질별 한 메시로 묶는다. 옛 패널·벽등·난간은 30x 숨김 컬렉션으로 옮긴다. 재실행 가능.
"""
import bpy, bmesh, math
from math import sin, cos, pi
from mathutils import Matrix, Vector

sc = bpy.context.scene
M = bpy.data.materials
white = M['Ivory marble']; gold = M['Antique gilded bronze']; blue = M['Sapphire stone']
iron = M['Wrought iron']; bulb = M['Candle light']

HIDDEN = '30x | P3 replaced originals (hidden)'
C_WALL = '36 | P3 - Wall panels and lanterns'
C_GAL = '37 | P3 - Gallery rails, fascia and entablature'


def ensure_coll(name, clear=True):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name); sc.collection.children.link(c)
    if clear:
        for o in list(c.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    return c


hidden = ensure_coll(HIDDEN, clear=False)
colls = {k: ensure_coll(k) for k in (C_WALL, C_GAL)}
coll = None
parked = []


def park(o):
    if hidden in o.users_collection:
        return
    o['p3_original_collections'] = ','.join(c.name for c in o.users_collection)
    for c in list(o.users_collection):
        c.objects.unlink(o)
    hidden.objects.link(o)
    parked.append(o.name)


def centre(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return [sum(p[i] for p in pts) / 8 for i in range(3)]


for o in list(sc.objects):
    n = o.name
    if n.startswith(('Side gilded panel', 'Side inner moulding', 'Forehall | Side gilded panel', 'Forehall | Side inner moulding',
                     'Recessed wall panel', 'Gold panel moulding', 'Inner panel bead',
                     'Wall sconce arm', 'Sconce candle', 'Sconce flame',
                     'Gallery filigree', 'Forehall | Gallery filigree',
                     'Entrance balcony railing', 'Entrance balcony inner return')):
        park(o)
    elif n.startswith(('Gilt acanthus scroll', 'Forehall | Gilt acanthus scroll')):
        cx, cy_, cz = centre(o)
        if abs(cx) > 13 or cy_ > 13:
            park(o)


class Batch:
    """Many primitives of one material merged into a single mesh object."""

    def __init__(self, name, mat, smooth=False):
        self.name, self.mat, self.smooth = name, mat, smooth
        self.bm = bmesh.new()

    def box(self, c, d):
        bmesh.ops.create_cube(self.bm, size=1, matrix=Matrix.Translation(c) @ Matrix.Diagonal((*d, 1)))

    def cone(self, c, r1, r2, h, segs=12):
        bmesh.ops.create_cone(self.bm, cap_ends=True, segments=segs, radius1=r1, radius2=r2, depth=h, matrix=Matrix.Translation(c))

    def ball(self, c, rad, segs=12):
        bmesh.ops.create_uvsphere(self.bm, u_segments=segs, v_segments=8, radius=1, matrix=Matrix.Translation(c) @ Matrix.Diagonal((*rad, 1)))

    def finish(self):
        me = bpy.data.meshes.new(self.name); self.bm.to_mesh(me); self.bm.free()
        me.materials.append(self.mat)
        if self.smooth:
            for p in me.polygons:
                p.use_smooth = True
        o = bpy.data.objects.new(self.name, me); coll.objects.link(o)
        return o


def curves(name, splines, r, mat, closed=False):
    if not splines:
        return None
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 2 if r >= .03 else 1
    cu.resolution_u = 1; cu.use_fill_caps = True
    for pts in splines:
        sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
        for v, p in zip(sp.points, pts):
            v.co = (*p, 1)
        sp.use_cyclic_u = closed
    cu.materials.append(mat)
    o = bpy.data.objects.new(name, cu); coll.objects.link(o)
    return o


def scroll_splines(pos_fn, w):
    out = []
    for sign in (-1, 1):
        pts = []
        for i in range(30):
            t = i / 29 * 2.5 * pi; rr = w * (1 - i / 36)
            pts.append(pos_fn(sign * (w * .8 + rr * cos(t)), rr * sin(t) * .45))
        out.append(pts)
    return out


def spiral_2d(cu_, cz, r, turns, start, direction, n=36):
    return [(cu_ + r * (1 - .8 * t) * cos(start + direction * turns * 2 * pi * t), cz + r * (1 - .8 * t) * sin(start + direction * turns * 2 * pi * t)) for t in [i / (n - 1) for i in range(n)]]


class Wall:
    """Local wall coordinates: u along the wall, z up, d = offset from the wall face into the hall."""

    def __init__(self, kind, s=1):
        self.kind, self.s = kind, s

    def pt(self, u, z, d):
        return (self.s * (15.775 - d), u, z) if self.kind == 'side' else (u, 13.775 - d, z)

    def dims(self, lu, h, dd):
        return (dd, lu, h) if self.kind == 'side' else (lu, dd, h)


def wbox(B, W, u, z, d, lu, h, dd):
    B.box(W.pt(u, z, d), W.dims(lu, h, dd))


def wframe(B, W, u, z, d, w, h, t, dd):
    for du in (-w / 2, w / 2):
        wbox(B, W, u + du, z, d, t, h + t, dd)
    for dz in (-h / 2, h / 2):
        wbox(B, W, u, z + dz, d, w + t, t, dd)


def balustrade(name, pos, L, z0):
    n = max(2, round(L / .5)); du = L / n
    posts, hearts = [], []
    for k in range(n + 1):
        x, y = pos(k * du)
        posts.append([(x, y, z0), (x, y, z0 + .95)])
    for k in range(n):
        um = (k + .5) * du; w = du * .78; h = .52; zc = z0 + .5
        pts = []
        for q in range(28):
            th = q / 28 * 2 * pi
            hx = (sin(th) ** 3) * (w / 2)
            hz = (13 * cos(th) - 5 * cos(2 * th) - 2 * cos(3 * th) - cos(4 * th)) / 17 * (h / 2)
            x, y = pos(um + hx)
            pts.append((x, y, zc + hz))
        hearts.append(pts)
    ends = [pos(0), pos(L)]
    curves(name + ' iron posts', posts, .02, iron)
    curves(name + ' iron heart scrolls', hearts, .012, iron, True)
    curves(name + ' gilt handrail', [[(x, y, z0 + .95) for x, y in ends]], .045, gold)
    curves(name + ' iron bottom rail', [[(x, y, z0 + .13) for x, y in ends]], .025, iron)


# ================================================================== walls
coll = colls[C_WALL]
Bw = Batch('P3 wall marble panels', white)
Bg = Batch('P3 wall gilt frames', gold)
Bgs = Batch('P3 wall gilt rosettes and lantern metal', gold, smooth=True)
Bb = Batch('P3 wall sapphire narrow panels', blue)
Bl = Batch('P3 lantern glow', bulb, smooth=True)
wall_scrolls, lantern_arms = [], []


def wide_panel(W, u, zc, w, h):
    wbox(Bw, W, u, zc, .02, w, h, .04)
    wframe(Bg, W, u, zc, .05, w, h, .07, .06)
    wframe(Bg, W, u, zc, .05, w - .36, h - .36, .035, .05)
    for zz, flip in ((zc + h / 2 - .5, 1), (zc - h / 2 + .5, -1)):
        wall_scrolls.extend(scroll_splines(lambda dt, dz, zz=zz, flip=flip: W.pt(u + dt, zz + flip * dz, .085), min(.36, w * .12)))
        Bgs.ball(W.pt(u, zz + flip * .08, .085), (.06, .06, .06) if W.kind == 'rear' else (.06, .06, .06))
    for du in (-(w / 2 - .45), w / 2 - .45):
        for dz in (-(h / 2 - .45), h / 2 - .45):
            Bgs.ball(W.pt(u + du, zc + dz, .08), (.045, .045, .045))


def lantern(W, u, z):
    lantern_arms.append([W.pt(u, z + .05, .0), W.pt(u, z + .32, .12), W.pt(u, z + .38, .3), W.pt(u, z + .3, .4)])
    lx, ly, _ = W.pt(u, z, .4)
    Bgs.cone((lx, ly, z + .23), .12, .03, .12)
    Bgs.ball((lx, ly, z + .31), (.03, .03, .05))
    Bgs.cone((lx, ly, z - .16), .025, .11, .1)
    Bgs.ball((lx, ly, z - .27), (.03, .03, .06))
    for k in range(6):
        a = k * pi / 3
        Bg.box((lx + .1 * cos(a), ly + .1 * sin(a), z + .03), (.016, .016, .32))
    Bl.cone((lx, ly, z + .03), .075, .075, .26)


def narrow_panel(W, u, zc, w, h, lz):
    wbox(Bb, W, u, zc, .03, w, h, .05)
    wframe(Bg, W, u, zc, .06, w, h, .05, .05)
    wframe(Bg, W, u, zc, .06, w - .2, h - .2, .025, .04)
    lantern(W, u, lz)


TIERS = (('upper', 8.05, 4.7, 8.25), ('lower', 2.475, 3.85, 2.85))
COLS = [-41, -36, -31, -26, -21, -16, -13, -8, -3, 2, 7, 12]
for s in (1, -1):
    W = Wall('side', s)
    for tier, zc, h, lz in TIERS:
        for yc in COLS:
            if tier == 'lower' and yc > 7.5:
                continue   # wing portal doors
            if yc < -40:
                continue   # entrance facade corner column stands here
            narrow_panel(W, yc, zc, .8, h - .2, lz)
        for a, b in zip(COLS, COLS[1:]):
            mid = (a + b) / 2
            if tier == 'lower' and mid > 7.2:
                continue
            wide_panel(W, mid, zc, min(3.4, b - a - 1.3), h)

Wr = Wall('rear')
for s in (1, -1):
    for tier, zc, h, lz in TIERS:
        for u, w in ((5.7, 2.6), (9.8, 3.0), (13.65, 2.4)):
            wide_panel(Wr, s * u, zc, w, h)
        narrow_panel(Wr, s * 4.1, zc, .5, h - .2, lz)

# Rear window: sapphire border and flanking gilt S-scroll grilles on the glass.
for sx in (-1, 1):
    Bb.box((sx * 3.15, 13.6, 6.7), (.25, .05, 10.3))
    for xx in (sx * 3.02, sx * 3.28):
        Bg.box((xx, 13.56, 6.7), (.03, .05, 10.3))
Bb.box((0, 13.6, 11.93), (6.55, .05, .25))
Bg.box((0, 13.56, 11.8), (6.55, .05, .03))
grille = []
for sx in (-1, 1):
    for cz, r, turns, start in ((9.3, .62, 1.15, -pi / 2), (7.4, .5, 1.1, pi / 2), (3.3, .5, 1.1, -pi / 2), (2.1, .38, 1.05, pi / 2)):
        grille.append([(sx * p[0], 13.42, p[1]) for p in spiral_2d(2.15, cz, r, turns, start, 1)])
    # Short stems join each spiral pair into one S-scroll (upper pair 7.9-8.68, lower pair 2.48-2.8).
    grille.append([(sx * 2.15, 13.42, z) for z in (7.88, 8.7)])
    grille.append([(sx * 2.15, 13.42, z) for z in (2.46, 2.82)])
curves('P3 rear window gilt S-scroll grilles', grille, .05, gold)

Bw.finish(); Bg.finish(); Bgs.finish(); Bb.finish(); Bl.finish()
curves('P3 wall gilt panel scrolls', wall_scrolls, .018, gold)
curves('P3 lantern gilt brackets', lantern_arms, .025, gold)

# ================================================================== gallery fascia, rails, entablature
coll = colls[C_GAL]
Fw = Batch('P3 gallery fascia marble', white)
Fb = Batch('P3 entablature sapphire insets', blue)
fascia_lines, fascia_scrolls = [], []


def fascia(p0, p1, normal, name_tag):
    """Marble band 4.42-5.12m between p0 and p1 (xy), face offset along normal (unit xy toward the viewer)."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    tx, ty = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = normal
    # Band sits in front of the slab edge (edge .. edge + 0.1 n) so its face never coincides with the slab face.
    cx, cy_ = (x0 + x1) / 2 + nx * .05, (y0 + y1) / 2 + ny * .05
    Fw.box((cx, cy_, 4.77), (abs(tx) * L + abs(nx) * .1, abs(ty) * L + abs(ny) * .1, .7))
    fx, fy = nx * .106, ny * .106
    for z in (4.5, 5.04):
        fascia_lines.append([(x0 + fx, y0 + fy, z), (x1 + fx, y1 + fy, z)])
    k = int(L // 1.2)
    for i in range(k):
        u = (i + .5) * L / k
        bx, by = x0 + tx * u + fx, y0 + ty * u + fy
        fascia_scrolls.extend(scroll_splines(lambda dt, dz, bx=bx, by=by: (bx + tx * dt, by + ty * dt, 4.77 + dz), .2))


for s in (1, -1):
    fascia((s * 11.4, -38.58), (s * 11.4, 8.18), (-s, 0), 'side')
    fascia((s * 3.85, 8.18), (s * 11.3, 8.18), (0, -1), 'landing')
    fascia((s * 3.45, -38.58), (s * 11.4, -38.58), (0, 1), 'balcony')
    fascia((s * 3.45, -41.75), (s * 3.45, -38.58), (-s, 0), 'return')
    balustrade('P3 side gallery balustrade %s' % ('R' if s > 0 else 'L'), lambda u, s=s: (s * 11.38, -38.58 + u), 46.76, 5.12)
    balustrade('P3 entrance balcony balustrade %s' % ('R' if s > 0 else 'L'), lambda u, s=s: (s * (3.5 + u), -38.58), 7.88, 5.12)
    balustrade('P3 entrance balcony return balustrade %s' % ('R' if s > 0 else 'L'), lambda u, s=s: (s * 3.45, -38.6 - u), 3.15, 5.12)

    # Entablature beam over the gallery columns with sapphire insets and gilt volutes.
    Fw.box((s * 11.8, -14, 11.675), (.7, 56, .65))
    volutes = []
    for a, b in zip(COLS, COLS[1:]):
        mid, gap = (a + b) / 2, b - a
        for face in (11.445, 12.155):
            Fb.box((s * face, mid, 11.675), (.02, gap - 1.0, .34))
            for z in (11.47, 11.88):
                fascia_lines.append([(s * face, a + .45, z), (s * face, b - .45, z)])
    for yc in COLS:
        for face, sgn in ((11.44, -1), (12.16, 1)):
            for side_, start in ((-1, 0), (1, pi)):
                volutes.append([(s * face, p[0], p[1]) for p in spiral_2d(yc + side_ * .28, 11.62, .22, 1.2, start, side_)])
    curves('P3 entablature gilt volutes %s' % ('R' if s > 0 else 'L'), volutes, .03, gold)

Fw.finish(); Fb.finish()
curves('P3 gallery fascia gilt lines', fascia_lines, .022, gold)
curves('P3 gallery fascia gilt scrolls', fascia_scrolls, .016, gold)

result = {k: len(c.objects) for k, c in colls.items()}
result['parked'] = len(parked)
result['wall_scroll_splines'] = len(wall_scrolls)
result['scene_objects'] = len(sc.objects)
print('P3_P3_RESULT', result)
