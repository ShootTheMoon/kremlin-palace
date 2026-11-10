mat.use_nodes = True
nt = mat.node_tree
nodes = nt.nodes
links = nt.links
nodes.clear()
out = nodes.new('ShaderNodeOutputMaterial'); out.location = (1500, 0)
bsdf = nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (1240, 0)
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.5
links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

# ---- seamless torus coordinate: (cos u, sin u, cos v) + W = sin v, u = 2pi X, v = 2pi Y
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
V = co.outputs['Vector']
W = ps.outputs['Y']

# ---- glaze pooling: broad soft thickness variation (main tonal carrier)
pool = nodes.new('ShaderNodeTexNoise'); pool.noise_dimensions = '4D'; pool.location = (-620, 420)
pool.inputs['Scale'].default_value = 1.7
pool.inputs['Detail'].default_value = 3.0
pool.inputs['Roughness'].default_value = 0.5
links.new(V, pool.inputs['Vector']); links.new(W, pool.inputs['W'])

# ---- mid mottle
mid = nodes.new('ShaderNodeTexNoise'); mid.noise_dimensions = '4D'; mid.location = (-620, 200)
mid.inputs['Scale'].default_value = 4.6
mid.inputs['Detail'].default_value = 2.0
mid.inputs['Roughness'].default_value = 0.45
links.new(V, mid.inputs['Vector']); links.new(W, mid.inputs['W'])

# ---- fine orange-peel grain
fine = nodes.new('ShaderNodeTexNoise'); fine.noise_dimensions = '4D'; fine.location = (-620, -20)
fine.inputs['Scale'].default_value = 13.0
fine.inputs['Detail'].default_value = 1.0
fine.inputs['Roughness'].default_value = 0.5
links.new(V, fine.inputs['Vector']); links.new(W, fine.inputs['W'])

# ---- very low frequency drift
drift = nodes.new('ShaderNodeTexNoise'); drift.noise_dimensions = '4D'; drift.location = (-620, 640)
drift.inputs['Scale'].default_value = 0.40
drift.inputs['Detail'].default_value = 2.0
drift.inputs['Roughness'].default_value = 0.5
links.new(V, drift.inputs['Vector']); links.new(W, drift.inputs['W'])

# ---- crazing: fine network of hairlines
crz = nodes.new('ShaderNodeTexVoronoi'); crz.voronoi_dimensions = '4D'
crz.feature = 'DISTANCE_TO_EDGE'; crz.location = (-620, -260)
crz.inputs['Scale'].default_value = 6.0
crz.inputs['Randomness'].default_value = 1.0
links.new(V, crz.inputs['Vector']); links.new(W, crz.inputs['W'])

# ---- crazing depth modulation
cmk = nodes.new('ShaderNodeTexNoise'); cmk.noise_dimensions = '4D'; cmk.location = (-620, -500)
cmk.inputs['Scale'].default_value = 0.9
cmk.inputs['Detail'].default_value = 2.0
cmk.inputs['Roughness'].default_value = 0.5
links.new(V, cmk.inputs['Vector']); links.new(W, cmk.inputs['W'])

GP = 1.30
GM = 0.55
GF = 0.28
GD = 0.30
pa = nodes.new('ShaderNodeMath'); pa.operation = 'MULTIPLY_ADD'; pa.location = (-380, 420)
pa.inputs[1].default_value = GP; pa.inputs[2].default_value = -0.5 * GP
links.new(pool.outputs['Fac'], pa.inputs[0])
ma = nodes.new('ShaderNodeMath'); ma.operation = 'MULTIPLY_ADD'; ma.location = (-380, 200)
ma.inputs[1].default_value = GM; ma.inputs[2].default_value = -0.5 * GM
links.new(mid.outputs['Fac'], ma.inputs[0])
fa = nodes.new('ShaderNodeMath'); fa.operation = 'MULTIPLY_ADD'; fa.location = (-380, -20)
fa.inputs[1].default_value = GF; fa.inputs[2].default_value = -0.5 * GF
links.new(fine.outputs['Fac'], fa.inputs[0])
da = nodes.new('ShaderNodeMath'); da.operation = 'MULTIPLY_ADD'; da.location = (-380, 640)
da.inputs[1].default_value = GD; da.inputs[2].default_value = -0.5 * GD
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
ln.inputs[1].default_value = -70.0; ln.inputs[2].default_value = 1.0
links.new(crz.outputs['Distance'], ln.inputs[0])
cm = nodes.new('ShaderNodeMath'); cm.operation = 'MULTIPLY_ADD'; cm.use_clamp = True
cm.location = (-380, -500)
cm.inputs[1].default_value = 3.0; cm.inputs[2].default_value = -0.90
links.new(cmk.outputs['Fac'], cm.inputs[0])
cz = nodes.new('ShaderNodeMath'); cz.operation = 'MULTIPLY'; cz.location = (-180, -380)
links.new(ln.outputs[0], cz.inputs[0]); links.new(cm.outputs[0], cz.inputs[1])
cs = nodes.new('ShaderNodeMath'); cs.operation = 'MULTIPLY'; cs.location = (20, -380)
cs.inputs[1].default_value = 0.26
links.new(cz.outputs[0], cs.inputs[0])

fac = nodes.new('ShaderNodeMath'); fac.operation = 'SUBTRACT'; fac.location = (400, 200)
links.new(s4.outputs[0], fac.inputs[0]); links.new(cs.outputs[0], fac.inputs[1])

links.new(cs.outputs[0], bsdf.inputs["Base Color"])
