"""3차 P6: 낮/밤 조명 프리셋 + 움직임(분수 물결, 홀 드리프트 카메라).

조명 컬렉션
- LIGHTING_Shared : 샹들리에 광원(홀 4개를 새 돔 샹들리에 위치로 이동), 복도 랜턴·벽등 보조광
- LIGHTING_Day    : 해·기존 채광 보조광·복도 창 면광원 + 채광창 아래 면광원 2, 뒤 창 면광원
- LIGHTING_Night : 채광창 달빛 2, 벽 랜턴 광원, 촛대 광원, 샹들리에 보강
전환: 텍스트 데이터 'P3_toggle_day_night.py'에서 PRESET 을 'DAY' 또는 'NIGHT'로 바꾸고 Run Script.
재실행하면 P6가 만든 광원만 지우고 다시 만든다(기존 광원은 옮기기만 한다).
"""
import bpy, math
from math import pi
from mathutils import Vector

sc = bpy.context.scene
M = bpy.data.materials


def get_coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name); sc.collection.children.link(c)
    return c


L_SH, L_DAY, L_NIGHT = get_coll('LIGHTING_Shared'), get_coll('LIGHTING_Day'), get_coll('LIGHTING_Night')
for c in (L_SH, L_DAY, L_NIGHT):
    for o in list(c.objects):
        if o.get('p6_created'):
            bpy.data.objects.remove(o, do_unlink=True)


def move_to(o, c):
    if 'p6_from' not in o:
        o['p6_from'] = ','.join(x.name for x in o.users_collection)
    for x in list(o.users_collection):
        x.objects.unlink(o)
    c.objects.link(o)


moved = {'shared': 0, 'day': 0}
hall_warm = []
for o in list(sc.objects):
    if o.type != 'LIGHT' or o.get('p6_created'):
        continue
    if o.name.startswith(('Warm chandelier light', 'LGT_practical_wing')) and abs(o.location.x) > 16:
        # Corridor lights run at full power by day only; dimmer night copies are made below.
        move_to(o, L_DAY); moved['day'] += 1
    elif o.name.startswith(('Warm chandelier light', 'LGT_practical_wing')):
        move_to(o, L_SH); moved['shared'] += 1
        if o.name.startswith('Warm chandelier light') and abs(o.location.x) < 1:
            hall_warm.append(o)
    else:
        move_to(o, L_DAY); moved['day'] += 1

# Hall chandelier lights follow the new dome chandeliers (two per chandelier, lower and upper tier).
hall_warm.sort(key=lambda o: -o.location.y)
targets = [(0, .6, 8.3), (0, -.6, 9.4), (0, -27.4, 8.3), (0, -28.6, 9.4)]
for o, t in zip(hall_warm, targets):
    if 'p6_original_location' not in o:
        o['p6_original_location'] = list(o.location)
    o.location = t; o.data.energy = 1500; o.data.shadow_soft_size = .8


def light(coll, name, kind, loc, energy, color, rot=(0, 0, 0), size=None, size_y=None, soft=None, purpose=''):
    d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = color
    if kind == 'AREA':
        d.shape = 'RECTANGLE'; d.size = size; d.size_y = size_y
    if soft is not None and kind in {'POINT', 'SPOT'}:
        d.shadow_soft_size = soft
    o = bpy.data.objects.new(name, d); coll.objects.link(o)
    o.location = loc; o.rotation_euler = rot
    o['p6_created'] = True; o['purpose'] = purpose
    return o


# ---- Day
for tag, cy in (('rear', 0.0), ('front', -28.0)):
    light(L_DAY, 'LGT_key_day_skylight_%s' % tag, 'AREA', (0, cy, 14.6), 6000, (.85, .92, 1), size=8, size_y=7,
          purpose='Daylight falling through the dome skylight onto the fountain/salon floor')
light(L_DAY, 'LGT_fill_day_rear_window', 'AREA', (0, 13.2, 6.7), 2500, (.8, .88, 1), rot=(-pi / 2, 0, 0), size=5.5, size_y=9,
      purpose='Daylight from the tall rear window, back-lighting the stair and angel')

