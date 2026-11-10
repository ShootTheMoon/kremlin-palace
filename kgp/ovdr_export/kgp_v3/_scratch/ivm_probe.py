# -*- coding: utf-8 -*-
"""Ivory marble: measure what the noise signals actually do on the torus mapping."""
import bpy

TAU = 6.283185307
SIZE = 512


def fresh():
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
    return ob


def bake_float(ob, mat, size=SIZE):
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    img = bpy.data.images.new("bk", size, size, alpha=False, float_buffer=True)
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


def desc(v, label):
    n = len(v)
    s = sorted(v)
    mean = sum(v) / n
    sd = (sum((x - mean) ** 2 for x in v) / n) ** 0.5

    def q(f):
        return s[min(n - 1, int(f * n))]
    print("%-28s mean=%.4f sd=%.4f | min=%.4f p01=%.4f p05=%.4f p25=%.4f med=%.4f "
          "p75=%.4f p95=%.4f p99=%.4f max=%.4f"
          % (label, mean, sd, s[0], q(.01), q(.05), q(.25), q(.5), q(.75), q(.95), q(.99), s[-1]))
    return s


def base(nt):
    """torus coords -> (vector out, w out) plus the angle sockets"""
    nodes, links = nt.nodes, nt.links
    tc = nodes.new('ShaderNodeTexCoord')
    mp = nodes.new('ShaderNodeMapping')
    mp.inputs['Location'].default_value = (0.17, 0.43, 0.0)
    links.new(tc.outputs['Generated'], mp.inputs['Vector'])
    sep = nodes.new('ShaderNodeSeparateXYZ')
    links.new(mp.outputs['Vector'], sep.inputs['Vector'])
    mu = nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = TAU
    links.new(sep.outputs['X'], mu.inputs[0])
    mv = nodes.new('ShaderNodeMath'); mv.operation = 'MULTIPLY'; mv.inputs[1].default_value = TAU
    links.new(sep.outputs['Y'], mv.inputs[0])
    return mu.outputs[0], mv.outputs[0]


def embed(nt, ua, va):
    nodes, links = nt.nodes, nt.links
    su = nodes.new('ShaderNodeMath'); su.operation = 'SINE'; links.new(ua, su.inputs[0])
    cu = nodes.new('ShaderNodeMath'); cu.operation = 'COSINE'; links.new(ua, cu.inputs[0])
    sv = nodes.new('ShaderNodeMath'); sv.operation = 'SINE'; links.new(va, sv.inputs[0])
    cv = nodes.new('ShaderNodeMath'); cv.operation = 'COSINE'; links.new(va, cv.inputs[0])
    cmb = nodes.new('ShaderNodeCombineXYZ')
    links.new(su.outputs[0], cmb.inputs['X'])
    links.new(cu.outputs[0], cmb.inputs['Y'])
    links.new(sv.outputs[0], cmb.inputs['Z'])
    return cmb.outputs['Vector'], cv.outputs[0]


def newmat():
    mat = bpy.data.materials.new("probe")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Metallic'].default_value = 0.0
    b.inputs['Roughness'].default_value = 0.5
    nt.links.new(b.outputs['BSDF'], o.inputs['Surface'])
    return mat, nt, b


CFGS = [
    ("cloud  S0.50 D3 R0.55 X0.0", dict(Scale=0.50, Detail=3.0, Roughness=0.55, Distortion=0.0), 'Fac'),
    ("mottle S1.40 D4 R0.50 X0.0", dict(Scale=1.40, Detail=4.0, Roughness=0.50, Distortion=0.0), 'Fac'),
    ("warp   S0.90 D3 R0.55 X0.0", dict(Scale=0.90, Detail=3.0, Roughness=0.55, Distortion=0.0), 'Color'),
    ("fine   S2.20 D2 R0.40 X0.20", dict(Scale=2.20, Detail=2.0, Roughness=0.40, Distortion=0.20), 'Fac'),
    ("fine0  S2.20 D2 R0.40 X0.0", dict(Scale=2.20, Detail=2.0, Roughness=0.40, Distortion=0.0), 'Fac'),
    ("bold   S0.65 D3 R0.50 X0.30", dict(Scale=0.65, Detail=3.0, Roughness=0.50, Distortion=0.30), 'Fac'),
    ("gate   S0.30 D2 R0.50 X0.0", dict(Scale=0.30, Detail=2.0, Roughness=0.50, Distortion=0.0), 'Fac'),
]

ob = fresh()
for label, kw, out in CFGS:
    mat, nt, bsdf = newmat()
    ua, va = base(nt)
    vec, w = embed(nt, ua, va)
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.noise_dimensions = '4D'
    for k, v in kw.items():
        nz.inputs[k].default_value = v
    nt.links.new(vec, nz.inputs['Vector'])
    nt.links.new(w, nz.inputs['W'])
    nt.links.new(nz.outputs[out], bsdf.inputs['Base Color'])
    img = bake_float(ob, mat)
    p = list(img.pixels)
    desc(p[0::4], label + " R")
    if out == 'Color':
        desc(p[1::4], label + " G")
        desc(p[2::4], label + " B")
    bpy.data.images.remove(img)
print("PROBE DONE")
