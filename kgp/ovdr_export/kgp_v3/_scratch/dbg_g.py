mat.use_nodes = True
nt = mat.node_tree
nodes = nt.nodes
links = nt.links
nodes.clear()
N = lambda t: nodes.new(t)
L = lambda a, b: links.new(a, b)
S = lambda n, i: next(s for s in n.inputs if s.identifier == i)
O = lambda n: next(s for s in n.outputs if s.identifier == 'Result_Color')
TAU = 6.283185307
out = N('ShaderNodeOutputMaterial'); out.location = (2400, 0)
bsdf = N('ShaderNodeBsdfPrincipled'); bsdf.location = (2160, 0)
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.5
L(bsdf.outputs['BSDF'], out.inputs['Surface'])
tc = N('ShaderNodeTexCoord'); tc.location = (-2400, 0)
sep = N('ShaderNodeSeparateXYZ'); sep.location = (-2220, 0)
L(tc.outputs['Generated'], sep.inputs['Vector'])
u0 = N('ShaderNodeMath'); u0.operation = 'MULTIPLY'; u0.inputs[1].default_value = TAU
u0.location = (-2040, 160); L(sep.outputs['X'], u0.inputs[0])
v0 = N('ShaderNodeMath'); v0.operation = 'MULTIPLY'; v0.inputs[1].default_value = TAU
v0.location = (-2040, -160); L(sep.outputs['Y'], v0.inputs[0])
su = N('ShaderNodeMath'); su.operation = 'SINE'; su.location = (-1880, 300); L(u0.outputs[0], su.inputs[0])
cu = N('ShaderNodeMath'); cu.operation = 'COSINE'; cu.location = (-1880, 140); L(u0.outputs[0], cu.inputs[0])
sv = N('ShaderNodeMath'); sv.operation = 'SINE'; sv.location = (-1880, -20); L(v0.outputs[0], sv.inputs[0])
cv = N('ShaderNodeMath'); cv.operation = 'COSINE'; cv.location = (-1880, -180); L(v0.outputs[0], cv.inputs[0])
tor = N('ShaderNodeCombineXYZ'); tor.location = (-1700, 140)
L(su.outputs[0], tor.inputs['X']); L(cu.outputs[0], tor.inputs['Y']); L(sv.outputs[0], tor.inputs['Z'])
wn = N('ShaderNodeTexNoise'); wn.noise_dimensions = '4D'; wn.location = (-1520, 320)
wn.inputs['Scale'].default_value = 0.7; wn.inputs['Detail'].default_value = 2.0
wn.inputs['Roughness'].default_value = 0.5; wn.inputs['Distortion'].default_value = 0.0
L(tor.outputs['Vector'], wn.inputs['Vector']); L(cv.outputs[0], wn.inputs['W'])
wsp = N('ShaderNodeSeparateColor'); wsp.location = (-1340, 320); L(wn.outputs['Color'], wsp.inputs['Color'])
dx = N('ShaderNodeMath'); dx.operation = 'MULTIPLY_ADD'; dx.location = (-1160, 400)
dx.inputs[1].default_value = 0.075; dx.inputs[2].default_value = -0.0375
L(wsp.outputs['Red'], dx.inputs[0])
dy = N('ShaderNodeMath'); dy.operation = 'MULTIPLY_ADD'; dy.location = (-1160, 240)
dy.inputs[1].default_value = 0.075; dy.inputs[2].default_value = -0.0375
L(wsp.outputs['Green'], dy.inputs[0])
xw = N('ShaderNodeMath'); xw.operation = 'ADD'; xw.location = (-980, 400)
L(sep.outputs['X'], xw.inputs[0]); L(dx.outputs[0], xw.inputs[1])
yw = N('ShaderNodeMath'); yw.operation = 'ADD'; yw.location = (-980, 240)
L(sep.outputs['Y'], yw.inputs[0]); L(dy.outputs[0], yw.inputs[1])
uw = N('ShaderNodeMath'); uw.operation = 'MULTIPLY'; uw.inputs[1].default_value = TAU
uw.location = (-800, 400); L(xw.outputs[0], uw.inputs[0])
vw = N('ShaderNodeMath'); vw.operation = 'MULTIPLY'; vw.inputs[1].default_value = TAU
vw.location = (-800, 240); L(yw.outputs[0], vw.inputs[0])
WAVES = [(4, 2, 1.00, 0.00, 0), (-3, 5, 0.85, 1.90, 0), (7, -2, 0.60, 3.40, 0),
         (2, 9, 0.50, 0.80, 0), (11, 5, 0.38, 4.60, 1), (-8, 11, 0.30, 2.20, 1),
         (14, -9, 0.22, 5.50, 1), (6, 17, 0.17, 1.10, 1), (19, 8, 0.13, 3.95, 1),
         (-13, 20, 0.10, 0.35, 1)]
