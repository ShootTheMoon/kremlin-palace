mat.use_nodes = True
nt = mat.node_tree
nodes = nt.nodes
links = nt.links
nodes.clear()
TAU = 6.2831853

out = nodes.new('ShaderNodeOutputMaterial'); out.location = (1100, 0)
bsdf = nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (820, 0)
bsdf.inputs['Metallic'].default_value = 0.0; bsdf.inputs['Roughness'].default_value = 0.5
bsdf.inputs['Specular IOR Level'].default_value = 0.5; bsdf.inputs['Emission Strength'].default_value = 0.0
links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
tc = nodes.new('ShaderNodeTexCoord'); tc.location = (-1500, 0)

# Seamless tiling: wrap both tile axes onto circles and read 4D noise AND 4D voronoi at
# (cos u, sin u, cos v, sin v), u,v = 2*pi*Generated.xy. Equal radii on all four axes make
# it a local isometry, so the pattern is isotropic and repeats with no seam on either axis.
sep = nodes.new('ShaderNodeSeparateXYZ'); sep.location = (-1320, 120)
links.new(tc.outputs['Generated'], sep.inputs['Vector'])
ang = []
for i, ch in enumerate(('X', 'Y')):
    a = nodes.new('ShaderNodeMath'); a.operation = 'MULTIPLY'; a.location = (-1140, 220 - i * 150)
    a.inputs[1].default_value = TAU; links.new(sep.outputs[ch], a.inputs[0]); ang.append(a)
trig = []
for i, (op, src) in enumerate((('COSINE', 0), ('SINE', 0), ('COSINE', 1), ('SINE', 1))):
    t = nodes.new('ShaderNodeMath'); t.operation = op; t.location = (-960, 320 - i * 130)
    links.new(ang[src].outputs['Value'], t.inputs[0]); trig.append(t)
cxyz = nodes.new('ShaderNodeCombineXYZ'); cxyz.location = (-780, 220)
for ch, t in zip(('X', 'Y', 'Z'), trig[:3]): links.new(t.outputs['Value'], cxyz.inputs[ch])

ns = []
for i, (sc, det, rg, dis) in enumerate(((7.0 / TAU, 5.0, 0.62, 0.9), (26.0 / TAU, 6.0, 0.55, 0.0))):
    n = nodes.new('ShaderNodeTexNoise'); n.noise_dimensions = '4D'; n.location = (-600, 300 - i * 280)
    n.inputs['Scale'].default_value = sc; n.inputs['Detail'].default_value = det
    n.inputs['Roughness'].default_value = rg; n.inputs['Distortion'].default_value = dis
    links.new(cxyz.outputs['Vector'], n.inputs['Vector']); links.new(trig[3].outputs['Value'], n.inputs['W'])
    ns.append(n)

m1 = nodes.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; m1.location = (-400, 300); m1.inputs[1].default_value = 0.62
links.new(ns[0].outputs['Fac'], m1.inputs[0])
m2 = nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY_ADD'; m2.location = (-220, 180); m2.inputs[1].default_value = 0.38
m2.label = 'GROUND'
links.new(ns[1].outputs['Fac'], m2.inputs[0]); links.new(m1.outputs['Value'], m2.inputs[2])

# Ramp stops sit on the MEASURED quantiles of m2 (baked: mean 0.4832 sd 0.0446), at
# q04/q18/q42/q68/q96/q999, so every stop actually ships: deep navy veins -> lapis body
# -> pale calcite passages. A ramp spread over 0..1 would bake as one flat mid tone.
cr = nodes.new('ShaderNodeValToRGB'); cr.location = (-40, 180)
cr.label = 'RAMP'
cr.color_ramp.elements[0].position = 0.4063; cr.color_ramp.elements[1].position = 0.6198
for pos in (0.4422, 0.4735, 0.5039, 0.5624): cr.color_ramp.elements.new(pos)
for i, c in enumerate([(0.0065, 0.0115, 0.0500, 1.0), (0.0180, 0.0360, 0.1520, 1.0), (0.0390, 0.0820, 0.3200, 1.0),
                       (0.0720, 0.1330, 0.4850, 1.0), (0.1200, 0.1950, 0.6700, 1.0), (0.4000, 0.4500, 0.6200, 1.0)]):
    cr.color_ramp.elements[i].color = c
links.new(m2.outputs['Value'], cr.inputs['Fac'])

# Pyrite flecks on the SAME torus coords, so they tile too. Scale 30.9/TAU over a 2D surface
# embedded in 4D gives (2*pi*S)^2 * pi * r^2 = 72 dots per tile = 8 per m2 at r = 0.155.
# r2 is a narrow edge band (0.11..0.155), not a full-radius ramp: flat core, ~1.5 px falloff.
vf = nodes.new('ShaderNodeTexVoronoi'); vf.location = (-600, -340)
vf.voronoi_dimensions = '4D'; vf.feature = 'F1'
vf.inputs['Scale'].default_value = 30.9 / TAU; vf.inputs['Randomness'].default_value = 1.0
links.new(cxyz.outputs['Vector'], vf.inputs['Vector']); links.new(trig[3].outputs['Value'], vf.inputs['W'])
r2 = nodes.new('ShaderNodeMapRange'); r2.location = (-400, -340)
for k, v in zip(('From Min', 'From Max', 'To Min', 'To Max'), (0.11, 0.155, 1.0, 0.0)): r2.inputs[k].default_value = v
links.new(vf.outputs['Distance'], r2.inputs['Value'])
# Fleck brightness is driven by m2, the ground lightness itself, so gold drifts with the pale
# passages; To Min 0.55 is a floor, so every fleck reads as gold instead of a grey smudge.
r3 = nodes.new('ShaderNodeMapRange'); r3.location = (-400, -560)
r3.label = 'CLUSTER'
for k, v in zip(('From Min', 'From Max', 'To Min', 'To Max'), (0.4654, 0.5303, 0.55, 1.0)): r3.inputs[k].default_value = v
links.new(m2.outputs['Value'], r3.inputs['Value'])
m5 = nodes.new('ShaderNodeMath'); m5.operation = 'MULTIPLY'; m5.location = (-200, -420)
m5.label = 'FLECKMASK'
links.new(r2.outputs['Result'], m5.inputs[0]); links.new(r3.outputs['Result'], m5.inputs[1])

mx = nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.location = (300, 0)
links.new(m5.outputs['Value'], mx.inputs[0]); links.new(cr.outputs['Color'], mx.inputs[6])
mx.inputs[7].default_value = (0.7200, 0.5500, 0.2000, 1.0)
links.new(mx.outputs[2], bsdf.inputs['Base Color'])
