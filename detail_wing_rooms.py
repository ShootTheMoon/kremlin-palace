"""2차 세부 구현: 측면 의전실 내부 마감.

detail_wing_doors.py 이후 COMPLETE 장면에 실행한다. 재실행하면 19~21번 컬렉션을 비우고 다시 만든다.
의전실 내부: x 16~29.85 (좌우 대칭), y 8.15~13.85, 벽 높이 6m.
- 19 천장(숨겨서 위에서 볼 수 있음): 대리석 슬래브, 금장 크라운 코니스, 격자 보, 샹들리에 메달리온
- 20 벽·가구: 걸레받이, 의자 레일, 거울 베이 4, 사파이어 벽기둥 4 + 3구 벽등, 콘솔 3, 창가 벤치 4, 러너 금테
- 21 조명: 창문 동기 영역광 4, 벽등 보조 점광 4 (한쪽 기준)
천장을 뚫고 올라가던 샹들리에 줄기는 천장 밑까지 잘라 맞춘다(원래 값은 커스텀 속성에 보관).
"""
import bpy, bmesh, math
from math import sin, cos, pi
from mathutils import Vector

sc = bpy.context.scene
M = bpy.data.materials
white = M['Ivory marble']; gold = M['Antique gilded bronze']; blue = M['Sapphire stone']
velvet = M['Royal blue velvet']; bulb = M['Candle light']
mirror = M.get('Palace mirror')
if mirror is None:
    mirror = M.new('Palace mirror'); mirror.use_nodes = True
# EEVEE without ray tracing reflects only the dark world: a pure chrome mirror reads black.
p = mirror.node_tree.nodes.get('Principled BSDF')
p.inputs['Base Color'].default_value = (.72, .78, .85, 1)
p.inputs['Metallic'].default_value = .85
p.inputs['Roughness'].default_value = .22
mirror.diffuse_color = (.72, .78, .85, 1)

C_CEIL = '19 | DETAIL - Wing room ceilings'
C_ROOM = '20 | DETAIL - Wing room walls and furniture'
C_LGT = '21 | LIGHTING - Wing rooms'


def get_coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name); sc.collection.children.link(c)
    for o in list(c.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    return c


colls = {k: get_coll(k) for k in (C_CEIL, C_ROOM, C_LGT)}
coll = colls[C_ROOM]
_mesh = {}


def unit_mesh(kind, mat):
    key = (kind, mat.name)
    if key in _mesh:
        return _mesh[key]
    name = 'ROOM_unit_%s_%s' % (kind, mat.name)
    me = bpy.data.meshes.get(name)
    if me is None:
        me = bpy.data.meshes.new(name); bm = bmesh.new()
        if kind == 'box':
            bmesh.ops.create_cube(bm, size=1)
        elif kind == 'cyl':
            bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=1, radius2=1, depth=1)
        else:
            bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=1)
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


def box(name, loc, dims, mat):
    return add(name, 'box', mat, loc, dims)


def cyl(name, loc, r, h, mat):
    return add(name, 'cyl', mat, loc, (r, r, h))


def ball(name, loc, dims, mat):
    return add(name, 'ball', mat, loc, dims)


def line(name, pts, r, mat, closed=False):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 2; cu.resolution_u = 1
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for v, p in zip(sp.points, pts):
        v.co = (*p, 1)
    sp.use_cyclic_u = closed; cu.materials.append(mat)
    o = bpy.data.objects.new(name, cu); coll.objects.link(o)
    return o


def frame_xz(name, x, y, z, w, h, t, d):
    for dx in (-w / 2, w / 2):
        box(name, (x + dx, y, z), (t, d, h + t), gold)
    for dz in (-h / 2, h / 2):
        box(name, (x, y, z + dz), (w + t, d, t), gold)


def scroll(x, y, z, w):
    for sign in (-1, 1):
        pts = []
        for i in range(30):
            t = i / 29 * 2.5 * pi; r = w * (1 - i / 36)
            pts.append((x + sign * (w * .8 + r * cos(t)), y, z + r * sin(t) * .45))
        line('Room gilt scroll', pts, .016, gold)


MIRROR_BAYS = (17.5, 20.5, 23.5, 26.5)   # opposite the four windows
PILASTERS = (19.0, 22.0, 25.0, 28.0)
CONSOLES = (20.5, 23.5, 26.5)             # 17.5 is kept clear for the door leaf swing
BENCHES = (17.5, 20.5, 23.5, 26.5)        # under the windows, between wall columns
FRONT, OUTER = 8.15, 13.85

