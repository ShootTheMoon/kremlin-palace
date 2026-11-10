# -*- coding: utf-8 -*-
import bpy, math, os
import numpy as np

OUT = r"C:\Work\blender\ovdr_export\kgp_v3\_scratch\p3berry"
PX = 512

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 1
bpy.ops.mesh.primitive_plane_add(size=1, location=(0,0,0))
ob = bpy.context.active_object

def torus(nt, nodes, links, R, off=(0.0,0.0,0.0), woff=0.0):
    tc = nodes.new('ShaderNodeTexCoord')
    sep = nodes.new('ShaderNodeSeparateXYZ')
    links.new(tc.outputs['Generated'], sep.inputs['Vector'])
    TAU = 6.283185307
    mu = nodes.new('ShaderNodeMath'); mu.operation='MULTIPLY'; mu.inputs[1].default_value = TAU
    mv = nodes.new('ShaderNodeMath'); mv.operation='MULTIPLY'; mv.inputs[1].default_value = TAU
    links.new(sep.outputs['X'], mu.inputs[0]); links.new(sep.outputs['Y'], mv.inputs[0])
    cu = nodes.new('ShaderNodeMath'); cu.operation='COSINE'; links.new(mu.outputs[0], cu.inputs[0])
    su = nodes.new('ShaderNodeMath'); su.operation='SINE';   links.new(mu.outputs[0], su.inputs[0])
    cv = nodes.new('ShaderNodeMath'); cv.operation='COSINE'; links.new(mv.outputs[0], cv.inputs[0])
    sv = nodes.new('ShaderNodeMath'); sv.operation='SINE';   links.new(mv.outputs[0], sv.inputs[0])
    cmb = nodes.new('ShaderNodeCombineXYZ')
    links.new(cu.outputs[0], cmb.inputs['X']); links.new(su.outputs[0], cmb.inputs['Y']); links.new(cv.outputs[0], cmb.inputs['Z'])
    sc = nodes.new('ShaderNodeVectorMath'); sc.operation='SCALE'
    links.new(cmb.outputs[0], sc.inputs[0]); sc.inputs['Scale'].default_value = R
    ad = nodes.new('ShaderNodeVectorMath'); ad.operation='ADD'
    links.new(sc.outputs[0], ad.inputs[0]); ad.inputs[1].default_value = off
    mw = nodes.new('ShaderNodeMath'); mw.operation='MULTIPLY_ADD'
    links.new(sv.outputs[0], mw.inputs[0]); mw.inputs[1].default_value = R; mw.inputs[2].default_value = woff
    return ad.outputs[0], mw.outputs[0]

def bake(tag, build, px=PX):
    mat = bpy.data.materials.new('M_'+tag)
    ob.data.materials.clear(); ob.data.materials.append(mat)
    mat.use_nodes = True
    nt = mat.node_tree; nodes = nt.nodes; links = nt.links; nodes.clear()
    o = nodes.new('ShaderNodeOutputMaterial')
    b = nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Metallic'].default_value = 0.0
    b.inputs['Roughness'].default_value = 0.5
    b.inputs['Specular IOR Level'].default_value = 0.0
    links.new(b.outputs['BSDF'], o.inputs['Surface'])
    build(nt, nodes, links, b)
    img = bpy.data.images.new('bi_'+tag, px, px, alpha=False, float_buffer=True)
    img.colorspace_settings.name = 'Non-Color'
    tex = nodes.new('ShaderNodeTexImage'); tex.image = img
    for n in nodes: n.select = False
    tex.select = True; nodes.active = tex
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, use_clear=True, margin=16)
    a = np.array(img.pixels[:], dtype=np.float32).reshape(px, px, 4)[:,:,0]
    q = np.percentile(a, [0,1,5,25,50,75,95,99,100])
    print("%-16s mean %.4f sd %.4f | min %.4f p05 %.4f p50 %.4f p95 %.4f max %.4f | seamV %.4f seamH %.4f"
          % (tag, a.mean(), a.std(), q[0], q[2], q[4], q[6], q[8],
             np.abs(a[0,:]-a[-1,:]).mean(), np.abs(a[:,0]-a[:,-1]).mean()))
    img.filepath_raw = os.path.join(OUT, 'probe_%s.png' % tag)
    img.file_format = 'PNG'
    img.save()
    return a

TAU = 6.283185307

# 1) flat colour: quantify specular loss on a DIFFUSE/COLOR bake
def flat_spec(val):
    def f(nt, nodes, links, b):
        b.inputs['Specular IOR Level'].default_value = val
        b.inputs['Base Color'].default_value = (0.5, 0.5, 0.5, 1.0)
    return f
bake('flat_spec05', flat_spec(0.5), 64)
bake('flat_spec00', flat_spec(0.0), 64)

# 2) voronoi 4D F1 distance on the torus, several radii
for cyc in (5, 7, 9, 12):
    R = cyc/TAU
    def f(nt, nodes, links, b, R=R):
        vec, w = torus(nt, nodes, links, R)
        v = nt.nodes.new('ShaderNodeTexVoronoi'); v.voronoi_dimensions='4D'; v.feature='F1'
        v.inputs['Scale'].default_value = 1.0
        v.inputs['Randomness'].default_value = 1.0
        links.new(vec, v.inputs['Vector']); links.new(w, v.inputs['W'])
        m = nodes.new('ShaderNodeMath'); m.operation='MULTIPLY'; m.inputs[1].default_value = 0.5
        links.new(v.outputs['Distance'], m.inputs[0])
        links.new(m.outputs[0], b.inputs['Base Color'])
    bake('vorD_c%02d' % cyc, f)

# 3) voronoi 4D smooth F1 + radius, at 8 cycles
R = 8/TAU
def f_rad(nt, nodes, links, b):
    vec, w = torus(nt, nodes, links, R)
    v = nt.nodes.new('ShaderNodeTexVoronoi'); v.voronoi_dimensions='4D'; v.feature='N_SPHERE_RADIUS'
    v.inputs['Scale'].default_value = 1.0
    v.inputs['Randomness'].default_value = 1.0
    links.new(vec, v.inputs['Vector']); links.new(w, v.inputs['W'])
    links.new(v.outputs['Radius'], b.inputs['Base Color'])
bake('vorRad_c08', f_rad)

# 4) noise 4D factor distribution
for cyc, det in ((4,3.0),(4,5.0)):
    R = cyc/TAU
    def f(nt, nodes, links, b, R=R, det=det):
        vec, w = torus(nt, nodes, links, R, off=(3.7,1.9,-2.3), woff=5.1)
        n = nodes.new('ShaderNodeTexNoise'); n.noise_dimensions='4D'
        n.inputs['Scale'].default_value = 1.0
        n.inputs['Detail'].default_value = det
        n.inputs['Roughness'].default_value = 0.5
        links.new(vec, n.inputs['Vector']); links.new(w, n.inputs['W'])
        links.new(n.outputs['Factor'], b.inputs['Base Color'])
    bake('noise_c%02d_d%d' % (cyc, int(det)), f)
print("=== probe done ===")
