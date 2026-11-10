mat.use_nodes = True
nt = mat.node_tree
nodes = nt.nodes
links = nt.links
nodes.clear()

tc = nodes.new('ShaderNodeTexCoord')
sep = nodes.new('ShaderNodeSeparateXYZ')
links.new(tc.outputs['Generated'], sep.inputs['Vector'])
mu = nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = 6.2831853
mv = nodes.new('ShaderNodeMath'); mv.operation = 'MULTIPLY'; mv.inputs[1].default_value = 6.2831853
links.new(sep.outputs['X'], mu.inputs[0]); links.new(sep.outputs['Y'], mv.inputs[0])
cu = nodes.new('ShaderNodeMath'); cu.operation = 'COSINE'; links.new(mu.outputs['Value'], cu.inputs[0])
su = nodes.new('ShaderNodeMath'); su.operation = 'SINE';   links.new(mu.outputs['Value'], su.inputs[0])
cv = nodes.new('ShaderNodeMath'); cv.operation = 'COSINE'; links.new(mv.outputs['Value'], cv.inputs[0])
sv = nodes.new('ShaderNodeMath'); sv.operation = 'SINE';   links.new(mv.outputs['Value'], sv.inputs[0])
cmb = nodes.new('ShaderNodeCombineXYZ')
links.new(cu.outputs['Value'], cmb.inputs['X']); links.new(su.outputs['Value'], cmb.inputs['Y']); links.new(cv.outputs['Value'], cmb.inputs['Z'])

RX, RY = 5.0, 1.45
CX, CY = 2.2, 1.0
va = nodes.new('ShaderNodeVectorMath'); va.operation = 'MULTIPLY'; va.inputs[1].default_value = (RX, RX, RY)
wa = nodes.new('ShaderNodeMath'); wa.operation = 'MULTIPLY'; wa.inputs[1].default_value = RY
vb = nodes.new('ShaderNodeVectorMath'); vb.operation = 'MULTIPLY'; vb.inputs[1].default_value = (CX, CX, CY)
wb = nodes.new('ShaderNodeMath'); wb.operation = 'MULTIPLY'; wb.inputs[1].default_value = CY
links.new(cmb.outputs['Vector'], va.inputs[0]); links.new(sv.outputs['Value'], wa.inputs[0])
links.new(cmb.outputs['Vector'], vb.inputs[0]); links.new(sv.outputs['Value'], wb.inputs[0])

nn = nodes.new('ShaderNodeTexNoise'); nn.noise_dimensions = '4D'
nn.inputs['Scale'].default_value = 1.0
nn.inputs['Detail'].default_value = 2.0
nn.inputs['Roughness'].default_value = 0.5
nn.inputs['Distortion'].default_value = 0.25
links.new(va.outputs['Vector'], nn.inputs['Vector']); links.new(wa.outputs['Value'], nn.inputs['W'])

ncr = nodes.new('ShaderNodeTexNoise'); ncr.noise_dimensions = '4D'
ncr.inputs['Scale'].default_value = 1.0
ncr.inputs['Detail'].default_value = 3.0
ncr.inputs['Distortion'].default_value = 0.5
links.new(vb.outputs['Vector'], ncr.inputs['Vector']); links.new(wb.outputs['Value'], ncr.inputs['W'])

mul = nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 0.40
mad = nodes.new('ShaderNodeMath'); mad.operation = 'MULTIPLY_ADD'; mad.inputs[1].default_value = 0.60
links.new(ncr.outputs['Fac'], mul.inputs[0]); links.new(nn.outputs['Fac'], mad.inputs[0])
links.new(mul.outputs['Value'], mad.inputs[2])

cc = nodes.new('ShaderNodeCombineColor'); cc.mode = 'RGB'
links.new(mad.outputs['Value'], cc.inputs['Red'])
links.new(nn.outputs['Fac'], cc.inputs['Green'])
links.new(ncr.outputs['Fac'], cc.inputs['Blue'])

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.5
out = nodes.new('ShaderNodeOutputMaterial')
links.new(cc.outputs['Color'], bsdf.inputs['Base Color'])
links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
