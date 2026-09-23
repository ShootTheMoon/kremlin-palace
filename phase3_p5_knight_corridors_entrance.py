"""3차 P5: 기사 복도(좌우 윙) + 정문 벽 마감 (레퍼런스 재구축).

복도 (x 16~30, y 8.15~13.85, 높이 6m, 좌우 대칭):
- 양쪽 긴 벽 u=19,22,25,28 에 깊은 기둥벽(청색 대리석 패널·금장 장식·랜턴), 그 앞에 생성 기사상(경량 메시 연결 복제)
- 바깥벽 u=17.5~26.5 아치 창(부채꼴 창살·금장 스크롤 창살·대리석 테두리), 안쪽 벽 같은 자리에 청색 막힌 아치
- 아치 아래 청색 벤치, 소형 크리스털 샹들리에 2(u=20, 26), 흰 대리석 타일 바닥, 천장 청색 격자판
- 끝문 흰색으로 전환 + 양옆 청색 기둥
정문 벽 (y=-41.75): 2단 패널, 문짝 흰색 전환, 청색 아치 테두리, 토피어리 화분·스탠드 촛대, 경비상을 생성 기사상으로 교체.
교체된 원본은 30x로 옮긴다. 재실행 가능.
"""
import bpy, bmesh, math
from math import sin, cos, pi
from mathutils import Matrix, Vector

sc = bpy.context.scene
M = bpy.data.materials
white = M['Ivory marble']; gold = M['Antique gilded bronze']; blue = M['Sapphire stone']
velvet = M['Royal blue velvet']; iron = M['Wrought iron']; bulb = M['Candle light']; glass = M['Pale azure glazing']


def mat_get(name, rgb, rough=.5, metal=0.0):
    m = M.get(name)
    if m is None:
        m = M.new(name); m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*rgb, 1); p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*rgb, 1)
    return m


pale = mat_get('P3 pale marble tile', (.76, .79, .84), .3)
daylight_glass = mat_get('P3 window daylight glass', (.6, .78, .95), .1)
_dg = daylight_glass.node_tree.nodes.get('Principled BSDF')
_dg.inputs['Emission Color'].default_value = (.62, .8, 1, 1); _dg.inputs['Emission Strength'].default_value = 1.2
green = mat_get('P3 topiary green', (.1, .33, .12), .85)

HIDDEN = '30x | P3 replaced originals (hidden)'
C_COR = '41 | P3 - Knight corridors'
C_ENT = '42 | P3 - Entrance wall and guards'
C_GEN = '34 | P3 - Generated props (source)'
C_LGT = '21 | LIGHTING - Wing rooms'


