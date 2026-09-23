"""P8b 세부 구현: 천장 금장 부조 + 샹들리에 크리스털 + 티테이블 조각 다리 + 촛대·갤러리 소파 + 깃발·시계 + 천사상.

- 평천장 모서리·옆면·앞뒤: 가는 금장 선 대신 두께 있는 아칸서스 부조(리본 메시: C 스크롤·잎 부채·조개)
- 돔 샹들리에 2: 각 팔 끝 크리스털 구슬 줄·물방울 프리즘, 아래 단 구슬 화환, 왕관→아래 단 구슬 줄
- 티테이블 16: 곧은 막대 다리를 무릎이 불룩한 S자 카브리올 다리 + 말린 발끝으로 교체(두께가 점마다 달라짐)
- 아래층 옆벽 스탠드 촛대 8(+밤 광원), 갤러리 소파 6
- 정문 깃발 2: 금장 가로대·끝장식, 아래 술, 모서리 태슬, 양면 백합 문장
- 사이드보드 시계 2: 문자판 눈금, 깨진 박공, 추 창
- 천사상: 옷주름이 흐르는 로브, 가슴·어깨, 얼굴(코·턱·귀), 머리칼 타래와 쪽머리, 들어올린 팔(굵기 변화)과 손, 월계관
옛 천장 선 장식과 천사 몸체는 30x로 옮긴다. 재실행하면 45·47 컬렉션을 다시 만든다.
"""
import bpy, bmesh, math
from math import sin, cos, pi, atan2
from mathutils import Matrix, Vector

sc = bpy.context.scene
M = bpy.data.materials
white = M['Ivory marble']; gold = M['Antique gilded bronze']; blue = M['Sapphire stone']
velvet = M['Royal blue velvet']; iron = M['Wrought iron']; bulb = M['Candle light']; glass = M['Pale azure glazing']
HIDDEN = '30x | P3 replaced originals (hidden)'
C_ORN = '47 | P8 - Ceiling reliefs, crystals, banners and statue'
C_FURN = '45 | P8 - Additional candelabra and gallery sofas'


