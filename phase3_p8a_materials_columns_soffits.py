"""P8a 세부 구현: 대리석 결 재질 + 코린트식 기둥 + 갤러리·계단참·발코니 아랫면 격자 + 홀 바닥 테두리.

- 재질: Ivory marble / Blue grey marble / Sapphire stone 에 월드 좌표 대리석 결, 금장 거칠기 변화, 바닥 광택
- 기둥 40개(갤러리 24, 뒤벽 8, 정문 8): 옛 받침·주두 조각을 코린트식 주두(아칸서스 2단·소용돌이 4·오목 판석)와
  아틱식 초석(사각 대좌·토러스·스코티아)으로 교체. 모양은 공유 메시 하나를 기둥마다 연결 복제한다.
- 갤러리·계단참·정문 발코니 아랫면: 청색 격자판 + 금장 틀 + 로제트
- 홀 바닥 둘레: 청회색 대리석 띠 + 금장 선
교체된 원본은 30x로 옮긴다. 재실행하면 46 컬렉션과 P8 공유 메시·재질 노드를 다시 만든다.
"""
import bpy, bmesh, math, re
from math import sin, cos, pi
from mathutils import Matrix

sc = bpy.context.scene
M = bpy.data.materials
white = M['Ivory marble']; gold = M['Antique gilded bronze']; blue = M['Sapphire stone']; tile = M['Blue grey marble']
HIDDEN = '30x | P3 replaced originals (hidden)'
C = '46 | P8 - Columns, soffits and floor border'


