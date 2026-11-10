mat.use_nodes = True
nt = mat.node_tree
nodes = nt.nodes
links = nt.links
nodes.clear()
out = nodes.new('ShaderNodeOutputMaterial'); out.location = (1120, 0)
bsdf = nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (880, 0)
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.5
bsdf.inputs['Specular IOR Level'].default_value = 0.0
bsdf.inputs['Emission Strength'].default_value = 0.0
links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

tc = nodes.new('ShaderNodeTexCoord'); tc.location = (-1560, 0)
sep = nodes.new('ShaderNodeSeparateXYZ'); sep.location = (-1380, 0)
links.new(tc.outputs['Generated'], sep.inputs['Vector'])
ua = nodes.new('ShaderNodeMath'); ua.operation = 'MULTIPLY'; ua.location = (-1200, 160)
ua.inputs[1].default_value = 6.283185307
links.new(sep.outputs['X'], ua.inputs[0])
va = nodes.new('ShaderNodeMath'); va.operation = 'MULTIPLY'; va.location = (-1200, -160)
va.inputs[1].default_value = 6.283185307
links.new(sep.outputs['Y'], va.inputs[0])
cu = nodes.new('ShaderNodeMath'); cu.operation = 'COSINE'; cu.location = (-1020, 280)
links.new(ua.outputs[0], cu.inputs[0])
su = nodes.new('ShaderNodeMath'); su.operation = 'SINE'; su.location = (-1020, 130)
links.new(ua.outputs[0], su.inputs[0])
cv = nodes.new('ShaderNodeMath'); cv.operation = 'COSINE'; cv.location = (-1020, -30)
links.new(va.outputs[0], cv.inputs[0])
sv = nodes.new('ShaderNodeMath'); sv.operation = 'SINE'; sv.location = (-1020, -190)
links.new(va.outputs[0], sv.inputs[0])
P = nodes.new('ShaderNodeCombineXYZ'); P.location = (-840, 120)
links.new(cu.outputs[0], P.inputs['X'])
links.new(su.outputs[0], P.inputs['Y'])
links.new(cv.outputs[0], P.inputs['Z'])

ob = nodes.new('ShaderNodeVectorMath'); ob.operation = 'ADD'; ob.location = (-840, -80)
ob.inputs[1].default_value = (3.7, -2.1, 5.3)
links.new(P.outputs['Vector'], ob.inputs[0])
ow = nodes.new('ShaderNodeMath'); ow.operation = 'ADD'; ow.location = (-840, -240)
ow.inputs[1].default_value = 1.9
links.new(sv.outputs[0], ow.inputs[0])
oc = nodes.new('ShaderNodeVectorMath'); oc.operation = 'ADD'; oc.location = (-840, -400)
oc.inputs[1].default_value = (-4.4, 6.2, 1.3)
links.new(P.outputs['Vector'], oc.inputs[0])
od = nodes.new('ShaderNodeMath'); od.operation = 'ADD'; od.location = (-840, -560)
od.inputs[1].default_value = -3.3
links.new(sv.outputs[0], od.inputs[0])

vA = nodes.new('ShaderNodeTexVoronoi'); vA.location = (-620, 260)
vA.voronoi_dimensions = '4D'
vA.feature = 'F1'
vA.inputs['Scale'].default_value = 2.4
vA.inputs['Randomness'].default_value = 1.0
links.new(P.outputs['Vector'], vA.inputs['Vector'])
links.new(sv.outputs[0], vA.inputs['W'])

vB = nodes.new('ShaderNodeTexVoronoi'); vB.location = (-620, -80)
vB.voronoi_dimensions = '4D'
vB.feature = 'F1'
vB.inputs['Scale'].default_value = 6.0
vB.inputs['Randomness'].default_value = 1.0
links.new(ob.outputs['Vector'], vB.inputs['Vector'])
links.new(ow.outputs[0], vB.inputs['W'])

ns = nodes.new('ShaderNodeTexNoise'); ns.location = (-620, -420)
ns.noise_dimensions = '4D'
ns.inputs['Scale'].default_value = 1.6
ns.inputs['Detail'].default_value = 4.0
ns.inputs['Roughness'].default_value = 0.62
ns.inputs['Distortion'].default_value = 0.8
links.new(oc.outputs['Vector'], ns.inputs['Vector'])
links.new(od.outputs[0], ns.inputs['W'])

t1 = nodes.new('ShaderNodeMath'); t1.operation = 'MULTIPLY_ADD'; t1.location = (-360, 260)
t1.inputs[1].default_value = -1.50
t1.inputs[2].default_value = 1.376
links.new(vA.outputs['Distance'], t1.inputs[0])
t2 = nodes.new('ShaderNodeMath'); t2.operation = 'MULTIPLY_ADD'; t2.location = (-360, -420)
t2.inputs[1].default_value = 1.40
t2.inputs[2].default_value = -0.70
links.new(ns.outputs[0], t2.inputs[0])
t3 = nodes.new('ShaderNodeMath'); t3.operation = 'MULTIPLY_ADD'; t3.location = (-360, -80)
t3.inputs[1].default_value = -0.40
t3.inputs[2].default_value = 0.2376
links.new(vB.outputs['Distance'], t3.inputs[0])
s1 = nodes.new('ShaderNodeMath'); s1.operation = 'ADD'; s1.location = (-120, 100)
links.new(t1.outputs[0], s1.inputs[0])
links.new(t2.outputs[0], s1.inputs[1])
s2 = nodes.new('ShaderNodeMath'); s2.operation = 'ADD'; s2.use_clamp = True; s2.location = (100, 0)
links.new(s1.outputs[0], s2.inputs[0])
links.new(t3.outputs[0], s2.inputs[1])

ramp = nodes.new('ShaderNodeValToRGB'); ramp.location = (340, 0)
el = ramp.color_ramp.elements
el[0].position = 0.0;  el[0].color = (0.010, 0.026, 0.012, 1.0)
el[1].position = 1.0;  el[1].color = (0.560, 0.700, 0.230, 1.0)
e = el.new(0.30); e.color = (0.035, 0.105, 0.045, 1.0)
e = el.new(0.52); e.color = (0.100, 0.330, 0.120, 1.0)
e = el.new(0.78); e.color = (0.270, 0.500, 0.150, 1.0)
links.new(s2.outputs[0], ramp.inputs['Fac'])
links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
