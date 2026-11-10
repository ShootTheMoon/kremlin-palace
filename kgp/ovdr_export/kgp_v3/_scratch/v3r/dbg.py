# -*- coding: utf-8 -*-
# Same rig as the round-1 harness, but bakes into a FLOAT buffer and reports the
# raw linear distribution + cross-channel correlation. Measurement only.
import bpy, sys
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
code_path = argv[0]
px = int(argv[1]) if len(argv) > 1 else 512

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.engine = 'CYCLES'
scn.cycles.device = 'CPU'
scn.cycles.samples = 1
try:
    scn.cycles.use_denoising = False
except Exception:
    pass

bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, 0))
ob = bpy.context.active_object
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.reset()
bpy.ops.object.mode_set(mode='OBJECT')

mat = bpy.data.materials.new('TileMat')
ob.data.materials.append(mat)
src = open(code_path, 'r', encoding='utf-8').read()
exec(compile(src, code_path, 'exec'), {'bpy': bpy, 'mat': mat})

img = bpy.data.images.new('BakeTgt', px, px, alpha=False, float_buffer=True)
nt = mat.node_tree
tex = nt.nodes.new('ShaderNodeTexImage')
tex.image = img
for n in nt.nodes:
    n.select = False
tex.select = True
nt.nodes.active = tex
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
scn.render.bake.margin = 16
scn.render.bake.use_clear = True
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, use_clear=True, margin=16)

buf = np.empty(px * px * 4, dtype=np.float32)
img.pixels.foreach_get(buf)
buf = buf.reshape(px, px, 4)[:, :, :3]
qs = [0.5, 1, 2, 5, 16, 50, 84, 95, 98, 99, 99.5]
for i, nm in enumerate('RGB'):
    c = buf[:, :, i].ravel().astype(np.float64)
    q = np.percentile(c, qs)
    print('CH %s mean=%.4f sd=%.4f min=%.4f max=%.4f' % (nm, c.mean(), c.std(), c.min(), c.max()))
    print('   ' + '  '.join('p%.4g=%.4f' % (a, b) for a, b in zip(qs, q)))
R = buf[:, :, 0].ravel().astype(np.float64)
G = buf[:, :, 1].ravel().astype(np.float64)
B = buf[:, :, 2].ravel().astype(np.float64)
print('corr RG=%.3f RB=%.3f GB=%.3f' % (np.corrcoef(R, G)[0, 1], np.corrcoef(R, B)[0, 1], np.corrcoef(G, B)[0, 1]))