hacc = None
cacc = None
facc = None
wy = 700
for a, b, am, ph, fine in WAVES:
    ib = N('ShaderNodeMath'); ib.operation = 'MULTIPLY_ADD'; ib.location = (-620, wy)
    ib.inputs[1].default_value = float(b); ib.inputs[2].default_value = ph
    L(vw.outputs[0], ib.inputs[0])
    ar = N('ShaderNodeMath'); ar.operation = 'MULTIPLY_ADD'; ar.location = (-460, wy)
    ar.inputs[1].default_value = float(a)
    L(uw.outputs[0], ar.inputs[0]); L(ib.outputs[0], ar.inputs[2])
    sn = N('ShaderNodeMath'); sn.operation = 'SINE'; sn.location = (-300, wy)
    L(ar.outputs[0], sn.inputs[0])
    cs = N('ShaderNodeMath'); cs.operation = 'COSINE'; cs.location = (-300, wy - 70)
    L(ar.outputs[0], cs.inputs[0])
    if hacc is None:
        hacc = N('ShaderNodeMath'); hacc.operation = 'MULTIPLY'; hacc.location = (-140, wy)
        hacc.inputs[1].default_value = am; L(sn.outputs[0], hacc.inputs[0])
    else:
        nx = N('ShaderNodeMath'); nx.operation = 'MULTIPLY_ADD'; nx.location = (-140, wy)
        nx.inputs[1].default_value = am
        L(sn.outputs[0], nx.inputs[0]); L(hacc.outputs[0], nx.inputs[2])
        hacc = nx
    gw = am * (0.75 * a + 0.66 * b)
    gn = N('ShaderNodeMath'); gn.operation = 'MULTIPLY_ADD'; gn.location = (20, wy - 70)
    gn.inputs[1].default_value = gw
    L(cs.outputs[0], gn.inputs[0])
    if fine:
        if facc is not None:
            L(facc.outputs[0], gn.inputs[2])
        facc = gn
    else:
        if cacc is not None:
            L(cacc.outputs[0], gn.inputs[2])
        cacc = gn
    wy -= 150