def ensure_coll(name, clear=True):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name); sc.collection.children.link(c)
    if clear:
        for o in list(c.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    return c


hidden = ensure_coll(HIDDEN, clear=False)
colls = {k: ensure_coll(k) for k in (C_ORN, C_FURN)}
coll = colls[C_ORN]
parked = []


def park(o):
    if o is None or hidden in o.users_collection:
        return
    o['p3_original_collections'] = ','.join(c.name for c in o.users_collection)
    for c in list(o.users_collection):
        c.objects.unlink(o)
    hidden.objects.link(o); parked.append(o.name)


class Batch:
    def __init__(self, name, mat, smooth=False):
        self.name, self.mat, self.smooth = name, mat, smooth
        self.bm = bmesh.new(); self.n = 0

    @staticmethod
    def _m(c, d=(1, 1, 1), rz=0.0, rx=0.0, ry=0.0):
        return (Matrix.Translation(c) @ Matrix.Rotation(rz, 4, 'Z') @ Matrix.Rotation(ry, 4, 'Y') @ Matrix.Rotation(rx, 4, 'X')
                @ Matrix.Diagonal((*d, 1)))

    def box(self, c, d, rz=0.0, ry=0.0):
        bmesh.ops.create_cube(self.bm, size=1, matrix=self._m(c, d, rz, 0.0, ry)); self.n += 1

    def cone(self, c, r1, r2, h, segs=16, rx=0.0, ry=0.0):
        bmesh.ops.create_cone(self.bm, cap_ends=True, segments=segs, radius1=r1, radius2=r2, depth=h, matrix=self._m(c, (1, 1, 1), 0.0, rx, ry)); self.n += 1

    def ball(self, c, rad, segs=10, rz=0.0, rx=0.0, ry=0.0):
        bmesh.ops.create_uvsphere(self.bm, u_segments=segs, v_segments=max(6, segs // 2 + 2), radius=1, matrix=self._m(c, rad, rz, rx, ry)); self.n += 1

    def lathe(self, profile, c=(0, 0, 0), segs=24):
        before = set(self.bm.verts)
        vs = [self.bm.verts.new((c[0] + r, c[1], c[2] + z)) for r, z in profile]
        es = [self.bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
        bmesh.ops.spin(self.bm, geom=vs + es, angle=2 * pi, steps=segs, axis=(0, 0, 1), cent=c)
        bmesh.ops.remove_doubles(self.bm, verts=[v for v in self.bm.verts if v not in before], dist=1e-5); self.n += 1

    def prism_xz(self, pts_xz, y0, y1):
        f = [self.bm.verts.new((x, y0, z)) for x, z in pts_xz]
        b = [self.bm.verts.new((x, y1, z)) for x, z in pts_xz]
        self.bm.faces.new(f); self.bm.faces.new(b[::-1])
        for i in range(len(pts_xz)):
            j = (i + 1) % len(pts_xz)
            self.bm.faces.new((f[j], f[i], b[i], b[j]))
        self.n += 1

    def ribbon(self, pts, widths, z0, thick=.05):
        n = len(pts); L, R = [], []
        for i in range(n):
            x0, y0 = pts[max(i - 1, 0)]; x1, y1 = pts[min(i + 1, n - 1)]
            dx, dy = x1 - x0, y1 - y0; l = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / l, dx / l; w = max(widths[i], .015) / 2
            L.append((pts[i][0] + nx * w, pts[i][1] + ny * w)); R.append((pts[i][0] - nx * w, pts[i][1] - ny * w))
        bm = self.bm
        Lb = [bm.verts.new((x, y, z0)) for x, y in L]; Rb = [bm.verts.new((x, y, z0)) for x, y in R]
        Lt = [bm.verts.new((x, y, z0 + thick)) for x, y in L]; Rt = [bm.verts.new((x, y, z0 + thick)) for x, y in R]
        for i in range(n - 1):
            bm.faces.new((Lb[i], Rb[i], Rb[i + 1], Lb[i + 1]))
            bm.faces.new((Lt[i], Lt[i + 1], Rt[i + 1], Rt[i]))
            bm.faces.new((Lb[i], Lb[i + 1], Lt[i + 1], Lt[i]))
            bm.faces.new((Rb[i], Rt[i], Rt[i + 1], Rb[i + 1]))
        self.n += 1

    def finish(self, matrix=None):
        if self.n == 0:
            self.bm.free(); return None
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        me = bpy.data.meshes.new(self.name); self.bm.to_mesh(me); self.bm.free()
        me.materials.append(self.mat)
        if self.smooth:
            for p in me.polygons:
                p.use_smooth = True
        o = bpy.data.objects.new(self.name, me); coll.objects.link(o)
        if matrix is not None:
            o.matrix_world = matrix
        return o


def curves(name, splines, r, mat, closed=False, matrix=None, radii=None, smooth=False):
    splines = [s_ for s_ in splines if s_]
    if not splines:
        return None
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 2 if r >= .02 else 1
    cu.resolution_u = 8 if smooth else 1; cu.use_fill_caps = True
    for si, pts in enumerate(splines):
        sp = cu.splines.new('NURBS' if smooth else 'POLY'); sp.points.add(len(pts) - 1)
        if smooth:
            sp.order_u = 3; sp.use_endpoint_u = not closed
        for pi_, (v, p) in enumerate(zip(sp.points, pts)):
            v.co = (*p, 1)
            if radii is not None:
                v.radius = radii[si][pi_]
        sp.use_cyclic_u = closed
    cu.materials.append(mat)
    o = bpy.data.objects.new(name, cu); coll.objects.link(o)
    if matrix is not None:
        o.matrix_world = matrix
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


def place(x, y, z=0.0, rz=0.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(rz, 4, 'Z')


# ================================================================== 1. ceiling acanthus reliefs
for tag in ('rear', 'front'):
    for nm in ('P3 ceiling gilt acanthus corners %s', 'P3 ceiling gilt acanthus corners inner %s', 'P3 ceiling gilt side cartouches %s'):
        park(bpy.data.objects.get(nm % tag))
    for o in [o for o in list(sc.objects) if o.name.startswith('P3 ceiling cartouche sapphire diamond %s' % tag)]:
        park(o)

Rg = Batch('P8 ceiling gilt acanthus reliefs', gold)
Z_REL = 11.945


def spiral_ribbon(cx, cy, R, turns, start, dirn, w0, n=64):
    pts, ws = [], []
    for i in range(n):
        t = i / (n - 1)
        rr = R * (1 - .78 * t); a = start + dirn * turns * 2 * pi * t
        pts.append((cx + rr * cos(a), cy + rr * sin(a)))
        ws.append(w0 * (1 - .72 * t) * (1 + .22 * sin(20 * pi * t)) + .02)
    Rg.ribbon(pts, ws, Z_REL)
    return pts


def petal(bx, by, ang, length, width):
    dx, dy = cos(ang), sin(ang); px, py = -dy, dx
    pts, ws = [], []
    for i in range(18):
        t = i / 17
        pts.append((bx + dx * length * t + px * .12 * length * sin(pi * t), by + dy * length * t + py * .12 * length * sin(pi * t)))
        ws.append(width * sin(pi * t) ** .8 * (1 + .15 * sin(6 * pi * t)) + .015)
    Rg.ribbon(pts, ws, Z_REL + .004, .045)


def fan(bx, by, ang, n, spread, length, width):
    for k in range(n):
        petal(bx, by, ang + spread * (k / (n - 1) - .5), length * (1 - .25 * abs(k / (n - 1) - .5) * 2), width)


for cy0 in (0.0, -28.0):
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * 13.9, cy0 + sy * 10.3
            base_ang = atan2(-sy, -sx)
            main = spiral_ribbon(cx, cy, 1.25, 1.15, base_ang, sx * sy, .26)
            sec = spiral_ribbon(cx, cy - sy * 2.2, .75, 1.05, base_ang + pi, -sx * sy, .16)
            spiral_ribbon(cx + sx * .15, cy + sy * 1.85, .42, 1.0, base_ang + pi / 2, -sx * sy, .11)
            Rg.ribbon([main[0], ((main[0][0] + sec[0][0]) / 2 + sx * .2, (main[0][1] + sec[0][1]) / 2), sec[0]], [.1, .07, .1], Z_REL)
            fan(cx + sx * .75, cy + sy * .75, atan2(sy, sx), 5, 1.6, .75, .2)
        cx, cy = sx * 13.9, cy0
        spiral_ribbon(cx, cy + 1.0, .9, 1.1, -pi / 2, sx, .19)
        spiral_ribbon(cx, cy - 1.0, .9, 1.1, pi / 2, -sx, .19)
        fan(cx + sx * .45, cy, atan2(0, -sx), 7, 2.2, .85, .2)
    for sy in (-1, 1):
        cy = cy0 + sy * 11.3
        for sx in (-1, 1):
            spiral_ribbon(sx * 1.0, cy, .85, 1.1, 0 if sx > 0 else pi, sx * sy, .18)
        fan(0, cy + sy * .45, atan2(-sy, 0), 7, 2.2, .85, .2)
Rg.finish()

# ================================================================== 2. chandelier crystal strands and garlands
for tag, cy in (('rear dome', 0.0), ('front dome', -28.0)):
    Bx = Batch('P8 chandelier %s crystal beads' % tag, glass, True)
    tips_a = []
    for tz, R, n in ((8.25, 1.95, 16), (9.1, 1.35, 12), (9.9, .8, 8)):
        for k in range(n):
            a = 2 * pi * (k + (.5 if n == 12 else 0)) / n
            ex, ey, ez = R * cos(a), cy + R * sin(a), tz - .1
            if R > 1:
                for i in range(5):
                    Bx.ball((ex, ey, ez - .38 - .065 * i), (.017, .017, .017), 8)
                Bx.ball((ex, ey, ez - .75), (.022, .022, .06), 8)
            if n == 16:
                tips_a.append((ex, ey, ez))
    for k in range(16):
        p, q = tips_a[k], tips_a[(k + 1) % 16]
        for i in range(1, 10):
            t = i / 10
            Bx.ball((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t, p[2] - .05 - .34 * sin(pi * t) - .04), (.016, .016, .016), 8)
        a = 2 * pi * k / 16
        for i in range(1, 8):
            t = i / 8
            Bx.ball((.55 * cos(a) * (1 - t) + 1.95 * cos(a) * t, cy + .55 * sin(a) * (1 - t) + 1.95 * sin(a) * t, 10.95 - 2.8 * t - .35 * sin(pi * t)), (.014, .014, .014), 8)
    Bx.finish()

# ================================================================== 3. carved cabriole tea-table legs
legs_done = 0
for o in bpy.data.collections['38 | P3 - Tea salons with generated chairs'].objects:
    if not o.name.endswith('carved table feet') or o.type != 'CURVE':
        continue
    cu = o.data; cu.splines.clear()
    cu.bevel_depth = .034; cu.bevel_resolution = 3
    prof = [(.1, .32, 1.25), (.19, .31, 1.5), (.28, .25, 1.4), (.36, .16, 1.05), (.42, .08, .7), (.46, .035, .78), (.51, .04, .95), (.54, .085, .75), (.52, .125, .55), (.48, .13, .4)]
    for k in range(4):
        a = pi / 4 + k * pi / 2
        sp = cu.splines.new('POLY'); sp.points.add(len(prof) - 1)
        for v, (r, z, rad) in zip(sp.points, prof):
            v.co = (r * cos(a), r * sin(a), z, 1); v.radius = rad
    Bk = Batch(o.name.replace('carved table feet', 'P8 leg gilt knee leaves'), gold, True)
    for k in range(4):
        a = pi / 4 + k * pi / 2
        for dz, sc_ in ((.27, 1.0), (.23, .8)):
            Bk.ball((.25 * cos(a), .25 * sin(a), dz), (.05 * sc_, .05 * sc_, .025 * sc_), 10, rz=a)
    Bk.finish(o.matrix_world.copy())
    legs_done += 1

# ================================================================== 4. extra candelabra and gallery sofas
coll = colls[C_FURN]


def candelabrum(tag, Mtx):
    Bg = Batch('P8 candelabrum %s gilt' % tag, gold, smooth=True)
    Bc = Batch('P8 candelabrum %s candles' % tag, white, smooth=True)
    Bf = Batch('P8 candelabrum %s flames' % tag, bulb, smooth=True)
    Bx = Batch('P8 candelabrum %s crystals' % tag, glass, smooth=True)
    irons = [[(0, 0, .35), (0, 0, 1.56)]]
    for k in range(3):
        a = 2 * pi * k / 3; c_, s_ = cos(a), sin(a)
        irons.append([(0, 0, .36), (.15 * c_, .15 * s_, .2), (.28 * c_, .28 * s_, .05), (.31 * c_, .31 * s_, .01)])
        Bg.ball((.31 * c_, .31 * s_, .03), (.03, .03, .03))
    for z, r in ((.36, .05), (.9, .045), (1.5, .05)):
        Bg.ball((0, 0, z), (r, r, r * 1.2))
    Bg.cone((0, 0, 1.58), .03, .12, .04)
    arms = []
    for k in range(5):
        a = 2 * pi * k / 5; c_, s_ = cos(a), sin(a)
        arms.append([(r * c_, r * s_, 1.58 + .14 * sin(pi * t) + .1 * t) for t, r in [(i / 10, .03 + .27 * i / 10) for i in range(11)]])
        ex, ey = .3 * c_, .3 * s_
        Bg.cone((ex, ey, 1.7), .025, .045, .04)
        Bc.cone((ex, ey, 1.8), .018, .018, .16, segs=10)
        Bf.ball((ex, ey, 1.91), (.017, .017, .035))
        for i in range(3):
            Bx.ball((ex, ey, 1.6 - .05 * i), (.014, .014, .02 if i < 2 else .04))
    Bc.cone((0, 0, 1.72), .02, .02, .22, segs=10); Bf.ball((0, 0, 1.86), (.018, .018, .038))
    curves('P8 candelabrum %s iron stand' % tag, irons, .022, iron, False, Mtx)
    curves('P8 candelabrum %s gilt arms' % tag, arms, .014, gold, False, Mtx)
    for b in (Bg, Bc, Bf, Bx):
        b.finish(Mtx)


def sofa(tag, Mtx):
    Bv = Batch('P8 sofa %s velvet' % tag, velvet, smooth=True)
    Bw = Batch('P8 sofa %s carved frame' % tag, white)
    Bg = Batch('P8 sofa %s gilt' % tag, gold, smooth=True)
    Bv.box((0, -.03, .5), (1.78, .6, .15))
    Bw.box((0, 0, .38), (1.94, .72, .12))
    top = lambda x: .96 + .16 * cos(pi * x / 1.8)
    xs = [-.9 + 1.8 * i / 20 for i in range(21)]
    Bv.prism_xz([(x, top(x)) for x in xs] + [(.9, .55), (-.9, .55)], .24, .36)
    Bv.ball((-.5, .15, .74), (.22, .07, .2)); Bv.ball((.5, .15, .74), (.22, .07, .2))
    for sx in (-1, 1):
        Bv.box((sx * .92, -.02, .66), (.1, .5, .08))
    frame = [[(x, .23, top(x) + .035) for x in xs]]
    frame += [[(sx * .95, .3, .95), (sx * 1.0, .12, .82), (sx * 1.03, -.12, .74), (sx * 1.01, -.32, .64), (sx * .97, -.37, .52), (sx * .93, -.3, .45)] for sx in (-1, 1)]
    curves('P8 sofa %s carved rails' % tag, frame, .045, white, False, Mtx)
    legs = [[(sx * .85, sy * .28, .33), (sx * .92, sy * .34, .2), (sx * .87, sy * .3, .06), (sx * .9, sy * .33, .02)] for sx in (-1, 1) for sy in (-1, 1)]
    curves('P8 sofa %s gilt cabriole legs' % tag, legs, .03, gold, False, Mtx)
    curves('P8 sofa %s gilt crest' % tag, scroll_splines(lambda dt, dz: (dt, .2, top(0) + .14 + dz), .13), .016, gold, False, Mtx)
    for sx in (-1, 1):
        Bg.ball((sx * .93, -.3, .45), (.03, .03, .03))
    for b in (Bv, Bw, Bg):
        b.finish(Mtx)


L_NIGHT = bpy.data.collections.get('LIGHTING_Night')
if L_NIGHT:
    for o in list(L_NIGHT.objects):
        if o.name.startswith('LGT_night_p8_candelabrum'):
            bpy.data.objects.remove(o, do_unlink=True)
for s in (1, -1):
    side = 'R' if s > 0 else 'L'
    for y in (-28.5, -18.5, -10.5, -0.5):
        candelabrum('%s %.1f' % (side, y), place(s * 15.3, y, 0))
        if L_NIGHT:
            d = bpy.data.lights.new('LGT_night_p8_candelabrum_%s_%.1f' % (side, y), 'POINT'); d.energy = 45; d.color = (1, .7, .4); d.shadow_soft_size = .2
            lo = bpy.data.objects.new(d.name, d); L_NIGHT.objects.link(lo); lo.location = (s * 15.3, y, 1.95)
            lo['p6_created'] = True; lo['purpose'] = 'P8 standing candelabrum practical'
    for y in (-28.5, -18.5, 4.5):
        sofa('gallery %s %.1f' % (side, y), place(s * (15.775 - .42), y, 5.12, -s * pi / 2))

# ================================================================== 5. entrance banners
coll = colls[C_ORN]
FLEUR = [
    [(0, .55), (.1, .36), (.13, .16), (.06, .01), (0, -.04), (-.06, .01), (-.13, .16), (-.1, .36)],
    [(.05, .05), (.22, .12), (.34, .3), (.3, .43), (.2, .37), (.2, .22), (.12, .1)],
    [(-.05, .05), (-.22, .12), (-.34, .3), (-.3, .43), (-.2, .37), (-.2, .22), (-.12, .1)],
    [(-.22, -.03), (.22, -.03), (.22, -.11), (-.22, -.11)],
    [(0, -.11), (.13, -.32), (0, -.26), (-.13, -.32)],
]
banners = 0
for o in [o for o in sc.objects if o.name.startswith('Blue imperial standard')]:   # snapshot: new objects are linked below
    bx, by, bz = o.location
    top, bot = bz + 1.4, bz - 1.4
    Bg = Batch('P8 banner gilt fittings %.0f' % bx, gold, True)
    Bg.cone((bx, by, top + .08), .03, .03, 1.55, 16, ry=pi / 2)
    for sx in (-1, 1):
        Bg.ball((bx + sx * .8, by, top + .08), (.055, .055, .07))
        Bg.cone((bx + sx * .66, by, bot - .15), .025, .06, .16, 12)
        Bg.ball((bx + sx * .66, by, bot - .04), (.035, .035, .035))
    for i in range(27):
        Bg.box((bx - .6 + 1.2 * i / 26, by, bot - .07), (.012, .012, .14))
    Bg.finish()
    em = []
    for face in (-1, 1):
        for shape in FLEUR:
            em.append([(bx + u, by + face * .035, bz - .05 + v) for u, v in shape])
    curves('P8 banner gilt fleur-de-lis %.0f' % bx, em, .02, gold, True, smooth=True)
    banners += 1

# ================================================================== 6. sideboard clock details
for s in (1, -1):
    Mtx = place(s * (15.775 - .36), 4.5, 0, -s * pi / 2)
    Bg = Batch('P8 clock %s gilt details' % ('R' if s > 0 else 'L'), gold)
    Bx = Batch('P8 clock %s pendulum glass' % ('R' if s > 0 else 'L'), glass)
    cyk = -.66
    for k in range(12):
        a = 2 * pi * k / 12
        Bg.box((.095 * sin(a), cyk - .135, 1.44 + .095 * cos(a)), (.01, .006, .028 if k % 3 else .04), ry=-a)
    Bx.box((0, cyk - .15, .6), (.12, .01, .5))
    Bg.box((0, cyk - .155, .45), (.004, .004, .3))
    Bg.cone((0, cyk - .158, .29), .045, .045, .008, 20, rx=pi / 2)
    ped = [[(-.22, cyk - .1, 1.64), (-.07, cyk - .1, 1.75), (-.05, cyk - .1, 1.72)], [(.22, cyk - .1, 1.64), (.07, cyk - .1, 1.75), (.05, cyk - .1, 1.72)]]
    for sx in (-1, 1):
        ped.append([(sx * .22 + .04 * (1 - u / 9) * cos(u) * sx, cyk - .1, 1.62 + .04 * (1 - u / 9) * sin(u)) for u in [j * .5 for j in range(12)]])
    Bg.finish(Mtx); Bx.finish(Mtx)
    curves('P8 clock %s gilt pediment' % ('R' if s > 0 else 'L'), ped, .018, gold, False, Mtx)

# ================================================================== 7. angel statue
FX, FY = 0.0, 4.0
for nm in ('P3 angel robe', 'P3 angel robe folds', 'P3 angel torso', 'P3 angel neck', 'P3 angel head', 'P3 angel hair', 'P3 angel raised arm', 'P3 angel hand'):
    for o in [o for o in list(sc.objects) if o.name == nm or o.name.startswith(nm + '.')]:
        park(o)


def lathe_obj(name, profile, segs, displace=None, yscale=1.0):
    bm = bmesh.new()
    vs = [bm.verts.new((FX + r, FY, z)) for r, z in profile]
    es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + es, angle=2 * pi, steps=segs, axis=(0, 0, 1), cent=(FX, FY, 0))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    for v in bm.verts:
        dx, dy = v.co.x - FX, v.co.y - FY
        r = math.hypot(dx, dy)
        if r > 1e-5 and displace:
            th = atan2(dy, dx); r2 = displace(r, th, v.co.z)
            dx, dy = r2 * cos(th), r2 * sin(th)
        v.co.x, v.co.y = FX + dx, FY + dy * yscale
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(white)
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    return o


def robe_folds(r, th, z):
    zn = min(max((z - 3.3) / 1.33, 0.0), 1.0)
    amp = .05 * (1 - zn) ** 1.3 + .006
    return r + amp * sin(11 * th + 3 * zn) + .02 * (1 - zn) * sin(3 * th + .6)


lathe_obj('P8 angel draped robe', [(0, 3.3), (.37, 3.3), (.36, 3.36), (.33, 3.55), (.29, 3.8), (.25, 4.02), (.215, 4.2), (.2, 4.32), (.19, 4.42), (.16, 4.55), (.12, 4.62), (0, 4.63)], 72, robe_folds)
lathe_obj('P8 angel torso', [(0, 4.42), (.165, 4.44), (.17, 4.54), (.165, 4.64), (.145, 4.73), (.105, 4.81), (.05, 4.87), (0, 4.88)], 48, None, .7)
Ba = Batch('P8 angel carved details', white, True)
for sx in (-1, 1):
    Ba.ball((FX + sx * .16, FY + .01, 4.78), (.07, .06, .06), 14)          # shoulders, blended into the torso
    Ba.ball((FX + sx * .088, FY + .005, 5.05), (.014, .01, .026))           # ears
    Ba.ball((FX + sx * .13, FY - .04, 5.53), (.032, .02, .05))              # hands
Ba.cone((FX, FY, 4.93), .042, .038, .12, 16)
Ba.ball((FX, FY - .005, 5.05), (.088, .096, .116), 18)                     # smooth idealised head
Ba.ball((FX, FY - .086, 5.045), (.012, .016, .022))                          # subtle nose
Ba.ball((FX, FY + .07, 5.11), (.07, .066, .064), 14)                        # hair bun
for k in range(20):
    a = 2 * pi * k / 20
    Ba.ball((FX + .1 * cos(a), FY - .04, 5.62 + .1 * sin(a)), (.02, .01, .012), 8, ry=-a)
Ba.finish()
curves('P8 angel sash', [[(FX + .205 * cos(t), FY + .16 * sin(t), 4.36 + .03 * sin(t)) for t in [i * 2 * pi / 32 for i in range(32)]]], .024, white, True)
locks = []
for k in range(14):
    a = -pi / 2 + .9 + (2 * pi - 1.8) * k / 13
    ca, sa = cos(a), sin(a)
    locks.append([(FX + .02 * ca, FY + .02 * sa, 5.17), (FX + .095 * ca, FY + .1 * sa, 5.12), (FX + .112 * ca, FY + .115 * sa, 5.02 + .01 * sin(3 * a)),
                  (FX + .1 * ca, FY + .11 * sa, 4.95), (FX + .07 * ca, FY + .09 * sa + .02, 4.9)])
curves('P8 angel hair locks', locks, .017, white)
arms, arm_r = [], []
for sx in (-1, 1):
    arms.append([(FX + sx * .18, FY, 4.8), (FX + sx * .26, FY - .01, 4.98), (FX + sx * .3, FY - .03, 5.12), (FX + sx * .26, FY - .04, 5.3), (FX + sx * .17, FY - .04, 5.46)])
    arm_r.append([1.0, .9, .78, .68, .55])
curves('P8 angel raised arms', arms, .05, white, radii=arm_r)
fingers = []
for sx in (-1, 1):
    for f in range(4):
        fingers.append([(FX + sx * (.12 + .012 * f), FY - .05, 5.56), (FX + sx * (.1 + .012 * f), FY - .05, 5.62)])
curves('P8 angel fingers', fingers, .008, white)
curves('P8 angel laurel wreath', [[(FX + .1 * cos(t), FY - .04, 5.62 + .1 * sin(t)) for t in [i * 2 * pi / 40 for i in range(40)]]], .013, white, True)

result = {'ornament_objects': len(colls[C_ORN].objects), 'furniture_objects': len(colls[C_FURN].objects),
          'legs_rebuilt': legs_done, 'banners': banners, 'parked': parked, 'scene_objects': len(sc.objects)}
print('P8B_RESULT', result)
