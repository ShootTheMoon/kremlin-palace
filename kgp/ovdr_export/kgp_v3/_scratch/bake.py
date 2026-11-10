# Blender harness: build ONE material from a code file, bake Base Color to a PNG tile.
# usage: blender -b -P bake.py -- <code.py> <outdir> <px> [<tag>] [<probe,node,names>]
import bpy, sys, os

argv = sys.argv[sys.argv.index('--') + 1:]
code_path = argv[0]
out_dir = argv[1]
px = int(argv[2]) if len(argv) > 2 else 1024
tag = argv[3] if len(argv) > 3 else 'tile'
probes = [p for p in (argv[4].split(',') if len(argv) > 4 and argv[4] else []) if p]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 1
try:
    sc.cycles.use_denoising = False
except Exception:
    pass
sc.render.bake.use_pass_direct = False
sc.render.bake.use_pass_indirect = False
sc.render.bake.use_pass_color = True
sc.render.bake.margin = 16
sc.render.bake.use_clear = True

me = bpy.data.meshes.new('P')
me.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [], [(0, 1, 2, 3)])
me.update()
uvl = me.uv_layers.new(name='UVMap')
co = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
for i, l in enumerate(me.loops):
    uvl.data[i].uv = co[l.vertex_index]
ob = bpy.data.objects.new('P', me)
sc.collection.objects.link(ob)
bpy.context.view_layer.objects.active = ob
ob.select_set(True)

mat = bpy.data.materials.new('M')
ob.data.materials.append(mat)

ns = {'bpy': bpy, 'mat': mat}
src = open(code_path, 'r', encoding='utf-8').read()
exec(compile(src, code_path, 'exec'), ns)

nt = mat.node_tree
img = bpy.data.images.new('bk', px, px, alpha=False)
tex = nt.nodes.new('ShaderNodeTexImage')
tex.image = img
tex.location = (-400, -900)
nt.nodes.active = tex


def do_bake(name):
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, use_clear=True, margin=16)
    p = os.path.join(out_dir, name + '.png')
    img.filepath_raw = p
    img.file_format = 'PNG'
    img.save()
    print('SAVED %s' % p)


do_bake(tag)

if probes:
    bsdf = None
    for n in nt.nodes:
        if n.bl_idname == 'ShaderNodeBsdfPrincipled':
            bsdf = n
    bc = bsdf.inputs['Base Color']
    for nm in probes:
        node = ns.get(nm)
        if node is None:
            print('NOPROBE %s' % nm)
            continue
        sock = None
        for cand in ('Fac', 'Color', 'Value', 'Result'):
            if cand in node.outputs:
                sock = node.outputs[cand]
                break
        if sock is None:
            sock = node.outputs[0]
        for l in list(bc.links):
            nt.links.remove(l)
        nt.links.new(sock, bc)
        do_bake('%s_probe_%s' % (tag, nm))
print('DONE')
