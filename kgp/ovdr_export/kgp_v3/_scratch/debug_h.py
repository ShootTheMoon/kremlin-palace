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
out = N('ShaderNodeOutputMaterial'); out.location = (2200, 0)
bsdf = N('ShaderNodeBsdfPrincipled'); bsdf.location = (1960, 0)
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
wn.inputs['Scale'].default_value = 0.64; wn.inputs['Detail'].default_value = 2.0
wn.inputs['Roughness'].default_value = 0.5; wn.inputs['Distortion'].default_value = 0.0
L(tor.outputs['Vector'], wn.inputs['Vector']); L(cv.outputs[0], wn.inputs['W'])
wsp = N('ShaderNodeSeparateColor'); wsp.location = (-1340, 320); L(wn.outputs['Color'], wsp.inputs['Color'])
dx = N('ShaderNodeMath'); dx.operation = 'MULTIPLY_ADD'; dx.location = (-1160, 400)
dx.inputs[1].default_value = 0.55; dx.inputs[2].default_value = -0.275
L(wsp.outputs['Red'], dx.inputs[0])
dy = N('ShaderNodeMath'); dy.operation = 'MULTIPLY_ADD'; dy.location = (-1160, 240)
dy.inputs[1].default_value = 0.55; dy.inputs[2].default_value = -0.275
L(wsp.outputs['Green'], dy.inputs[0])
xw = N('ShaderNodeMath'); xw.operation = 'ADD'; xw.location = (-980, 400)
L(sep.outputs['X'], xw.inputs[0]); L(dx.outputs[0], xw.inputs[1])
yw = N('ShaderNodeMath'); yw.operation = 'ADD'; yw.location = (-980, 240)
L(sep.outputs['Y'], yw.inputs[0]); L(dy.outputs[0], yw.inputs[1])
uw = N('ShaderNodeMath'); uw.operation = 'MULTIPLY'; uw.inputs[1].default_value = TAU
uw.location = (-800, 400); L(xw.outputs[0], uw.inputs[0])
vw = N('ShaderNodeMath'); vw.operation = 'MULTIPLY'; vw.inputs[1].default_value = TAU
vw.location = (-800, 240); L(yw.outputs[0], vw.inputs[0])
WAVES = [(1, 1, 1.00, 0.00), (2, -1, 0.85, 1.90), (-1, 3, 0.70, 3.40),
         (3, 3, 0.55, 0.80), (5, -2, 0.45, 4.60), (-4, 5, 0.34, 2.20),
         (7, 3, 0.26, 5.50), (2, 8, 0.20, 1.10)]
acc = None
wy = 560
for a, b, am, ph in WAVES:
    ib = N('ShaderNodeMath'); ib.operation = 'MULTIPLY_ADD'; ib.location = (-620, wy)
    ib.inputs[1].default_value = float(b); ib.inputs[2].default_value = ph
    L(vw.outputs[0], ib.inputs[0])
    ar = N('ShaderNodeMath'); ar.operation = 'MULTIPLY_ADD'; ar.location = (-460, wy)
    ar.inputs[1].default_value = float(a)
    L(uw.outputs[0], ar.inputs[0]); L(ib.outputs[0], ar.inputs[2])
    sn = N('ShaderNodeMath'); sn.operation = 'SINE'; sn.location = (-300, wy)
    L(ar.outputs[0], sn.inputs[0])
    if acc is None:
        acc = N('ShaderNodeMath'); acc.operation = 'MULTIPLY'; acc.location = (-140, wy)
        acc.inputs[1].default_value = am
        L(sn.outputs[0], acc.inputs[0])
    else:
        nx = N('ShaderNodeMath'); nx.operation = 'MULTIPLY_ADD'; nx.location = (-140, wy)
        nx.inputs[1].default_value = am
        L(sn.outputs[0], nx.inputs[0]); L(acc.outputs[0], nx.inputs[2])
        acc = nx
    wy -= 150
