# -*- coding: utf-8 -*-
import bpy, os, math

SCR = r"C:\Work\blender\ovdr_export\kgp_v3\_scratch"
os.makedirs(SCR, exist_ok=True)
PX = 512
TAU = 6.283185307179586

def to_srgb(x):
    if x <= 0.0:
        return 0
    v = x * 12.92 if x <= 0.0031308 else 1.055 * (x ** (1.0 / 2.4)) - 0.055
    return max(0, min(255, int(round(v * 255.0))))

def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 1
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    ob = bpy.context.object
    return ob

def torus(nodes, links):
    tc = nodes.new('ShaderNodeTexCoord')
    sep = nodes.new('ShaderNodeSeparateXYZ')
    links.new(tc.outputs['Generated'], sep.inputs['Vector'])
    mu = nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = TAU
    links.new(sep.outputs['X'], mu.inputs[0])
    mv = nodes.new('ShaderNodeMath'); mv.operation = 'MULTIPLY'; mv.inputs[1].default_value = TAU
    links.new(sep.outputs['Y'], mv.inputs[0])
    cu = nodes.new('ShaderNodeMath'); cu.operation = 'COSINE'; links.new(mu.outputs[0], cu.inputs[0])
    su = nodes.new('ShaderNodeMath'); su.operation = 'SINE';   links.new(mu.outputs[0], su.inputs[0])
    cv = nodes.new('ShaderNodeMath'); cv.operation = 'COSINE'; links.new(mv.outputs[0], cv.inputs[0])
    sv = nodes.new('ShaderNodeMath'); sv.operation = 'SINE';   links.new(mv.outputs[0], sv.inputs[0])
    cmb = nodes.new('ShaderNodeCombineXYZ')
    links.new(cu.outputs[0], cmb.inputs['X'])
    links.new(su.outputs[0], cmb.inputs['Y'])
    links.new(cv.outputs[0], cmb.inputs['Z'])
    scl = nodes.new('ShaderNodeVectorMath'); scl.operation = 'SCALE'
    links.new(cmb.outputs[0], scl.inputs[0])
    scl.inputs['Scale'].default_value = 1.0 / TAU
    wsc = nodes.new('ShaderNodeMath'); wsc.operation = 'MULTIPLY'; wsc.inputs[1].default_value = 1.0 / TAU
    links.new(sv.outputs[0], wsc.inputs[0])
    return scl.outputs[0], wsc.outputs[0]

def bake_variant(ob, name, build):
    for m in list(bpy.data.materials):
        bpy.data.materials.remove(m)
    ob.data.materials.clear()
    mat = bpy.data.materials.new("probe")
    ob.data.materials.append(mat)
    mat.use_nodes = True
    nt = mat.node_tree; nodes = nt.nodes; links = nt.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.5
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    V, W = torus(nodes, links)
    sock = build(nodes, links, V, W)
    links.new(sock, bsdf.inputs['Base Color'])
    img = bpy.data.images.get(name)
    if img:
        bpy.data.images.remove(img)
    img = bpy.data.images.new(name, PX, PX, alpha=False, float_buffer=True)
    tn = nodes.new('ShaderNodeTexImage'); tn.image = img
    nt.nodes.active = tn
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, use_clear=True, margin=16)
    px = list(img.pixels)
    return img, px

def report(name, px):
    n = PX * PX
    lines = []
    for ci, cn in ((0, 'R'), (1, 'G'), (2, 'B')):
        v = px[ci::4]
        mn, mx = min(v), max(v)
        mean = sum(v) / n
        sd = (sum((a - mean) ** 2 for a in v) / n) ** 0.5
        sv = sorted(v)
        q = [sv[int(n * p)] for p in (0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99)]
        s8 = [to_srgb(a) for a in v]
        s8mean = sum(s8) / n
        s8sd = (sum((a - s8mean) ** 2 for a in s8) / n) ** 0.5
        lines.append("  %s lin min%.4f max%.4f mean%.4f sd%.4f | p1 %.3f p5 %.3f p25 %.3f p50 %.3f p75 %.3f p95 %.3f p99 %.3f | sRGB %d-%d mean%.1f sd%.2f"
                     % (cn, mn, mx, mean, sd, q[0], q[1], q[2], q[3], q[4], q[5], q[6],
                        min(s8), max(s8), s8mean, s8sd))
    # seam on sRGB R channel
    r8 = [to_srgb(a) for a in px[0::4]]
    top = r8[0:PX]; bot = r8[(PX - 1) * PX:PX * PX]
    seam_v = sum(abs(top[k] - bot[k]) for k in range(PX)) / PX
    left = [r8[y * PX] for y in range(PX)]
    right = [r8[y * PX + PX - 1] for y in range(PX)]
    seam_h = sum(abs(left[k] - right[k]) for k in range(PX)) / PX
    print("== %s" % name)
    for l in lines:
        print(l)
    print("  seam_v %.2f seam_h %.2f" % (seam_v, seam_h))

ob = setup()

def v_noise(scale, detail, rough, ntype='FBM'):
    def b(nodes, links, V, W):
        n = nodes.new('ShaderNodeTexNoise')
        n.noise_dimensions = '4D'
        try:
            n.noise_type = ntype
        except Exception as e:
            print("   noise_type unsupported:", e)
        links.new(V, n.inputs['Vector']); links.new(W, n.inputs['W'])
        n.inputs['Scale'].default_value = scale
        n.inputs['Detail'].default_value = detail
        n.inputs['Roughness'].default_value = rough
        return n.outputs['Fac']
    return b

def v_vor(scale, feature, rand=1.0, outname='Distance', sep_channel=None, smooth=None):
    def b(nodes, links, V, W):
        n = nodes.new('ShaderNodeTexVoronoi')
        n.voronoi_dimensions = '4D'
        n.feature = feature
        links.new(V, n.inputs['Vector']); links.new(W, n.inputs['W'])
        n.inputs['Scale'].default_value = scale
        n.inputs['Randomness'].default_value = rand
        if smooth is not None and 'Smoothness' in n.inputs:
            n.inputs['Smoothness'].default_value = smooth
        if sep_channel is not None:
            sc = nodes.new('ShaderNodeSeparateColor')
            links.new(n.outputs['Color'], sc.inputs['Color'])
            return sc.outputs[sep_channel]
        return n.outputs[outname]
    return b

VARIANTS = [
    ("noise_s40_d4_r055", v_noise(40, 4, 0.55)),
    ("noise_s9_d3_r05",   v_noise(9, 3, 0.5)),
    ("noise_s3_d3_r05",   v_noise(3, 3, 0.5)),
    ("vor_s11_dist",      v_vor(11, 'F1', 1.0, 'Distance')),
    ("vor_s11_edge",      v_vor(11, 'DISTANCE_TO_EDGE', 1.0, 'Distance')),
    ("vor_s11_colR",      v_vor(11, 'F1', 1.0, sep_channel=0)),
    ("vor_s11_smooth",    v_vor(11, 'SMOOTH_F1', 1.0, 'Distance', smooth=0.35)),
]

print("blender", bpy.app.version_string)
for nm, b in VARIANTS:
    img, px = bake_variant(ob, nm, b)
    report(nm, px)
    img.filepath_raw = os.path.join(SCR, nm + ".png")
    img.file_format = 'PNG'
    img.save()
print("DONE")
