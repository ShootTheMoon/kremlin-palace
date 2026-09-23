import bpy, math
from math import sin, cos, pi
from mathutils import Vector
from pathlib import Path

root = Path(bpy.data.filepath).parent
sc = bpy.context.scene
original_objects = list(sc.objects)
original_collections = {c.name: list(c.objects) for c in bpy.data.collections}
white=bpy.data.materials['Ivory marble'];gold=bpy.data.materials['Antique gilded bronze']
blue=bpy.data.materials['Sapphire stone'];velvet=bpy.data.materials['Royal blue velvet']
dark=bpy.data.materials['Wrought iron'];glass=bpy.data.materials['Pale azure glazing']
bulb=bpy.data.materials['Candle light']
# Load only reusable geometry functions, never the scene reset/build statements.
source=(root/'build_palace.py').read_text(encoding='utf-8')
helpers=source[source.index('cache={}'):source.index("section('01 | Marble architecture')")]
exec(helpers)
def clone(o,dy=-28):
    n=o.copy();coll.objects.link(n);n.name='Forehall | '+o.name
    n.location.y+=dy
    return n

section('11 | NEW HALF - Forehall architecture')
for o in original_collections['01 | Marble architecture']:
    if o.name.startswith(('Foundation','Polished checkerboard','Lateral cornice','Side gilded panel','Side inner moulding')):
        clone(o)
    elif o.name.startswith('Gilt acanthus scroll') and abs(o.location.x)>15:
        clone(o)
    elif o.name.startswith(('Square pedestal','Column base and capital','Sapphire column shaft','Gilded collar')) and abs(abs(o.location.x)-11.8)<.01 and o.location.y<13:
        clone(o)
for x in [-16,16]:box('Forehall solid side wall',(x,-28,6),(.45,28,12),white)

section('12 | NEW HALF - Continuous upper galleries')
for o in original_collections['03 | Upper galleries and twin stairs']:
    if o.name.startswith(('Upper promenade','Sapphire gallery runner','Runner gold edge','Gallery filigree')):clone(o)
for side in [-1,1]:
    box('Entrance balcony marble deck',(side*9.7,-40.3,4.95),(12.6,3.4,.3),white)
    box('Entrance balcony carpet',(side*9.7,-40.3,5.12),(12,2.8,.03),velvet)
    railing('Entrance balcony railing',[(side*(3.5+i*.4),-38.58,5.12) for i in range(21)])
    railing('Entrance balcony inner return',[(side*3.45,-38.6-i*.4,5.12) for i in range(9)])

section('13 | NEW HALF - Furnished reception salons')
for o in original_collections['07 | Salon furniture']:clone(o)

section('14 | NEW HALF - Ceiling and chandeliers')
for name in ['05 | Coffered ceiling crown','10 | Removable ornamental ceiling']:
    for o in original_collections[name]:
        if any(t in o.name for t in ['ceiling','Ceiling','medallion']):clone(o)
chandelier(0,-25,9,2.2);chandelier(0,-36,9.2,1.65)
for y in [-20,-28,-36]:
    light('Forehall daylight fill',(-7,y,10),2200,(.8,.88,1),4)
    light('Forehall warm bounce',(8,y,8),1700,(1,.85,.66),4)

section('15 | COMPLETE - Monumental entrance facade')
# Front wall closes the previously missing end. Centre remains a real door opening.
for side in [-1,1]:box('Entrance wall wing',(side*9.7,-42,6),(12.6,.5,12),white)
box('Entrance overdoor wall',(0,-42,10.8),(6.8,.5,2.4),white)
for z in [.25,4.78,5.1,10.85,11.6,12]:
    if z<10:
        for side in [-1,1]:box('Entrance facade cornice',(side*9.7,-41.62,z),(12.6,.22,.13),gold)
    else:box('Entrance facade cornice',(0,-41.62,z),(32,.22,.13),gold)
for x in [-15.2,-11.4,-7.6,-3.4,3.4,7.6,11.4,15.2]:column(x,-41.2)
# Two gilded door leaves at original human/architectural scale.
for side in [-1,1]:
    hinge=bpy.data.objects.new('Entrance door hinge LEFT' if side<0 else 'Entrance door hinge RIGHT',None)
    coll.objects.link(hinge);hinge.location=(side*3.05,-41.9,0)
    parts=[]
    parts.append(box('Royal double door leaf',(side*1.525,-41.8,4.6),(3.02,.20,9.2),blue))
    before=set(sc.objects)
    for z,h in [(2.25,3.55),(6.4,3.5)]:
        frame('Entrance door raised panel',side*1.525,-41.63,z,2.5,h)
        frame('Entrance door inner bead',side*1.525,-41.56,z,2.27,h-.25)
        flourish(side*1.525,-41.48,z+h*.3,.43)
    parts.extend(set(sc.objects)-before)
    parts.append(ball('Door bronze handle',(side*.28,-41.38,4.2),(.085,.10,.085),gold))
    for o in parts:
        world=o.matrix_world.copy();bpy.context.view_layer.update();world=o.matrix_world.copy()
        o.parent=hinge;o.matrix_world=world
    hinge['Open angle degrees']='Rotate local Z to open this door leaf'
for rr in [3.12,3.3]:
    line('Entrance semicircular arch',[(rr*cos(t),-41.5,6.2+rr*sin(t)) for t in [i*pi/64 for i in range(65)]],.10,gold)
