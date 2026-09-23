"""P7: 분수대 세부 구현 + 실제 물 효과 (phase3_p1 이후 실행).

- 물 덩어리: 수반·아래 볼·위 볼 안에 실제 깊이의 물(굴절 IOR 1.333, 레이트레이싱 굴절)
- 수면: 시간에 따라 흐르는 노이즈 물결 + 중심에서 퍼지는 동심원 파문 + 물줄기·물막이 떨어지는 반지름에 거품 링
- 물줄기 28개: 물리 포물선 경로(위 볼 → 아래 볼 8, 아래 볼 → 수반 12, 수반 분수구 → 안쪽 8)
  Geometry Nodes가 경로를 흐르는 물줄기 관(길이 방향 흐름 무늬)과 경로를 따라 날아가는 물방울로 만든다.
  시뮬레이션 굽기 없이 어떤 프레임에서도 같은 결과.
- 넘치는 물막: 두 볼 가장자리에서 떨어지는 얇은 물 커튼(아래로 흐르는 줄무늬)
- 조각: 청백 모자이크 수반 바닥, 물결형 금장 테두리, 볼 아랫면 아칸서스 잎, 금장 분수구·노즐, 받침 소용돌이
- EEVEE 레이트레이싱을 켠다(물 굴절·반사용).
옛 물 원판·물줄기는 30x로 옮긴다. 재실행하면 44 컬렉션과 P7 노드 그룹을 다시 만든다.
"""
import bpy, bmesh, math
from math import sin, cos, pi
from mathutils import Matrix

sc = bpy.context.scene
M = bpy.data.materials
white = M['Ivory marble']; gold = M['Antique gilded bronze']; blue = M['Sapphire stone']

HIDDEN = '30x | P3 replaced originals (hidden)'
C_W = '44 | P7 - Fountain water and details'
FX, FY = 0.0, 4.0
FPS = sc.render.fps
T_END = (sc.frame_end - 1) / FPS


