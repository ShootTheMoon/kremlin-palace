"""2차 세부 구현: 측면 의전실(윙) 문.

Kremlin_Grand_Palace_COMPLETE 장면에 실행한다. 재실행해도 18번 컬렉션을 비우고 다시 만든다.
- 중앙 홀 좌우 윙 입구(x=±16, y 8~14): 벽 채움 + 금장 문틀 + 양개문(열림 애니메이션)
- 윙 끝벽(x=±30): 닫힌 장식 양개문
- 입구를 가로지르던 벽 패널은 18x 숨김 컬렉션으로 이동, 걸레받이 코니스는 문 폭만큼 분할
"""
import bpy, bmesh, math
from math import sin, cos, pi
from mathutils import Vector

sc = bpy.context.scene
M = bpy.data.materials
white = M['Ivory marble']; gold = M['Antique gilded bronze']
blue = M['Sapphire stone']; velvet = M['Royal blue velvet']
COL = '18 | DETAIL - Wing room doors'
HID = '18x | Replaced by doors (hidden)'


def get_coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        sc.collection.children.link(c)
    return c


coll = get_coll(COL)
for o in list(coll.objects):
    bpy.data.objects.remove(o, do_unlink=True)

_mesh = {}


def unit_mesh(kind, mat):
    key = (kind, mat.name)
    if key in _mesh:
        return _mesh[key]
    name = 'DOOR_unit_%s_%s' % (kind, mat.name)
    me = bpy.data.meshes.get(name)
    if me is None:
        me = bpy.data.meshes.new(name)
        bm = bmesh.new()
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


def add(name, kind, mat, loc, dims, parent):
    o = bpy.data.objects.new(name, unit_mesh(kind, mat))
    coll.objects.link(o)
    o.parent = parent; o.location = loc; o.scale = dims
    return o


def box(name, parent, loc, dims, mat):
    return add(name, 'box', mat, loc, dims, parent)


def line(name, parent, pts, r, mat, closed=False):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 2; cu.resolution_u = 1
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for v, p in zip(sp.points, pts):
        v.co = (*p, 1)
    sp.use_cyclic_u = closed
    cu.materials.append(mat)
    o = bpy.data.objects.new(name, cu); coll.objects.link(o); o.parent = parent
    return o


def empty(name, parent, loc, size=.4, kind='ARROWS'):
    o = bpy.data.objects.new(name, None); coll.objects.link(o)
    o.parent = parent; o.location = loc
    o.empty_display_type = kind; o.empty_display_size = size
    return o


def frame(name, parent, x, y, z, w, h, t=.05, d=.04):
    for dx in (-w / 2, w / 2):
        box(name, parent, (x + dx, y, z), (t, d, h + t), gold)
    for dz in (-h / 2, h / 2):
        box(name, parent, (x, y, z + dz), (w + t, d, t), gold)


def scroll(parent, x, y, z, w):
    for sign in (-1, 1):
        pts = []
        for i in range(30):
            t = i / 29 * 2.5 * pi; r = w * (1 - i / 36)
            pts.append((x + sign * (w * .8 + r * cos(t)), y, z + r * sin(t) * .45))
        line('Door gilt scroll', parent, pts, .016, gold)


def leaf(hinge, direction, width, height, thick=.12):
    """Door leaf in hinge space; extends along +direction X, faces ±Y."""
    cx = direction * width / 2
    box('Door leaf sapphire', hinge, (cx, 0, height / 2 + .05), (width, thick, height), blue)
    pw = width - .42
    for fy in (-1, 1):
        y = fy * (thick / 2 + .02)
        for zc, ph in ((height * .28, height * .36), (height * .71, height * .38)):
            frame('Door raised panel gilt', hinge, cx, y, zc, pw, ph)
            frame('Door inner bead gilt', hinge, cx, y + fy * .01, zc, pw - .2, ph - .2, .03, .03)
            scroll(hinge, cx, y + fy * .03, zc, min(.26, pw * .22))
        box('Door kick plate gilt', hinge, (cx, y, .2), (width - .2, .03, .18), gold)
        hx = direction * (width - .16); hz = height * .48
        line('Door handle stem', hinge, [(hx, fy * thick / 2, hz), (hx, fy * (thick / 2 + .06), hz)], .02, gold)
        add('Door bronze handle', 'ball', gold, (hx, fy * (thick / 2 + .08), hz), (.055, .06, .055), hinge)