h = N('ShaderNodeMath'); h.operation = 'MULTIPLY_ADD'; h.location = (200, 760)
h.inputs[1].default_value = 0.26; h.inputs[2].default_value = 0.5
L(hacc.outputs[0], h.inputs[0])
cn = N('ShaderNodeTexNoise'); cn.noise_dimensions = '4D'; cn.location = (200, 420)
cn.inputs['Scale'].default_value = 1.1; cn.inputs['Detail'].default_value = 3.0
cn.inputs['Roughness'].default_value = 0.55; cn.inputs['Distortion'].default_value = 0.0
L(tor.outputs['Vector'], cn.inputs['Vector']); L(cv.outputs[0], cn.inputs['W'])
cr = N('ShaderNodeValToRGB'); cr.location = (380, 420); cr.color_ramp.interpolation = 'EASE'
L(cn.outputs['Fac'], cr.inputs['Fac'])
cr.color_ramp.elements[0].position = 0.40; cr.color_ramp.elements[0].color = (0.22, 0.22, 0.22, 1)
cr.color_ramp.elements[1].position = 0.60; cr.color_ramp.elements[1].color = (1, 1, 1, 1)
fm = N('ShaderNodeMath'); fm.operation = 'MULTIPLY'; fm.location = (600, 300)
L(facc.outputs[0], fm.inputs[0]); L(cr.outputs['Color'], fm.inputs[1])
gsum = N('ShaderNodeMath'); gsum.operation = 'ADD'; gsum.location = (760, 300)
L(cacc.outputs[0], gsum.inputs[0]); L(fm.outputs[0], gsum.inputs[1])
g = N('ShaderNodeMath'); g.operation = 'MULTIPLY_ADD'; g.location = (920, 300)
g.inputs[1].default_value = 0.042; g.inputs[2].default_value = 0.5
L(gsum.outputs[0], g.inputs[0])
sh = N('ShaderNodeValToRGB'); sh.location = (1100, 480); sh.color_ramp.interpolation = 'LINEAR'
L(g.outputs[0], sh.inputs['Fac'])
sh.color_ramp.elements[0].position = 0.16; sh.color_ramp.elements[0].color = (0, 0, 0, 1)
sh.color_ramp.elements[1].position = 0.84; sh.color_ramp.elements[1].color = (1, 1, 1, 1)
gl = N('ShaderNodeValToRGB'); gl.location = (1100, 240); gl.color_ramp.interpolation = 'EASE'
L(g.outputs[0], gl.inputs['Fac'])
gl.color_ramp.elements[0].position = 0.86; gl.color_ramp.elements[0].color = (0, 0, 0, 1)
gl.color_ramp.elements[1].position = 0.97; gl.color_ramp.elements[1].color = (1, 1, 1, 1)
dp = N('ShaderNodeTexNoise'); dp.noise_dimensions = '4D'; dp.location = (1100, -40)
dp.inputs['Scale'].default_value = 0.55; dp.inputs['Detail'].default_value = 2.0
dp.inputs['Roughness'].default_value = 0.5; dp.inputs['Distortion'].default_value = 0.0
L(tor.outputs['Vector'], dp.inputs['Vector']); L(cv.outputs[0], dp.inputs['W'])
dr = N('ShaderNodeValToRGB'); dr.location = (1280, -40); dr.color_ramp.interpolation = 'EASE'
L(dp.outputs['Fac'], dr.inputs['Fac'])
dr.color_ramp.elements[0].position = 0.40; dr.color_ramp.elements[0].color = (0, 0, 0, 1)
dr.color_ramp.elements[1].position = 0.62; dr.color_ramp.elements[1].color = (1, 1, 1, 1)
df = N('ShaderNodeMath'); df.operation = 'MULTIPLY'; df.inputs[1].default_value = 0.45
df.location = (1460, -40); L(dr.outputs['Color'], df.inputs[0])
fn = N('ShaderNodeTexNoise'); fn.noise_dimensions = '4D'; fn.location = (1100, -340)
fn.inputs['Scale'].default_value = 7.0; fn.inputs['Detail'].default_value = 5.0
fn.inputs['Roughness'].default_value = 0.72; fn.inputs['Distortion'].default_value = 0.0
L(tor.outputs['Vector'], fn.inputs['Vector']); L(cv.outputs[0], fn.inputs['W'])
fr = N('ShaderNodeValToRGB'); fr.location = (1280, -340); fr.color_ramp.interpolation = 'EASE'
L(fn.outputs['Fac'], fr.inputs['Fac'])
fr.color_ramp.elements[0].position = 0.565; fr.color_ramp.elements[0].color = (0, 0, 0, 1)
fr.color_ramp.elements[1].position = 0.640; fr.color_ramp.elements[1].color = (1, 1, 1, 1)
fg = N('ShaderNodeValToRGB'); fg.location = (1280, -560); fg.color_ramp.interpolation = 'EASE'
L(h.outputs[0], fg.inputs['Fac'])
fg.color_ramp.elements[0].position = 0.58; fg.color_ramp.elements[0].color = (0, 0, 0, 1)
fg.color_ramp.elements[1].position = 0.80; fg.color_ramp.elements[1].color = (1, 1, 1, 1)
f1 = N('ShaderNodeMath'); f1.operation = 'MULTIPLY'; f1.location = (1460, -420)
L(fr.outputs['Color'], f1.inputs[0]); L(fg.outputs['Color'], f1.inputs[1])
ff = N('ShaderNodeMath'); ff.operation = 'MULTIPLY'; ff.location = (1620, -420)
L(f1.outputs[0], ff.inputs[0]); L(cr.outputs['Color'], ff.inputs[1])
c1 = N('ShaderNodeMix'); c1.data_type = 'RGBA'; c1.location = (1300, 760)
S(c1, 'A_Color').default_value = (0.035, 0.070, 0.078, 1.0)
S(c1, 'B_Color').default_value = (0.230, 0.320, 0.315, 1.0)
L(sh.outputs['Color'], S(c1, 'Factor_Float'))
c2 = N('ShaderNodeMix'); c2.data_type = 'RGBA'; c2.location = (1480, 760)
S(c2, 'B_Color').default_value = (0.020, 0.048, 0.056, 1.0)
L(O(c1), S(c2, 'A_Color')); L(df.outputs[0], S(c2, 'Factor_Float'))
c3 = N('ShaderNodeMix'); c3.data_type = 'RGBA'; c3.location = (1660, 760)
S(c3, 'B_Color').default_value = (0.470, 0.545, 0.540, 1.0)
L(O(c2), S(c3, 'A_Color')); L(gl.outputs['Color'], S(c3, 'Factor_Float'))
c4 = N('ShaderNodeMix'); c4.data_type = 'RGBA'; c4.location = (1840, 760)
S(c4, 'B_Color').default_value = (0.800, 0.845, 0.850, 1.0)
L(O(c3), S(c4, 'A_Color')); L(ff.outputs[0], S(c4, 'Factor_Float'))
L(O(c4), bsdf.inputs['Base Color'])
mat.diffuse_color = (0.120, 0.190, 0.195, 1.0)
L(g.outputs[0], bsdf.inputs['Base Color'])