def ensure_coll(name, clear=True):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name); sc.collection.children.link(c)
    if clear:
        for o in list(c.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    return c


hidden = ensure_coll(HIDDEN, clear=False)
coll = ensure_coll(C_W)
parked = []
for n in ('P3 fountain basin water', 'P3 fountain lower bowl water', 'P3 fountain upper bowl water', 'P3 fountain water jets'):
    o = bpy.data.objects.get(n)
    if o and hidden not in o.users_collection:
        o['p3_original_collections'] = ','.join(c.name for c in o.users_collection)
        for c in list(o.users_collection):
            c.objects.unlink(o)
        hidden.objects.link(o); parked.append(n)

# ------------------------------------------------------------------ render settings for refraction
sc.eevee.use_raytracing = True
sc.eevee.ray_tracing_method = 'SCREEN'


# ------------------------------------------------------------------ shader helpers
def new_material(name):
    m = M.get(name)
    if m is None:
        m = M.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    if nt.animation_data:
        nt.animation_data_clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (900, 0)
    p = nt.nodes.new('ShaderNodeBsdfPrincipled'); p.location = (600, 0)
    nt.links.new(p.outputs['BSDF'], out.inputs['Surface'])
    m.surface_render_method = 'DITHERED'
    m.use_raytrace_refraction = True
    m.use_backface_culling = False
    return m, nt, p


def inp(node, name):
    return node.inputs[name]


def math_node(nt, op, a=None, b=None, clamp=False):
    n = nt.nodes.new('ShaderNodeMath'); n.operation = op; n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def time_socket(nt):
    """Seconds as a keyframed Value node (linear 0 -> T_END over the frame range)."""
    v = nt.nodes.new('ShaderNodeValue'); v.label = 'P7 time seconds'
    prefs = bpy.context.preferences.edit
    old = prefs.keyframe_new_interpolation_type
    prefs.keyframe_new_interpolation_type = 'LINEAR'
    try:
        v.outputs[0].default_value = 0.0; v.outputs[0].keyframe_insert('default_value', frame=sc.frame_start)
        v.outputs[0].default_value = T_END; v.outputs[0].keyframe_insert('default_value', frame=sc.frame_end)
    finally:
        prefs.keyframe_new_interpolation_type = old
    return v.outputs[0]


def water_principled(p, base, rough):
    inp(p, 'Base Color').default_value = (*base, 1)
    inp(p, 'Roughness').default_value = rough
    inp(p, 'IOR').default_value = 1.333
    inp(p, 'Transmission Weight').default_value = 1.0
    inp(p, 'Specular IOR Level').default_value = .5


def body_material(name, foam_radii):
    m, nt, p = new_material(name)
    water_principled(p, (.72, .9, .94), .02)
    m.thickness_mode = 'SLAB'
    t = time_socket(nt)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    noise = nt.nodes.new('ShaderNodeTexNoise'); noise.noise_dimensions = '4D'
    nt.links.new(tc.outputs['Object'], inp(noise, 'Vector'))
    inp(noise, 'Scale').default_value = 7.0; inp(noise, 'Detail').default_value = 3.0
    nt.links.new(math_node(nt, 'MULTIPLY', t, .9), inp(noise, 'W'))
    wave = nt.nodes.new('ShaderNodeTexWave'); wave.wave_type = 'RINGS'; wave.rings_direction = 'SPHERICAL'
    nt.links.new(tc.outputs['Object'], inp(wave, 'Vector'))
    inp(wave, 'Scale').default_value = 3.2; inp(wave, 'Distortion').default_value = 1.5
    nt.links.new(math_node(nt, 'MULTIPLY', t, -7.0), inp(wave, 'Phase Offset'))
    height = math_node(nt, 'ADD', math_node(nt, 'MULTIPLY', noise.outputs['Fac'], .55), math_node(nt, 'MULTIPLY', wave.outputs['Fac'], .45))
    bump = nt.nodes.new('ShaderNodeBump'); inp(bump, 'Strength').default_value = .22; inp(bump, 'Distance').default_value = .02
    nt.links.new(height, inp(bump, 'Height')); nt.links.new(bump.outputs['Normal'], inp(p, 'Normal'))
    if foam_radii:
        sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sep.inputs[0])
        rad = math_node(nt, 'SQRT', math_node(nt, 'ADD', math_node(nt, 'POWER', sep.outputs['X'], 2), math_node(nt, 'POWER', sep.outputs['Y'], 2)))
        mask = None
        for R, w in foam_radii:
            ring = math_node(nt, 'SUBTRACT', 1.0, math_node(nt, 'DIVIDE', math_node(nt, 'ABSOLUTE', math_node(nt, 'SUBTRACT', rad, R)), w), clamp=True)
            mask = ring if mask is None else math_node(nt, 'MAXIMUM', mask, ring)
        fn = nt.nodes.new('ShaderNodeTexNoise'); fn.noise_dimensions = '4D'
        nt.links.new(tc.outputs['Object'], inp(fn, 'Vector')); inp(fn, 'Scale').default_value = 28.0; inp(fn, 'Detail').default_value = 4.0
        nt.links.new(math_node(nt, 'MULTIPLY', t, 3.0), inp(fn, 'W'))
        speck = math_node(nt, 'MULTIPLY', math_node(nt, 'SUBTRACT', fn.outputs['Fac'], .45), 3.0, clamp=True)
        foam = math_node(nt, 'MULTIPLY', mask, speck, clamp=True)
        mixc = nt.nodes.new('ShaderNodeMix'); mixc.data_type = 'RGBA'
        sock_in = {s.identifier: s for s in mixc.inputs}; sock_out = {s.identifier: s for s in mixc.outputs}
        sock_in['A_Color'].default_value = (.72, .9, .94, 1); sock_in['B_Color'].default_value = (.95, .98, 1, 1)
        nt.links.new(foam, sock_in['Factor_Float'])
        nt.links.new(sock_out['Result_Color'], inp(p, 'Base Color'))
        nt.links.new(math_node(nt, 'ADD', .02, math_node(nt, 'MULTIPLY', foam, .45)), inp(p, 'Roughness'))
        nt.links.new(math_node(nt, 'SUBTRACT', 1.0, math_node(nt, 'MULTIPLY', foam, .75)), inp(p, 'Transmission Weight'))
    return m


