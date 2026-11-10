mat.use_nodes = True
nt = mat.node_tree
nodes = nt.nodes
links = nt.links
nodes.clear()
out = nodes.new('ShaderNodeOutputMaterial'); out.location = (1560, 0)
bsdf = nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (1300, 0)
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.5
links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
tc = nodes.new('ShaderNodeTexCoord'); tc.location = (-1560, 0)
mp = nodes.new('ShaderNodeMapping'); mp.location = (-1380, 0)
mp.inputs['Scale'].default_value = (6.283185307, 6.283185307, 0.0)
links.new(tc.outputs['Generated'], mp.inputs['Vector'])
vc = nodes.new('ShaderNodeVectorMath'); vc.operation = 'COSINE'; vc.location = (-1200, 140)
vs = nodes.new('ShaderNodeVectorMath'); vs.operation = 'SINE'; vs.location = (-1200, -100)
links.new(mp.outputs['Vector'], vc.inputs[0])
links.new(mp.outputs['Vector'], vs.inputs[0])
pc = nodes.new('ShaderNodeSeparateXYZ'); pc.location = (-1020, 140)
ps = nodes.new('ShaderNodeSeparateXYZ'); ps.location = (-1020, -100)
links.new(vc.outputs['Vector'], pc.inputs[0])
links.new(vs.outputs['Vector'], ps.inputs[0])
co = nodes.new('ShaderNodeCombineXYZ'); co.location = (-840, 20)
links.new(pc.outputs['X'], co.inputs['X'])
links.new(ps.outputs['X'], co.inputs['Y'])
links.new(pc.outputs['Y'], co.inputs['Z'])
tor = co.outputs['Vector']
torw = ps.outputs['Y']
w1 = nodes.new('ShaderNodeTexNoise'); w1.noise_dimensions = '4D'; w1.location = (-620, 420)
w1.inputs['Scale'].default_value = 1.25
w1.inputs['Detail'].default_value = 2.0
w1.inputs['Roughness'].default_value = 0.35
links.new(tor, w1.inputs['Vector']); links.new(torw, w1.inputs['W'])
w2 = nodes.new('ShaderNodeTexNoise'); w2.noise_dimensions = '4D'; w2.location = (-620, 200)
w2.inputs['Scale'].default_value = 2.90
w2.inputs['Detail'].default_value = 1.0
w2.inputs['Roughness'].default_value = 0.5
links.new(tor, w2.inputs['Vector']); links.new(torw, w2.inputs['W'])
fine = nodes.new('ShaderNodeTexNoise'); fine.noise_dimensions = '4D'; fine.location = (-620, -20)
fine.inputs['Scale'].default_value = 18.0
fine.inputs['Detail'].default_value = 1.0
fine.inputs['Roughness'].default_value = 0.5
links.new(tor, fine.inputs['Vector']); links.new(torw, fine.inputs['W'])
drift = nodes.new('ShaderNodeTexNoise'); drift.noise_dimensions = '4D'; drift.location = (-620, 640)
drift.inputs['Scale'].default_value = 0.38
drift.inputs['Detail'].default_value = 2.0
drift.inputs['Roughness'].default_value = 0.5
links.new(tor, drift.inputs['Vector']); links.new(torw, drift.inputs['W'])
crz = nodes.new('ShaderNodeTexVoronoi'); crz.voronoi_dimensions = '4D'
crz.feature = 'DISTANCE_TO_EDGE'; crz.location = (-620, -260)
crz.inputs['Scale'].default_value = 6.0
crz.inputs['Randomness'].default_value = 1.0
links.new(tor, crz.inputs['Vector']); links.new(torw, crz.inputs['W'])
cmk = nodes.new('ShaderNodeTexNoise'); cmk.noise_dimensions = '4D'; cmk.location = (-620, -500)
cmk.inputs['Scale'].default_value = 0.9
cmk.inputs['Detail'].default_value = 2.0
cmk.inputs['Roughness'].default_value = 0.5
links.new(tor, cmk.inputs['Vector']); links.new(torw, cmk.inputs['W'])
pa = nodes.new('ShaderNodeMath'); pa.operation = 'MULTIPLY_ADD'; pa.location = (-380, 420)
pa.inputs[1].default_value = 1.15; pa.inputs[2].default_value = -0.575
links.new(w1.outputs['Fac'], pa.inputs[0])
ma = nodes.new('ShaderNodeMath'); ma.operation = 'MULTIPLY_ADD'; ma.location = (-380, 200)
ma.inputs[1].default_value = 0.60; ma.inputs[2].default_value = -0.30
links.new(w2.outputs['Fac'], ma.inputs[0])
fa = nodes.new('ShaderNodeMath'); fa.operation = 'MULTIPLY_ADD'; fa.location = (-380, -20)
fa.inputs[1].default_value = 0.07; fa.inputs[2].default_value = -0.035
links.new(fine.outputs['Fac'], fa.inputs[0])
da = nodes.new('ShaderNodeMath'); da.operation = 'MULTIPLY_ADD'; da.location = (-380, 640)
da.inputs[1].default_value = 0.22; da.inputs[2].default_value = -0.11
links.new(drift.outputs['Fac'], da.inputs[0])
s1 = nodes.new('ShaderNodeMath'); s1.operation = 'ADD'; s1.location = (-180, 520)
links.new(pa.outputs[0], s1.inputs[0]); links.new(da.outputs[0], s1.inputs[1])
s2 = nodes.new('ShaderNodeMath'); s2.operation = 'ADD'; s2.location = (-180, 300)
links.new(ma.outputs[0], s2.inputs[0]); links.new(fa.outputs[0], s2.inputs[1])
s3 = nodes.new('ShaderNodeMath'); s3.operation = 'ADD'; s3.location = (20, 420)
links.new(s1.outputs[0], s3.inputs[0]); links.new(s2.outputs[0], s3.inputs[1])
s4 = nodes.new('ShaderNodeMath'); s4.operation = 'ADD'; s4.location = (200, 420)
s4.inputs[1].default_value = 0.5
links.new(s3.outputs[0], s4.inputs[0])
ln = nodes.new('ShaderNodeMath'); ln.operation = 'MULTIPLY_ADD'; ln.use_clamp = True
ln.location = (-380, -260)
ln.inputs[1].default_value = -85.0; ln.inputs[2].default_value = 1.0
links.new(crz.outputs['Distance'], ln.inputs[0])
cm = nodes.new('ShaderNodeMath'); cm.operation = 'MULTIPLY_ADD'; cm.use_clamp = True
cm.location = (-380, -500)
cm.inputs[1].default_value = 3.0; cm.inputs[2].default_value = -0.90
links.new(cmk.outputs['Fac'], cm.inputs[0])
cz = nodes.new('ShaderNodeMath'); cz.operation = 'MULTIPLY'; cz.location = (-180, -380)
links.new(ln.outputs[0], cz.inputs[0]); links.new(cm.outputs[0], cz.inputs[1])
cs = nodes.new('ShaderNodeMath'); cs.operation = 'MULTIPLY'; cs.location = (20, -380)
cs.inputs[1].default_value = 0.34
links.new(cz.outputs[0], cs.inputs[0])
fac = nodes.new('ShaderNodeMath'); fac.operation = 'SUBTRACT'; fac.location = (400, 200)
links.new(s4.outputs[0], fac.inputs[0]); links.new(cs.outputs[0], fac.inputs[1])
ramp = nodes.new('ShaderNodeValToRGB'); ramp.location = (600, 200)
cr = ramp.color_ramp
cr.interpolation = 'LINEAR'
stops = [(0.1485, (0.4342, 0.4179, 0.3968, 1.0)),
         (0.2213, (0.5394, 0.5332, 0.5271, 1.0)),
         (0.2984, (0.6377, 0.6446, 0.6725, 1.0)),
         (0.4080, (0.7379, 0.7454, 0.7605, 1.0)),
         (0.4805, (0.7991, 0.7991, 0.7991, 1.0)),
         (0.5526, (0.8550, 0.8469, 0.8308, 1.0)),
         (0.6588, (0.9301, 0.9131, 0.8797, 1.0)),
         (0.8133, (0.9823, 0.9647, 0.9216, 1.0))]