def ensure_coll(name, clear=True):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name); sc.collection.children.link(c)
    if clear:
        for o in list(c.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    return c


hidden = ensure_coll(HIDDEN, clear=False)
colls = {k: ensure_coll(k) for k in (C_COR, C_ENT)}
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


# ------------------------------------------------------------------ park
c20 = bpy.data.collections.get('20 | DETAIL - Wing room walls and furniture')
if c20:
    for o in list(c20.objects):
        park(o)
CHANDELIER_PARTS = ('Chandelier stem', 'Chandelier heart', 'Chandelier tier', 'Curled candle arm', 'Candle cup', 'Ivory candle', 'Candle flame', 'Sapphire crystal drop', 'Crystal swag')
c08 = bpy.data.collections.get('08 | Lateral ceremonial wings')
if c08:
    for o in list(c08.objects):
        if o.type not in {'MESH', 'CURVE'}:
            continue
        n = o.name
        cx, cy_, cz = centre(o)
        if n.startswith(('Wing azure window', 'Wing window gilding', 'Wing window mullion', 'Wing window transom', 'Wing sapphire runner')):
            park(o)
        elif n.startswith(('Square pedestal', 'Column base and capital', 'Sapphire column shaft', 'Gilded collar')) and abs(cx) > 16.5:
            park(o)
        elif n.startswith(CHANDELIER_PARTS) and abs(cx) > 16:
            park(o)
c19 = bpy.data.collections.get('19 | DETAIL - Wing room ceilings')
c15 = bpy.data.collections.get('15 | COMPLETE - Monumental entrance facade')
if c15:
    for o in list(c15.objects):
        n = o.name
        if o.parent is None and n.startswith(('Entrance lower moulding', 'Entrance upper moulding', 'Entrance window glazing', 'Window rectangular gilding',
                                              'Window arch crest', 'Window vertical bars', 'Window transom', 'Sapphire curtain pleat', 'Gold curtain tie',
                                              'Entrance sconce', 'Gilt acanthus scroll')):
            park(o)
c16 = bpy.data.collections.get('16 | COMPLETE - Imperial standards and guards')
if c16:
    for o in list(c16.objects):
        if o.name.startswith(('Guard statue base', 'Armour', 'Helmet golden visor', 'Heraldic shield', 'Guard spear')):
            park(o)


# ------------------------------------------------------------------ helpers
class Batch:
    def __init__(self, name, mat, smooth=False):
        self.name, self.mat, self.smooth = name, mat, smooth
        self.bm = bmesh.new(); self.n = 0

    @staticmethod
    def _m(c, rz=0.0, d=(1, 1, 1), rx=0.0):
        return Matrix.Translation(c) @ Matrix.Rotation(rz, 4, 'Z') @ Matrix.Rotation(rx, 4, 'X') @ Matrix.Diagonal((*d, 1))

    def box(self, c, d, rz=0.0):
        bmesh.ops.create_cube(self.bm, size=1, matrix=self._m(c, rz, d)); self.n += 1

    def cone(self, c, r1, r2, h, segs=16):
        bmesh.ops.create_cone(self.bm, cap_ends=True, segments=segs, radius1=r1, radius2=r2, depth=h, matrix=self._m(c)); self.n += 1

    def ball(self, c, rad, segs=12):
        bmesh.ops.create_uvsphere(self.bm, u_segments=segs, v_segments=8, radius=1, matrix=self._m(c, 0.0, rad)); self.n += 1

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


def spiral_xz(cx, y, cz, r, turns, start, direction, n=32):
    return [(cx + r * (1 - .8 * t) * cos(start + direction * turns * 2 * pi * t), y, cz + r * (1 - .8 * t) * sin(start + direction * turns * 2 * pi * t)) for t in [i / (n - 1) for i in range(n)]]


def circle(cx, cy, cz, r, n=24, plane='XY'):
    if plane == 'XY':
        return [(cx + r * cos(2 * pi * i / n), cy + r * sin(2 * pi * i / n), cz) for i in range(n)]
    return [(cx + r * cos(2 * pi * i / n), cy, cz + r * sin(2 * pi * i / n)) for i in range(n)]


def place(x, y, z=0.0, rz=0.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(rz, 4, 'Z')


def arch_outline(w, z1, z2, off=0.0, n=24):
    h = w / 2 + off
    pts = [(-h, z1 - off), (-h, z2)]
    pts += [(h * cos(pi - pi * i / n), z2 + h * sin(pi - pi * i / n)) for i in range(1, n)]
    pts += [(h, z2), (h, z1 - off)]
    return pts


def generated_lod(src_name, lod_name, ratio):
    gen = bpy.data.collections[C_GEN]
    lod = bpy.data.meshes.get(lod_name)
    if lod is not None:
        return lod
    for lc in bpy.context.view_layer.layer_collection.children:
        if lc.name == C_GEN:
            lc.exclude = False
    src = bpy.data.objects[src_name]
    tmp = src.copy(); tmp.data = src.data.copy(); gen.objects.link(tmp)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    tmp.select_set(True); bpy.context.view_layer.objects.active = tmp
    mod = tmp.modifiers.new('LOD decimate', 'DECIMATE'); mod.ratio = ratio
    with bpy.context.temp_override(object=tmp, active_object=tmp, selected_objects=[tmp], selected_editable_objects=[tmp]):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    lod = tmp.data; lod.name = lod_name; lod.use_fake_user = True
    bpy.data.objects.remove(tmp)
    for lc in bpy.context.view_layer.layer_collection.children:
        if lc.name == C_GEN:
            lc.exclude = True
    return lod


knight_lod = generated_lod('GEN_knight_armor_source', 'GEN_knight_armor_LOD', .4)
knights = 0


def knight(name, x, y, rz):
    global knights
    o = bpy.data.objects.new(name, knight_lod); coll.objects.link(o)
    o.location = (x, y, 0); o.rotation_euler = (0, 0, rz)
    knights += 1
    return o


def lantern_parts(Bgs, Bg, Bl, lx, ly, z):
    Bgs.cone((lx, ly, z + .23), .12, .03, .12)
    Bgs.ball((lx, ly, z + .31), (.03, .03, .05))
    Bgs.cone((lx, ly, z - .16), .025, .11, .1)
    Bgs.ball((lx, ly, z - .27), (.03, .03, .06))
    for k in range(6):
        a = k * pi / 3
        Bg.box((lx + .1 * cos(a), ly + .1 * sin(a), z + .03), (.016, .016, .32))
    Bl.cone((lx, ly, z + .03), .075, .075, .26)


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


# ================================================================== knight corridors
coll = colls[C_COR]
PIERS = (19.0, 22.0, 25.0, 28.0)
ARCHES = (17.5, 20.5, 23.5, 26.5)
for s in (1, -1):
    side = 'R' if s > 0 else 'L'
    for wall, y_face, rz in (('outer', 13.85, 0.0), ('inner', 8.15, pi)):
        # Local frame per wall: x along the wall, wall face at local y=0, corridor toward local -Y.
        Wm = Matrix.Translation((0, y_face, 0)) @ Matrix.Rotation(rz, 4, 'Z')
        tag = '%s %s' % (side, wall)
        Bw = Batch('P3 corridor %s marble piers' % tag, white)
        Bb = Batch('P3 corridor %s sapphire panels' % tag, blue)
        Bg = Batch('P3 corridor %s gilt frames' % tag, gold)
        Bgs = Batch('P3 corridor %s gilt lantern metal' % tag, gold, smooth=True)
        Bl = Batch('P3 corridor %s lantern glow' % tag, bulb, smooth=True)
        Bgl = Batch('P3 corridor %s glazing' % tag, daylight_glass)
        Bv = Batch('P3 corridor %s bench velvet' % tag, velvet)
        orn, fine, rings, arms, grilles, legs, surrounds = [], [], [], [], [], [], []

        def lx(u):   # local x for a world u on this side/wall
            return (s * u) if rz == 0.0 else -(s * u)

        for u in PIERS:
            x = lx(u)
            Bw.box((x, -.25, 2.875), (1.1, .5, 5.75))
            Bw.box((x, -.31, .45), (1.26, .62, .9))
            Bw.box((x, -.33, 5.65), (1.3, .66, .22))
            Bb.box((x, -.625, .45), (.8, .02, .45))
            for dx in (-.43, .43):
                Bg.box((x + dx, -.635, .45), (.03, .02, .52))
            for dz in (-.24, .24):
                Bg.box((x, -.635, .45 + dz), (.89, .02, .03))
            for z in (5.53, 5.77, .92):
                fine.append([(x - .65, -.665, z), (x + .65, -.665, z)])
            Bb.box((x, -.51, 2.95), (.74, .02, 3.4))
            for dx, t in ((-.4, .05), (.4, .05)):
                Bg.box((x + dx, -.525, 2.95), (t, .02, 3.5))
            for dz in (-1.73, 1.73):
                Bg.box((x, -.525, 2.95 + dz), (.85, .02, .05))
            for dx in (-.3, .3):
                Bg.box((x + dx, -.53, 2.95), (.02, .02, 3.2))
            for cz, r, st, dr in ((3.78, .17, -pi / 2, 1), (2.62, .17, pi / 2, -1)):
                for sx_ in (-1, 1):
                    orn.append(spiral_xz(x + sx_ * .17, -.535, cz, r, 1.15, st, dr * sx_))
            for k in range(5):
                a = pi / 2 + (k - 2) * .55
                orn.append([(x + .12 * cos(a) + .07 * cos(t) * cos(a) - .03 * sin(t) * sin(a), -.535, 4.35 + .12 * sin(a) + .07 * cos(t) * sin(a) + .03 * sin(t) * cos(a)) for t in [q * 2 * pi / 16 for q in range(17)]])
            fine += scroll_splines(lambda dt, dz, x=x: (x + dt, -.535, 4.45 + dz), .16) + scroll_splines(lambda dt, dz, x=x: (x + dt, -.535, 1.45 - dz), .16)
            arms.append([(x, -.53, 3.0), (x, -.72, 3.3), (x, -.85, 3.36), (x, -.85, 3.28)])
            lantern_parts(Bgs, Bg, Bl, x, -.85, 3.05)
            ky = y_face + (-1.0 if rz == 0.0 else 1.0)
            knight('P3 corridor %s GEN knight %.0f' % (tag, u), s * u, ky, rz)

        for u in ARCHES:
            x = lx(u)
            w, z1, z2 = 1.6, 1.0, 3.6
            outline = arch_outline(w, z1, z2)
            if wall == 'outer':
                Bgl.prism_xz(outline, -.03, -.01)
                mull = [[(x + dx, -.05, z1), (x + dx, -.05, z2)] for dx in (-.27, .27)]
                mull += [[(x - w / 2, -.05, z), (x + w / 2, -.05, z)] for z in (1.65, 2.3, 2.95, z2)]
                mull += [[(x, -.05, z2), (x + .8 * cos(a), -.05, z2 + .8 * sin(a))] for a in (pi / 6, pi / 3, pi / 2, 2 * pi / 3, 5 * pi / 6)]
                mull.append([(x + .32 * cos(pi - pi * i / 16), -.05, z2 + .32 * sin(pi - pi * i / 16)) for i in range(17)])
                grilles += mull
            else:
                Bb.prism_xz(outline, -.05, -.01)
                grilles.append([(x + .45 * cos(pi - pi * i / 16), -.06, z2 + .45 * sin(pi - pi * i / 16)) for i in range(17)])
                grilles += [[(x, -.06, z2), (x + .78 * cos(a), -.06, z2 + .78 * sin(a))] for a in (pi / 4, pi / 2, 3 * pi / 4)]
            rings.append([(x + px, -.06, pz) for px, pz in arch_outline(w, z1, z2, 0.0)])
            surrounds.append([(x + px, -.09, pz) for px, pz in arch_outline(w, z1, z2, .14)])
            for sx_ in (-1, 1):
                grilles.append(spiral_xz(x + sx_ * .45, -.07, 1.5, .28, 1.1, -pi / 2, sx_))
                grilles.append(spiral_xz(x + sx_ * .45, -.07, 2.55, .22, 1.05, pi / 2, -sx_))
                grilles.append([(x + sx_ * .45, -.07, 1.78), (x + sx_ * .45, -.07, 2.33)])
            Bw.box((x, -.12, z2 + w / 2 + .2), (.24, .16, .32))
            Bw.box((x, -.1, .95), (2.0, .2, .1))
            fine += scroll_splines(lambda dt, dz, x=x: (x + dt, -.21, z2 + w / 2 + .45 + dz), .14)
            # bench under the arch
            Bv.box((x, -.36, .5), (1.3, .44, .12))
            Bw.box((x, -.36, .41), (1.36, .5, .08))
            for sx_ in (-1, 1):
                for sy_ in (-1, 1):
                    legs.append([(x + sx_ * .56, -.36 + sy_ * .18, .38), (x + sx_ * .64, -.36 + sy_ * .22, .25), (x + sx_ * .58, -.36 + sy_ * .2, .08), (x + sx_ * .62, -.36 + sy_ * .22, .02)])
        for b in (Bw, Bb, Bg, Bgs, Bl, Bgl, Bv):
            b.finish(Wm)
        curves('P3 corridor %s gilt ornaments' % tag, orn, .02, gold, False, Wm)
        curves('P3 corridor %s marble arch surround' % tag, surrounds, .09, white, False, Wm)
        curves('P3 corridor %s gilt fine lines' % tag, fine, .014, gold, False, Wm)
        curves('P3 corridor %s gilt arch frames' % tag, rings, .045, gold, False, Wm)
        curves('P3 corridor %s gilt grilles' % tag, grilles, .018, gold, False, Wm)
        curves('P3 corridor %s gilt lantern brackets' % tag, arms, .025, gold, False, Wm)
        curves('P3 corridor %s bench scroll legs' % tag, legs, .03, white, False, Wm)

    # Marble tile floor, ceiling sapphire coffers, mini chandeliers, end door columns.
    bm = bmesh.new()
    xs = [16.25 + 1.5 * i for i in range(10)] + [29.85]
    ys = [8.15 + 1.425 * i for i in range(5)]
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            f = bm.faces.new([bm.verts.new((s * x, y, .004)) for x, y in ((xs[i], ys[j]), (xs[i + 1], ys[j]), (xs[i + 1], ys[j + 1]), (xs[i], ys[j + 1]))])
            f.material_index = (i + j) % 2
    bm.normal_update()
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    me = bpy.data.meshes.new('P3 corridor %s marble tiles' % side); bm.to_mesh(me); bm.free()
    me.materials.append(white); me.materials.append(pale)
    o = bpy.data.objects.new(me.name, me); coll.objects.link(o)
    grout = [[(s * x, 8.15, .007), (s * x, 13.85, .007)] for x in xs] + [[(s * 16.25, y, .007), (s * 29.85, y, .007)] for y in ys]
    curves('P3 corridor %s gilt tile inlay' % side, grout, .008, gold)

    Bb = Batch('P3 corridor %s ceiling sapphire coffers' % side, blue)
    for u in (19.65, 26.35):
        Bb.box((s * u, 11, 5.992), (6.1, 2.9, .01))
    Bb.finish()

    Bg = Batch('P3 corridor %s chandelier gilt' % side, gold, smooth=True)
    Bc = Batch('P3 corridor %s chandelier candles' % side, white, smooth=True)
    Bf = Batch('P3 corridor %s chandelier flames' % side, bulb, smooth=True)
    Bx = Batch('P3 corridor %s chandelier crystals' % side, glass, smooth=True)
    carms, cswags = [], []
    for u in (20.0, 26.0):
        cx, cy = s * u, 11.0
        Bg.lathe([(0, 4.1), (.05, 4.15), (.1, 4.3), (.07, 4.5), (.12, 4.7), (.06, 4.95), (.09, 5.2), (.04, 5.5), (.06, 5.8), (.1, 5.94), (0, 5.96)], (cx, cy, 0), 20)
        for tz, R, n in ((4.55, .7, 10), (5.0, .42, 8)):
            tips = []
            for k in range(n):
                a = 2 * pi * k / n; c_, s_ = cos(a), sin(a)
                carms.append([(cx + (.08 + (R - .08) * t) * c_, cy + (.08 + (R - .08) * t) * s_, tz + .2 * sin(pi * t) - .06 * t) for t in [i / 10 for i in range(11)]])
                ex, ey, ez = cx + R * c_, cy + R * s_, tz - .06
                tips.append((ex, ey, ez))
                Bg.cone((ex, ey, ez + .02), .02, .05, .02, segs=10)
                Bc.cone((ex, ey, ez + .1), .015, .015, .13, segs=8)
                Bf.ball((ex, ey, ez + .19), (.014, .014, .03))
                Bx.ball((ex, ey, ez - .1), (.016, .016, .045))
            for k in range(n):
                p, q = tips[k], tips[(k + 1) % n]
                cswags.append([(p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t, p[2] - .03 - .16 * sin(pi * t)) for t in [i / 10 for i in range(11)]])
        Bx.ball((cx, cy, 3.98), (.05, .05, .12))
    for b in (Bg, Bc, Bf, Bx):
        b.finish()
    curves('P3 corridor %s chandelier arms' % side, carms, .018, gold)
    curves('P3 corridor %s chandelier crystal strands' % side, cswags, .007, glass)

    Bb = Batch('P3 corridor %s end door sapphire columns' % side, blue, smooth=True)
    Bw = Batch('P3 corridor %s end door column bases' % side, white, smooth=True)
    Bg = Batch('P3 corridor %s end door column collars' % side, gold, smooth=True)
    for y in (9.2, 12.8):
        x = s * 29.45
        Bw.box((x, y, .2), (.56, .56, .4)); Bw.cone((x, y, 4.85), .26, .3, .2, segs=24); Bw.box((x, y, 5.1), (.62, .62, .2))
        Bb.cone((x, y, 2.6), .2, .2, 4.3, segs=24)
        for z in (.55, 1.4, 4.0, 4.7):
            Bg.cone((x, y, z), .23, .23, .06, segs=24)
    for b in (Bb, Bw, Bg):
        b.finish()

# End-wall doors become white-and-gold.
recoloured = 0
for o in sc.objects:
    if o.name.startswith('Door leaf sapphire') and o.parent and 'Wing end' in (o.parent.parent.name if o.parent.parent else ''):
        o.material_slots[0].link = 'OBJECT'; o.material_slots[0].material = white
        recoloured += 1

# Move/add practical helper lights to the new lanterns.
lc = bpy.data.collections.get(C_LGT)
moved = 0
if lc:
    for o in list(lc.objects):
        if o.name.startswith('LGT_practical_wing_lantern_outer'):
            bpy.data.objects.remove(o, do_unlink=True)
    for o in lc.objects:
        if o.type == 'LIGHT' and o.name.startswith('LGT_practical_wing_sconce'):
            o.location = (o.location.x, 8.15 + .85, 3.05); moved += 1
    for s in (1, -1):
        for u in PIERS:
            d = bpy.data.lights.new('LGT_practical_wing_lantern_outer_%s_%.0f' % ('R' if s > 0 else 'L', u), 'POINT')
            d.energy = 60; d.color = (1, .78, .5); d.shadow_soft_size = .12
            o = bpy.data.objects.new(d.name, d); lc.objects.link(o)
            o.location = (s * u, 13.85 - .85, 3.05)
            o['purpose'] = 'Helper light matching the visible corridor lantern'

# ================================================================== entrance wall
coll = colls[C_ENT]
FACE = -41.75
Bw = Batch('P3 entrance wall marble panels', white)
Bg = Batch('P3 entrance wall gilt frames', gold)
Bgs = Batch('P3 entrance wall gilt rosettes', gold, smooth=True)
esc = []


def fpt(u, z, d):
    return (u, FACE + d, z)


def fbox(B, u, z, d, lu, h, dd):
    B.box(fpt(u, z, d), (lu, dd, h))


def fframe(B, u, z, d, w, h, t, dd):
    for du in (-w / 2, w / 2):
        fbox(B, u + du, z, d, t, h + t, dd)
    for dz in (-h / 2, h / 2):
        fbox(B, u, z + dz, d, w + t, t, dd)


for s in (1, -1):
    for zc, h in ((8.05, 4.7), (2.475, 3.85)):
        for u, w in ((5.5, 2.9), (9.5, 2.6), (13.3, 2.6)):
            fbox(Bw, s * u, zc, .02, w, h, .04)
            fframe(Bg, s * u, zc, .05, w, h, .07, .06)
            fframe(Bg, s * u, zc, .05, w - .36, h - .36, .035, .05)
            for zz, flip in ((zc + h / 2 - .5, 1), (zc - h / 2 + .5, -1)):
                esc += scroll_splines(lambda dt, dz, u=u, zz=zz, flip=flip, s=s: fpt(s * u + dt, zz + flip * dz, .085), .32)
                Bgs.ball(fpt(s * u, zz + flip * .08, .085), (.06, .06, .06))
for b in (Bw, Bg, Bgs):
    b.finish()
curves('P3 entrance wall gilt scrolls', esc, .018, gold)

# Door: white leaves inside a sapphire arch surround.
for o in sc.objects:
    if o.name.startswith('Royal double door leaf') and o.parent and o.parent.name.startswith('Entrance door hinge'):
        o.material_slots[0].link = 'OBJECT'; o.material_slots[0].material = white
door_arch = [(x, FACE + .2, z) for x, z in arch_outline(6.5, 0.0, 6.2, 0.0, 48)]
curves('P3 entrance door sapphire arch surround', [door_arch], .16, blue)
curves('P3 entrance door gilt arch lines', [[(x, FACE + .24, z) for x, z in arch_outline(6.5, 0.0, 6.2, off, 48)] for off in (-.2, .2)], .03, gold)

# Topiaries and candelabra flanking the door; generated knights replace the old guards.
Bu = Batch('P3 entrance topiary urns', blue, smooth=True)
Bug = Batch('P3 entrance topiary urn gilt', gold, smooth=True)
Btg = Batch('P3 entrance topiary foliage', green, smooth=True)
for sx in (-1, 1):
    x, y = sx * 4.4, -40.4
    Bu.lathe([(0, 0), (.3, 0), (.32, .08), (.22, .18), (.34, .5), (.38, .72), (.3, .78), (0, .78)], (x, y, 0), 24)
    Bug.cone((x, y, .76), .39, .39, .04, segs=24)
    Bug.cone((x, y, .09), .33, .33, .03, segs=24)
    Btg.lathe([(0, .78), (.36, .82), (.33, 1.2), (.25, 1.6), (.14, 1.95), (0, 2.1)], (x, y, 0), 20)
    Btg.ball((x, y, 2.18), (.1, .1, .12))
    candelabrum('entrance %s' % ('R' if sx > 0 else 'L'), place(sx * 5.5, -41.2, 0))
    knight('P3 entrance GEN knight %s' % ('R' if sx > 0 else 'L'), sx * 13.5, -36.0, -sx * pi / 2)
for b in (Bu, Bug, Btg):
    b.finish()

result = {k: len(c.objects) for k, c in colls.items()}
result.update({'knights': knights, 'knight_lod_polys': len(knight_lod.polygons), 'parked': len(parked),
               'end_door_leaves_white': recoloured, 'lantern_lights_moved': moved, 'scene_objects': len(sc.objects)})
print('P3_P5_RESULT', result)