def doorway(label, s, wall_x, y_center, opening_w, opening_h, wall_t, wall_h, y_min, y_max, through):
    """s=+1 right / -1 left. Root local -Y faces the room the door is seen from
    (hall for a through portal, wing interior for an end-wall door)."""
    k = -s
    root = bpy.data.objects.new('DOOR_ROOT | %s' % label, None); coll.objects.link(root)
    root.location = (s * wall_x, y_center, 0); root.rotation_euler = (0, 0, -s * pi / 2)
    root.empty_display_type = 'PLAIN_AXES'; root.empty_display_size = .8
    hw = opening_w / 2

    if through:
        for wy0, wy1 in ((y_min, y_center - hw), (y_center + hw, y_max)):
            a = k * (wy0 - y_center); b = k * (wy1 - y_center)
            box('Door wall infill marble', root, ((a + b) / 2, 0, wall_h / 2), (abs(b - a), wall_t, wall_h), white)
        box('Door header marble', root, (0, 0, (opening_h + wall_h) / 2), (opening_w, wall_t, wall_h - opening_h), white)
        for sx in (-1, 1):
            box('Door reveal gilt lining', root, (sx * (hw - .02), 0, opening_h / 2), (.04, wall_t + .01, opening_h), gold)
        box('Door soffit gilt lining', root, (0, 0, opening_h - .02), (opening_w, wall_t + .01, .04), gold)
        box('Door marble threshold', root, (0, 0, .02), (opening_w, wall_t + .1, .04), white)

    for fy in ((-1, 1) if through else (-1,)):
        y = fy * (wall_t / 2 + .05)
        for sx in (-1, 1):
            box('Door architrave jamb gilt', root, (sx * (hw + .1), y, (opening_h + .1) / 2), (.2, .1, opening_h + .1), gold)
            box('Door plinth block marble', root, (sx * (hw + .1), fy * (wall_t / 2 + .07), .2), (.3, .14, .4), white)
        box('Door architrave head gilt', root, (0, y, opening_h + .1), (opening_w + .4, .1, .2), gold)
        box('Door cornice gilt', root, (0, fy * (wall_t / 2 + .08), opening_h + .3), (opening_w + .7, .16, .12), gold)

    # Overdoor crest: wing side of a portal (hall side sits under the gallery slab).
    cf = 1 if through else -1
    yc = cf * (wall_t / 2 + .06); zc = opening_h + .42
    for rr in (.9, 1.02):
        line('Overdoor gilt arch', root, [(rr * cos(t), yc, zc + rr * sin(t)) for t in [i * pi / 40 for i in range(41)]], .035, gold)
    add('Overdoor sapphire medallion', 'ball', blue, (0, cf * (wall_t / 2 + .1), zc + .48), (.22, .06, .22), root)
    line('Overdoor medallion rim', root, [(.26 * cos(t), cf * (wall_t / 2 + .13), zc + .48 + .26 * sin(t)) for t in [i * 2 * pi / 32 for i in range(32)]], .025, gold, True)
    scroll(root, 0, yc, zc + .1, .3)

    # Leaves: hinges sit just inside the reveal; portal leaves are flush to the wing face.
    thick = .12; lw = hw - .09; lh = opening_h - .08
    hy = (wall_t / 2 - thick / 2) if through else -(wall_t / 2 + thick / 2 + .01)
    hinges = []
    for tag, sx in (('A', -1), ('B', 1)):
        h = empty('DOOR_HINGE | %s | %s' % (label, tag), root, (sx * (hw - .08), hy, 0))
        leaf(h, -sx, lw, lh, thick)
        h['Open direction'] = 'Rotate local Z: A positive, B negative (degrees 0-90)' if through else 'Decorative closed door; wall behind'
        hinges.append((h, -sx))
    return root, hinges


