import bpy, math
from math import sin,cos,pi
from mathutils import Vector
coll=bpy.data.collections.new('10 | Removable ornamental ceiling');bpy.context.scene.collection.children.link(coll)
gold=bpy.data.materials['Antique gilded bronze'];blue=bpy.data.materials['Sapphire stone'];white=bpy.data.materials['Ivory marble'];dark=bpy.data.materials['Wrought iron']
def line(n,pts,r,m,closed=False):
 c=bpy.data.curves.new(n,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=2;s=c.splines.new('POLY');s.points.add(len(pts)-1)
 for p,v in zip(s.points,pts):p.co=(*v,1)
 s.use_cyclic_u=closed;o=bpy.data.objects.new(n,c);coll.objects.link(o);c.materials.append(m);return o
def box(n,p,scale,m):
 src=next(o for o in bpy.data.objects if o.type=='MESH' and o.data.name.startswith('Cube') and o.data.materials and o.data.materials[0]==m)
 o=bpy.data.objects.new(n,src.data);coll.objects.link(o);o.location=p;o.scale=scale;return o
roofmat=white.copy();roofmat.name='Ceiling ivory single sided';roofmat.use_backface_culling=True
me=bpy.data.meshes.new('Downward facing ceiling');me.from_pydata([(-12,-14,12.32),(-12,14,12.32),(12,14,12.32),(12,-14,12.32)],[],[(0,1,2,3)])
o=bpy.data.objects.new('Removable ceiling skin',me);coll.objects.link(o);me.materials.append(roofmat)
# layered blue and gold oval bands
for rr in [1,.96,.87,.83,.72]:
 line('Ceiling concentric relief',[(11*rr*cos(t),12.2*rr*sin(t),12.07) for t in [i*2*pi/96 for i in range(96)]],.09 if rr in [1,.87] else .055,gold,True)
# central star and radiating scrolling petals
for i in range(12):
 a=i*2*pi/12
 pts=[]
 for j in range(65):
  t=j*2*pi/64;r=3.4+2.3*cos(t)
  pts.append((r*cos(a)-.85*sin(t)*sin(a),r*sin(a)+.85*sin(t)*cos(a),12.04))
 line('Ceiling rosette petal',pts,.065,gold,True)
line('Ceiling central medallion',[(1.3*cos(t),1.3*sin(t),12) for t in [i*2*pi/64 for i in range(64)]],.12,gold,True)
for x in [-13.5,13.5]:
 for y in [-10,-5,0,5,10]:
  for dx in [-1.2,1.2]:line('Gallery ceiling coffer',[(x+dx,y-2,11.96),(x+dx,y+2,11.96)],.045,gold)
  for dy in [-2,2]:line('Gallery ceiling coffer',[(x-1.2,y+dy,11.96),(x+1.2,y+dy,11.96)],.045,gold)
# remove rail crossing stair exits; rebuild three separate segments
for o in list(bpy.data.objects):
 if o.name.startswith('Rear landing rail'):bpy.data.objects.remove(o,do_unlink=True)
for lo,hi in [(-11.3,-4.5),(-3.05,3.05),(4.5,11.3)]:
 for zz in [5.28,6.17]:line('Landing gilt safety rail',[(lo,8.18,zz),(hi,8.18,zz)],.045,gold)
 for i in range(int((hi-lo)/.4)+1):
  x=lo+i*.4
  line('Landing iron upright',[(x,8.18,5.28),(x,8.18,6.17)],.023,dark)
# small bridge extensions under final stair treads
for side in [-1,1]:box('Stair to landing bridge',(side*3.8,7.5,4.95),(1.35,1.5,.3),white)
# procedural marble detail in editable Blender materials
for name in ['Ivory marble','Sapphire stone']:
 m=bpy.data.materials[name];nt=m.node_tree;p=nt.nodes.get('Principled BSDF')
 n=nt.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=4;n.inputs['Detail'].default_value=3;n.inputs['Roughness'].default_value=.7
 b=nt.nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=.13;b.inputs['Distance'].default_value=.04
 nt.links.new(n.outputs['Fac'],b.inputs['Height']);nt.links.new(b.outputs['Normal'],p.inputs['Normal'])
sc=bpy.context.scene
sc['Design']='Reference-inspired palace map. Ceiling skin is single-sided for top-down GLB inspection; collection 10 can be hidden for Blender dollhouse views.'
result={'objects':len(bpy.data.objects),'ceiling':'single-sided removable','stair_exit_openings':True}
sc.eevee.taa_render_samples=8
sc.render.resolution_x=1000
sc.render.resolution_y=700
bpy.data.objects['CAM 02 | Dollhouse'].data.lens=28
