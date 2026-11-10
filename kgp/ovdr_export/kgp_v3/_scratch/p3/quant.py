# -*- coding: utf-8 -*-
import bpy, sys, os, math
argv = sys.argv[sys.argv.index('--')+1:]
code_path = argv[0]; px = int(argv[1]) if len(argv)>1 else 512
mode = argv[2] if len(argv)>2 else 'probe'   # probe | final
outp = argv[3] if len(argv)>3 else 'none'
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.cycles.samples=1
bpy.ops.mesh.primitive_plane_add(size=1, location=(0,0,0))
ob = bpy.context.active_object
mat = bpy.data.materials.new('M'); ob.data.materials.append(mat)
g = {'bpy': bpy, 'math': math, 'mat': mat}
exec(open(code_path,'r',encoding='utf-8').read(), g)
nt = mat.node_tree
if mode == 'probe':
    rmp = [n for n in nt.nodes if n.type=='VALTORGB'][0]
    src = [l.from_socket for l in nt.links if l.to_node is rmp and l.to_socket.name=='Fac'][0]
    bs  = [n for n in nt.nodes if n.type=='BSDF_PRINCIPLED'][0]
    for l in list(nt.links):
        if l.to_node is bs and l.to_socket.name=='Base Color': nt.links.remove(l)
    nt.links.new(src, bs.inputs['Base Color'])
fb = (mode=='probe')
img = bpy.data.images.new('bk', px, px, alpha=False, float_buffer=fb)
if fb: img.colorspace_settings.name='Non-Color'
tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img
for n in nt.nodes: n.select=False
tex.select=True; nt.nodes.active=tex
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, use_clear=True, margin=16)
if outp != 'none':
    img.filepath_raw = outp; img.file_format='PNG'; img.save()
p=list(img.pixels); n=px*px
if mode=='probe':
    v=sorted(p[0::4]); mean=sum(v)/n; sd=(sum((x-mean)**2 for x in v)/n)**0.5
    print("=== QUANT n=%d mean %.4f sd %.4f min %.4f max %.4f" % (n, mean, sd, v[0], v[-1]))
    print("  " + " ".join("p%s=%.4f"%(("%.1f"%(q*100)).rstrip('0').rstrip('.'), v[min(n-1,int(q*n))])
        for q in (0.002,0.005,0.01,0.02,0.05,0.10,0.25,0.35,0.50,0.65,0.75,0.90,0.95,0.98,0.995,0.999)))
else:
    for ci,cn in enumerate("RGB"):
        v=sorted(p[ci::4]); mean=sum(v)/n; sd=(sum((x-mean)**2 for x in v)/n)**0.5
        print("  %s x255: min %.0f p01 %.0f p50 %.0f p99 %.0f max %.0f mean %.1f sd %.2f"
              % (cn, v[0]*255, v[int(n*0.01)]*255, v[n//2]*255, v[int(n*0.99)]*255, v[-1]*255, mean*255, sd*255))
print("=== done ===")