def ensure_coll(name, clear=True):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name); sc.collection.children.link(c)
    if clear:
        for o in list(c.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    return c


hidden = ensure_coll(HIDDEN, clear=False)
coll = ensure_coll(C)
parked = []


def park(o):
    if hidden in o.users_collection:
        return
    o['p3_original_collections'] = ','.join(c.name for c in o.users_collection)
    for c in list(o.users_collection):
        c.objects.unlink(o)
    hidden.objects.link(o); parked.append(o.name)


# ================================================================== materials
def strip_p8(nt):
    for n in [n for n in nt.nodes if n.name.startswith('P8 ')]:
        nt.nodes.remove(n)


def marble_veins(m, vein_rgb, strength, scale, rough):
    nt = m.node_tree; p = nt.nodes['Principled BSDF']
    strip_p8(nt)
    base = tuple(m.get('p8_base_color', list(p.inputs['Base Color'].default_value)))
    m['p8_base_color'] = list(base)
    geo = nt.nodes.new('ShaderNodeNewGeometry'); geo.name = 'P8 geometry'
    warp = nt.nodes.new('ShaderNodeTexNoise'); warp.name = 'P8 marble warp'
    warp.inputs['Scale'].default_value = scale * .6; warp.inputs['Detail'].default_value = 6.0
    nt.links.new(geo.outputs['Position'], warp.inputs['Vector'])
    add = nt.nodes.new('ShaderNodeVectorMath'); add.name = 'P8 marble offset'; add.operation = 'ADD'
    nt.links.new(geo.outputs['Position'], add.inputs[0]); nt.links.new(warp.outputs['Color'], add.inputs[1])
    wave = nt.nodes.new('ShaderNodeTexWave'); wave.name = 'P8 marble wave'
    wave.wave_type = 'BANDS'; wave.bands_direction = 'DIAGONAL'
    wave.inputs['Scale'].default_value = scale; wave.inputs['Distortion'].default_value = 9.0
    wave.inputs['Detail'].default_value = 8.0; wave.inputs['Detail Scale'].default_value = 1.4
    nt.links.new(add.outputs[0], wave.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.name = 'P8 vein ramp'
    el = ramp.color_ramp.elements
    el[0].position = 0.0; el[0].color = (1, 1, 1, 1)
    el[1].position = .045; el[1].color = (0, 0, 0, 1)   # thin hairline veins, not bold bands
    nt.links.new(wave.outputs['Fac'], ramp.inputs['Fac'])
    mul = nt.nodes.new('ShaderNodeMath'); mul.name = 'P8 vein strength'; mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = strength
    nt.links.new(ramp.outputs['Color'], mul.inputs[0])
    mix = nt.nodes.new('ShaderNodeMix'); mix.name = 'P8 vein mix'; mix.data_type = 'RGBA'
    si = {s.identifier: s for s in mix.inputs}; so = {s.identifier: s for s in mix.outputs}
    si['A_Color'].default_value = base; si['B_Color'].default_value = (*vein_rgb, 1)
    nt.links.new(mul.outputs[0], si['Factor_Float'])
    nt.links.new(so['Result_Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = rough


marble_veins(white, (.6, .64, .72), .3, .9, .2)
marble_veins(tile, (.78, .84, .9), .25, .9, .1)
marble_veins(blue, (.34, .5, .74), .3, 1.3, .22)

gnt = gold.node_tree; gp = gnt.nodes['Principled BSDF']
strip_p8(gnt)
ggeo = gnt.nodes.new('ShaderNodeNewGeometry'); ggeo.name = 'P8 geometry'
gno = gnt.nodes.new('ShaderNodeTexNoise'); gno.name = 'P8 gold wear noise'; gno.inputs['Scale'].default_value = 16.0; gno.inputs['Detail'].default_value = 4.0
gnt.links.new(ggeo.outputs['Position'], gno.inputs['Vector'])
gmr = gnt.nodes.new('ShaderNodeMapRange'); gmr.name = 'P8 gold roughness range'
gmr.inputs['To Min'].default_value = .15; gmr.inputs['To Max'].default_value = .34
gnt.links.new(gno.outputs['Fac'], gmr.inputs['Value']); gnt.links.new(gmr.outputs['Result'], gp.inputs['Roughness'])

# ================================================================== helpers
GAL_Y = (-41, -36, -31, -26, -21, -16, -13, -8, -3, 2, 7, 12)
COLS = [(s * 11.8, y) for s in (1, -1) for y in GAL_Y] + \
       [(x, 13.35) for x in (3.6, -3.6, 7.8, -7.8, 11.8, -11.8, 15.5, -15.5)] + \
       [(x, -41.2) for x in (3.4, -3.4, 7.6, -7.6, 11.4, -11.4, 15.2, -15.2)]


def at_column(o):
    return any(abs(o.location.x - cx) < .05 and abs(o.location.y - cy) < .05 for cx, cy in COLS)


for o in list(sc.objects):
    if o.type != 'MESH':
        continue
    b = re.sub(r'\.\d+$', '', re.sub(r'^Forehall \| ', '', o.name))
    if b in ('Square pedestal', 'Column base and capital') and at_column(o):
        park(o)
    elif b == 'Gilded collar' and o.location.z > 10.5 and at_column(o):
        park(o)


def lathe_into(bm, profile, segs=32, cent=(0, 0, 0)):
    before = set(bm.verts)
    vs = [bm.verts.new((cent[0] + r, cent[1], cent[2] + z)) for r, z in profile]
    es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + es, angle=2 * pi, steps=segs, axis=(0, 0, 1), cent=cent)
    bmesh.ops.remove_doubles(bm, verts=[v for v in bm.verts if v not in before], dist=1e-5)


def fresh_mesh(name, bm, mat, smooth):
    old = bpy.data.meshes.get(name)
    if old is not None and old.users == 0:
        bpy.data.meshes.remove(old)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(mat)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return me


def curves_data(name, splines, r, mat, closed=False):
    old = bpy.data.curves.get(name)
    if old is not None and old.users == 0:
        bpy.data.curves.remove(old)
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 2; cu.resolution_u = 1; cu.use_fill_caps = True
    for pts in splines:
        sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
        for v, p in zip(sp.points, pts):
            v.co = (*p, 1)
        sp.use_cyclic_u = closed
    cu.materials.append(mat)
    return cu


# ================================================================== Corinthian capital and Attic base (shared data)
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation((0, 0, .1)) @ Matrix.Diagonal((.95, .95, .2, 1)))
lathe_into(bm, [(.47, .2), (.5, .23), (.5, .29), (.46, .33), (.4, .345), (.38, .38), (.39, .42), (.43, .455), (.43, .49), (.39, .515), (.35, .53), (.34, .6)], 40)
me_base_w = fresh_mesh('P8 column attic base marble', bm, white, True)
bm = bmesh.new()
lathe_into(bm, [(.345, .545), (.37, .56), (.37, .575), (.345, .59)], 40)
lathe_into(bm, [(.475, .195), (.505, .205), (.505, .215), (.475, .225)], 40)
me_base_g = fresh_mesh('P8 column attic base gilt fillets', bm, gold, True)

bm = bmesh.new()
lathe_into(bm, [(.3, 0.0), (.315, .08), (.345, .2), (.39, .32), (.43, .4)], 40)
ab = []
corners = [(.5, -.5), (.5, .5), (-.5, .5), (-.5, -.5)]
for i in range(4):
    ax, ay = corners[i]; bx, by = corners[(i + 1) % 4]
    mx, my = (ax + bx) / 2, (ay + by) / 2; ml = math.hypot(mx, my)
    for j in range(10):
        t = j / 10
        ab.append((ax + (bx - ax) * t - mx / ml * .08 * sin(pi * t), ay + (by - ay) * t - my / ml * .08 * sin(pi * t)))
bot = [bm.verts.new((x, y, .4)) for x, y in ab]; top = [bm.verts.new((x, y, .5)) for x, y in ab]
bm.faces.new(top); bm.faces.new(bot[::-1])
for i in range(len(ab)):
    j = (i + 1) % len(ab)
    bm.faces.new((bot[i], bot[j], top[j], top[i]))
me_cap_w = fresh_mesh('P8 column corinthian bell and abacus marble', bm, white, False)

bm = bmesh.new()
lathe_into(bm, [(.3, -.01), (.33, .005), (.33, .035), (.3, .05)], 40)


def leaf(bm, a, r0, z0, h, w, lean):
    U, V = 6, 9
    grid = []
    for iv in range(V + 1):
        v = iv / V
        row = []
        for iu in range(U + 1):
            u = -1 + 2 * iu / U
            r = r0 + .04 * sin(pi * v * .8) + .03 * (1 - u * u) * v
            z = z0 + h * v
            if v > .75:
                k = (v - .75) / .25
                r += lean * k * k; z -= .035 * k * k
            # tapered, lobed blade that closes to a point at the curled tip
            tt = u * (w / 2) * (1 - v) ** .6 * (1 + .18 * sin(4 * pi * v))
            row.append(bm.verts.new((r * cos(a) - tt * sin(a), r * sin(a) + tt * cos(a), z)))
        grid.append(row)
    for iv in range(V):
        for iu in range(U):
            bm.faces.new((grid[iv][iu], grid[iv][iu + 1], grid[iv + 1][iu + 1], grid[iv + 1][iu]))


for k in range(8):
    leaf(bm, 2 * pi * k / 8, .305, .04, .2, .17, .05)
    leaf(bm, 2 * pi * (k + .5) / 8, .33, .13, .26, .16, .065)
for k in range(8):
    a = 2 * pi * (k + .5) / 8
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=1, matrix=Matrix.Translation((.41 * cos(a), .41 * sin(a), .34)) @ Matrix.Diagonal((.03, .03, .03, 1)))
bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=1, matrix=Matrix.Translation((0, -.5, .45)) @ Matrix.Diagonal((.055, .02, .045, 1)))
bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=1, matrix=Matrix.Translation((0, .5, .45)) @ Matrix.Diagonal((.055, .02, .045, 1)))
bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=1, matrix=Matrix.Translation((.5, 0, .45)) @ Matrix.Diagonal((.02, .055, .045, 1)))
bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=1, matrix=Matrix.Translation((-.5, 0, .45)) @ Matrix.Diagonal((.02, .055, .045, 1)))
me_cap_g = fresh_mesh('P8 column corinthian acanthus gilt', bm, gold, True)

