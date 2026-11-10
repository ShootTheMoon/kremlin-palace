mat.use_nodes = True
nt = mat.node_tree
nodes = nt.nodes
links = nt.links
nodes.clear()
out = nodes.new('ShaderNodeOutputMaterial'); out.location = (1240, 0)
bsdf = nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (1000, 0)
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.5
links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
tc = nodes.new('ShaderNodeTexCoord'); tc.location = (-1560, 0)
mp = nodes.new('ShaderNodeMapping'); mp.location = (-1380, 0)
mp.inputs['Scale'].default_value = (6.28319, 6.28319, 6.28319)
links.new(tc.outputs['Generated'], mp.inputs['Vector'])
sep = nodes.new('ShaderNodeSeparateXYZ'); sep.location = (-1200, 0)
links.new(mp.outputs['Vector'], sep.inputs['Vector'])
cx = nodes.new('ShaderNodeMath'); cx.operation = 'COSINE'; cx.location = (-1020, 260)
sx = nodes.new('ShaderNodeMath'); sx.operation = 'SINE'; sx.location = (-1020, 100)
cy = nodes.new('ShaderNodeMath'); cy.operation = 'COSINE'; cy.location = (-1020, -60)
sy = nodes.new('ShaderNodeMath'); sy.operation = 'SINE'; sy.location = (-1020, -220)
links.new(sep.outputs['X'], cx.inputs[0]); links.new(sep.outputs['X'], sx.inputs[0])
links.new(sep.outputs['Y'], cy.inputs[0]); links.new(sep.outputs['Y'], sy.inputs[0])
cmb = nodes.new('ShaderNodeCombineXYZ'); cmb.location = (-830, 120)
links.new(cx.outputs[0], cmb.inputs['X']); links.new(sx.outputs[0], cmb.inputs['Y']); links.new(cy.outputs[0], cmb.inputs['Z'])
nm = nodes.new('ShaderNodeTexNoise'); nm.location = (-620, 330)
nm.inputs['Scale'].default_value = 1.90; nm.inputs['Detail'].default_value = 10.0
nm.inputs['Roughness'].default_value = 0.60; nm.inputs['Distortion'].default_value = 0.25
ng = nodes.new('ShaderNodeTexNoise'); ng.location = (-620, 90)
ng.inputs['Scale'].default_value = 17.5; ng.inputs['Detail'].default_value = 4.0; ng.inputs['Roughness'].default_value = 0.55
nv = nodes.new('ShaderNodeTexNoise'); nv.location = (-620, -190)
nv.inputs['Scale'].default_value = 2.90; nv.inputs['Detail'].default_value = 4.0
nv.inputs['Roughness'].default_value = 0.5; nv.inputs['Distortion'].default_value = 1.10
for n in (nm, ng, nv): n.noise_dimensions = '4D'; links.new(cmb.outputs['Vector'], n.inputs['Vector']); links.new(sy.outputs[0], n.inputs['W'])
ct = nodes.new('ShaderNodeMath'); ct.operation = 'MULTIPLY_ADD'; ct.location = (-380, 330)
ct.inputs[1].default_value = 1.45; ct.inputs[2].default_value = -0.15
links.new(nm.outputs['Fac'], ct.inputs[0])
gr = nodes.new('ShaderNodeMath'); gr.operation = 'MULTIPLY_ADD'; gr.location = (-380, 110)
gr.inputs[1].default_value = 0.36; gr.inputs[2].default_value = -0.18
links.new(ng.outputs['Fac'], gr.inputs[0])
ad = nodes.new('ShaderNodeMath'); ad.operation = 'ADD'; ad.location = (-170, 230)
links.new(ct.outputs[0], ad.inputs[0]); links.new(gr.outputs[0], ad.inputs[1])
ce = nodes.new('ShaderNodeMath'); ce.operation = 'MULTIPLY_ADD'; ce.location = (-380, -190)
ce.inputs[1].default_value = 1.0; ce.inputs[2].default_value = -0.5
links.new(nv.outputs['Fac'], ce.inputs[0])
ab = nodes.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'; ab.location = (-170, -190)
links.new(ce.outputs[0], ab.inputs[0])
vn = nodes.new('ShaderNodeValToRGB'); vn.location = (30, -240)
vn.color_ramp.elements[0].position = 0.0; vn.color_ramp.elements[0].color = (0.15, 0.15, 0.15, 1.0)
vn.color_ramp.elements[1].position = 0.035; vn.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)
links.new(ab.outputs[0], vn.inputs['Fac'])
sb = nodes.new('ShaderNodeMath'); sb.operation = 'SUBTRACT'; sb.use_clamp = True; sb.location = (380, 0)
links.new(ad.outputs[0], sb.inputs[0]); links.new(vn.outputs['Color'], sb.inputs[1])
gd = nodes.new('ShaderNodeValToRGB'); gd.location = (600, 0)
el = gd.color_ramp.elements
el[0].position = 0.0; el[0].color = (0.020, 0.024, 0.016, 1.0)
el[1].position = 1.0; el[1].color = (0.995, 0.815, 0.300, 1.0)
for p, c in ((0.12, (0.045, 0.045, 0.026)), (0.26, (0.105, 0.072, 0.030)), (0.42, (0.235, 0.135, 0.038)), (0.58, (0.500, 0.290, 0.062)), (0.80, (0.780, 0.500, 0.115)), (0.92, (0.930, 0.690, 0.190))):
    el.new(p).color = (c[0], c[1], c[2], 1.0)
links.new(sb.outputs[0], gd.inputs['Fac'])
links.new(gd.outputs['Color'], bsdf.inputs['Base Color'])