for s in (1, -1):
    X = lambda u: s * u
    tag = 'R' if s > 0 else 'L'

    # ---- 19 ceiling
    coll = colls[C_CEIL]
    box('Wing ceiling marble slab', (X(23), 11, 6.1), (14.0, 6.3, .2), white)
    box('Wing crown cornice gilt', (X(23), FRONT + .08, 5.85), (13.6, .16, .12), gold)
    box('Wing crown cornice gilt', (X(23), OUTER - .08, 5.85), (13.6, .16, .12), gold)
    box('Wing crown cornice gilt', (X(29.77), 11, 5.85), (.16, 5.7, .12), gold)
    box('Wing crown cornice gilt', (X(16.305), 11, 5.85), (.16, 5.7, .12), gold)
    for y in (9.4, 12.6):
        box('Wing ceiling beam gilt', (X(23), y, 5.97), (13.4, .1, .06), gold)
        ball('Wing ceiling beam rosette', (X(23), y, 5.95), (.09, .09, .05), gold)
    box('Wing ceiling beam gilt', (X(23), 11, 5.97), (.1, 5.6, .06), gold)
    for u0, u1 in ((16.5, 22.8), (23.2, 29.5)):
        line('Wing ceiling panel moulding', [(X(u0), 9.55, 5.975), (X(u1), 9.55, 5.975), (X(u1), 12.45, 5.975), (X(u0), 12.45, 5.975)], .025, gold, True)
    for u in (20, 26):
        cyl('Wing ceiling sapphire medallion', (X(u), 11, 5.975), .45, .03, blue)
        for rr in (.55, .8):
            line('Wing ceiling medallion ring', [(X(u) + rr * cos(t), 11 + rr * sin(t), 5.97) for t in [i * 2 * pi / 40 for i in range(40)]], .03, gold, True)

    # ---- 20 walls and furniture
    coll = colls[C_ROOM]
    # Baseboards; broken at the portal and end-wall door frames.
    box('Wing baseboard marble', (X(23), FRONT + .03, .15), (13.6, .06, .3), white)
    box('Wing baseboard gilt cap', (X(23), FRONT + .04, .32), (13.6, .08, .04), gold)
    box('Wing baseboard marble', (X(23), OUTER - .03, .15), (13.6, .06, .3), white)
    box('Wing baseboard gilt cap', (X(23), OUTER - .04, .32), (13.6, .08, .04), gold)
    for u_face, segs in ((29.82, ((8.15, 9.5), (12.5, 13.85))), (16.255, ((8.15, 8.7), (12.7, 13.85)))):
        for y0, y1 in segs:
            box('Wing baseboard marble', (X(u_face), (y0 + y1) / 2, .15), (.06, y1 - y0, .3), white)
            box('Wing baseboard gilt cap', (X(u_face), (y0 + y1) / 2, .32), (.08, y1 - y0, .04), gold)
    box('Wing chair rail gilt', (X(23), FRONT + .04, 1.0), (13.6, .05, .05), gold)
    for y in (9.78, 12.22):
        box('Wing runner gilt border', (X(23), y, .056), (13.5, .05, .012), gold)

    # Front wall: arched mirror bays.
    for u in MIRROR_BAYS:
        box('Wing mirror glass', (X(u), FRONT + .05, 3.0), (1.7, .04, 3.6), mirror)
        frame_xz('Wing mirror frame gilt', X(u), FRONT + .09, 3.0, 1.8, 3.8, .08, .06)
        frame_xz('Wing mirror inner bead gilt', X(u), FRONT + .11, 3.0, 1.6, 3.6, .03, .03)
        for rr in (.86, .94):
            line('Wing mirror arch crest', [(X(u) + rr * cos(t), FRONT + .1, 4.9 + rr * sin(t)) for t in [i * pi / 32 for i in range(33)]], .03, gold)
        ball('Wing mirror crest medallion', (X(u), FRONT + .12, 5.42), (.14, .05, .14), blue)
        scroll(X(u), FRONT + .12, 5.1, .22)

    # Pilasters with three-arm sconces.
    for u in PILASTERS:
        box('Wing sapphire pilaster', (X(u), FRONT + .06, 2.9), (.5, .12, 5.0), blue)
        box('Wing pilaster base marble', (X(u), FRONT + .09, .2), (.62, .18, .4), white)
        box('Wing pilaster capital gilt', (X(u), FRONT + .09, 5.46), (.62, .18, .12), gold)
        for zz in (1.0, 4.2):
            box('Wing pilaster collar gilt', (X(u), FRONT + .07, zz), (.54, .14, .06), gold)
        for dx in (-.22, 0, .22):
            line('Wing sconce arm', [(X(u), FRONT + .13, 2.95), (X(u) + dx, FRONT + .4, 3.2), (X(u) + dx, FRONT + .47, 3.45)], .03, gold)
            cyl('Wing sconce candle', (X(u) + dx, FRONT + .47, 3.6), .04, .28, white)
            ball('Wing sconce flame', (X(u) + dx, FRONT + .47, 3.79), (.045, .045, .09), bulb)

    # Console tables with sapphire vases.
    for u in CONSOLES:
        y0 = FRONT + .35
        box('Wing console marble top', (X(u), y0, .92), (1.3, .48, .06), white)
        box('Wing console gilt apron', (X(u), y0 + .22, .82), (1.24, .05, .14), gold)
        scroll(X(u), y0 + .255, .82, .16)
        for sx in (-1, 1):
            line('Wing console cabriole leg', [(X(u) + sx * .58, y0 + .18, .85), (X(u) + sx * .63, y0 + .28, .45), (X(u) + sx * .55, y0 + .16, .04)], .03, gold)
            cyl('Wing console rear leg', (X(u) + sx * .58, y0 - .18, .44), .03, .85, gold)
        cyl('Wing vase gilt foot', (X(u), y0, .98), .1, .06, gold)
        ball('Wing vase sapphire body', (X(u), y0, 1.17), (.16, .16, .22), blue)
        cyl('Wing vase gilt neck', (X(u), y0, 1.43), .06, .12, gold)

    # Window benches.
    for u in BENCHES:
        # 1.3m keeps clear of the wall column bases (r .55 at u ±1.25 from each window).
        box('Wing bench velvet cushion', (X(u), 13.5, .5), (1.3, .48, .14), velvet)
        box('Wing bench gilt seat rail', (X(u), 13.5, .4), (1.36, .54, .07), gold)
        box('Wing bench velvet back', (X(u), 13.74, .82), (1.3, .1, .42), velvet)
        box('Wing bench gilt back rail', (X(u), 13.74, 1.05), (1.34, .12, .04), gold)
        for sx in (-1, 1):
            for yy in (13.3, 13.7):
                cyl('Wing bench gilt leg', (X(u) + sx * .55, yy, .18), .035, .36, gold)

    # ---- 21 lighting (motivated by the windows and sconces)
    coll = colls[C_LGT]
    for u in MIRROR_BAYS:
        d = bpy.data.lights.new('LGT_key_wing_window_%s_%s' % (tag, u), 'AREA')
        d.shape = 'RECTANGLE'; d.size = 1.6; d.size_y = 3.6; d.energy = 150; d.color = (.8, .88, 1)
        d.specular_factor = 0.0  # no light-card reflection in the mirrors opposite
        o = bpy.data.objects.new(d.name, d); coll.objects.link(o)
        o.location = (X(u), 13.45, 3.0); o.rotation_euler = (-pi / 2, 0, 0)
        o['purpose'] = 'Daylight through the window bay; lifts the room and the mirror wall opposite'
    for u in PILASTERS:
        d = bpy.data.lights.new('LGT_practical_wing_sconce_%s_%s' % (tag, u), 'POINT')
        d.energy = 60; d.color = (1, .78, .5); d.shadow_soft_size = .12
        o = bpy.data.objects.new(d.name, d); coll.objects.link(o)
        o.location = (X(u), FRONT + .47, 3.85)
        o['purpose'] = 'Helper light matching the visible three-candle sconce'