vol = []
for k in range(4):
    a = pi / 4 + k * pi / 2; dx, dy = cos(a), sin(a)
    cx_, cz_ = .47, .37
    vol.append([((cx_ + .085 * (1 - .8 * t) * cos(pi + 1.3 * 2 * pi * t)) * dx, (cx_ + .085 * (1 - .8 * t) * cos(pi + 1.3 * 2 * pi * t)) * dy, cz_ + .085 * (1 - .8 * t) * sin(pi + 1.3 * 2 * pi * t)) for t in [i / 30 for i in range(31)]])
    vol.append([((.36 + .03 * t) * dx, (.36 + .03 * t) * dy, .22 + .15 * t) for t in [i / 6 for i in range(7)]])
cu_vol = curves_data('P8 column corinthian volutes', vol, .018, gold)
cu_abacus_line = curves_data('P8 column abacus gilt edge', [[(x, y, .5) for x, y in ab]], .012, gold, True)

placed = 0
for cx, cy in COLS:
    tag = '(%.1f, %.1f)' % (cx, cy)
    for nm, data, z in (('P8 column base marble', me_base_w, 0.0), ('P8 column base gilt', me_base_g, 0.0),
                        ('P8 column capital marble', me_cap_w, 10.85), ('P8 column capital acanthus', me_cap_g, 10.85),
                        ('P8 column capital volutes', cu_vol, 10.85), ('P8 column capital abacus edge', cu_abacus_line, 10.85)):
        o = bpy.data.objects.new('%s %s' % (nm, tag), data); coll.objects.link(o)
        o.location = (cx, cy, z)
    placed += 1


