# -*- coding: utf-8 -*-
import bpy, sys, os, math
import numpy as np

argv = sys.argv[sys.argv.index('--')+1:]
code_path = argv[0]
out_path  = argv[1]
px        = int(argv[2]) if len(argv) > 2 else 512

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
exec(src, {'bpy': bpy, 'math': math, 'mat': mat})

img = bpy.data.images.new('bakeimg', px, px, alpha=False)
nt = mat.node_tree
tex = nt.nodes.new('ShaderNodeTexImage')
tex.image = img
for n in nt.nodes: n.select = False
tex.select = True
nt.nodes.active = tex
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, use_clear=True, margin=16)
img.filepath_raw = out_path
img.file_format = 'PNG'
img.save()

a = np.array(img.pixels[:], dtype=np.float64).reshape(px, px, 4)[:, :, :3]
a = np.clip(a, 0.0, 1.0)
b = np.clip(np.rint(a * 255.0), 0, 255)
lin = np.where(a <= 0.04045, a / 12.92, np.power((a + 0.055) / 1.055, 2.4))
print("=== %s ===" % os.path.basename(out_path))
for ci, cn in enumerate("RGB"):
    c = b[:, :, ci]
    print("  %s min %3d max %3d mean %6.1f sd %6.2f  spread %3d"
          % (cn, c.min(), c.max(), c.mean(), c.std(), c.max() - c.min()))
sp = int(max(b[:, :, i].max() - b[:, :, i].min() for i in range(3)))
sd = max(b[:, :, i].std() for i in range(3))
sv = np.abs(b[0, :, 0] - b[-1, :, 0]).mean()
sh = np.abs(b[:, 0, 0] - b[:, -1, 0]).mean()
print("  SPREAD %d  STD %.2f  seam_v %.1f  seam_h %.1f" % (sp, sd, sv, sh))
lum = 0.2126*lin[:,:,0] + 0.7152*lin[:,:,1] + 0.0722*lin[:,:,2]
q = np.percentile(lum, [5, 50, 95])
print("  linear lum p05 %.4f p50 %.4f p95 %.4f" % (q[0], q[1], q[2]))
print("=== done ===")