# ---- Night
for tag, cy in (('rear', 0.0), ('front', -28.0)):
    light(L_NIGHT, 'LGT_night_moon_skylight_%s' % tag, 'AREA', (0, cy, 14.6), 400, (.35, .45, .9), size=8, size_y=7,
          purpose='Faint moonlight through the skylight; keeps the dome readable')
    light(L_NIGHT, 'LGT_night_chandelier_boost_%s' % tag, 'POINT', (0, cy, 8.8), 2500, (1, .72, .42), soft=1.2,
          purpose='Chandelier as the night key')
for o in [o for o in L_DAY.objects if o.type == 'LIGHT' and abs(o.location.x) > 16
          and o.name.startswith(('Warm chandelier light', 'LGT_practical_wing'))]:
    chand = o.name.startswith('Warm chandelier light')
    d = o.data.copy(); d.name = 'LGT_night_corridor_' + o.name
    d.energy = o.data.energy * (.35 if chand else .5); d.color = (1, .68, .38)
    n = bpy.data.objects.new('LGT_night_corridor_' + o.name, d); L_NIGHT.objects.link(n)
    n.matrix_world = o.matrix_world.copy(); n['p6_created'] = True
    n['purpose'] = 'Dimmer night version of the corridor ' + ('chandelier' if chand else 'lantern helper')
for s in (1, -1):
    for y in (-36, -26, -16, -3, 7):
        light(L_NIGHT, 'LGT_night_lantern_upper_%s_%d' % ('R' if s > 0 else 'L', y), 'POINT', (s * 15.3, y, 8.25), 90, (1, .76, .45), soft=.15,
              purpose='Wall lantern practical (upper tier)')
        if y < 7:
            light(L_NIGHT, 'LGT_night_lantern_lower_%s_%d' % ('R' if s > 0 else 'L', y), 'POINT', (s * 15.3, y, 2.85), 90, (1, .76, .45), soft=.15,
                  purpose='Wall lantern practical (lower tier)')
    for z in (8.25, 2.85):
        light(L_NIGHT, 'LGT_night_rear_lantern_%s_%.1f' % ('R' if s > 0 else 'L', z), 'POINT', (s * 4.1, 13.3, z), 90, (1, .76, .45), soft=.15,
              purpose='Rear wall lantern practical')
    for y in (-7.0, -4.0, -35.0, -32.0):
        light(L_NIGHT, 'LGT_night_candelabrum_%s_%.0f' % ('R' if s > 0 else 'L', y), 'POINT', (s * 15.25, y, 1.95), 45, (1, .7, .4), soft=.2,
              purpose='Standing candelabrum practical')
    light(L_NIGHT, 'LGT_night_entrance_candelabrum_%s' % ('R' if s > 0 else 'L'), 'POINT', (s * 5.5, -41.0, 1.95), 45, (1, .7, .4), soft=.2,
          purpose='Entrance candelabrum practical')

# ---- Worlds and window/skylight glow for the two presets
for name, col in (('P3 world day', (.5, .55, .62)), ('P3 world night', (.015, .02, .045))):
    w = bpy.data.worlds.get(name) or bpy.data.worlds.new(name)
    w.color = col
rear_glass = bpy.data.objects.get('Central azure window')
dg = M.get('P3 window daylight glass')
if rear_glass and dg:
    rear_glass.material_slots[0].link = 'OBJECT'; rear_glass.material_slots[0].material = dg

