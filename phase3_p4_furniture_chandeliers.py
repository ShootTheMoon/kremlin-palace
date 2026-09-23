"""3차 P4: 티테이블 세트(생성 의자) + 소파·스탠드 촛대 + 사이드보드 소품 + 돔 크리스털 샹들리에.

- 티테이블 16세트(바닥 8, 갤러리 8): 12각 대리석 상판·금장 상감·조각 받침·원형 러그·식기·케이크·3단 스탠드.
  의자는 Higgsfield 생성 의자(GEN_rococo_armchair_source)의 경량 메시를 연결 복제해 세트마다 4개.
- 로코코 청색 소파 4(옆벽 아래층), 소파 양옆 스탠드 촛대.
- 사이드보드 2(옆벽 y=4.5): 받침 시계, 주전자 한 쌍, 서빙 트롤리, 전화기 받침대, 타원 거울.
- 돔 중앙 크리스털 샹들리에 2(y=0, -28): 3단 스크롤 팔, 촛대, 크리스털, 채광창까지 사슬.
옛 살롱 가구(07, 13)와 홀 샹들리에 형상(06, 14)은 30x로 옮긴다. 조명 오브젝트는 그대로 둔다. 재실행 가능.
각 소품은 제자리를 원점으로 한 오브젝트라 통째로 옮기거나 돌릴 수 있다.
"""
import bpy, bmesh, math
from math import sin, cos, pi, radians
from mathutils import Matrix, Vector

sc = bpy.context.scene
M = bpy.data.materials
white = M['Ivory marble']; gold = M['Antique gilded bronze']; blue = M['Sapphire stone']
velvet = M['Royal blue velvet']; iron = M['Wrought iron']; bulb = M['Candle light']
glass = M['Pale azure glazing']; mirror = M['Palace mirror']


def mat_get(name, rgb, rough=.5, metal=0.0):
    m = M.get(name)
    if m is None:
        m = M.new(name); m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*rgb, 1); p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*rgb, 1)
    return m


lavender = mat_get('P3 cake lavender icing', (.52, .44, .86), .45)
berry = mat_get('P3 berry red', (.62, .03, .07), .35)
porcelain = mat_get('P3 porcelain white', (.93, .93, .96), .22)

HIDDEN = '30x | P3 replaced originals (hidden)'
C_TEA = '38 | P3 - Tea salons with generated chairs'
C_FURN = '39 | P3 - Sofas, candelabra and sideboards'
C_CHAN = '40 | P3 - Dome crystal chandeliers'
C_GEN = '34 | P3 - Generated props (source)'


