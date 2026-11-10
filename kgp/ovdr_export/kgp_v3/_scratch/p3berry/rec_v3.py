mat.use_nodes = True
nt = mat.node_tree
nodes = nt.nodes
links = nt.links
nodes.clear()
out = nodes.new('ShaderNodeOutputMaterial'); out.location = (1180, 0)
bsdf = nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (940, 0)
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.5
bsdf.inputs['Specular IOR Level'].default_value = 0.0
bsdf.inputs['Emission Strength'].default_value = 0.0
links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
tc = nodes.new('ShaderNodeTexCoord'); tc.location = (-1620, 0)
sep = nodes.new('ShaderNodeSeparateXYZ'); sep.location = (-1440, 0)
links.new(tc.outputs['Generated'], sep.inputs['Vector'])
au = nodes.new('ShaderNodeMath'); au.operation = 'MULTIPLY'; au.location = (-1260, 160)
au.inputs[1].default_value = 6.283185307
links.new(sep.outputs['X'], au.inputs[0])
av = nodes.new('ShaderNodeMath'); av.operation = 'MULTIPLY'; av.location = (-1260, -160)
av.inputs[1].default_value = 6.283185307
links.new(sep.outputs['Y'], av.inputs[0])
cu = nodes.new('ShaderNodeMath'); cu.operation = 'COSINE'; cu.location = (-1080, 300)
links.new(au.outputs[0], cu.inputs[0])
su = nodes.new('ShaderNodeMath'); su.operation = 'SINE'; su.location = (-1080, 160)
links.new(au.outputs[0], su.inputs[0])
cv = nodes.new('ShaderNodeMath'); cv.operation = 'COSINE'; cv.location = (-1080, 20)
links.new(av.outputs[0], cv.inputs[0])
sv = nodes.new('ShaderNodeMath'); sv.operation = 'SINE'; sv.location = (-1080, -140)
links.new(av.outputs[0], sv.inputs[0])
cmb = nodes.new('ShaderNodeCombineXYZ'); cmb.location = (-900, 160)
links.new(cu.outputs[0], cmb.inputs['X'])
links.new(su.outputs[0], cmb.inputs['Y'])
links.new(cv.outputs[0], cmb.inputs['Z'])
vsc = nodes.new('ShaderNodeVectorMath'); vsc.operation = 'SCALE'; vsc.location = (-720, 300)
vsc.inputs['Scale'].default_value = 1.1141
links.new(cmb.outputs['Vector'], vsc.inputs[0])
vw = nodes.new('ShaderNodeMath'); vw.operation = 'MULTIPLY'; vw.location = (-720, 160)
vw.inputs[1].default_value = 1.1141
links.new(sv.outputs[0], vw.inputs[0])
nsc = nodes.new('ShaderNodeVectorMath'); nsc.operation = 'MULTIPLY_ADD'; nsc.location = (-720, -20)
nsc.inputs[1].default_value = (0.6366, 0.6366, 0.6366)
nsc.inputs[2].default_value = (4.3, -2.7, 1.9)
links.new(cmb.outputs['Vector'], nsc.inputs[0])
nw = nodes.new('ShaderNodeMath'); nw.operation = 'MULTIPLY_ADD'; nw.location = (-720, -200)
nw.inputs[1].default_value = 0.6366
nw.inputs[2].default_value = 5.1
links.new(sv.outputs[0], nw.inputs[0])
vor = nodes.new('ShaderNodeTexVoronoi'); vor.location = (-520, 280)
vor.voronoi_dimensions = '4D'
vor.feature = 'F1'
vor.inputs['Scale'].default_value = 1.0
vor.inputs['Randomness'].default_value = 1.0
links.new(vsc.outputs['Vector'], vor.inputs['Vector'])
links.new(vw.outputs[0], vor.inputs['W'])
nse = nodes.new('ShaderNodeTexNoise'); nse.location = (-520, -140)
nse.noise_dimensions = '4D'
nse.inputs['Scale'].default_value = 1.0
nse.inputs['Detail'].default_value = 3.0
nse.inputs['Roughness'].default_value = 0.5
nse.inputs['Distortion'].default_value = 0.0
links.new(nsc.outputs['Vector'], nse.inputs['Vector'])
links.new(nw.outputs[0], nse.inputs['W'])
scol = nodes.new('ShaderNodeSeparateColor'); scol.location = (-300, 120)
links.new(vor.outputs['Color'], scol.inputs['Color'])
mshape = nodes.new('ShaderNodeMath'); mshape.operation = 'MULTIPLY_ADD'; mshape.location = (-300, 320)
mshape.inputs[1].default_value = -1.15
mshape.inputs[2].default_value = 1.06
links.new(vor.outputs['Distance'], mshape.inputs[0])
mtint = nodes.new('ShaderNodeMath'); mtint.operation = 'MULTIPLY_ADD'; mtint.location = (-100, 120)
mtint.inputs[1].default_value = 0.20
mtint.inputs[2].default_value = -0.10
links.new(scol.outputs['Red'], mtint.inputs[0])
mmott = nodes.new('ShaderNodeMath'); mmott.operation = 'MULTIPLY_ADD'; mmott.location = (-300, -140)
mmott.inputs[1].default_value = 0.46
mmott.inputs[2].default_value = -0.2364
links.new(nse.outputs['Factor'], mmott.inputs[0])
add1 = nodes.new('ShaderNodeMath'); add1.operation = 'ADD'; add1.location = (100, 240)
links.new(mshape.outputs[0], add1.inputs[0])
links.new(mtint.outputs[0], add1.inputs[1])
add2 = nodes.new('ShaderNodeMath'); add2.operation = 'ADD'; add2.use_clamp = True; add2.location = (300, 120)
links.new(add1.outputs[0], add2.inputs[0])
links.new(mmott.outputs[0], add2.inputs[1])
ramp = nodes.new('ShaderNodeValToRGB'); ramp.location = (520, 0)
ramp.color_ramp.interpolation = 'LINEAR'
el = ramp.color_ramp.elements
el[0].position = 0.0; el[0].color = (0.010, 0.0012, 0.0022, 1.0)
el[1].position = 1.0; el[1].color = (0.995, 0.520, 0.330, 1.0)
e = el.new(0.06); e.color = (0.028, 0.0030, 0.0050, 1.0)
e = el.new(0.13); e.color = (0.072, 0.0050, 0.0080, 1.0)
e = el.new(0.20); e.color = (0.050, 0.0040, 0.0065, 1.0)
e = el.new(0.40); e.color = (0.250, 0.0120, 0.0170, 1.0)
e = el.new(0.62); e.color = (0.520, 0.0300, 0.0300, 1.0)
e = el.new(0.80); e.color = (0.800, 0.0750, 0.0550, 1.0)
e = el.new(0.93); e.color = (0.960, 0.2100, 0.1200, 1.0)
links.new(add2.outputs[0], ramp.inputs['Fac'])
links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