cr.elements[0].position = stops[0][0]; cr.elements[0].color = stops[0][1]
cr.elements[1].position = stops[-1][0]; cr.elements[1].color = stops[-1][1]
for sp, sc in stops[1:-1]:
    el = cr.elements.new(sp); el.color = sc
links.new(fac.outputs[0], ramp.inputs['Fac'])
dw = nodes.new('ShaderNodeMath'); dw.operation = 'MULTIPLY_ADD'; dw.use_clamp = True
dw.location = (200, 700)
dw.inputs[1].default_value = 7.0; dw.inputs[2].default_value = -3.0
links.new(drift.outputs['Fac'], dw.inputs[0])
tint = nodes.new('ShaderNodeMix'); tint.data_type = 'RGBA'; tint.blend_type = 'MIX'
tint.location = (600, 640)
tint.inputs[0].default_value = 0.5
[s for s in tint.inputs if s.name == 'A' and s.type == 'RGBA'][0].default_value = (1.014, 1.000, 0.980, 1.0)
[s for s in tint.inputs if s.name == 'B' and s.type == 'RGBA'][0].default_value = (0.989, 0.999, 1.019, 1.0)
links.new(dw.outputs[0], tint.inputs[0])
tone = nodes.new('ShaderNodeMix'); tone.data_type = 'RGBA'; tone.blend_type = 'MULTIPLY'
tone.location = (940, 300)
tone.inputs[0].default_value = 1.0
links.new(ramp.outputs['Color'], [s for s in tone.inputs if s.name == 'A' and s.type == 'RGBA'][0])
links.new([s for s in tint.outputs if s.name == 'Result' and s.type == 'RGBA'][0],
          [s for s in tone.inputs if s.name == 'B' and s.type == 'RGBA'][0])
links.new([s for s in tone.outputs if s.name == 'Result' and s.type == 'RGBA'][0],
          bsdf.inputs['Base Color'])
