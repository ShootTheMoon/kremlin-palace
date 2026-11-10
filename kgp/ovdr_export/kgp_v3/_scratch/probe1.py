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
cmb = nodes.new('ShaderNodeCombineXYZ')
links.new(cu.outputs[0], cmb.inputs['X'])
links.new(su.outputs[0], cmb.inputs['Y'])
links.new(cv.outputs[0], cmb.inputs['Z'])

vor = nodes.new('ShaderNodeTexVoronoi')
print("VOR dims opts:", [i.identifier for i in vor.bl_rna.properties['voronoi_dimensions'].enum_items])
vor.voronoi_dimensions = '4D'
vor.feature = 'F1'
vor.inputs['Scale'].default_value = 2.4
vor.inputs['Randomness'].default_value = 1.0
links.new(cmb.outputs['Vector'], vor.inputs['Vector'])
links.new(sv.outputs[0], vor.inputs['W'])
print("VOR in:", [s.name for s in vor.inputs], "out:", [s.name for s in vor.outputs])

vor2 = nodes.new('ShaderNodeTexVoronoi')
vor2.voronoi_dimensions = '4D'
vor2.feature = 'F1'
vor2.inputs['Scale'].default_value = 4.8
vor2.inputs['Randomness'].default_value = 1.0
links.new(cmb.outputs['Vector'], vor2.inputs['Vector'])
links.new(sv.outputs[0], vor2.inputs['W'])

nse = nodes.new('ShaderNodeTexNoise')
nse.noise_dimensions = '4D'
nse.inputs['Scale'].default_value = 1.6
nse.inputs['Detail'].default_value = 4.0
nse.inputs['Roughness'].default_value = 0.62
nse.inputs['Distortion'].default_value = 0.8
links.new(cmb.outputs['Vector'], nse.inputs['Vector'])
links.new(sv.outputs[0], nse.inputs['W'])
print("NSE in:", [s.name for s in nse.inputs], "out:", [s.name for s in nse.outputs])

cc = nodes.new('ShaderNodeCombineColor')
cc.mode = 'RGB'
print("CC in:", [s.name for s in cc.inputs])
links.new(vor.outputs['Distance'], cc.inputs[0])
links.new(nse.outputs['Fac'], cc.inputs[1])
links.new(vor2.outputs['Distance'], cc.inputs[2])
links.new(cc.outputs['Color'], bsdf.inputs['Base Color'])