def streak_material(name, along_flow):
    """Moving streaks: along the GN 'flow' attribute for jets, downward in Z for overflow sheets."""
    m, nt, p = new_material(name)
    water_principled(p, (.86, .95, 1.0), .04)
    m.thickness_mode = 'SLAB' if not along_flow else 'SPHERE'
    t = time_socket(nt)
    comb = nt.nodes.new('ShaderNodeCombineXYZ')
    if along_flow:
        at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'flow'
        nt.links.new(math_node(nt, 'SUBTRACT', math_node(nt, 'MULTIPLY', at.outputs['Fac'], 26.0), math_node(nt, 'MULTIPLY', t, 11.0)), comb.inputs['X'])
    else:
        tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(tc.outputs['Object'], sep.inputs[0])
        nt.links.new(math_node(nt, 'MULTIPLY', sep.outputs['X'], 26.0), comb.inputs['X'])
        nt.links.new(math_node(nt, 'MULTIPLY', sep.outputs['Y'], 26.0), comb.inputs['Y'])
        nt.links.new(math_node(nt, 'ADD', math_node(nt, 'MULTIPLY', sep.outputs['Z'], 2.2), math_node(nt, 'MULTIPLY', t, 4.5)), comb.inputs['Z'])
    noise = nt.nodes.new('ShaderNodeTexNoise')
    nt.links.new(comb.outputs[0], inp(noise, 'Vector')); inp(noise, 'Scale').default_value = 1.6; inp(noise, 'Detail').default_value = 3.0
    # Sheets stay mostly clear so the carved stem reads through them; jets keep more body.
    lo, hi = (.5, 1.0) if along_flow else (.05, .55)
    alpha = math_node(nt, 'ADD', lo, math_node(nt, 'MULTIPLY', math_node(nt, 'MULTIPLY', math_node(nt, 'SUBTRACT', noise.outputs['Fac'], .38), 3.3, clamp=True), hi - lo))
    nt.links.new(alpha, inp(p, 'Alpha'))
    foam = math_node(nt, 'MULTIPLY', math_node(nt, 'SUBTRACT', noise.outputs['Fac'], .6), 4.0, clamp=True)
    inp(p, 'Emission Color').default_value = (1, 1, 1, 1)
    nt.links.new(math_node(nt, 'MULTIPLY', foam, .25 if along_flow else .1), inp(p, 'Emission Strength'))
    bump = nt.nodes.new('ShaderNodeBump'); inp(bump, 'Strength').default_value = .3
    nt.links.new(noise.outputs['Fac'], inp(bump, 'Height')); nt.links.new(bump.outputs['Normal'], inp(p, 'Normal'))
    return m


mat_basin = body_material('P7 water basin', [(.78, .12), (1.55, .1), (1.85, .14)])
mat_lower = body_material('P7 water lower bowl', [(.95, .08), (1.1, .1)])
mat_upper = body_material('P7 water upper bowl', [(.32, .06)])
mat_stream = streak_material('P7 water stream', True)
mat_sheet = streak_material('P7 water overflow sheet', False)
mat_drop, _nt, _p = new_material('P7 water droplet')
water_principled(_p, (.9, .97, 1.0), .015)
mat_drop.thickness_mode = 'SPHERE'