# ================================================================== soffits and floor border
class Batch:
    def __init__(self, name, mat, smooth=False):
        self.name, self.mat, self.smooth = name, mat, smooth
        self.bm = bmesh.new()

    def box(self, c, d):
        bmesh.ops.create_cube(self.bm, size=1, matrix=Matrix.Translation(c) @ Matrix.Diagonal((*d, 1)))

    def ball(self, c, rad):
        bmesh.ops.create_uvsphere(self.bm, u_segments=14, v_segments=8, radius=1, matrix=Matrix.Translation(c) @ Matrix.Diagonal((*rad, 1)))

    def finish(self):
        me = fresh_mesh(self.name, self.bm, self.mat, self.smooth)
        o = bpy.data.objects.new(self.name, me); coll.objects.link(o)
        return o


Sb = Batch('P8 soffit sapphire coffers', blue)
Sg = Batch('P8 soffit gilt frames', gold)
Sr = Batch('P8 soffit gilt rosettes', gold, True)
Z_S = 4.787


def coffer(cx, cy, w, d):
    Sb.box((cx, cy, Z_S), (w, d, .012))
    for dx in (-w / 2, w / 2):
        Sg.box((cx + dx, cy, Z_S - .012), (.05, d + .05, .02))
        Sg.box((cx + dx * .86, cy, Z_S - .01), (.025, d * .86, .015))
    for dy in (-d / 2, d / 2):
        Sg.box((cx, cy + dy, Z_S - .012), (w + .05, .05, .02))
        Sg.box((cx, cy + dy * .86, Z_S - .01), (w * .86, .025, .015))
    Sr.ball((cx, cy, Z_S - .03), (.14, .14, .045))
    for dx in (-.3, .3):
        for dy in (-.3, .3):
            Sr.ball((cx + dx * w / 2 * 1.4, cy + dy * d / 2 * 1.4, Z_S - .02), (.045, .045, .025))


for s in (1, -1):
    for a, b in zip(GAL_Y, GAL_Y[1:]):
        coffer(s * 13.9, (a + b) / 2, 3.1, (b - a) - .8)
    for x in (5.6, 9.3):
        coffer(s * x, 11.2, 3.1, 4.6)
    for x in (5.5, 9.4):
        coffer(s * x, -40.25, 3.3, 2.5)
Sb.finish(); Sg.finish(); Sr.finish()

Fb = Batch('P8 hall floor border blue grey marble', tile)
Fg = Batch('P8 hall floor border gilt inlay', gold)
for s in (1, -1):
    Fb.box((s * 15.4875, -13.9875, .003), (.575, 55.525, .006))
    for off in (15.2, 15.14):
        Fg.box((s * off, -13.9875, .0065), (.02, 55.525 - 1.2, .004))
for y_mid, y_off in ((13.4875, (13.2, 13.14)), (-41.4625, (-41.2, -41.14))):
    Fb.box((0, y_mid, .003), (30.4, .575, .006))
    for yy in y_off:
        Fg.box((0, yy, .0065), (30.4 - 1.2 if abs(yy) != 13.2 and abs(yy) != 41.2 else 30.4, .02, .004))
Fb.finish(); Fg.finish()

result = {'collection_objects': len(coll.objects), 'columns': placed, 'parked': len(parked),
          'materials_veined': [white.name, tile.name, blue.name], 'scene_objects': len(sc.objects)}
print('P8A_RESULT', result)
