import bpy, math
from mathutils import Vector
from math import sin,cos,pi
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
def mat(n,c,metal=0,rough=.35,emit=0):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if emit:p.inputs['Emission Color'].default_value=(*c,1);p.inputs['Emission Strength'].default_value=emit
 return m
white=mat('Ivory marble',(.83,.87,.91))
gold=mat('Antique gilded bronze',(.72,.46,.12),.72,.23)
blue=mat('Sapphire stone',(.055,.16,.34),.15)
velvet=mat('Royal blue velvet',(.035,.12,.29),0,.8)
dark=mat('Wrought iron',(.025,.035,.055),.7)
tile=mat('Blue grey marble',(.30,.40,.53),.05,.25)
glass=mat('Pale azure glazing',(.33,.58,.72),.25,.2)
water=mat('Fountain water',(.045,.25,.35),.55,.16)
bulb=mat('Candle light', (1,.66,.26),0,.25,4)
cache={}
coll=None
def section(n):
 global coll
 coll=bpy.data.collections.new(n);bpy.context.scene.collection.children.link(coll)
def obj(n,mesh,loc,scale,ma):
 o=bpy.data.objects.new(n,mesh);coll.objects.link(o);o.location=loc;o.scale=scale
 if len(mesh.materials)==0:mesh.materials.append(ma)
 return o
def primitive(kind,ma):
 key=(kind,ma.name)
 if key not in cache:
  if kind=='box':bpy.ops.mesh.primitive_cube_add(size=1)
  elif kind=='cyl':bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=1,depth=1)
  elif kind=='ball':bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1)
  o=bpy.context.object;me=o.data;me.materials.append(ma)
  if kind!='box':
   for p in me.polygons:p.use_smooth=True
  bpy.data.objects.remove(o,do_unlink=True);cache[key]=me
 return cache[key]
