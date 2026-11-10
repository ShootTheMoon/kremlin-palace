mat.use_nodes = True
nt = mat.node_tree
nodes = nt.nodes
links = nt.links
nodes.clear()
out = nodes.new('ShaderNodeOutputMaterial'); out.location = (1500, 0)
bsdf = nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (1220, 0)
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.5
links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
tau = 6.283185307179586
tc = nodes.new('ShaderNodeTexCoord'); tc.location = (-1900, 0)
sep = nodes.new('ShaderNodeSeparateXYZ'); sep.location = (-1720, 0)
links.new(tc.outputs['Generated'], sep.inputs['Vector'])
mu = nodes.new('ShaderNodeMath'); mu.location = (-1540, 140); mu.operation = 'MULTIPLY'
mu.inputs[1].default_value = tau
links.new(sep.outputs['X'], mu.inputs[0])
mv = nodes.new('ShaderNodeMath'); mv.location = (-1540, -140); mv.operation = 'MULTIPLY'
mv.inputs[1].default_value = tau
links.new(sep.outputs['Y'], mv.inputs[0])
cu = nodes.new('ShaderNodeMath'); cu.location = (-1360, 260); cu.operation = 'COSINE'
links.new(mu.outputs[0], cu.inputs[0])
su = nodes.new('ShaderNodeMath'); su.location = (-1360, 100); su.operation = 'SINE'
links.new(mu.outputs[0], su.inputs[0])
cv = nodes.new('ShaderNodeMath'); cv.location = (-1360, -60); cv.operation = 'COSINE'
links.new(mv.outputs[0], cv.inputs[0])
sv = nodes.new('ShaderNodeMath'); sv.location = (-1360, -220); sv.operation = 'SINE'
links.new(mv.outputs[0], sv.inputs[0])
cmb = nodes.new('ShaderNodeCombineXYZ'); cmb.location = (-1180, 140)
links.new(cu.outputs[0], cmb.inputs['X'])
links.new(su.outputs[0], cmb.inputs['Y'])
links.new(cv.outputs[0], cmb.inputs['Z'])
vsc = nodes.new('ShaderNodeVectorMath'); vsc.location = (-1000, 140); vsc.operation = 'SCALE'
links.new(cmb.outputs[0], vsc.inputs[0])
vsc.inputs['Scale'].default_value = 1.0 / tau
wsc = nodes.new('ShaderNodeMath'); wsc.location = (-1000, -220); wsc.operation = 'MULTIPLY'
wsc.inputs[1].default_value = 1.0 / tau
links.new(sv.outputs[0], wsc.inputs[0])
vor = nodes.new('ShaderNodeTexVoronoi'); vor.location = (-780, 320)
vor.voronoi_dimensions = '4D'; vor.feature = 'F1'
links.new(vsc.outputs[0], vor.inputs['Vector'])
links.new(wsc.outputs[0], vor.inputs['W'])
vor.inputs['Scale'].default_value = 11.0
vor.inputs['Randomness'].default_value = 1.0
fsep = nodes.new('ShaderNodeSeparateColor'); fsep.location = (-580, 420)
links.new(vor.outputs['Color'], fsep.inputs['Color'])
fm = nodes.new('ShaderNodeMath'); fm.location = (-400, 420); fm.operation = 'MULTIPLY_ADD'
links.new(fsep.outputs[0], fm.inputs[0])
fm.inputs[1].default_value = 0.30
fm.inputs[2].default_value = -0.15
grn = nodes.new('ShaderNodeTexNoise'); grn.location = (-780, 40)
grn.noise_dimensions = '4D'
links.new(vsc.outputs[0], grn.inputs['Vector'])
links.new(wsc.outputs[0], grn.inputs['W'])
grn.inputs['Scale'].default_value = 45.0
grn.inputs['Detail'].default_value = 6.0
grn.inputs['Roughness'].default_value = 0.55
gm = nodes.new('ShaderNodeMath'); gm.location = (-580, 40); gm.operation = 'MULTIPLY_ADD'
links.new(grn.outputs['Fac'], gm.inputs[0])
gm.inputs[1].default_value = 0.60
gm.inputs[2].default_value = -0.288
a1 = nodes.new('ShaderNodeMath'); a1.location = (-200, 320); a1.operation = 'ADD'
links.new(vor.outputs['Distance'], a1.inputs[0])
links.new(fm.outputs[0], a1.inputs[1])
a2 = nodes.new('ShaderNodeMath'); a2.location = (-20, 320); a2.operation = 'ADD'
links.new(a1.outputs[0], a2.inputs[0])
links.new(gm.outputs[0], a2.inputs[1])
iron = nodes.new('ShaderNodeValToRGB'); iron.location = (200, 460)
ie0 = iron.color_ramp.elements[0]; ie0.position = 0.13; ie0.color = (0.0107, 0.0118, 0.0130, 1.0)
ie1 = iron.color_ramp.elements[1]; ie1.position = 0.95; ie1.color = (0.1599, 0.1775, 0.1950, 1.0)
ie2 = iron.color_ramp.elements.new(0.42); ie2.color = (0.0303, 0.0337, 0.0370, 1.0)
ie3 = iron.color_ramp.elements.new(0.72); ie3.color = (0.0672, 0.0746, 0.0820, 1.0)
links.new(a2.outputs[0], iron.inputs['Fac'])
rust = nodes.new('ShaderNodeValToRGB'); rust.location = (200, 140)
re0 = rust.color_ramp.elements[0]; re0.position = 0.13; re0.color = (0.0300, 0.0140, 0.0080, 1.0)
re1 = rust.color_ramp.elements[1]; re1.position = 0.95; re1.color = (0.2100, 0.1050, 0.0550, 1.0)
re2 = rust.color_ramp.elements.new(0.42); re2.color = (0.0720, 0.0330, 0.0170, 1.0)
re3 = rust.color_ramp.elements.new(0.72); re3.color = (0.1250, 0.0580, 0.0300, 1.0)
links.new(a2.outputs[0], rust.inputs['Fac'])
rn = nodes.new('ShaderNodeTexNoise'); rn.location = (-780, -320)
rn.noise_dimensions = '4D'
links.new(vsc.outputs[0], rn.inputs['Vector'])
links.new(wsc.outputs[0], rn.inputs['W'])
rn.inputs['Scale'].default_value = 4.5
rn.inputs['Detail'].default_value = 3.0
rn.inputs['Roughness'].default_value = 0.5
rr = nodes.new('ShaderNodeValToRGB'); rr.location = (-580, -320)
rr.color_ramp.elements[0].position = 0.545
rr.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
rr.color_ramp.elements[1].position = 0.640
rr.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
links.new(rn.outputs['Fac'], rr.inputs['Fac'])
sb = nodes.new('ShaderNodeMath'); sb.location = (-400, -560); sb.operation = 'SUBTRACT'
sb.inputs[0].default_value = 1.05
links.new(vor.outputs['Distance'], sb.inputs[1])
sbm = nodes.new('ShaderNodeMath'); sbm.location = (-220, -560); sbm.operation = 'MULTIPLY'
sbm.use_clamp = True
links.new(sb.outputs[0], sbm.inputs[0])
sbm.inputs[1].default_value = 1.25
rmul = nodes.new('ShaderNodeMath'); rmul.location = (-20, -400); rmul.operation = 'MULTIPLY'
links.new(rr.outputs['Color'], rmul.inputs[0])
links.new(sbm.outputs[0], rmul.inputs[1])
mx = nodes.new('ShaderNodeMix'); mx.location = (640, 300); mx.data_type = 'RGBA'; mx.blend_type = 'MIX'
mxf = next((s for s in mx.inputs if s.identifier == 'Factor_Float'), mx.inputs[0])
mxa = next((s for s in mx.inputs if s.identifier == 'A_Color'), mx.inputs[6])
mxb = next((s for s in mx.inputs if s.identifier == 'B_Color'), mx.inputs[7])
mxo = next((s for s in mx.outputs if s.identifier == 'Result_Color'), mx.outputs[2])
links.new(rmul.outputs[0], mxf)
links.new(iron.outputs['Color'], mxa)
links.new(rust.outputs['Color'], mxb)
links.new(mxo, bsdf.inputs['Base Color'])
