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

def torus(rx, ry):
    v = nodes.new('ShaderNodeVectorMath'); v.operation = 'MULTIPLY'; v.inputs[1].default_value = (rx, rx, ry)
    w = nodes.new('ShaderNodeMath'); w.operation = 'MULTIPLY'; w.inputs[1].default_value = ry
    links.new(cmb.outputs['Vector'], v.inputs[0]); links.new(sv.outputs['Value'], w.inputs[0])
    return v, w

va, wa = torus(5.0, 1.45)
vb, wb = torus(2.2, 1.0)
vc, wc = torus(11.0, 3.2)

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

nf = nodes.new('ShaderNodeTexNoise'); nf.noise_dimensions = '4D'
nf.inputs['Scale'].default_value = 1.0
nf.inputs['Detail'].default_value = 1.0
nf.inputs['Roughness'].default_value = 0.5
nf.inputs['Distortion'].default_value = 0.10
links.new(vc.outputs['Vector'], nf.inputs['Vector']); links.new(wc.outputs['Value'], nf.inputs['W'])

m1 = nodes.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; m1.inputs[1].default_value = 0.34
links.new(ncr.outputs['Fac'], m1.inputs[0])
m2 = nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY_ADD'; m2.inputs[1].default_value = 0.12
links.new(nf.outputs['Fac'], m2.inputs[0]); links.new(m1.outputs['Value'], m2.inputs[2])
m3 = nodes.new('ShaderNodeMath'); m3.operation = 'MULTIPLY_ADD'; m3.inputs[1].default_value = 0.54
links.new(nn.outputs['Fac'], m3.inputs[0]); links.new(m2.outputs['Value'], m3.inputs[2])

sy = nodes.new('ShaderNodeSeparateXYZ')
links.new(ncr.outputs['Color'], sy.inputs['Vector'])

cc = nodes.new('ShaderNodeCombineColor'); cc.mode = 'RGB'
links.new(m3.outputs['Value'], cc.inputs['Red'])
links.new(nf.outputs['Fac'], cc.inputs['Green'])
links.new(sy.outputs['Y'], cc.inputs['Blue'])

bsdf = nodes.new('ShaderNodeBsdfPrincipled')
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.5
out = nodes.new('ShaderNodeOutputMaterial')
links.new(cc.outputs['Color'], bsdf.inputs['Base Color'])
links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
