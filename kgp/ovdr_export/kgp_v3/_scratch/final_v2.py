mat.use_nodes = True
nt = mat.node_tree
nodes = nt.nodes
links = nt.links
nodes.clear()
out = nodes.new('ShaderNodeOutputMaterial'); out.location = (1320, 0)
bsdf = nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (1080, 0)
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.5
bsdf.inputs['Specular IOR Level'].default_value = 0.0
bsdf.inputs['Emission Strength'].default_value = 0.0
links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

tc = nodes.new('ShaderNodeTexCoord'); tc.location = (-1700, 0)
sep = nodes.new('ShaderNodeSeparateXYZ'); sep.location = (-1520, 0)
links.new(tc.outputs['Generated'], sep.inputs['Vector'])
ua = nodes.new('ShaderNodeMath'); ua.operation = 'MULTIPLY'; ua.location = (-1340, 160)
ua.inputs[1].default_value = 6.283185307
links.new(sep.outputs['X'], ua.inputs[0])
va = nodes.new('ShaderNodeMath'); va.operation = 'MULTIPLY'; va.location = (-1340, -160)
va.inputs[1].default_value = 6.283185307
links.new(sep.outputs['Y'], va.inputs[0])
cu = nodes.new('ShaderNodeMath'); cu.operation = 'COSINE'; cu.location = (-1160, 300)
links.new(ua.outputs[0], cu.inputs[0])
su = nodes.new('ShaderNodeMath'); su.operation = 'SINE'; su.location = (-1160, 150)
links.new(ua.outputs[0], su.inputs[0])
cv = nodes.new('ShaderNodeMath'); cv.operation = 'COSINE'; cv.location = (-1160, 0)
links.new(va.outputs[0], cv.inputs[0])
sv = nodes.new('ShaderNodeMath'); sv.operation = 'SINE'; sv.location = (-1160, -150)
links.new(va.outputs[0], sv.inputs[0])
P = nodes.new('ShaderNodeCombineXYZ'); P.location = (-980, 200)
links.new(cu.outputs[0], P.inputs['X'])
links.new(su.outputs[0], P.inputs['Y'])
links.new(cv.outputs[0], P.inputs['Z'])

pb = nodes.new('ShaderNodeVectorMath'); pb.operation = 'ADD'; pb.location = (-980, 20)
pb.inputs[1].default_value = (3.7, -2.1, 5.3)
links.new(P.outputs['Vector'], pb.inputs[0])
wb = nodes.new('ShaderNodeMath'); wb.operation = 'ADD'; wb.location = (-980, -140)
wb.inputs[1].default_value = 1.9
links.new(sv.outputs[0], wb.inputs[0])
pc = nodes.new('ShaderNodeVectorMath'); pc.operation = 'ADD'; pc.location = (-980, -300)
pc.inputs[1].default_value = (-4.4, 6.2, 1.3)
links.new(P.outputs['Vector'], pc.inputs[0])
wc = nodes.new('ShaderNodeMath'); wc.operation = 'ADD'; wc.location = (-980, -460)
wc.inputs[1].default_value = -3.3
links.new(sv.outputs[0], wc.inputs[0])

vA = nodes.new('ShaderNodeTexVoronoi'); vA.location = (-760, 300)
vA.voronoi_dimensions = '4D'
vA.feature = 'F1'
vA.inputs['Scale'].default_value = 3.0
vA.inputs['Randomness'].default_value = 1.0
links.new(P.outputs['Vector'], vA.inputs['Vector'])
links.new(sv.outputs[0], vA.inputs['W'])
cA = nodes.new('ShaderNodeSeparateColor'); cA.mode = 'RGB'; cA.location = (-540, 420)
links.new(vA.outputs['Color'], cA.inputs['Color'])