for x in [-3.15,3.15]:box('Entrance arch jamb',(x,-41.48,3.1),(.18,.22,6.2),gold)
# Wall bays combine high arched glazing, drapes, lower panels and sconces.
for x in [-13.3,-9.5,-5.65,5.65,9.5,13.3]:
    frame('Entrance lower moulding',x,-41.64,2.45,3.0,3.55)
    frame('Entrance upper moulding',x,-41.64,8.45,3.05,5.2)
    flourish(x,-41.48,3.75,.5)
    box('Entrance window glazing',(x,-41.62,8.2),(2.15,.10,3.45),glass)
    frame('Window rectangular gilding',x,-41.48,8.15,2.2,3.5)
    line('Window arch crest',[(x+1.1*cos(t),-41.45,9.9+1.1*sin(t)) for t in [i*pi/32 for i in range(33)]],.055,gold)
    for dx in [-.55,0,.55]:box('Window vertical bars',(x+dx,-41.40,8.15),(.035,.07,3.5),gold)
    for zz in [7.1,8.0,8.9,9.8]:box('Window transom',(x,-41.40,zz),(2.2,.07,.035),gold)
    for side in [-1,1]:
        for j in range(4):
            cyl('Sapphire curtain pleat',(x+side*(1.16+j*.09),-41.18,8.45),.09,4.5,velvet)
        line('Gold curtain tie',[(x+side*(1.1+t*.38),-41.04,7.6-.1*sin(t*pi)) for t in [i/12 for i in range(13)]],.03,gold)
    for dx in [-.24,0,.24]:
        line('Entrance sconce arm',[(x,-41.3,2.4),(x+dx,-41.0,2.7),(x+dx,-40.85,3)],.035,gold)
        cyl('Entrance sconce candle',(x+dx,-40.85,3.17),.045,.3,white)
        ball('Entrance sconce flame',(x+dx,-40.85,3.4),(.055,.055,.11),bulb)

section('16 | COMPLETE - Imperial standards and guards')
for x in [-5,5]:
    cyl('Standard pedestal',(x,-37.8,.16),.36,.32,white)
    cyl('Standard gold pole',(x,-37.8,2.5),.045,4.8,gold)
    ball('Standard finial',(x,-37.8,5),(.10,.10,.22),gold)
    box('Blue imperial standard',(x,-37.73,3.2),(1.25,.04,2.8),velvet)
    frame('Standard gilt border',x,-37.67,3.2,1.12,2.67)
    flourish(x,-37.61,3.2,.31)
for x in [-13.5,13.5]:
    box('Guard statue base',(x,-36,.14),(.9,.8,.28),white)
    for dx in [-.16,.16]:
        ball('Armour greave',(x+dx,-36,.73),(.13,.15,.5),dark)
        ball('Armour boot',(x+dx,-35.91,.32),(.14,.26,.11),dark)
    ball('Armour breastplate',(x,-36,1.48),(.36,.22,.5),dark)
    ball('Armour helm',(x,-36,2.15),(.23,.22,.3),dark)
    line('Helmet golden visor',[(x-.19,-35.79,2.15),(x+.19,-35.79,2.15)],.025,gold)
    for dx in [-.42,.42]:ball('Armour shoulder',(x+dx,-36,1.74),(.2,.18,.16),dark)
    ball('Heraldic shield',(x-.4,-35.75,1.15),(.28,.085,.48),blue)
    line('Guard spear',[(x+.5,-36,.28),(x+.5,-36,2.85)],.025,gold)

section('17 | COMPLETE - Cameras')
def camera(name,p,target,lens):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);coll.objects.link(o)
    o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=400
    return o
front=camera('CAM 04 | NEW HALF - Entrance facade',(0,-16,6.6),(0,-41,6),24)
camera('CAM 05 | COMPLETE - Long axis',(0,-39,3.8),(0,8,5.2),25)
camera('CAM 06 | COMPLETE - Map overview',(63,-86,70),(0,-14,0),42)
camera('CAM 07 | NEW HALF - Balcony',(-10,-19,7.2),(0,-40,5),25)
sc.camera=front
sc['Design']='Completed two-half palace: original stair hall plus a full 28m reception forehall, enclosed monumental entrance, continuous galleries and ceilings. Object scale unchanged.'
sc['Hall dimensions metres']='32 x 56 x 12; extension y=-42 to -14; original y=-14 to 14'
sc['Navigation']='Ground 0m / gallery 5.12m. Door leaves have editable hinge objects. No gameplay collision or navigation mesh.'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.clip_end=400
            area.spaces.active.shading.type='MATERIAL'
sc.render.engine='BLENDER_EEVEE';sc.eevee.taa_render_samples=16
sc.render.resolution_x=1000;sc.render.resolution_y=700;sc.render.resolution_percentage=100
sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG'
bpy.context.view_layer.update()
assert abs(bpy.data.objects['Foundation'].scale.x - 32.4) < .001
assert len([o for o in sc.objects if o.name.startswith('Forehall | Polished checkerboard')])==2
bpy.ops.wm.save_as_mainfile(filepath=str(root/'Kremlin_Grand_Palace_COMPLETE.blend'))
bpy.ops.export_scene.gltf(filepath=str(root/'Kremlin_Grand_Palace_COMPLETE.glb'),export_format='GLB',export_cameras=True,export_lights=True)
print('COMPLETE_VERIFIED',len(sc.objects),'objects; 32x56x12m; no uniform scale applied')
sc.render.filepath=str(root/'palace-complete-entrance.png')
bpy.ops.render.render(write_still=True)
# Inspection render only: reveal enclosed rooms without changing the saved scene.
sc.camera=bpy.data.objects['CAM 06 | COMPLETE - Map overview']
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.color_type='MATERIAL';sc.display.shading.light='STUDIO'
for o in sc.objects:
    if any(t in o.name.lower() for t in ['ceiling','medallion']):o.hide_render=True
sc.render.filepath=str(root/'palace-complete-map.png')
bpy.ops.render.render(write_still=True)