# ------------------------------------------------------------------ geometry helpers
def lathe_obj(name, profile, mat, segs=64, smooth=True):
    bm = bmesh.new()
    vs = [bm.verts.new((r, 0, z)) for r, z in profile]
    es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + es, angle=2 * pi, steps=segs, axis=(0, 0, 1), cent=(0, 0, 0))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(mat)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    o = bpy.data.objects.new(name, me); coll.objects.link(o); o.location = (FX, FY, 0)
    return o


def curves(name, splines, r, mat, closed=False):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 2 if r >= .02 else 1
    cu.resolution_u = 1; cu.use_fill_caps = True
    for pts in splines:
        sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
        for v, p in zip(sp.points, pts):
            v.co = (*p, 1)
        sp.use_cyclic_u = closed
    if mat:
        cu.materials.append(mat)
    o = bpy.data.objects.new(name, cu); coll.objects.link(o)
    return o


def P(r, a, z):
    return (FX + r * cos(a), FY + r * sin(a), z)


# ------------------------------------------------------------------ water bodies and overflow sheets
lathe_obj('P7 water basin body', [(0, .12), (2.07, .12), (2.07, .5), (0, .5)], mat_basin, 96)
lathe_obj('P7 water lower bowl body', [(0, 1.747), (1.05, 1.784), (1.17, 1.84), (0, 1.84)], mat_lower, 72)
lathe_obj('P7 water upper bowl body', [(0, 2.767), (.5, 2.806), (.62, 2.87), (0, 2.87)], mat_upper, 48)
lathe_obj('P7 water overflow sheet upper', [(.835, 2.915), (.875, 2.8), (.92, 2.3), (.95, 1.84)], mat_sheet, 72)
lathe_obj('P7 water overflow sheet lower', [(1.435, 1.895), (1.475, 1.76), (1.53, 1.1), (1.56, .5)], mat_sheet, 96)

# ------------------------------------------------------------------ carved and gilt details
# Mosaic basin floor: concentric rings of alternating sapphire and marble tesserae.
bm = bmesh.new()
rings = [0.0, .45, .9, 1.3, 1.7, 2.07]
for ri in range(len(rings) - 1):
    r0, r1 = rings[ri], rings[ri + 1]
    n = 8 * (ri + 1)
    for k in range(n):
        a0, a1 = 2 * pi * k / n, 2 * pi * (k + 1) / n
        sub = 3
        pts = [(r1 * cos(a0 + (a1 - a0) * j / sub), r1 * sin(a0 + (a1 - a0) * j / sub)) for j in range(sub + 1)]
        pts += [(r0 * cos(a0 + (a1 - a0) * j / sub), r0 * sin(a0 + (a1 - a0) * j / sub)) for j in range(sub, -1, -1)] if r0 > 0 else [(0.0, 0.0)]
        f = bm.faces.new([bm.verts.new((FX + x, FY + y, .105)) for x, y in pts])
        f.material_index = (ri + k) % 2
bm.normal_update()
for f in bm.faces:
    if f.normal.z < 0:
        f.normal_flip()
me = bpy.data.meshes.new('P7 fountain mosaic floor'); bm.to_mesh(me); bm.free()
me.materials.append(blue); me.materials.append(white)
coll.objects.link(bpy.data.objects.new(me.name, me))
curves('P7 fountain mosaic gilt rings', [[P(r, 2 * pi * i / 96, .108) for i in range(96)] for r in rings[1:]], .012, gold, True)

# Scalloped gilt rims.
curves('P7 lower bowl scalloped gilt rim', [[P(1.43 + .055 * abs(sin(8 * a)), a, 1.905) for a in [2 * pi * i / 192 for i in range(192)]]], .022, gold, True)
curves('P7 upper bowl scalloped gilt rim', [[P(.83 + .04 * abs(sin(6 * a)), a, 2.925) for a in [2 * pi * i / 144 for i in range(144)]]], .018, gold, True)
curves('P7 basin scalloped gilt rim', [[P(2.37 + .05 * abs(sin(12 * a)), a, .675) for a in [2 * pi * i / 288 for i in range(288)]]], .02, gold, True)