vB = nodes.new('ShaderNodeTexVoronoi'); vB.location = (-760, -40)
vB.voronoi_dimensions = '4D'
vB.feature = 'F1'
vB.inputs['Scale'].default_value = 7.0
vB.inputs['Randomness'].default_value = 1.0
links.new(pb.outputs['Vector'], vB.inputs['Vector'])
links.new(wb.outputs[0], vB.inputs['W'])
cB = nodes.new('ShaderNodeSeparateColor'); cB.mode = 'RGB'; cB.location = (-540, 80)
links.new(vB.outputs['Color'], cB.inputs['Color'])

ns = nodes.new('ShaderNodeTexNoise'); ns.location = (-760, -420)
ns.noise_dimensions = '4D'
ns.inputs['Scale'].default_value = 1.6
ns.inputs['Detail'].default_value = 4.0
ns.inputs['Roughness'].default_value = 0.62
ns.inputs['Distortion'].default_value = 0.8
links.new(pc.outputs['Vector'], ns.inputs['Vector'])
links.new(wc.outputs[0], ns.inputs['W'])

t1 = nodes.new('ShaderNodeMath'); t1.operation = 'MULTIPLY_ADD'; t1.location = (-300, 420)
t1.inputs[1].default_value = 0.62
t1.inputs[2].default_value = 0.19
links.new(cA.outputs[0], t1.inputs[0])
t2 = nodes.new('ShaderNodeMath'); t2.operation = 'MULTIPLY_ADD'; t2.location = (-300, 260)
t2.inputs[1].default_value = -1.05
t2.inputs[2].default_value = 0.6237
links.new(vA.outputs['Distance'], t2.inputs[0])
t3 = nodes.new('ShaderNodeMath'); t3.operation = 'MULTIPLY_ADD'; t3.location = (-300, 80)
t3.inputs[1].default_value = 0.28
t3.inputs[2].default_value = -0.14
links.new(cB.outputs[0], t3.inputs[0])
t4 = nodes.new('ShaderNodeMath'); t4.operation = 'MULTIPLY_ADD'; t4.location = (-300, -80)
t4.inputs[1].default_value = -0.22
t4.inputs[2].default_value = 0.1307
links.new(vB.outputs['Distance'], t4.inputs[0])
t5 = nodes.new('ShaderNodeMath'); t5.operation = 'MULTIPLY_ADD'; t5.location = (-300, -420)
t5.inputs[1].default_value = 1.10
t5.inputs[2].default_value = -0.55
links.new(ns.outputs[0], t5.inputs[0])

a1 = nodes.new('ShaderNodeMath'); a1.operation = 'ADD'; a1.location = (-60, 340)
links.new(t1.outputs[0], a1.inputs[0])
links.new(t2.outputs[0], a1.inputs[1])
a2 = nodes.new('ShaderNodeMath'); a2.operation = 'ADD'; a2.location = (-60, 0)
links.new(t3.outputs[0], a2.inputs[0])
links.new(t4.outputs[0], a2.inputs[1])
a3 = nodes.new('ShaderNodeMath'); a3.operation = 'ADD'; a3.location = (160, 170)
links.new(a1.outputs[0], a3.inputs[0])
links.new(a2.outputs[0], a3.inputs[1])
a4 = nodes.new('ShaderNodeMath'); a4.operation = 'ADD'; a4.use_clamp = True; a4.location = (380, 0)
links.new(a3.outputs[0], a4.inputs[0])
links.new(t5.outputs[0], a4.inputs[1])

ramp = nodes.new('ShaderNodeValToRGB'); ramp.location = (600, 0)
el = ramp.color_ramp.elements
el[0].position = 0.0;  el[0].color = (0.010, 0.026, 0.012, 1.0)
el[1].position = 1.0;  el[1].color = (0.500, 0.660, 0.220, 1.0)
e = el.new(0.30); e.color = (0.035, 0.105, 0.045, 1.0)
e = el.new(0.52); e.color = (0.100, 0.330, 0.120, 1.0)
e = el.new(0.78); e.color = (0.270, 0.500, 0.150, 1.0)
links.new(a4.outputs[0], ramp.inputs['Fac'])
links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