# --- Remove the hall-side wall panel that floated across each portal opening.
hid = get_coll(HID)
hid.hide_render = True
moved = []
for o in list(sc.objects):
    if not o.name.startswith(('Side gilded panel', 'Side inner moulding', 'Gilt acanthus scroll')):
        continue
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    cx, cy, cz = [sum(p[i] for p in pts) / 8 for i in range(3)]
    if abs(abs(cx) - 15.72) < .25 and 6.8 < cy < 11.2 and cz < 5.2:
        o['doors_original_collections'] = ','.join(c.name for c in o.users_collection)
        for c in list(o.users_collection):
            c.objects.unlink(o)
        hid.objects.link(o)
        moved.append(o.name)
for lc in bpy.context.view_layer.layer_collection.children:
    if lc.name == HID:
        lc.exclude = True

# --- Split the floor-level cornice that ran across both doorways (hall side).
split = []
for o in list(sc.objects):
    if o.name.startswith('Lateral cornice') and abs(o.location.z - .25) < .01 and abs(abs(o.location.x) - 15.65) < .01:
        if o.get('doors_split'):
            continue
        s = 1 if o.location.x > 0 else -1
        o.location.y = (-14 + 8.8) / 2; o.scale.y = 14 + 8.8; o['doors_split'] = 'y -14 to 8.8'
        b = o.copy(); coll.objects.link(b); b.name = 'Door-side cornice return %s' % ('R' if s > 0 else 'L')
        b.location.y = (12.6 + 14) / 2; b.scale.y = 14 - 12.6; b['doors_split'] = 'y 12.6 to 14'
        split.append(o.name)

# --- Build doors.
portal_hinges = []
for s, side in ((1, 'RIGHT'), (-1, 'LEFT')):
    _, hs = doorway('Wing portal %s' % side, s, 16, 10.7, 3.4, 4.4, .45, 6, 8, 14, True)
    portal_hinges += hs
    doorway('Wing end %s' % side, s, 30, 11, 2.6, 3.7, .3, 6, 8, 14, False)

# Opening motion: closed hold, ease open 90 deg into the wing, open hold.
for h, sign in portal_hinges:
    h.animation_data_clear()
    h.rotation_euler.z = 0
    for f in (1, 30):
        h.keyframe_insert('rotation_euler', index=2, frame=f)
    h.rotation_euler.z = sign * math.radians(90)
    h.keyframe_insert('rotation_euler', index=2, frame=78)
    h.rotation_euler.z = 0

# --- Cameras.
def camera(name, p, target, lens):
    d = bpy.data.cameras.new(name); o = bpy.data.objects.new(name, d); coll.objects.link(o)
    o.location = p; o.rotation_euler = (Vector(target) - o.location).to_track_quat('-Z', 'Y').to_euler()
    d.lens = lens; d.clip_end = 400
    return o

camera('CAM 08 | DETAIL - Wing portal door', (10.2, 10.0, 2.0), (16, 10.7, 2.3), 24)
camera('CAM 09 | DETAIL - Inside wing room', (27.2, 10.2, 2.0), (16, 10.9, 2.6), 22)

sc.frame_set(1)
sc['Doors'] = ('Wing portals x=±16: 3.4 x 4.4m double doors, open frames 30-78 via DOOR_HINGE empties. '
               'Wing end walls x=±30: closed decorative doors. Replaced panels in 18x collection.')
result = {
    'door_objects': len(coll.objects),
    'moved_panels': len(moved),
    'split_cornices': split,
    'hinges': [h.name for h, _ in portal_hinges],
    'scene_objects': len(sc.objects),
}
print('DOORS_RESULT', result)