def underside_z(r, prof):
    for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
        if r0 <= r <= r1:
            return z0 + (z1 - z0) * (r - r0) / (r1 - r0)
    return prof[-1][1]


def leaves(name, n, r_in, r_out, prof, width):
    out, ribs = [], []
    for k in range(n):
        a = 2 * pi * k / n
        side_l, side_r, rib = [], [], []
        for j in range(15):
            t = j / 14
            r = r_in + (r_out - r_in) * t
            z = underside_z(r, prof) - .025
            wdt = width * sin(pi * t) * (1 - .35 * t) * (1 + .25 * sin(5 * pi * t))
            da = wdt / r
            side_l.append(P(r, a - da, z)); side_r.append(P(r, a + da, z)); rib.append(P(r, a, z - .01))
        out.append(side_l + side_r[::-1])
        ribs.append(rib)
    curves(name + ' outline', out, .022, white, True)
    curves(name + ' midrib', ribs, .012, gold)


leaves('P7 lower bowl acanthus', 12, .42, 1.36, [(.4, 1.5), (1.1, 1.66), (1.42, 1.84)], .2)
leaves('P7 upper bowl acanthus', 10, .26, .78, [(.25, 2.55), (.62, 2.7), (.82, 2.86)], .11)

# Volute brackets between the pedestal and the lower bowl.
vol = []
for k in range(4):
    a = pi / 4 + k * pi / 2
    vol.append([P(.3 + .5 * t, a, 1.12 + .5 * t * t) for t in [i / 12 for i in range(13)]])
    vol.append([P(.3 + .09 * (1 - u / 9) * cos(u), a, 1.12 + .09 * (1 - u / 9) * sin(u)) for u in [j * .5 for j in range(14)]])
    vol.append([P(.8 + .07 * (1 - u / 9) * cos(u + pi), a, 1.62 + .07 * (1 - u / 9) * sin(u + pi)) for u in [j * .5 for j in range(14)]])
curves('P7 pedestal gilt volute brackets', vol, .028, gold)

# Gilt spouts on the basin rim (sources of the inward jets) and nozzles on the bowl rims.
spouts, shells = [], []
Bm = bmesh.new()
for k in range(8):
    a = (k + .5) * 2 * pi / 8
    spouts.append([P(2.42, a, .58), P(2.36, a, .66), P(2.24, a, .7), P(2.13, a, .67)])
    shells.append([P(2.42 + .16 * sin(u) * .2, a + .16 * cos(u) / 2.42, .6 + .16 * abs(sin(u))) for u in [i * pi / 12 for i in range(13)]])
    x, y, z = P(2.42, a, .58)
    bmesh.ops.create_uvsphere(Bm, u_segments=12, v_segments=8, radius=.055, matrix=Matrix.Translation((x, y, z)))
for k in range(8):
    x, y, z = P(.82, k * 2 * pi / 8, 2.935)
    bmesh.ops.create_uvsphere(Bm, u_segments=10, v_segments=6, radius=.022, matrix=Matrix.Translation((x, y, z)))
for k in range(12):
    x, y, z = P(1.43, (k + .5) * 2 * pi / 12, 1.925)
    bmesh.ops.create_uvsphere(Bm, u_segments=10, v_segments=6, radius=.026, matrix=Matrix.Translation((x, y, z)))
me = bpy.data.meshes.new('P7 fountain gilt spout heads and nozzles'); Bm.to_mesh(me); Bm.free()
me.materials.append(gold)
for p in me.polygons:
    p.use_smooth = True
coll.objects.link(bpy.data.objects.new(me.name, me))
curves('P7 basin gilt spouts', spouts, .038, gold)
curves('P7 basin gilt spout shells', shells, .018, gold)


