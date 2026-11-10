import bpy, sys, os

argv = sys.argv[sys.argv.index('--') + 1:]
code_path = argv[0]
out_path = argv[1]
px = int(argv[2]) if len(argv) > 2 else 512

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
g = {'bpy': bpy, 'mat': mat}
exec(compile(src, code_path, 'exec'), g)

img = bpy.data.images.new('P7BakeTarget', px, px, alpha=False)
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

img.filepath_raw = out_path
img.file_format = 'PNG'
img.save()
print("P7SAVED " + out_path)