def box(n,p,s,m):return obj(n,primitive('box',m),p,s,m)
def cyl(n,p,r,h,m):return obj(n,primitive('cyl',m),p,(r,r,h),m)
def ball(n,p,s,m):return obj(n,primitive('ball',m),p,s,m)
def line(n,pts,r,m,closed=False):
 cu=bpy.data.curves.new(n,'CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=r;cu.bevel_resolution=2
 sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
 for v,p in zip(sp.points,pts):v.co=(*p,1)
 sp.use_cyclic_u=closed
 o=bpy.data.objects.new(n,cu);coll.objects.link(o);cu.materials.append(m);return o
def ring(n,x,y,z,rx,ry,r,m):
 return line(n,[(x+rx*cos(i*2*pi/64),y+ry*sin(i*2*pi/64),z) for i in range(64)],r,m,True)
def frame(n,x,y,z,w,h,m=gold):
 for dx in [-w/2,w/2]:box(n,(x+dx,y,z),(.055,.09,h),m)
 for dz in [-h/2,h/2]:box(n,(x,y,z+dz),(w,.09,.055),m)
def flourish(x,y,z,w=.65):
 for sign in [-1,1]:
  pts=[]
  for i in range(34):
   t=i/33*2.7*pi;r=w*(1-i/39)
   pts.append((x+sign*(w*.8+r*cos(t)),y,z+r*sin(t)*.45))
  line('Gilt acanthus scroll',pts,.023,gold)
def column(x,y,z=0,h=11.8):
 box('Square pedestal',(x,y,z+.18),(.92,.92,.36),white)
 for zz,r,hh,ma in [(.4,.55,.14,gold),(.62,.45,.30,white),(h-.36,.53,.16,gold),(h-.16,.62,.2,white)]:
  cyl('Column base and capital',(x,y,z+zz),r,hh,ma)
 cyl('Sapphire column shaft',(x,y,z+h/2),.31,h-1,blue)
 for zz in [1.0,2.8,3,5,5.16,h-1,h-.7]:cyl('Gilded collar',(x,y,z+zz),.35,.1,gold)
def railing(n,points):
 line(n+' top rail',[(x,y,z+1.05) for x,y,z in points],.055,gold)
 line(n+' bottom rail',[(x,y,z+.13) for x,y,z in points],.035,dark)
 for i,(x,y,z) in enumerate(points):
  cyl(n+' baluster',(x,y,z+.57),.026,.92,dark)
  if i<len(points)-1:
   a=Vector(points[max(0,i-1)]);b=Vector(points[min(len(points)-1,i+1)]);d=(b-a).normalized()
   pts=[(x+d.x*.16*sin(t),y+d.y*.16*sin(t),z+.56+.37*cos(t)) for t in [j*2*pi/20 for j in range(21)]]
   line(n+' arabesque',pts,.016,gold)
def light(n,p,power,color,size=1,kind='POINT'):
 d=bpy.data.lights.new(n,kind);d.energy=power;d.color=color
 if kind=='POINT':d.shadow_soft_size=size
 o=bpy.data.objects.new(n,d);coll.objects.link(o);o.location=p
 return o
def chandelier(x,y,z,r=2):
 cyl('Chandelier stem',(x,y,z+1),.1,2.5,gold)
 ball('Chandelier heart',(x,y,z),(.28,.28,.6),gold)
 for zz,rr,num in [(0,r,12),(.85,r*.66,8)]:
  ring('Chandelier tier',x,y,z+zz,rr,rr,.045,gold)
  for i in range(num):
   a=i*2*pi/num
   line('Curled candle arm',[(x+cos(a)*rr*t,y+sin(a)*rr*t,z+zz-.4*sin(pi*t)) for t in [j/12 for j in range(13)]],.045,gold)
   xx=x+cos(a)*rr;yy=y+sin(a)*rr
   cyl('Candle cup',(xx,yy,z+zz+.04),.13,.1,gold)
   cyl('Ivory candle',(xx,yy,z+zz+.27),.055,.4,white)
   ball('Candle flame',(xx,yy,z+zz+.5),(.055,.055,.12),bulb)
   ball('Sapphire crystal drop',(xx,yy,z+zz-.45),(.07,.07,.2),glass)
   a2=a+2*pi/num
   line('Crystal swag',[(x+rr*cos(a+(a2-a)*t),y+rr*sin(a+(a2-a)*t),z+zz-.5*sin(pi*t)) for t in [j/16 for j in range(17)]],.022,gold)
 light('Warm chandelier light',(x,y,z-.4),1000,(1,.78,.49),2)
section('01 | Marble architecture')
# checkerboard as two batched meshes
for parity,ma in [(0,white),(1,tile)]:
 verts=[];faces=[]
 for ix in range(32):
  for iy in range(28):
   if (ix+iy)%2==parity:
    x=ix-16;y=iy-14;k=len(verts);verts.extend([(x,y,0),(x+1,y,0),(x+1,y+1,0),(x,y+1,0)]);faces.append((k,k+1,k+2,k+3))
 me=bpy.data.meshes.new('Checker tiles');me.from_pydata(verts,[],faces);obj('Polished checkerboard',me,(0,0,0),(1,1,1),ma)
box('Foundation',(0,0,-.22),(32.4,28.4,.4),white)
box('Rear palace wall',(0,14,6),(32,.45,12),white)
for x in [-16,16]:
 box('Lateral palace wall',(x,-3,6),(.45,22,12),white)
 box('Wing portal lintel',(x,11,9),(.45,6,6),white)
for z in [.25,4.75,5.1,10.8,11.6,12]:
 box('Rear cornice',(0,13.65,z),(32,.3,.13),gold)
 for x in [-15.65,15.65]:box('Lateral cornice',(x,0,z),(.3,28,.13),gold)
# rear panels
for x in [-14,-10,-6,6,10,14]:
 for z,h in [(2.4,3.5),(8.35,5.0)]:
  box('Recessed wall panel',(x,13.72,z),(3.35,.08,h),white)
  frame('Gold panel moulding',x,13.62,z,3.3,h)
  frame('Inner panel bead',x,13.55,z,3.05,h-.3)
  flourish(x,13.46,z+h/2-.6,.5);flourish(x,13.46,z-h/2+.6,.5)
for side in [-1,1]:
 for y in [-11,-6,-1,4,9]:
  # assemble flat panel then rotate to side
  before=set(bpy.data.objects)
  for z,h in [(2.35,3.6),(8.35,5)]:
   frame('Side gilded panel',0,0,z,4,h);frame('Side inner moulding',0,-.06,z,3.7,h-.3)
   flourish(0,-.15,z+h/2-.55)
  for o in set(bpy.data.objects)-before:
   p=o.location.copy();o.rotation_euler.z=side*pi/2;o.location=(side*15.70-p.y*side,p.x*side+y,p.z)
 for y in [-13,-8,-3,2,7,12]:column(side*11.8,y)
# rear columns
for x in [-15.5,-11.8,-7.8,-3.6,3.6,7.8,11.8,15.5]:column(x,13.35)
section('02 | Royal glazing')
box('Central azure window',(0,13.69,6.7),(6,.12,10),glass)
for x in [-3,-2,-1,0,1,2,3]:box('Window vertical gold mullion',(x,13.5,6.7),(.075,.1,10),gold)
for z in [1.7,2.7,3.7,4.7,5.7,6.7,7.7,8.7,9.7,10.7,11.7]:box('Window horizontal mullion',(0,13.48,z),(6,.1,.065),gold)
for rad in [1.6,1.75]:
 line('Rose window gilded rim',[(rad*cos(i*2*pi/64),13.28,9.6+rad*sin(i*2*pi/64)) for i in range(64)],.075,gold,True)
for i in range(6):
 a=2*pi*i/6
 line('Rose window petal',[(.94*cos(a)+.53*cos(t),13.23,9.6+.94*sin(a)+.53*sin(t)) for t in [j*2*pi/32 for j in range(32)]],.04,gold,True)
section('03 | Upper galleries and twin stairs')
for side in [-1,1]:
 box('Upper promenade',(side*13.7,0,4.95),(4.6,28,.3),white)
 box('Sapphire gallery runner',(side*13.7,0,5.12),(3.5,27.5,.035),velvet)
 for xx in [side*12,side*15.4]:box('Runner gold edge',(xx,0,5.15),(.05,27.5,.025),gold)
 railing('Gallery filigree',[(side*11.38,-13.5+i*.5,5.12) for i in range(55)])
box('Rear landing',(0,11.1,4.95),(23,5.8,.3),white)
box('Rear landing blue carpet',(0,11.2,5.12),(22,4.9,.035),velvet)
railing('Rear landing rail',[(x,8.18,5.12) for x in [-11+i*.5 for i in range(45)] if abs(x)>6.8])
for side in [-1,1]:
 N=32
 for i in range(N):
  a=i*pi/2/N;b=(i+1)*pi/2/N;z=(i+1)*5.12/N
  pts=[(side*(3.8+r*cos(t)),3+r*sin(t),zz) for zz in [0,z] for r,t in [(3.8,a),(6.2,a),(6.2,b),(3.8,b)]]
  me=bpy.data.meshes.new('Curved stair wedge');me.from_pydata(pts,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
  obj('Marble stair tread %s %02d'%(side,i),me,(0,0,0),(1,1,1),white)
  line('Gilt tread nosing',[(side*(3.8+r*cos(a)),3+r*sin(a),z+.006) for r in [3.8,6.2]],.02,gold)
 for r in [3.8,6.2]:
  railing('Curving stair balustrade',[(side*(3.8+r*cos(t)),3+r*sin(t),.16+5.12*t/(pi/2)) for t in [i*pi/2/40 for i in range(41)]])
 for r in [3.8,6.2]:
  x=side*(3.8+r);box('Stair newel pedestal',(x,3,.42),(.45,.45,.84),blue);ball('Newel finial',(x,3,1),(.2,.2,.26),gold)
section('04 | Fountain and winged sculpture')
for z,r,h,ma in [(.12,2.2,.24,gold),(.32,2.12,.28,white),(.5,2.2,.12,gold),(.53,1.96,.045,water),(1,.36,1,white),(1.55,.65,.18,gold),(1.75,1.1,.14,white)]:
 cyl('Fountain basin and pedestal',(0,4,z),r,h,ma)
ring('Fountain rim',0,4,.58,2.12,2.12,.065,gold)
for i in range(16):
 a=2*pi*i/16
 ball('Basin gilded rosette',(2.12*cos(a),4+2.12*sin(a),.32),(.095,.095,.095),gold)
for i in range(8):
 a=i*2*pi/8
 line('Sculpted water jet',[(cos(a)*(.8+t),4+sin(a)*(.8+t),1.82+1.1*t-2.3*t*t) for t in [j/24 for j in range(25)]],.026,glass)
box('Statue plinth',(0,4,2.1),(.66,.66,.65),white)
ball('Draped angel body',(0,4,3),(.33,.27,.8),white)
ball('Angel head',(0,4,3.95),(.22,.2,.27),white)
for side in [-1,1]:
 line('Angel arm',[(side*.22,4,3.52),(side*.47,3.98,3.35),(side*.58,3.92,3.62)],.09,white)
 for j in range(9):
  x=side*(.35+j*.105);z=3.65-j*.08
  ob=ball('Carved angel wing feather',(x,4.13,z),(.13,.11,.62-j*.025),white);ob.rotation_euler.y=side*(.3+j*.06)
section('05 | Coffered ceiling crown')
# Open centre permits dollhouse inspection; raised perimeter and ornamental oval
for x in [-14,14]:box('Gallery ceiling',(x,0,12.15),(4,28,.22),white)
box('Rear ceiling',(0,12,12.15),(24,4,.22),white)
for r,ma in [(1,blue),(.97,gold),(.93,white),(.90,gold)]:
 ring('Oval ceiling cornice',0,0,12.15,11.2*r,12.4*r,.12 if ma==blue else .055,ma)
for i in range(24):
 a=i*2*pi/24
 line('Ceiling floral petal',[(8.8*cos(a)+1.0*cos(t)*cos(a)-.45*sin(t)*sin(a),9.8*sin(a)+1*cos(t)*sin(a)+.45*sin(t)*cos(a),12.17) for t in [j*2*pi/32 for j in range(32)]],.045,gold,True)
section('06 | Chandeliers and sconces')
chandelier(0,3,9,2.2);chandelier(0,-8,9.2,1.65)
for x in [-14,-10,-6,6,10,14]:
 for z in [2.8,8.3]:
  for dx in [-.22,0,.22]:
   line('Wall sconce arm',[(x,13.3,z-.25),(x+dx,12.98,z),(x+dx,12.92,z+.2)],.035,gold)
   cyl('Sconce candle',(x+dx,12.92,z+.35),.04,.28,white)
   ball('Sconce flame',(x+dx,12.92,z+.52),(.045,.045,.09),bulb)
section('07 | Salon furniture')
def chair(x,y,a):
 before=set(bpy.data.objects)
 cyl('Blue velvet seat',(0,0,.6),.38,.16,velvet)
 for xx in [-.27,.27]:
  for yy in [-.24,.24]:line('Gilded chair leg',[(xx,yy,.55),(xx*1.2,yy*1.2,.06)],.04,gold)
 ball('Oval upholstered back',(0,.27,1.17),(.33,.08,.43),velvet)
 line('Oval chair gilt frame',[(.36*cos(t),.28,1.17+.47*sin(t)) for t in [j*2*pi/36 for j in range(36)]],.045,gold,True)
 for o in set(bpy.data.objects)-before:
  p=o.location.copy();o.location=(x+p.x*cos(a)-p.y*sin(a),y+p.x*sin(a)+p.y*cos(a),p.z);o.rotation_euler.z+=a
for x in [-7,7]:
 for y in [-8,-3]:
  cyl('Blue salon rug',(x,y,.025),2.1,.035,velvet);ring('Rug gilded border',x,y,.05,2.03,2.03,.025,gold)
  cyl('Marble tea table',(x,y,.92),.83,.1,white);ring('Table gilt rim',x,y,.96,.84,.84,.035,gold);cyl('Table pedestal',(x,y,.45),.12,.9,gold)
  for a in [0,pi/2,pi,3*pi/2]:chair(x+1.35*sin(a),y+1.35*cos(a),-a)
for side in [-1,1]:
 x=side*13.4
 for y in [-9,0,9]:
  box('Gallery settee blue cushion',(x,y,5.65),(1.1,2.1,.25),velvet)
  box('Gallery settee back',(x+side*.45,y,6.1),(.18,2.15,.95),velvet)
  for dy in [-.85,.85]:
   for dx in [-.4,.4]:cyl('Settee gold foot',(x+dx,y+dy,5.37),.055,.5,gold)
section('08 | Lateral ceremonial wings')
for side in [-1,1]:
 x=side*23
 box('Wing marble floor',(x,11,-.12),(14,6,.24),white)
 box('Wing outer wall',(x,14,3),(14,.3,6),white)
 box('Wing front wall',(x,8,3),(14,.3,6),white)
 box('Wing end wall',(side*30,11,3),(.3,6,6),white)
 box('Wing sapphire runner',(x,11,.03),(13.5,2.5,.035),velvet)
 for xx in [side*(17.5+3*j) for j in range(4)]:
  box('Wing azure window',(xx,13.78,3),(1.8,.12,3.8),glass)
  frame('Wing window gilding',xx,13.65,3,1.8,3.8)
  for dx in [-.45,0,.45]:box('Wing window mullion',(xx+dx,13.58,3),(.04,.08,3.8),gold)
  for zz in [1.5,2.3,3.1,3.9,4.7]:box('Wing window transom',(xx,13.56,zz),(1.8,.08,.04),gold)
  column(xx+1.25,13.5,0,5.8)
 for xx in [side*20,side*26]:chandelier(xx,11,4.5,.7)
section('09 | Cameras and lighting')
sc=bpy.context.scene
def camera(n,p,target,lens):
 d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);coll.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=300;return o
sc.camera=camera('CAM 01 | Grand hall',(0,-18.5,5.8),(0,6,6),22)
camera('CAM 02 | Dollhouse',(39,-46,40),(0,3,2.5),43)
camera('CAM 03 | Upper gallery',(-10,0,7),(0,5,3.5),25)
light('Daylight key',(-8,-3,11),2400,(.73,.84,1),5)
light('Daylight fill',(9,7,10),2600,(.82,.9,1),4)
light('Entrance bounce',(0,-12,7),1800,(1,.9,.76),5)
sun=light('Soft sun',(0,0,16),1.5,(1,.92,.8),kind='SUN');sun.rotation_euler=(.3,-.4,-.3);sun.data.angle=.35
sc.world=bpy.data.worlds.new('Palace ambient')
sc.world.color=(.3,.3,.3)
sc.render.engine='BLENDER_EEVEE'
sc.render.resolution_x=1200;sc.render.resolution_y=800;sc.render.resolution_percentage=100
sc.render.image_settings.media_type='IMAGE';sc.render.image_settings.file_format='PNG'
sc['Design']='Reference-inspired Kremlin Grand Palace fantasy interior; dimensions inferred in metres. Open roof for map inspection.'
sc['Navigation']='Ground floor 0m / gallery 5.12m. Twin curved staircases and rear landing.'
result={'objects':len(bpy.data.objects),'collections':len(bpy.data.collections),'hall_metres':[32,28,12],'cameras':[o.name for o in bpy.data.objects if o.type=='CAMERA']}