# ------------------------------------------------------------------ jet paths (physical parabolas)
def parabola(r0, z0, r1, z1, peak, a, n=28):
    return [P(r0 + (r1 - r0) * t, a, z0 + (z1 - z0) * t + peak * 4 * t * (1 - t)) for t in [i / (n - 1) for i in range(n)]]


paths = []
for k in range(8):
    paths.append(parabola(.83, 2.935, 1.1, 1.845, .26, k * 2 * pi / 8))
for k in range(12):
    paths.append(parabola(1.44, 1.93, 1.85, .505, .24, (k + .5) * 2 * pi / 12))
for k in range(8):
    paths.append(parabola(2.12, .67, .78, .505, 1.0, (k + .5) * 2 * pi / 8, 36))
path_obj = curves('P7 fountain jet paths (GN source, not rendered)', paths, 0.0, None)

# ------------------------------------------------------------------ Geometry Nodes: flowing tubes + travelling droplets
old = bpy.data.node_groups.get('P7 fountain streams')
if old:
    bpy.data.node_groups.remove(old)
ng = bpy.data.node_groups.new('P7 fountain streams', 'GeometryNodeTree')
ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
N, L = ng.nodes, ng.links
g_out = N.new('NodeGroupOutput'); N.new('NodeGroupInput')
oi = N.new('GeometryNodeObjectInfo'); oi.inputs['Object'].default_value = path_obj; oi.transform_space = 'RELATIVE'
join = N.new('GeometryNodeJoinGeometry')

# tubes with a 'flow' attribute (0 at nozzle -> 1 at landing)
sp = N.new('GeometryNodeSplineParameter')
store = N.new('GeometryNodeStoreNamedAttribute'); store.data_type = 'FLOAT'; store.domain = 'POINT'
store.inputs['Name'].default_value = 'flow'
L.new(oi.outputs['Geometry'], store.inputs['Geometry']); L.new(sp.outputs['Factor'], store.inputs['Value'])
circle = N.new('GeometryNodeCurvePrimitiveCircle'); circle.inputs['Resolution'].default_value = 8; circle.inputs['Radius'].default_value = .013
c2m = N.new('GeometryNodeCurveToMesh')
L.new(store.outputs['Geometry'], c2m.inputs['Curve']); L.new(circle.outputs['Curve'], c2m.inputs['Profile Curve'])
setm = N.new('GeometryNodeSetMaterial'); setm.inputs['Material'].default_value = mat_stream
L.new(c2m.outputs['Mesh'], setm.inputs['Geometry']); L.new(setm.outputs['Geometry'], join.inputs['Geometry'])
smooth = N.new('GeometryNodeSetShadeSmooth') if hasattr(bpy.types, 'GeometryNodeSetShadeSmooth') else None

# droplets travelling along each path
res = N.new('GeometryNodeResampleCurve'); res.inputs['Count'].default_value = 14
L.new(oi.outputs['Geometry'], res.inputs['Curve'])
sp2 = N.new('GeometryNodeSplineParameter'); cop = N.new('GeometryNodeCurveOfPoint')
st = N.new('GeometryNodeInputSceneTime'); idx = N.new('GeometryNodeInputIndex')
# Full random phase so droplets scatter along the jet instead of forming an evenly spaced bead chain.
rnd = N.new('FunctionNodeRandomValue'); rnd.data_type = 'FLOAT'; rnd.inputs['Min'].default_value = 0.0; rnd.inputs['Max'].default_value = 1.0
L.new(idx.outputs['Index'], rnd.inputs['ID'])
jit = N.new('ShaderNodeCombineXYZ')
for axis, seed in (('X', 11), ('Y', 23), ('Z', 37)):
    rj = N.new('FunctionNodeRandomValue'); rj.data_type = 'FLOAT'
    rj.inputs['Min'].default_value = -.03; rj.inputs['Max'].default_value = .03; rj.inputs['Seed'].default_value = seed
    L.new(idx.outputs['Index'], rj.inputs['ID']); L.new(rj.outputs['Value'], jit.inputs[axis])