def ensure_coll(name, clear=True):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name); sc.collection.children.link(c)
    if clear:
        for o in list(c.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    return c


hidden = ensure_coll(HIDDEN, clear=False)
colls = {k: ensure_coll(k) for k in (C_TEA, C_FURN, C_CHAN)}
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


for cname in ('07 | Salon furniture', '13 | NEW HALF - Furnished reception salons'):
    c = bpy.data.collections.get(cname)
    if c:
        for o in list(c.objects):
            park(o)
for cname in ('06 | Chandeliers and sconces', '14 | NEW HALF - Ceiling and chandeliers'):
    c = bpy.data.collections.get(cname)
    if c:
        for o in list(c.objects):
            if o.type in {'MESH', 'CURVE'}:
                park(o)


class Batch:
    def __init__(self, name, mat, smooth=False):
        self.name, self.mat, self.smooth = name, mat, smooth
        self.bm = bmesh.new(); self.n = 0

    @staticmethod
    def _m(c, rz=0.0, d=(1, 1, 1), rx=0.0):
        return Matrix.Translation(c) @ Matrix.Rotation(rz, 4, 'Z') @ Matrix.Rotation(rx, 4, 'X') @ Matrix.Diagonal((*d, 1))

    def box(self, c, d, rz=0.0, rx=0.0):
        bmesh.ops.create_cube(self.bm, size=1, matrix=self._m(c, rz, d, rx)); self.n += 1

    def cone(self, c, r1, r2, h, segs=16, rz=0.0, rx=0.0):
        bmesh.ops.create_cone(self.bm, cap_ends=True, segments=segs, radius1=r1, radius2=r2, depth=h, matrix=self._m(c, rz, (1, 1, 1), rx)); self.n += 1

    def ball(self, c, rad, segs=12):
        bmesh.ops.create_uvsphere(self.bm, u_segments=segs, v_segments=8, radius=1, matrix=self._m(c, 0.0, rad)); self.n += 1

    def lathe(self, profile, c=(0, 0, 0), segs=24):
        before = set(self.bm.verts)
        vs = [self.bm.verts.new((c[0] + r, c[1], c[2] + z)) for r, z in profile]
        es = [self.bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
        bmesh.ops.spin(self.bm, geom=vs + es, angle=2 * pi, steps=segs, axis=(0, 0, 1), cent=c)
        new = [v for v in self.bm.verts if v not in before]
        bmesh.ops.remove_doubles(self.bm, verts=new, dist=1e-5); self.n += 1

    def prism_xz(self, pts_xz, y0, y1):
        """Extrude a polygon drawn in the XZ plane between y0 and y1."""
        f = [self.bm.verts.new((x, y0, z)) for x, z in pts_xz]
        b = [self.bm.verts.new((x, y1, z)) for x, z in pts_xz]
        self.bm.faces.new(f); self.bm.faces.new(b[::-1])
        n = len(pts_xz)
        for i in range(n):
            j = (i + 1) % n
            self.bm.faces.new((f[j], f[i], b[i], b[j]))
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


def curves(name, splines, r, mat, closed=False, matrix=None):
    splines = [s_ for s_ in splines if s_]
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


def circle(cx, cy, cz, r, n=24, plane='XY'):
    if plane == 'XY':
        return [(cx + r * cos(2 * pi * i / n), cy + r * sin(2 * pi * i / n), cz) for i in range(n)]
    if plane == 'XZ':
        return [(cx + r * cos(2 * pi * i / n), cy, cz + r * sin(2 * pi * i / n)) for i in range(n)]
    return [(cx, cy + r * cos(2 * pi * i / n), cz + r * sin(2 * pi * i / n)) for i in range(n)]


def place(x, y, z=0.0, rz=0.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(rz, 4, 'Z')


# ------------------------------------------------------------------ chair LOD from the generated source
gen = bpy.data.collections[C_GEN]
for lc in bpy.context.view_layer.layer_collection.children:
    if lc.name == C_GEN:
        lc.exclude = False
src = bpy.data.objects['GEN_rococo_armchair_source']
lod = bpy.data.meshes.get('GEN_rococo_armchair_LOD')
if lod is None:
    tmp = src.copy(); tmp.data = src.data.copy(); gen.objects.link(tmp)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    tmp.select_set(True); bpy.context.view_layer.objects.active = tmp
    mod = tmp.modifiers.new('LOD decimate', 'DECIMATE'); mod.ratio = .4
    with bpy.context.temp_override(object=tmp, active_object=tmp, selected_objects=[tmp], selected_editable_objects=[tmp]):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    lod = tmp.data; lod.name = 'GEN_rococo_armchair_LOD'; lod.use_fake_user = True
    bpy.data.objects.remove(tmp)
gen.hide_render = True

# ------------------------------------------------------------------ tea salons
coll = colls[C_TEA]
TEA_SETS = [(sx * 7, y, 0.0) for sx in (-1, 1) for y in (-3, -8, -31, -36)] + \
           [(sx * 13.7, y, 5.12) for sx in (-1, 1) for y in (-9.5, .5, -24, -33)]
chairs = 0
for idx, (cx, cy, cz) in enumerate(TEA_SETS):
    tag = 'T%02d' % idx
    Mtx = place(cx, cy, cz)
    Bv = Batch('P3 tea %s rug velvet' % tag, velvet)
    Bw = Batch('P3 tea %s marble table' % tag, white, smooth=True)
    Bg = Batch('P3 tea %s gilt metal' % tag, gold, smooth=True)
    Bp = Batch('P3 tea %s porcelain' % tag, porcelain, smooth=True)
    Bi = Batch('P3 tea %s cutlery' % tag, iron)
    Bl = Batch('P3 tea %s cake' % tag, lavender, smooth=True)
    Br = Batch('P3 tea %s berries' % tag, berry, smooth=True)
    Bx = Batch('P3 tea %s crystal plates' % tag, glass, smooth=True)
    lines, fine = [], []
    # Rug
    Bv.cone((0, 0, .006), 1.8, 1.8, .012, segs=64)
    lines += [circle(0, 0, .014, r, 64) for r in (1.74, 1.62, .95)]
    for k in range(16):
        a = 2 * pi * k / 16; nx_, ny_ = cos(a), sin(a); tx_, ty_ = -sin(a), cos(a)
        fine += scroll_splines(lambda dt, dz, nx_=nx_, ny_=ny_, tx_=tx_, ty_=ty_: (nx_ * (1.28 + dz) + tx_ * dt, ny_ * (1.28 + dz) + ty_ * dt, .014), .17)
    # Table
    Bw.cone((0, 0, .76), .62, .62, .06, segs=12)
    Bw.cone((0, 0, .69), .56, .56, .08, segs=12)
    Bw.lathe([(0, .05), (.3, .05), (.32, .1), (.12, .16), (.09, .3), (.16, .45), (.07, .6), (.1, .66), (0, .66)], (0, 0, 0), 20)
    lines += [[(.625 * cos(2 * pi * i / 12 + pi / 12), .625 * sin(2 * pi * i / 12 + pi / 12), z) for i in range(12)] for z in (.79, .73)]
    lines += [circle(0, 0, z, r, 20) for z, r in ((.16, .125), (.45, .165), (.6, .105))]
    fine += [circle(0, 0, .792, r, 36) for r in (.3, .12)]
    for k in range(8):
        a = 2 * pi * k / 8; nx_, ny_ = cos(a), sin(a); tx_, ty_ = -sin(a), cos(a)
        fine += scroll_splines(lambda dt, dz, nx_=nx_, ny_=ny_, tx_=tx_, ty_=ty_: (nx_ * (.46 + dz) + tx_ * dt, ny_ * (.46 + dz) + ty_ * dt, .792), .07)
    feet = []
    for k in range(4):
        a = pi / 4 + k * pi / 2; c_, s_ = cos(a), sin(a)
        feet.append([(.1 * c_, .1 * s_, .3), (.28 * c_, .28 * s_, .16), (.42 * c_, .42 * s_, .05), (.47 * c_, .47 * s_, .1), (.43 * c_, .43 * s_, .14)])
        Bg.ball((.47 * c_, .47 * s_, .06), (.035, .035, .035))
    # Place settings facing the four chairs
    for k in range(4):
        a = k * pi / 2; c_, s_ = cos(a), sin(a)
        Bp.box((.42 * c_, .42 * s_, .7925), (.24, .34, .004), rz=a)
        Bp.cone((.42 * c_, .42 * s_, .8), .085, .085, .008, segs=24)
        fine.append(circle(.42 * c_, .42 * s_, .805, .085, 24))
        for off in (-.14, .14):
            Bi.box((.42 * c_ - s_ * off, .42 * s_ + c_ * off, .797), (.14, .012, .004), rz=a)
    # Cake and tiered stand
    Bg.cone((0, 0, .8), .15, .15, .012, segs=24)
    Bl.cone((0, 0, .866), .11, .11, .12, segs=24)
    for k in range(10):
        a = 2 * pi * k / 10
        Bl.ball((.11 * cos(a), .11 * sin(a), .9), (.018, .018, .035))
    for k in range(5):
        a = 2 * pi * k / 5
        Bx.ball((.06 * cos(a), .06 * sin(a), .94), (.025, .025, .014))
    sx_, sy_ = .2, .14
    Bg.cone((sx_, sy_, 1.03), .012, .012, .46, segs=8)
    Bg.ball((sx_, sy_, 1.28), (.02, .02, .03))
    for z, r, n in ((.86, .16, 7), (1.02, .12, 5), (1.16, .08, 3)):
        Bx.cone((sx_, sy_, z), r, r, .008, segs=24)
        fine.append(circle(sx_, sy_, z + .005, r, 24))
        for k in range(n):
            a = 2 * pi * k / n
            Bp.cone((sx_ + r * .62 * cos(a), sy_ + r * .62 * sin(a), z + .02), .018, .024, .03, segs=10)
            Br.ball((sx_ + r * .62 * cos(a), sy_ + r * .62 * sin(a), z + .045), (.017, .017, .017))
    for b in (Bv, Bw, Bg, Bp, Bi, Bl, Br, Bx):
        b.finish(Mtx)
    curves('P3 tea %s gilt lines' % tag, lines, .014, gold, True, Mtx)
    curves('P3 tea %s gilt inlay and rug scrolls' % tag, fine, .008, gold, False, Mtx)
    curves('P3 tea %s carved table feet' % tag, feet, .032, white, False, Mtx)
    for k in range(4):
        phi = k * pi / 2
        ch = bpy.data.objects.new('P3 tea %s GEN armchair %d' % (tag, k), lod); coll.objects.link(ch)
        ch.location = (cx + 1.05 * cos(phi), cy + 1.05 * sin(phi), cz)
        ch.rotation_euler = (0, 0, phi - pi / 2)
        chairs += 1

# ------------------------------------------------------------------ sofas and candelabra
coll = colls[C_FURN]


def sofa(tag, Mtx):
    Bv = Batch('P3 sofa %s velvet' % tag, velvet, smooth=True)
    Bw = Batch('P3 sofa %s carved frame' % tag, white)
    Bg = Batch('P3 sofa %s gilt' % tag, gold, smooth=True)
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
    curves('P3 sofa %s carved rails' % tag, frame, .045, white, False, Mtx)
    gl = [[(x, .22, top(x) - .03) for x in xs], [(x, -.365, .44) for x in (-.97, .97)]]
    legs = [[(sx * .85, sy * .28, .33), (sx * .92, sy * .34, .2), (sx * .87, sy * .3, .06), (sx * .9, sy * .33, .02)] for sx in (-1, 1) for sy in (-1, 1)]
    curves('P3 sofa %s gilt beads' % tag, gl, .014, gold, False, Mtx)
    curves('P3 sofa %s gilt cabriole legs' % tag, legs, .03, gold, False, Mtx)
    curves('P3 sofa %s gilt crest' % tag, scroll_splines(lambda dt, dz: (dt, .2, top(0) + .14 + dz), .13), .016, gold, False, Mtx)
    for sx in (-1, 1):
        Bg.ball((sx * .93, -.3, .45), (.03, .03, .03))
    for b in (Bv, Bw, Bg):
        b.finish(Mtx)


def candelabrum(tag, Mtx):
    Bg = Batch('P3 candelabrum %s gilt' % tag, gold, smooth=True)
    Bc = Batch('P3 candelabrum %s candles' % tag, white, smooth=True)
    Bf = Batch('P3 candelabrum %s flames' % tag, bulb, smooth=True)
    Bx = Batch('P3 candelabrum %s crystals' % tag, glass, smooth=True)
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
        Bx.ball((ex, ey, 1.6), (.018, .018, .05))
    Bc.cone((0, 0, 1.72), .02, .02, .22, segs=10); Bf.ball((0, 0, 1.86), (.018, .018, .038))
    curves('P3 candelabrum %s iron stand' % tag, irons, .022, iron, False, Mtx)
    curves('P3 candelabrum %s gilt arms' % tag, arms, .014, gold, False, Mtx)
    for b in (Bg, Bc, Bf, Bx):
        b.finish(Mtx)


for s in (1, -1):
    for y in (-5.5, -33.5):
        tag = '%s%.1f' % ('R' if s > 0 else 'L', y)
        sofa(tag, place(s * (15.775 - .42), y, 0, -s * pi / 2))
        for dy in (-1.5, 1.5):
            candelabrum('%s%+.1f' % (tag, dy), place(s * 15.25, y + dy, 0))

# ------------------------------------------------------------------ sideboards with clock, ewers, trolley, telephone
def sideboard(tag, Mtx):
    Bw = Batch('P3 sideboard %s marble' % tag, white)
    Bws = Batch('P3 sideboard %s marble turned' % tag, white, smooth=True)
    Bb = Batch('P3 sideboard %s sapphire panels' % tag, blue)
    Bg = Batch('P3 sideboard %s gilt' % tag, gold)
    Bgs = Batch('P3 sideboard %s gilt turned' % tag, gold, smooth=True)
    Bp = Batch('P3 sideboard %s porcelain' % tag, porcelain, smooth=True)
    Bm = Batch('P3 sideboard %s mirror glass' % tag, mirror)
    Bx = Batch('P3 sideboard %s crystal' % tag, glass, smooth=True)
    Bi = Batch('P3 sideboard %s iron' % tag, iron)
    lines, fine = [], []
    # Body
    Bw.box((0, 0, .04), (3.1, .62, .08)); Bw.box((0, 0, .5), (3.0, .56, .84)); Bw.box((0, 0, .95), (3.2, .7, .06))
    lines += [[(-1.6, -.351, z), (1.6, -.351, z)] for z in (.92, .98)] + [[(-1.55, -.311, .082), (1.55, -.311, .082)]]
    for x in (-1, 0, 1):
        Bb.box((x, -.285, .5), (.8, .02, .5))
        for dx in (-.44, .44):
            Bg.box((x + dx, -.3, .5), (.03, .02, .61))
        for dz in (-.29, .29):
            Bg.box((x, -.3, .5 + dz), (.91, .02, .03))
    for x in (-1.5, -.5, .5, 1.5):
        Bw.box((x, -.3, .5), (.1, .04, .8)); Bg.box((x, -.31, .88), (.14, .05, .04))
    fine += scroll_splines(lambda dt, dz: (dt, -.311, .5 + dz), .17) + scroll_splines(lambda dt, dz: (dt, -.311, .5 - dz * .6), .09)
    # Oval mirror on the wall above
    bm = Bm.bm; cen = bm.verts.new((0, .3, 2.15))
    rim = [bm.verts.new((.55 * cos(2 * pi * i / 40), .3, 2.15 + .7 * sin(2 * pi * i / 40))) for i in range(40)]
    for i in range(40):
        bm.faces.new((cen, rim[i], rim[(i + 1) % 40]))
    Bm.n += 1
    curves('P3 sideboard %s mirror gilt frame' % tag, [[(.6 * cos(2 * pi * i / 48), .28, 2.15 + .75 * sin(2 * pi * i / 48)) for i in range(48)]], .05, gold, True, Mtx)
    curves('P3 sideboard %s mirror sapphire frame' % tag, [[(.7 * cos(2 * pi * i / 48), .29, 2.15 + .86 * sin(2 * pi * i / 48)) for i in range(48)]], .04, blue, True, Mtx)
    fine += scroll_splines(lambda dt, dz: (dt, .26, 3.02 + dz), .2) + scroll_splines(lambda dt, dz: (dt, .26, 1.3 - dz), .16)
    # Ewers on the top
    for x in (-1.0, 1.0):
        Bp.lathe([(0, 0), (.07, 0), (.08, .03), (.05, .08), (.1, .2), (.11, .3), (.07, .4), (.05, .48), (.08, .52), (0, .52)], (x, 0, .98), 20)
        lines.append(circle(x, 0, .98 + .3, .112, 20))
        fine += [[(x + .08, 0, 1.4), (x + .2, 0, 1.38), (x + .21, 0, 1.25), (x + .1, 0, 1.17)]]
        fine += [[(x - .06, 0, 1.46), (x - .16, 0, 1.52)]]
    # Floor-standing pedestal clock in front of the centre
    cxk, cyk = 0, -.66
    Bw.box((cxk, cyk, .05), (.42, .36, .1)); Bw.cone((cxk, cyk, .62), .27, .2, 1.04, segs=4, rz=pi / 4)
    Bw.box((cxk, cyk, 1.16), (.38, .32, .06)); Bw.box((cxk, cyk, 1.42), (.36, .24, .46))
    Bws.ball((cxk, cyk, 1.66), (.18, .12, .1)); Bgs.ball((cxk, cyk, 1.79), (.04, .04, .06))
    Bg.box((cxk, cyk - .145, .62), (.16, .02, .7))
    Bp.cone((cxk, cyk - .125, 1.44), .11, .11, .01, segs=32, rx=pi / 2)
    lines.append(circle(cxk, cyk - .135, 1.44, .12, 32, 'XZ'))
    fine += [[(cxk, cyk - .14, 1.44), (cxk + .06, cyk - .14, 1.48)], [(cxk, cyk - .14, 1.44), (cxk, cyk - .14, 1.53)]]
    fine += scroll_splines(lambda dt, dz: (cxk + dt, cyk - .14, 1.25 + dz), .09)
    # Serving trolley
    tx0, ty0 = -1.2, -.95
    rails = [[(tx0 + x, ty0 + y, z) for x, y in ((-.5, -.22), (.5, -.22), (.5, .22), (-.5, .22), (-.5, -.22))] for z in (.78, .38)]
    rails += [[(tx0 + x, ty0 + y, .3), (tx0 + x, ty0 + y, .8)] for x in (-.5, .5) for y in (-.22, .22)]
    rails += [[(tx0 + .5, ty0 - .2, .8), (tx0 + .68, ty0 - .2, .95), (tx0 + .68, ty0 + .2, .95), (tx0 + .5, ty0 + .2, .8)]]
    for z in (.78, .38):
        Bx.box((tx0, ty0, z), (.98, .42, .012))
    wheels = []
    for y in (-.27, .27):
        wheels.append(circle(tx0 - .42, ty0 + y, .28, .28, 32, 'XZ'))
        for k in range(12):
            a = 2 * pi * k / 12
            wheels.append([(tx0 - .42, ty0 + y, .28), (tx0 - .42 + .27 * cos(a), ty0 + y, .28 + .27 * sin(a))])
        Bgs.ball((tx0 - .42, ty0 + y, .28), (.035, .02, .035))
        Bi.box((tx0 + .45, ty0 + y, .07), (.02, .02, .1))
        wheels.append(circle(tx0 + .45, ty0 + y, .07, .07, 16, 'XZ'))
    for k in range(3):
        Bp.cone((tx0 - .25 + k * .25, ty0, .795), .09, .09, .008, segs=20)
    Bx.lathe([(0, 0), (.06, 0), (.08, .1), (.05, .2), (.025, .28), (.035, .3), (0, .3)], (tx0 + .2, ty0, .39), 16)
    curves('P3 sideboard %s trolley gilt frame' % tag, rails, .014, gold, False, Mtx)
    curves('P3 sideboard %s trolley sapphire wheels' % tag, wheels, .012, blue, False, Mtx)
    # Telephone on a marble pedestal
    px, py = 1.3, -.75
    Bws.lathe([(0, 0), (.16, 0), (.16, .06), (.07, .14), (.05, .4), (.1, .6), (.05, .8), (.06, .92), (0, .92)], (px, py, 0), 20)
    Bgs.cone((px, py, .93), .17, .17, .02, segs=24)
    Bg.box((px, py, .98), (.14, .12, .07))
    Bp.cone((px, py - .062, .99), .035, .035, .006, segs=16, rx=pi / 2)
    fine += [[(px - .09, py, 1.06), (px - .05, py, 1.11), (px + .05, py, 1.11), (px + .09, py, 1.06)],
             [(px + .07, py + .05, .96), (px + .15, py + .12, .9), (px + .12, py + .2, .93)]]
    for b in (Bw, Bws, Bb, Bg, Bgs, Bp, Bm, Bx, Bi):
        b.finish(Mtx)
    curves('P3 sideboard %s gilt lines' % tag, lines, .014, gold, True, Mtx)
    curves('P3 sideboard %s gilt ornaments' % tag, fine, .014, gold, False, Mtx)


for s in (1, -1):
    sideboard('R' if s > 0 else 'L', place(s * (15.775 - .36), 4.5, 0, -s * pi / 2))

# ------------------------------------------------------------------ dome crystal chandeliers
coll = colls[C_CHAN]


def chandelier(tag, cy):
    Mtx = place(0, cy, 0)
    Bg = Batch('P3 chandelier %s gilt cast' % tag, gold, smooth=True)
    Bc = Batch('P3 chandelier %s candles' % tag, white, smooth=True)
    Bf = Batch('P3 chandelier %s flames' % tag, bulb, smooth=True)
    Bx = Batch('P3 chandelier %s crystals' % tag, glass, smooth=True)
    Bg.lathe([(0, 7.35), (.06, 7.4), (.14, 7.6), (.2, 7.85), (.1, 8.05), (.16, 8.25), (.24, 8.5), (.12, 8.8), (.1, 9.1), (.18, 9.35),
              (.09, 9.6), (.08, 9.9), (.13, 10.1), (.07, 10.4), (.05, 10.9), (.1, 11.05), (.05, 11.2), (0, 11.25)], (0, 0, 0), 24)
    arms, curls, swags, rings = [], [], [], []
    for tz, R, n in ((8.25, 1.95, 16), (9.1, 1.35, 12), (9.9, .8, 8)):
        rings.append(circle(0, 0, tz + .02, .42 if R > 1 else .3, 32))
        tips = []
        for k in range(n):
            a = 2 * pi * (k + (.5 if n == 12 else 0)) / n; c_, s_ = cos(a), sin(a)
            arms.append([((.16 + (R - .16) * t) * c_, (.16 + (R - .16) * t) * s_, tz + .42 * sin(pi * t) * (1 - .35 * t) - .1 * t) for t in [i / 16 for i in range(17)]])
            mr = .5 * R
            curls.append([((mr + .12 * cos(u)) * c_, (mr + .12 * cos(u)) * s_, tz - .02 + .12 * sin(u) * (1 - u / 9)) for u in [pi + j * .45 for j in range(14)]])
            ex, ey, ez = R * c_, R * s_, tz - .1
            tips.append((ex, ey, ez))
            Bg.cone((ex, ey, ez + .03), .03, .085, .03, segs=12)
            Bc.cone((ex, ey, ez + .15), .024, .024, .2, segs=10)
            Bf.ball((ex, ey, ez + .29), (.022, .022, .045))
            Bx.ball((ex, ey, ez - .16), (.026, .026, .075))
            Bx.ball((ex, ey, ez - .3), (.018, .018, .045))
        for k in range(n):
            p, q = tips[k], tips[(k + 1) % n]
            swags.append([(p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t, p[2] - .05 - (.34 if R > 1.5 else .24) * sin(pi * t)) for t in [i / 12 for i in range(13)]])
    for k in range(16):
        a = 2 * pi * k / 16
        swags.append([(.55 * cos(a) * (1 - t) + 1.95 * cos(a) * t, .55 * sin(a) * (1 - t) + 1.95 * sin(a) * t, 10.95 - 2.8 * t + .35 * sin(pi * t) * -1) for t in [i / 14 for i in range(15)]])
    rings.append(circle(0, 0, 11.0, .55, 32))
    links = []
    z = 11.28
    i = 0
    while z < 15.0:
        links.append(circle(0, 0, z, .045, 12, 'XZ' if i % 2 == 0 else 'YZ'))
        z += .075; i += 1
    Bx.ball((0, 0, 7.12), (.07, .07, .19))
    curves('P3 chandelier %s gilt scroll arms' % tag, arms, .035, gold, False, Mtx)
    curves('P3 chandelier %s gilt curls' % tag, curls, .022, gold, False, Mtx)
    curves('P3 chandelier %s gilt rings' % tag, rings, .03, gold, True, Mtx)
    curves('P3 chandelier %s crystal strands' % tag, swags, .011, glass, False, Mtx)
    curves('P3 chandelier %s gilt chain' % tag, links, .012, gold, True, Mtx)
    for b in (Bg, Bc, Bf, Bx):
        b.finish(Mtx)


chandelier('rear dome', 0.0)
chandelier('front dome', -28.0)

for lc in bpy.context.view_layer.layer_collection.children:
    if lc.name == C_GEN:
        lc.exclude = True

result = {k: len(c.objects) for k, c in colls.items()}
result['chairs'] = chairs
result['parked'] = len(parked)
result['chair_lod_polys'] = len(lod.polygons)
result['scene_objects'] = len(sc.objects)
print('P3_P4_RESULT', result)
