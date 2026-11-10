# -*- coding: utf-8 -*-
import bpy, sys, os, math

argv = sys.argv[sys.argv.index('--')+1:]
code_path = argv[0]
out_path  = argv[1]
px        = int(argv[2]) if len(argv) > 2 else 512
floatbuf  = (len(argv) > 3 and argv[3] == 'float')

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 1

bpy.ops.mesh.primitive_plane_add(size=1, location=(0,0,0))
ob = bpy.context.active_object
mat = bpy.data.materials.new('PROBE')
ob.data.materials.append(mat)

src = open(code_path, 'r', encoding='utf-8').read()
g = {'bpy': bpy, 'math': math, 'mat': mat}
exec(src, g)

img = bpy.data.images.new('bakeimg', px, px, alpha=False, float_buffer=floatbuf)
if floatbuf:
    img.colorspace_settings.name = 'Non-Color'
nt = mat.node_tree
tex = nt.nodes.new('ShaderNodeTexImage')
tex.image = img
for n in nt.nodes:
    n.select = False
tex.select = True
nt.nodes.active = tex

bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, use_clear=True, margin=16)

if out_path != 'none':
    img.filepath_raw = out_path
    img.file_format = 'PNG'
    img.save()

p = list(img.pixels)
n = px*px
print("=== STATS %s  (float=%s) ===" % (os.path.basename(out_path), floatbuf))
for ci, cn in enumerate("RGB"):
    v = p[ci::4]
    v2 = sorted(v)
    mean = sum(v)/n
    var = sum((x-mean)**2 for x in v)/n
    print("  %s  min %.4f p01 %.4f p05 %.4f p25 %.4f p50 %.4f p75 %.4f p95 %.4f p99 %.4f max %.4f mean %.4f sd %.4f"
          % (cn, v2[0], v2[int(n*0.01)], v2[int(n*0.05)], v2[int(n*0.25)], v2[n//2], v2[int(n*0.75)],
             v2[int(n*0.95)], v2[int(n*0.99)], v2[-1], mean, var**0.5))
# seam on raw signal (row0 vs last row, col0 vs last col), R channel
row0 = [p[(0*px+x)*4] for x in range(px)]
rowL = [p[((px-1)*px+x)*4] for x in range(px)]
col0 = [p[(y*px+0)*4] for y in range(px)]
colL = [p[(y*px+px-1)*4] for y in range(px)]
print("  seam_v_raw %.4f   seam_h_raw %.4f" % (sum(abs(a-b) for a,b in zip(row0,rowL))/px,
                                               sum(abs(a-b) for a,b in zip(col0,colL))/px))
print("=== done ===")