h = N('ShaderNodeMath'); h.operation = 'MULTIPLY_ADD'; h.location = (40, 560)
h.inputs[1].default_value = 0.24; h.inputs[2].default_value = 0.5
L(acc.outputs[0], h.inputs[0])
m1 = N('ShaderNodeValToRGB'); m1.location = (220, 700); L(h.outputs[0], m1.inputs['Fac'])
m1.color_ramp.interpolation = 'EASE'
m1.color_ramp.elements[0].position = 0.14; m1.color_ramp.elements[0].color = (0, 0, 0, 1)
m1.color_ramp.elements[1].position = 0.80; m1.color_ramp.elements[1].color = (1, 1, 1, 1)
ga = N('ShaderNodeMath'); ga.operation = 'SUBTRACT'; ga.inputs[1].default_value = 0.74
ga.location = (220, 400); L(h.outputs[0], ga.inputs[0])
gb = N('ShaderNodeMath'); gb.operation = 'ABSOLUTE'; gb.location = (380, 400); L(ga.outputs[0], gb.inputs[0])
gr = N('ShaderNodeValToRGB'); gr.location = (540, 400); gr.color_ramp.interpolation = 'EASE'
L(gb.outputs[0], gr.inputs['Fac'])
gr.color_ramp.elements[0].color = (1, 1, 1, 1)
gr.color_ramp.elements[1].position = 0.05; gr.color_ramp.elements[1].color = (0, 0, 0, 1)
ta = N('ShaderNodeMath'); ta.operation = 'SUBTRACT'; ta.inputs[1].default_value = 0.27
ta.location = (220, 160); L(h.outputs[0], ta.inputs[0])
tb = N('ShaderNodeMath'); tb.operation = 'ABSOLUTE'; tb.location = (380, 160); L(ta.outputs[0], tb.inputs[0])
tr = N('ShaderNodeValToRGB'); tr.location = (540, 160); tr.color_ramp.interpolation = 'EASE'
L(tb.outputs[0], tr.inputs['Fac'])
tr.color_ramp.elements[0].color = (1, 1, 1, 1)
tr.color_ramp.elements[1].position = 0.045; tr.color_ramp.elements[1].color = (0, 0, 0, 1)
tf = N('ShaderNodeMath'); tf.operation = 'MULTIPLY'; tf.inputs[1].default_value = 0.55
tf.location = (760, 160); L(tr.outputs['Color'], tf.inputs[0])
mn = N('ShaderNodeTexNoise'); mn.noise_dimensions = '4D'; mn.location = (220, -120)
mn.inputs['Scale'].default_value = 0.5; mn.inputs['Detail'].default_value = 3.0
mn.inputs['Roughness'].default_value = 0.55; mn.inputs['Distortion'].default_value = 0.2
L(tor.outputs['Vector'], mn.inputs['Vector']); L(cv.outputs[0], mn.inputs['W'])
mr = N('ShaderNodeValToRGB'); mr.location = (400, -120); mr.color_ramp.interpolation = 'EASE'
L(mn.outputs['Fac'], mr.inputs['Fac'])
mr.color_ramp.elements[0].position = 0.50; mr.color_ramp.elements[0].color = (0, 0, 0, 1)
mr.color_ramp.elements[1].position = 0.63; mr.color_ramp.elements[1].color = (1, 1, 1, 1)
mf = N('ShaderNodeMath'); mf.operation = 'MULTIPLY'; mf.inputs[1].default_value = 0.40
mf.location = (620, -120); L(mr.outputs['Color'], mf.inputs[0])
fn = N('ShaderNodeTexNoise'); fn.noise_dimensions = '4D'; fn.location = (220, -400)
fn.inputs['Scale'].default_value = 6.4; fn.inputs['Detail'].default_value = 5.0
fn.inputs['Roughness'].default_value = 0.75; fn.inputs['Distortion'].default_value = 0.0
L(tor.outputs['Vector'], fn.inputs['Vector']); L(cv.outputs[0], fn.inputs['W'])
fr = N('ShaderNodeValToRGB'); fr.location = (400, -400); fr.color_ramp.interpolation = 'EASE'
L(fn.outputs['Fac'], fr.inputs['Fac'])
fr.color_ramp.elements[0].position = 0.575; fr.color_ramp.elements[0].color = (0, 0, 0, 1)
fr.color_ramp.elements[1].position = 0.645; fr.color_ramp.elements[1].color = (1, 1, 1, 1)
fg = N('ShaderNodeValToRGB'); fg.location = (400, -640); fg.color_ramp.interpolation = 'EASE'
L(h.outputs[0], fg.inputs['Fac'])
fg.color_ramp.elements[0].position = 0.60; fg.color_ramp.elements[0].color = (0, 0, 0, 1)
fg.color_ramp.elements[1].position = 0.82; fg.color_ramp.elements[1].color = (1, 1, 1, 1)
ff = N('ShaderNodeMath'); ff.operation = 'MULTIPLY'; ff.location = (620, -500)
L(fr.outputs['Color'], ff.inputs[0]); L(fg.outputs['Color'], ff.inputs[1])
c1 = N('ShaderNodeMix'); c1.data_type = 'RGBA'; c1.location = (1000, 700)
S(c1, 'A_Color').default_value = (0.040, 0.080, 0.085, 1.0)
S(c1, 'B_Color').default_value = (0.250, 0.350, 0.345, 1.0)
L(m1.outputs['Color'], S(c1, 'Factor_Float'))
c2 = N('ShaderNodeMix'); c2.data_type = 'RGBA'; c2.location = (1180, 700)
S(c2, 'B_Color').default_value = (0.010, 0.030, 0.038, 1.0)
L(O(c1), S(c2, 'A_Color')); L(tf.outputs[0], S(c2, 'Factor_Float'))
c3 = N('ShaderNodeMix'); c3.data_type = 'RGBA'; c3.location = (1360, 700)
S(c3, 'B_Color').default_value = (0.430, 0.520, 0.515, 1.0)
L(O(c2), S(c3, 'A_Color')); L(gr.outputs['Color'], S(c3, 'Factor_Float'))
c4 = N('ShaderNodeMix'); c4.data_type = 'RGBA'; c4.location = (1540, 700)
S(c4, 'B_Color').default_value = (0.480, 0.545, 0.540, 1.0)
L(O(c3), S(c4, 'A_Color')); L(mf.outputs[0], S(c4, 'Factor_Float'))
c5 = N('ShaderNodeMix'); c5.data_type = 'RGBA'; c5.location = (1720, 700)
S(c5, 'B_Color').default_value = (0.800, 0.840, 0.845, 1.0)
L(O(c4), S(c5, 'A_Color')); L(ff.outputs[0], S(c5, 'Factor_Float'))
L(O(c5), bsdf.inputs['Base Color'])
mat.diffuse_color = (0.120, 0.190, 0.195, 1.0)
L(h.outputs[0], bsdf.inputs['Base Color'])
