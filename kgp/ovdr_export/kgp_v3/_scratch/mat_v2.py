mat.use_nodes = True
nt = mat.node_tree
nodes = nt.nodes
links = nt.links
nodes.clear()
BASE = 0.620
KC = 0.25
KM = 0.40
KG = 1.00
KS = 0.48
KH = 7.00
out = nodes.new('ShaderNodeOutputMaterial'); out.location = (1720, 0)
bsdf = nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (1480, 0)
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.5
links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
tc = nodes.new('ShaderNodeTexCoord'); tc.location = (-2060, 0)
mp = nodes.new('ShaderNodeMapping'); mp.location = (-1880, 0)
mp.inputs['Scale'].default_value = (6.283185, 6.283185, 6.283185)
links.new(tc.outputs['Generated'], mp.inputs['Vector'])
sep = nodes.new('ShaderNodeSeparateXYZ'); sep.location = (-1700, 0)
links.new(mp.outputs['Vector'], sep.inputs['Vector'])
cx = nodes.new('ShaderNodeMath'); cx.operation = 'COSINE'; cx.location = (-1520, 320)
sx = nodes.new('ShaderNodeMath'); sx.operation = 'SINE'; sx.location = (-1520, 160)
cy = nodes.new('ShaderNodeMath'); cy.operation = 'COSINE'; cy.location = (-1520, 0)
sy = nodes.new('ShaderNodeMath'); sy.operation = 'SINE'; sy.location = (-1520, -160)
links.new(sep.outputs['X'], cx.inputs[0]); links.new(sep.outputs['X'], sx.inputs[0])
links.new(sep.outputs['Y'], cy.inputs[0]); links.new(sep.outputs['Y'], sy.inputs[0])
cmb = nodes.new('ShaderNodeCombineXYZ'); cmb.location = (-1330, 200)
links.new(cx.outputs[0], cmb.inputs['X']); links.new(sx.outputs[0], cmb.inputs['Y']); links.new(cy.outputs[0], cmb.inputs['Z'])
ay = nodes.new('ShaderNodeMath'); ay.operation = 'MULTIPLY'; ay.inputs[1].default_value = 0.10; ay.location = (-1330, -100)
aw = nodes.new('ShaderNodeMath'); aw.operation = 'MULTIPLY'; aw.inputs[1].default_value = 0.10; aw.location = (-1330, -260)
links.new(cy.outputs[0], ay.inputs[0]); links.new(sy.outputs[0], aw.inputs[0])
cmb2 = nodes.new('ShaderNodeCombineXYZ'); cmb2.location = (-1150, -160)
links.new(cx.outputs[0], cmb2.inputs['X']); links.new(sx.outputs[0], cmb2.inputs['Y']); links.new(ay.outputs[0], cmb2.inputs['Z'])
nh = nodes.new('ShaderNodeTexNoise'); nh.location = (-960, 620)
nh.inputs['Scale'].default_value = 0.32; nh.inputs['Detail'].default_value = 2.0
nh.inputs['Roughness'].default_value = 0.50; nh.inputs['Distortion'].default_value = 0.0
nc = nodes.new('ShaderNodeTexNoise'); nc.location = (-960, 400)
nc.inputs['Scale'].default_value = 1.35; nc.inputs['Detail'].default_value = 3.0
nc.inputs['Roughness'].default_value = 0.52; nc.inputs['Distortion'].default_value = 0.30
nd = nodes.new('ShaderNodeTexNoise'); nd.location = (-960, 180)
nd.inputs['Scale'].default_value = 6.00; nd.inputs['Detail'].default_value = 3.0
nd.inputs['Roughness'].default_value = 0.55; nd.inputs['Distortion'].default_value = 0.20
ng = nodes.new('ShaderNodeTexNoise'); ng.location = (-960, -40)
ng.inputs['Scale'].default_value = 19.0; ng.inputs['Detail'].default_value = 3.0
ng.inputs['Roughness'].default_value = 0.60; ng.inputs['Distortion'].default_value = 0.0
nv = nodes.new('ShaderNodeTexNoise'); nv.location = (-960, -480)
nv.inputs['Scale'].default_value = 4.50; nv.inputs['Detail'].default_value = 5.0
nv.inputs['Roughness'].default_value = 0.50; nv.inputs['Distortion'].default_value = 0.85
for n in (nh, nc, nd, ng, nv):
    n.noise_dimensions = '4D'
    links.new(cmb.outputs['Vector'], n.inputs['Vector'])
    links.new(sy.outputs[0], n.inputs['W'])
