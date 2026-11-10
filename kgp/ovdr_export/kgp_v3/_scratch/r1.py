mat.use_nodes = True
nt = mat.node_tree
nodes = nt.nodes
links = nt.links
nodes.clear()

# --- seamless tile: wrap Generated x,y onto a 4D torus so the noise is exactly periodic ---
tc = nodes.new('ShaderNodeTexCoord'); tc.location = (-1800, 0)
sep = nodes.new('ShaderNodeSeparateXYZ'); sep.location = (-1620, 0)
links.new(tc.outputs['Generated'], sep.inputs['Vector'])
mu = nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = 6.2831853; mu.location = (-1450, 120)
mv = nodes.new('ShaderNodeMath'); mv.operation = 'MULTIPLY'; mv.inputs[1].default_value = 6.2831853; mv.location = (-1450, -60)
links.new(sep.outputs['X'], mu.inputs[0]); links.new(sep.outputs['Y'], mv.inputs[0])
cu = nodes.new('ShaderNodeMath'); cu.operation = 'COSINE'; cu.location = (-1280, 240); links.new(mu.outputs['Value'], cu.inputs[0])
su = nodes.new('ShaderNodeMath'); su.operation = 'SINE'; su.location = (-1280, 100); links.new(mu.outputs['Value'], su.inputs[0])
cv = nodes.new('ShaderNodeMath'); cv.operation = 'COSINE'; cv.location = (-1280, -40); links.new(mv.outputs['Value'], cv.inputs[0])
sv = nodes.new('ShaderNodeMath'); sv.operation = 'SINE'; sv.location = (-1280, -180); links.new(mv.outputs['Value'], sv.inputs[0])
cmb = nodes.new('ShaderNodeCombineXYZ'); cmb.location = (-1100, 120)
links.new(cu.outputs['Value'], cmb.inputs['X']); links.new(su.outputs['Value'], cmb.inputs['Y']); links.new(cv.outputs['Value'], cmb.inputs['Z'])
va = nodes.new('ShaderNodeVectorMath'); va.operation = 'MULTIPLY'; va.inputs[1].default_value = (8.75, 8.75, 1.40); va.location = (-920, 240)
wa = nodes.new('ShaderNodeMath'); wa.operation = 'MULTIPLY'; wa.inputs[1].default_value = 1.40; wa.location = (-920, 80)
vb = nodes.new('ShaderNodeVectorMath'); vb.operation = 'MULTIPLY'; vb.inputs[1].default_value = (0.75, 0.75, 0.3375); vb.location = (-920, -100)
wb = nodes.new('ShaderNodeMath'); wb.operation = 'MULTIPLY'; wb.inputs[1].default_value = 0.3375; wb.location = (-920, -260)
links.new(cmb.outputs['Vector'], va.inputs[0]); links.new(sv.outputs['Value'], wa.inputs[0])
links.new(cmb.outputs['Vector'], vb.inputs[0]); links.new(sv.outputs['Value'], wb.inputs[0])

# --- fine directional nap: ~55 streaks across the tile, 6x stretched along the lay ---
nn = nodes.new('ShaderNodeTexNoise'); nn.noise_dimensions = '4D'; nn.location = (-720, 220)
nn.inputs['Scale'].default_value = 1.0; nn.inputs['Detail'].default_value = 4.0
nn.inputs['Roughness'].default_value = 0.60; nn.inputs['Distortion'].default_value = 0.45
links.new(va.outputs['Vector'], nn.inputs['Vector']); links.new(wa.outputs['Value'], nn.inputs['W'])

# --- broad crushed patches where the pile is pressed flat ---
ncr = nodes.new('ShaderNodeTexNoise'); ncr.noise_dimensions = '4D'; ncr.location = (-720, -120)
ncr.inputs['Scale'].default_value = 1.0; ncr.inputs['Detail'].default_value = 3.0
ncr.inputs['Distortion'].default_value = 0.5
links.new(vb.outputs['Vector'], ncr.inputs['Vector']); links.new(wb.outputs['Value'], ncr.inputs['W'])

# --- nap and the broad crushed patches, half and half, still centred on 0.5 ---
mul = nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 0.46; mul.location = (-520, -120)
mad = nodes.new('ShaderNodeMath'); mad.operation = 'MULTIPLY_ADD'; mad.inputs[1].default_value = 0.54; mad.location = (-340, 120)
links.new(ncr.outputs['Fac'], mul.inputs[0]); links.new(nn.outputs['Fac'], mad.inputs[0])
links.new(mul.outputs['Value'], mad.inputs[2])

# --- palette: deep pile -> royal body -> crushed crest ---
ramp = nodes.new('ShaderNodeValToRGB'); ramp.location = (-160, 200)
e = ramp.color_ramp.elements[0]; e.position = 0.27; e.color = (0.008, 0.026, 0.082, 1.0)
e = ramp.color_ramp.elements[1]; e.position = 0.73; e.color = (0.175, 0.355, 0.690, 1.0)
e = ramp.color_ramp.elements.new(0.45); e.color = (0.030, 0.100, 0.270, 1.0)
e = ramp.color_ramp.elements.new(0.58); e.color = (0.055, 0.170, 0.420, 1.0)
links.new(mad.outputs['Value'], ramp.inputs['Fac'])

# --- faint warm bloom on the laid-over pile (decorrelated channel of the crush noise) ---
rb = nodes.new('ShaderNodeValToRGB'); rb.location = (-160, -160)
rb.color_ramp.interpolation = 'EASE'
e = rb.color_ramp.elements[0]; e.position = 0.50; e.color = (0.0, 0.0, 0.0, 1.0)
e = rb.color_ramp.elements[1]; e.position = 0.80; e.color = (0.17, 0.17, 0.17, 1.0)
links.new(ncr.outputs['Color'], rb.inputs['Fac'])

mix = nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.location = (140, 60)
fac = [s for s in mix.inputs if s.name == 'Factor' and s.type == 'VALUE'][0]
ca = [s for s in mix.inputs if s.name == 'A' and s.type == 'RGBA'][0]
cb = [s for s in mix.inputs if s.name == 'B' and s.type == 'RGBA'][0]
res = [s for s in mix.outputs if s.name == 'Result' and s.type == 'RGBA'][0]
cb.default_value = (0.225, 0.190, 0.305, 1.0)
links.new(rb.outputs['Color'], fac); links.new(ramp.outputs['Color'], ca)

bsdf = nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (360, 0)
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.5
out = nodes.new('ShaderNodeOutputMaterial'); out.location = (600, 0)
links.new(res, bsdf.inputs['Base Color'])
links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])