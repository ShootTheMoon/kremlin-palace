# -*- coding: utf-8 -*-
"""Ivory marble: build ivm_code.py on a throwaway material, bake, measure.

usage: blender -b -P ivm_bake.py -- <mode> <tag>
   mode: probe | final | both
"""
import bpy, sys, os

SC = r"C:\Work\blender\ovdr_export\kgp_v3\_scratch"
OUT = os.path.join(SC, "_ivm_out")
CODE = os.path.join(SC, "ivm_code.py")
PX = 1024
TILE_M = 8.0

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
MODE = argv[0] if argv else 'both'
TAG = argv[1] if len(argv) > 1 else 'v2'

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 1
sc.render.bake.margin = 16
sc.render.bake.use_clear = True

me = bpy.data.meshes.new("plane")
me.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [], [(0, 1, 2, 3)])
me.update()
uvl = me.uv_layers.new(name="UVMap")
for i, co in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
    uvl.data[i].uv = co
ob = bpy.data.objects.new("plane", me)
bpy.context.collection.objects.link(ob)
bpy.context.view_layer.objects.active = ob
ob.select_set(True)

SRC = open(CODE, 'r', encoding='utf-8').read()


def build(name):
    mat = bpy.data.materials.new(name)
    exec(compile(SRC, CODE, 'exec'), {'bpy': bpy, 'mat': mat})
    return mat


def bake(mat, float_buf, size=PX):
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    img = bpy.data.images.new('bk_' + mat.name, size, size, alpha=False, float_buffer=float_buf)
    if not float_buf:
        img.colorspace_settings.name = 'sRGB'
    nt = mat.node_tree
    tn = nt.nodes.new('ShaderNodeTexImage')
    tn.image = img
    for n in nt.nodes:
        n.select = False
    tn.select = True
    nt.nodes.active = tn
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, use_clear=True, margin=16)
    return img


def find(mat, label):
    for n in mat.node_tree.nodes:
        if n.label == label:
            return n
    raise KeyError(label)


def runs(v, w, thr):
    """mean horizontal chord length (px) of regions above thr, toroidal rows"""
    tot = 0
    cnt = 0
    for y in range(0, w, 4):
        row = v[y * w:(y + 1) * w]
        on = [1 if x > thr else 0 for x in row]
        if not any(on) or all(on):
            tot += sum(on)
            continue
        # rotate so row starts off
        i0 = on.index(0)
        on = on[i0:] + on[:i0]
        run = 0
        for x in on:
            if x:
                run += 1
            elif run:
                tot += run
                cnt += 1
                run = 0
        if run:
            tot += run
            cnt += 1
    return (tot / cnt) if cnt else 0.0, cnt


def probe(label, title, size=512):
    mat = build('probe_' + label)
    node = find(mat, label)
    bsdf = [n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    for lk in list(mat.node_tree.links):
        if lk.to_node == bsdf and lk.to_socket.name == 'Base Color':
            mat.node_tree.links.remove(lk)
    mat.node_tree.links.new(node.outputs[0], bsdf.inputs['Base Color'])
    img = bake(mat, True, size)
    p = list(img.pixels)
    v = p[0::4]
    n = len(v)
    s = sorted(v)
    mean = sum(v) / n
    sd = (sum((x - mean) ** 2 for x in v) / n) ** 0.5
    cov50 = sum(1 for x in v if x > 0.5) / float(n)
    cov10 = sum(1 for x in v if x > 0.1) / float(n)
    chord, ncnt = runs(v, size, 0.5)
    med = s[n // 2]
    print("%-9s %-24s mean=%.4f med=%.4f sd=%.4f min=%.3f max=%.3f | cov>.5=%.3f cov>.1=%.3f "
          "| chord>.5 = %.1fpx = %.1fcm (%d runs)"
          % (label, title, mean, med, sd, s[0], s[-1], cov50, cov10,
             chord, chord / size * TILE_M * 100, ncnt))
    bpy.data.images.remove(img)
    bpy.data.materials.remove(mat)


def final():
    mat = build('Ivory_marble_' + TAG)
    img = bake(mat, False, PX)
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, 'Ivory_marble_%s.png' % TAG)
    img.filepath_raw = p
    img.file_format = 'PNG'
    img.save()
    print("saved", p)


if MODE in ('probe', 'both'):
    for lab, ttl in (('CNRAW', 'raw slab noise'),
                     ('MNRAW', 'raw mottle noise'),
                     ('FNRAW', 'raw hairline noise'),
                     ('GNRAW', 'raw bold noise'),
                     ('GMRAW', 'raw gate noise'),
                     ('CLOUDF', 'slab tone factor'),
                     ('MOTTF', 'mottle factor'),
                     ('FINEF', 'hairline vein mask'),
                     ('GATEF', 'bold vein gate'),
                     ('BOLDF', 'bold vein factor')):
        probe(lab, ttl)
if MODE in ('final', 'both'):
    final()
print("IVM DONE")