nst = nodes.new('ShaderNodeTexNoise'); nst.location = (-960, -260)
nst.inputs['Scale'].default_value = 14.0; nst.inputs['Detail'].default_value = 3.0
nst.inputs['Roughness'].default_value = 0.55; nst.inputs['Distortion'].default_value = 0.0
nst.noise_dimensions = '4D'
links.new(cmb2.outputs['Vector'], nst.inputs['Vector'])
links.new(aw.outputs[0], nst.inputs['W'])
gc = nodes.new('ShaderNodeMath'); gc.operation = 'MULTIPLY_ADD'; gc.location = (-700, 400)
gc.inputs[1].default_value = KC; gc.inputs[2].default_value = -0.5 * KC
links.new(nc.outputs['Fac'], gc.inputs[0])
gm = nodes.new('ShaderNodeMath'); gm.operation = 'MULTIPLY_ADD'; gm.location = (-700, 180)
gm.inputs[1].default_value = KM; gm.inputs[2].default_value = -0.5 * KM
links.new(nd.outputs['Fac'], gm.inputs[0])
gg = nodes.new('ShaderNodeMath'); gg.operation = 'MULTIPLY_ADD'; gg.location = (-700, -40)
gg.inputs[1].default_value = KG; gg.inputs[2].default_value = -0.5 * KG
links.new(ng.outputs['Fac'], gg.inputs[0])
gs = nodes.new('ShaderNodeMath'); gs.operation = 'MULTIPLY_ADD'; gs.location = (-700, -260)
gs.inputs[1].default_value = KS; gs.inputs[2].default_value = -0.5 * KS
links.new(nst.outputs['Fac'], gs.inputs[0])
a1 = nodes.new('ShaderNodeMath'); a1.operation = 'ADD'; a1.location = (-480, 300)
links.new(gc.outputs[0], a1.inputs[0]); links.new(gm.outputs[0], a1.inputs[1])
a2 = nodes.new('ShaderNodeMath'); a2.operation = 'ADD'; a2.location = (-480, -140)
links.new(gg.outputs[0], a2.inputs[0]); links.new(gs.outputs[0], a2.inputs[1])
a3 = nodes.new('ShaderNodeMath'); a3.operation = 'ADD'; a3.location = (-280, 80)
links.new(a1.outputs[0], a3.inputs[0]); links.new(a2.outputs[0], a3.inputs[1])
bs = nodes.new('ShaderNodeMath'); bs.operation = 'ADD'; bs.location = (-80, 80)
bs.inputs[1].default_value = BASE
links.new(a3.outputs[0], bs.inputs[0])
ce = nodes.new('ShaderNodeMath'); ce.operation = 'MULTIPLY_ADD'; ce.location = (-700, -480)
ce.inputs[1].default_value = 1.0; ce.inputs[2].default_value = -0.5
links.new(nv.outputs['Fac'], ce.inputs[0])
ab = nodes.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'; ab.location = (-500, -480)
links.new(ce.outputs[0], ab.inputs[0])
ax = nodes.new('ShaderNodeMath'); ax.operation = 'MULTIPLY'; ax.inputs[1].default_value = 20.0; ax.location = (-300, -480)
links.new(ab.outputs[0], ax.inputs[0])
vn = nodes.new('ShaderNodeValToRGB'); vn.location = (-100, -520)
ve = vn.color_ramp.elements
ve[0].position = 0.0; ve[0].color = (0.44, 0.44, 0.44, 1.0)
ve[1].position = 0.22; ve[1].color = (0.0, 0.0, 0.0, 1.0)
ve.new(0.05).color = (0.24, 0.24, 0.24, 1.0)
links.new(ax.outputs[0], vn.inputs['Fac'])
sb = nodes.new('ShaderNodeMath'); sb.operation = 'SUBTRACT'; sb.use_clamp = True; sb.location = (420, 0)
links.new(bs.outputs[0], sb.inputs[0]); links.new(vn.outputs['Color'], sb.inputs[1])
stops = [
    (0.00, (0.012, 0.013, 0.010)),
    (0.08, (0.022, 0.022, 0.014)),
    (0.18, (0.050, 0.036, 0.019)),
    (0.28, (0.105, 0.064, 0.026)),
    (0.38, (0.180, 0.114, 0.040)),
    (0.46, (0.250, 0.162, 0.056)),
    (0.54, (0.310, 0.203, 0.070)),
    (0.62, (0.375, 0.249, 0.086)),
    (0.70, (0.450, 0.303, 0.106)),
    (0.78, (0.540, 0.369, 0.132)),
    (0.86, (0.680, 0.481, 0.178)),
    (0.94, (0.850, 0.641, 0.252)),
    (1.00, (0.990, 0.800, 0.360)),
]
gd = nodes.new('ShaderNodeValToRGB'); gd.location = (660, 120)
el = gd.color_ramp.elements
el[0].position = stops[0][0]; el[0].color = (stops[0][1][0], stops[0][1][1], stops[0][1][2], 1.0)
el[1].position = stops[-1][0]; el[1].color = (stops[-1][1][0], stops[-1][1][1], stops[-1][1][2], 1.0)
for p, c in stops[1:-1]:
    el.new(p).color = (c[0], c[1], c[2], 1.0)
links.new(sb.outputs[0], gd.inputs['Fac'])
th = nodes.new('ShaderNodeMath'); th.operation = 'MULTIPLY_ADD'; th.use_clamp = True; th.location = (-700, 620)
th.inputs[1].default_value = KH; th.inputs[2].default_value = 0.5 - 0.5 * KH
links.new(nh.outputs['Fac'], th.inputs[0])
tn = nodes.new('ShaderNodeValToRGB'); tn.location = (660, -340)
te = tn.color_ramp.elements
te[0].position = 0.0; te[0].color = (1.10, 1.00, 0.78, 1.0)
te[1].position = 1.0; te[1].color = (0.87, 1.00, 1.26, 1.0)
te.new(0.5).color = (1.00, 1.00, 1.00, 1.0)
links.new(th.outputs[0], tn.inputs['Fac'])
mul = nodes.new('ShaderNodeVectorMath'); mul.operation = 'MULTIPLY'; mul.location = (1160, 0)
links.new(gd.outputs['Color'], mul.inputs[0])
links.new(tn.outputs['Color'], mul.inputs[1])
links.new(mul.outputs['Vector'], bsdf.inputs['Base Color'])