TOGGLE = '''import bpy
PRESET = 'DAY'   # 'DAY' or 'NIGHT' -> Run Script

sc = bpy.context.scene
day = PRESET.upper() == 'DAY'


def find(layer, name):
    for c in layer.children:
        if c.name == name:
            return c
        r = find(c, name)
        if r:
            return r


root = bpy.context.view_layer.layer_collection
find(root, 'LIGHTING_Day').exclude = not day
find(root, 'LIGHTING_Night').exclude = day
sc.world = bpy.data.worlds['P3 world day' if day else 'P3 world night']
for mat_name, day_vals, night_vals in (
        ('P3 skylight sky', ((.55, .76, .96, 1), (.62, .8, 1, 1), 1.6), ((.03, .05, .12, 1), (.06, .09, .22, 1), .35)),
        ('P3 window daylight glass', ((.6, .78, .95, 1), (.62, .8, 1, 1), 1.2), ((.03, .05, .12, 1), (.05, .08, .2, 1), .25))):
    m = bpy.data.materials.get(mat_name)
    if m:
        p = m.node_tree.nodes.get('Principled BSDF')
        base, emit, strength = day_vals if day else night_vals
        p.inputs['Base Color'].default_value = base
        p.inputs['Emission Color'].default_value = emit
        p.inputs['Emission Strength'].default_value = strength
sc['P3 lighting preset'] = 'DAY' if day else 'NIGHT'
'''
txt = bpy.data.texts.get('P3_toggle_day_night.py') or bpy.data.texts.new('P3_toggle_day_night.py')
txt.from_string(TOGGLE)


def apply_preset(preset):
    code = TOGGLE.replace("PRESET = 'DAY'", "PRESET = '%s'" % preset)
    exec(compile(code, 'P3_toggle_day_night', 'exec'), {})


# ---- Motion: fountain water ripple flow (linear, 1-250)
prefs = bpy.context.preferences.edit
old_interp = prefs.keyframe_new_interpolation_type
prefs.keyframe_new_interpolation_type = 'LINEAR'
try:
    wm = M['Fountain water']; nt = wm.node_tree
    pr = nt.nodes.get('Principled BSDF')
    noise = nt.nodes.get('P6 ripple noise')
    if noise is None:
        noise = nt.nodes.new('ShaderNodeTexNoise'); noise.name = 'P6 ripple noise'
        bump = nt.nodes.new('ShaderNodeBump'); bump.name = 'P6 ripple bump'
        noise.noise_dimensions = '4D'
        noise.inputs['Scale'].default_value = 6; noise.inputs['Detail'].default_value = 2
        bump.inputs['Strength'].default_value = .35; bump.inputs['Distance'].default_value = .02
        nt.links.new(noise.outputs['Fac'], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], pr.inputs['Normal'])
    w_in = noise.inputs['W']
    if nt.animation_data:
        nt.animation_data_clear()
    w_in.default_value = 0.0; w_in.keyframe_insert('default_value', frame=1)
    w_in.default_value = 6.0; w_in.keyframe_insert('default_value', frame=250)

    # ---- Motion: slow dolly camera in the hall, easing into a rest on the stair and fountain
    prefs.keyframe_new_interpolation_type = 'BEZIER'
    C_CAM = get_coll('43 | P3 - Motion cameras')
    for o in list(C_CAM.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    tgt = bpy.data.objects.new('CAM 12 target | fountain and stair', None); C_CAM.objects.link(tgt)
    tgt.location = (0, 7.0, 5.2); tgt.empty_display_size = .5
    cd = bpy.data.cameras.new('CAM 12 | P3 - Hall drift (animated)')
    cam = bpy.data.objects.new(cd.name, cd); C_CAM.objects.link(cam)
    cd.lens = 16; cd.clip_end = 400
    con = cam.constraints.new('TRACK_TO'); con.target = tgt; con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'
    cam.location = (-1.2, -15.5, 2.4); cam.keyframe_insert('location', frame=1)
    cam.location = (1.0, -10.5, 3.2); cam.keyframe_insert('location', frame=220)
finally:
    prefs.keyframe_new_interpolation_type = old_interp

sc.frame_start, sc.frame_end = 1, 250
apply_preset('DAY')
sc.camera = bpy.data.objects['CAM 11 | P3 - Reference front view']
sc.frame_set(1)

result = {
    'moved_existing_lights': moved,
    'hall_chandelier_lights_repositioned': len(hall_warm),
    'day_lights': len([o for o in L_DAY.objects if o.type == 'LIGHT']),
    'night_lights': len([o for o in L_NIGHT.objects if o.type == 'LIGHT']),
    'shared_lights': len([o for o in L_SH.objects if o.type == 'LIGHT']),
    'toggle_text': txt.name,
    'preset': sc.get('P3 lighting preset'),
    'active_camera': sc.camera.name,
}
print('P3_P6_RESULT', result)
