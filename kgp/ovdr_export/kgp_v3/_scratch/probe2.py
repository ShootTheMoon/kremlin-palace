mat.use_nodes = True
nt = mat.node_tree
nodes = nt.nodes
links = nt.links
nodes.clear()
out = nodes.new('ShaderNodeOutputMaterial')
bsdf = nodes.new('ShaderNodeBsdfPrincipled')
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.5
bsdf.inputs['Specular IOR Level'].default_value = 0.0
links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

TAU = 6.283185307
tc = nodes.new('ShaderNodeTexCoord')
sep = nodes.new('ShaderNodeSeparateXYZ')
links.new(tc.outputs['Generated'], sep.inputs['Vector'])
ua = nodes.new('ShaderNodeMath'); ua.operation = 'MULTIPLY'; ua.inputs[1].default_value = TAU
links.new(sep.outputs['X'], ua.inputs[0])
va = nodes.new('ShaderNodeMath'); va.operation = 'MULTIPLY'; va.inputs[1].default_value = TAU
links.new(sep.outputs['Y'], va.inputs[0])
cu = nodes.new('ShaderNodeMath'); cu.operation = 'COSINE'; links.new(ua.outputs[0], cu.inputs[0])
su = nodes.new('ShaderNodeMath'); su.operation = 'SINE';   links.new(ua.outputs[0], su.inputs[0])
cv = nodes.new('ShaderNodeMath'); cv.operation = 'COSINE'; links.new(va.outputs[0], cv.inputs[0])
sv = nodes.new('ShaderNodeMath'); sv.operation = 'SINE';   links.new(va.outputs[0], sv.inputs[0])
P = nodes.new('ShaderNodeCombineXYZ')
links.new(cu.outputs[0], P.inputs['X'])
links.new(su.outputs[0], P.inputs['Y'])
links.new(cv.outputs[0], P.inputs['Z'])

def offv(vec, dx):
    a = nodes.new('ShaderNodeVectorMath'); a.operation = 'ADD'
    a.inputs[1].default_value = dx
    links.new(vec, a.inputs[0])
    return a.outputs['Vector']

def offw(w, d):
    a = nodes.new('ShaderNodeMath'); a.operation = 'ADD'
    a.inputs[1].default_value = d
    links.new(w, a.inputs[0])
    return a.outputs[0]

vA = nodes.new('ShaderNodeTexVoronoi'); vA.voronoi_dimensions = '4D'; vA.feature = 'F1'
vA.inputs['Scale'].default_value = 2.4
vA.inputs['Randomness'].default_value = 1.0
links.new(P.outputs['Vector'], vA.inputs['Vector'])
links.new(sv.outputs[0], vA.inputs['W'])

vB = nodes.new('ShaderNodeTexVoronoi'); vB.voronoi_dimensions = '4D'; vB.feature = 'F1'
vB.inputs['Scale'].default_value = 6.0
vB.inputs['Randomness'].default_value = 1.0
links.new(offv(P.outputs['Vector'], (3.7, -2.1, 5.3)), vB.inputs['Vector'])
links.new(offw(sv.outputs[0], 1.9), vB.inputs['W'])

ns = nodes.new('ShaderNodeTexNoise'); ns.noise_dimensions = '4D'
ns.inputs['Scale'].default_value = 1.6
ns.inputs['Detail'].default_value = 4.0
ns.inputs['Roughness'].default_value = 0.62
ns.inputs['Distortion'].default_value = 0.8
links.new(offv(P.outputs['Vector'], (-4.4, 6.2, 1.3)), ns.inputs['Vector'])
links.new(offw(sv.outputs[0], -3.3), ns.inputs['W'])

t1 = nodes.new('ShaderNodeMath'); t1.operation = 'MULTIPLY_ADD'
t1.inputs[1].default_value = -1.50; t1.inputs[2].default_value = 1.376
links.new(vA.outputs['Distance'], t1.inputs[0])
t2 = nodes.new('ShaderNodeMath'); t2.operation = 'MULTIPLY_ADD'
t2.inputs[1].default_value = 1.40; t2.inputs[2].default_value = -0.70
links.new(ns.outputs[0], t2.inputs[0])
t3 = nodes.new('ShaderNodeMath'); t3.operation = 'MULTIPLY_ADD'
t3.inputs[1].default_value = -0.40; t3.inputs[2].default_value = 0.2376
links.new(vB.outputs['Distance'], t3.inputs[0])
s1 = nodes.new('ShaderNodeMath'); s1.operation = 'ADD'
links.new(t1.outputs[0], s1.inputs[0]); links.new(t2.outputs[0], s1.inputs[1])
s2 = nodes.new('ShaderNodeMath'); s2.operation = 'ADD'; s2.use_clamp = True
links.new(s1.outputs[0], s2.inputs[0]); links.new(t3.outputs[0], s2.inputs[1])

cc = nodes.new('ShaderNodeCombineColor'); cc.mode = 'RGB'
links.new(s2.outputs[0], cc.inputs[0])
links.new(vA.outputs['Distance'], cc.inputs[1])
links.new(vB.outputs['Distance'], cc.inputs[2])
links.new(cc.outputs['Color'], bsdf.inputs['Base Color'])