# ---- Trim wing chandelier stems to the new ceiling underside (z 6.0).
trimmed = []
for o in sc.objects:
    if o.name.startswith('Chandelier stem') and abs(o.location.x) > 16 and abs(o.location.y - 11) < .1:
        if 'wing_stem_original' not in o:
            o['wing_stem_original'] = [o.location.z, o.scale.z]
        z0, h0 = o['wing_stem_original']
        bottom = z0 - h0 / 2
        o.location.z = (bottom + 6.0) / 2; o.scale.z = 6.0 - bottom
        trimmed.append(o.name)

# ---- Camera toward the mirror wall.
coll = colls[C_ROOM]
cd = bpy.data.cameras.new('CAM 10 | DETAIL - Wing mirror wall')
cam = bpy.data.objects.new(cd.name, cd); coll.objects.link(cam)
cam.location = (18.2, 12.6, 1.9)
cam.rotation_euler = (Vector((26, 8.3, 2.6)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
cd.lens = 22; cd.clip_end = 400

sc['Wing rooms'] = ('Ceilings in 19 (hide for top view), walls/furniture in 20, lights in 21. '
                    'Chandelier stems trimmed to z 6.0; originals in wing_stem_original.')
result = {k: len(c.objects) for k, c in colls.items()}
result['trimmed_stems'] = trimmed
result['scene_objects'] = len(sc.objects)
print('WING_ROOMS_RESULT', result)