spd = N.new('ShaderNodeMath'); spd.operation = 'MULTIPLY'; spd.inputs[1].default_value = 1.35
L.new(st.outputs['Seconds'], spd.inputs[0])
add1 = N.new('ShaderNodeMath'); add1.operation = 'ADD'
L.new(sp2.outputs['Factor'], add1.inputs[0]); L.new(spd.outputs[0], add1.inputs[1])
add2 = N.new('ShaderNodeMath'); add2.operation = 'ADD'
L.new(add1.outputs[0], add2.inputs[0]); L.new(rnd.outputs['Value'], add2.inputs[1])
fr = N.new('ShaderNodeMath'); fr.operation = 'FRACT'
L.new(add2.outputs[0], fr.inputs[0])
samp = N.new('GeometryNodeSampleCurve'); samp.mode = 'FACTOR'; samp.use_all_curves = False
L.new(oi.outputs['Geometry'], samp.inputs['Curves']); L.new(fr.outputs[0], samp.inputs['Factor']); L.new(cop.outputs['Curve Index'], samp.inputs['Curve Index'])
setp = N.new('GeometryNodeSetPosition')
L.new(res.outputs['Curve'], setp.inputs['Geometry']); L.new(samp.outputs['Position'], setp.inputs['Position'])
L.new(jit.outputs['Vector'], setp.inputs['Offset'])
ico = N.new('GeometryNodeMeshIcoSphere'); ico.inputs['Radius'].default_value = .02; ico.inputs['Subdivisions'].default_value = 2
setd = N.new('GeometryNodeSetMaterial'); setd.inputs['Material'].default_value = mat_drop
L.new(ico.outputs['Mesh'], setd.inputs['Geometry'])
rs = N.new('FunctionNodeRandomValue'); rs.data_type = 'FLOAT'; rs.inputs['Min'].default_value = .5; rs.inputs['Max'].default_value = 1.2; rs.inputs['Seed'].default_value = 7
L.new(idx.outputs['Index'], rs.inputs['ID'])
iop = N.new('GeometryNodeInstanceOnPoints')
L.new(setp.outputs['Geometry'], iop.inputs['Points']); L.new(setd.outputs['Geometry'], iop.inputs['Instance']); L.new(rs.outputs['Value'], iop.inputs['Scale'])
L.new(iop.outputs['Instances'], join.inputs['Geometry'])
L.new(join.outputs['Geometry'], g_out.inputs['Geometry'])

holder_me = bpy.data.meshes.new('P7 fountain streams holder')
holder = bpy.data.objects.new('P7 fountain water streams (GN)', holder_me); coll.objects.link(holder)
mod = holder.modifiers.new('P7 streams', 'NODES'); mod.node_group = ng

# ------------------------------------------------------------------ close-up camera
from mathutils import Vector
CAM13 = 'CAM 13 | P7 - Fountain close-up'
for d_old in [d for d in bpy.data.cameras if d.name.startswith('CAM 13') and d.users == 0]:
    bpy.data.cameras.remove(d_old)   # a rerun leaves the old camera data behind; avoid a .001 name
cd = bpy.data.cameras.new(CAM13)
cam = bpy.data.objects.new(CAM13, cd); coll.objects.link(cam)
cam.location = (0.0, -1.2, 1.9)   # between the two stair feet, clear of the newel urns
cam.rotation_euler = (Vector((0, 4, 1.75)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
cd.lens = 32; cd.clip_end = 400

bpy.context.view_layer.update()
ev = holder.evaluated_get(bpy.context.evaluated_depsgraph_get())
result = {
    'collection_objects': len(coll.objects), 'parked': parked, 'jets': len(paths),
    'raytracing': sc.eevee.use_raytracing,
    'gn_mesh_verts_at_frame': len(ev.to_mesh().vertices) if ev else None,
}
ev.to_mesh_clear()
print('P7_RESULT', result)
