mat.use_nodes = True
nt = mat.node_tree
nodes = nt.nodes
links = nt.links
nodes.clear()
N = lambda t: nodes.new(t)
L = lambda a, b: links.new(a, b)
S = lambda n, i: next(s for s in n.inputs if s.identifier == i)
O = lambda n: next(s for s in n.outputs if s.identifier == 'Result_Color')
TAU = 6.283185307
out = N('ShaderNodeOutputMaterial'); out.location = (1700, 0)
bsdf = N('ShaderNodeBsdfPrincipled'); bsdf.location = (1440, 0)
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.5
L(bsdf.outputs['BSDF'], out.inputs['Surface'])
# ---- tile space -> Clifford torus: every texture below is exactly periodic in x and y
tc = N('ShaderNodeTexCoord'); tc.location = (-1900, 0)
mp = N('ShaderNodeMapping'); mp.location = (-1720, 0)
mp.inputs['Location'].default_value = (0.17, 0.43, 0.0)
L(tc.outputs['Generated'], mp.inputs['Vector'])
sep = N('ShaderNodeSeparateXYZ'); sep.location = (-1540, 0)
L(mp.outputs['Vector'], sep.inputs['Vector'])
ua = N('ShaderNodeMath'); ua.operation = 'MULTIPLY'; ua.inputs[1].default_value = TAU; ua.location = (-1380, 120)
L(sep.outputs['X'], ua.inputs[0])
va = N('ShaderNodeMath'); va.operation = 'MULTIPLY'; va.inputs[1].default_value = TAU; va.location = (-1380, -120)
L(sep.outputs['Y'], va.inputs[0])
su0 = N('ShaderNodeMath'); su0.operation = 'SINE'; su0.location = (-1220, 260); L(ua.outputs[0], su0.inputs[0])
cu0 = N('ShaderNodeMath'); cu0.operation = 'COSINE'; cu0.location = (-1220, 100); L(ua.outputs[0], cu0.inputs[0])
sv0 = N('ShaderNodeMath'); sv0.operation = 'SINE'; sv0.location = (-1220, -60); L(va.outputs[0], sv0.inputs[0])
cv0 = N('ShaderNodeMath'); cv0.operation = 'COSINE'; cv0.location = (-1220, -220); L(va.outputs[0], cv0.inputs[0])
cmb0 = N('ShaderNodeCombineXYZ'); cmb0.location = (-1050, 100)
L(su0.outputs[0], cmb0.inputs['X']); L(cu0.outputs[0], cmb0.inputs['Y']); L(sv0.outputs[0], cmb0.inputs['Z'])
# ---- isotropic domain warp: displace the two ANGLES, then re-embed.
# (displacing the embedded point instead would change the torus radius and make the
#  wander anisotropic - stronger along U than along V, i.e. aligned to world box axes)
wn = N('ShaderNodeTexNoise'); wn.noise_dimensions = '4D'; wn.location = (-880, 320)
wn.inputs['Scale'].default_value = 0.90
wn.inputs['Detail'].default_value = 3.0
wn.inputs['Roughness'].default_value = 0.55
wn.inputs['Distortion'].default_value = 0.0
L(cmb0.outputs['Vector'], wn.inputs['Vector']); L(cv0.outputs[0], wn.inputs['W'])
wsep = N('ShaderNodeSeparateXYZ'); wsep.location = (-700, 320); L(wn.outputs['Color'], wsep.inputs['Vector'])
wdu = N('ShaderNodeMath'); wdu.operation = 'SUBTRACT'; wdu.inputs[1].default_value = 0.478; wdu.location = (-540, 400)
L(wsep.outputs['X'], wdu.inputs[0])
wdv = N('ShaderNodeMath'); wdv.operation = 'SUBTRACT'; wdv.inputs[1].default_value = 0.471; wdv.location = (-540, 240)
L(wsep.outputs['Y'], wdv.inputs[0])
wku = N('ShaderNodeMath'); wku.operation = 'MULTIPLY'; wku.inputs[1].default_value = 2.10; wku.location = (-380, 400)
L(wdu.outputs[0], wku.inputs[0])
wkv = N('ShaderNodeMath'); wkv.operation = 'MULTIPLY'; wkv.inputs[1].default_value = 2.10; wkv.location = (-380, 240)
L(wdv.outputs[0], wkv.inputs[0])
ua2 = N('ShaderNodeMath'); ua2.operation = 'ADD'; ua2.location = (-220, 400)
L(ua.outputs[0], ua2.inputs[0]); L(wku.outputs[0], ua2.inputs[1])
va2 = N('ShaderNodeMath'); va2.operation = 'ADD'; va2.location = (-220, 240)
L(va.outputs[0], va2.inputs[0]); L(wkv.outputs[0], va2.inputs[1])
su1 = N('ShaderNodeMath'); su1.operation = 'SINE'; su1.location = (-60, 460); L(ua2.outputs[0], su1.inputs[0])
cu1 = N('ShaderNodeMath'); cu1.operation = 'COSINE'; cu1.location = (-60, 320); L(ua2.outputs[0], cu1.inputs[0])
sv1 = N('ShaderNodeMath'); sv1.operation = 'SINE'; sv1.location = (-60, 180); L(va2.outputs[0], sv1.inputs[0])
cv1 = N('ShaderNodeMath'); cv1.operation = 'COSINE'; cv1.location = (-60, 40); L(va2.outputs[0], cv1.inputs[0])
cmb1 = N('ShaderNodeCombineXYZ'); cmb1.location = (110, 320)
L(su1.outputs[0], cmb1.inputs['X']); L(cu1.outputs[0], cmb1.inputs['Y']); L(sv1.outputs[0], cmb1.inputs['Z'])
# W offsets pick decorrelated slices of each 4D noise (still periodic in x,y)
wA = N('ShaderNodeMath'); wA.operation = 'ADD'; wA.inputs[1].default_value = 7.0; wA.location = (-1050, -400)
L(cv0.outputs[0], wA.inputs[0])
wB = N('ShaderNodeMath'); wB.operation = 'ADD'; wB.inputs[1].default_value = 13.0; wB.location = (-1050, -540)
L(cv0.outputs[0], wB.inputs[0])
wC = N('ShaderNodeMath'); wC.operation = 'ADD'; wC.inputs[1].default_value = 19.0; wC.location = (-1050, -680)
L(cv0.outputs[0], wC.inputs[0])
wD = N('ShaderNodeMath'); wD.operation = 'ADD'; wD.inputs[1].default_value = 5.0; wD.location = (110, 160)
L(cv1.outputs[0], wD.inputs[0])
wE = N('ShaderNodeMath'); wE.operation = 'ADD'; wE.inputs[1].default_value = 11.0; wE.location = (110, 20)
L(cv1.outputs[0], wE.inputs[0])
# ---- slab tone: ~3 m drift between two ivories. Ramp stops sit on the noise's REAL
# range (p05..p95 of a Fac that lives at 0.49 +/- 0.07), so the pair is actually traversed.
cn = N('ShaderNodeTexNoise'); cn.noise_dimensions = '4D'; cn.location = (300, -300)
cn.inputs['Scale'].default_value = 0.50
cn.inputs['Detail'].default_value = 3.0
cn.inputs['Roughness'].default_value = 0.55
L(cmb0.outputs['Vector'], cn.inputs['Vector']); L(wA.outputs[0], cn.inputs['W'])
cr = N('ShaderNodeValToRGB'); cr.location = (480, -300); cr.label = 'CLOUDF'
cr.color_ramp.interpolation = 'LINEAR'
cr.color_ramp.elements[0].position = 0.415
cr.color_ramp.elements[1].position = 0.665
cn.label = 'CNRAW'
L(cn.outputs['Fac'], cr.inputs['Fac'])
# ---- mid mottle: ~0.9 m cool-grey blooms that break up the slab blobs
mn = N('ShaderNodeTexNoise'); mn.noise_dimensions = '4D'; mn.location = (300, -560)
mn.inputs['Scale'].default_value = 1.40
mn.inputs['Detail'].default_value = 4.0
mn.inputs['Roughness'].default_value = 0.50
mn.label = 'MNRAW'
L(cmb0.outputs['Vector'], mn.inputs['Vector']); L(wB.outputs[0], mn.inputs['W'])
mr = N('ShaderNodeValToRGB'); mr.location = (480, -560)
mr.color_ramp.interpolation = 'EASE'
mr.color_ramp.elements[0].position = 0.400
mr.color_ramp.elements[1].position = 0.605
L(mn.outputs['Fac'], mr.inputs['Fac'])
mf = N('ShaderNodeMath'); mf.operation = 'MULTIPLY'; mf.inputs[1].default_value = 0.34; mf.location = (760, -560)
mf.label = 'MOTTF'
L(mr.outputs['Color'], mf.inputs[0])
# ---- hairline veins: iso-line of the warped noise at its own median.
# Half-width 0.012 is set against the MEASURED sd (0.075), not against 0..1.
fn = N('ShaderNodeTexNoise'); fn.noise_dimensions = '4D'; fn.location = (300, 240)
fn.inputs['Scale'].default_value = 1.90
fn.inputs['Detail'].default_value = 2.0
fn.inputs['Roughness'].default_value = 0.40
fn.inputs['Distortion'].default_value = 0.20
fn.label = 'FNRAW'
L(cmb1.outputs['Vector'], fn.inputs['Vector']); L(wD.outputs[0], fn.inputs['W'])
fs = N('ShaderNodeMath'); fs.operation = 'SUBTRACT'; fs.inputs[1].default_value = 0.4784; fs.location = (480, 240)
L(fn.outputs['Fac'], fs.inputs[0])
fa = N('ShaderNodeMath'); fa.operation = 'ABSOLUTE'; fa.location = (640, 240); L(fs.outputs[0], fa.inputs[0])
fr = N('ShaderNodeValToRGB'); fr.location = (800, 240); fr.label = 'FINEF'
fr.color_ramp.interpolation = 'EASE'
fr.color_ramp.elements[0].color = (1, 1, 1, 1)
fr.color_ramp.elements[1].position = 0.0120
fr.color_ramp.elements[1].color = (0, 0, 0, 1)
L(fa.outputs[0], fr.inputs['Fac'])
# ---- bold vein: same median level set (that is what makes veins long and wandering)
# but SPATIALLY GATED, so it does not percolate into a crazed web over the whole tile.
gn = N('ShaderNodeTexNoise'); gn.noise_dimensions = '4D'; gn.location = (300, -20)
gn.inputs['Scale'].default_value = 0.65
gn.inputs['Detail'].default_value = 3.0
gn.inputs['Roughness'].default_value = 0.50
gn.inputs['Distortion'].default_value = 0.30
gn.label = 'GNRAW'
L(cmb1.outputs['Vector'], gn.inputs['Vector']); L(wE.outputs[0], gn.inputs['W'])
gs = N('ShaderNodeMath'); gs.operation = 'SUBTRACT'; gs.inputs[1].default_value = 0.4817; gs.location = (480, -20)
L(gn.outputs['Fac'], gs.inputs[0])
ga = N('ShaderNodeMath'); ga.operation = 'ABSOLUTE'; ga.location = (640, -20); L(gs.outputs[0], ga.inputs[0])
gr = N('ShaderNodeValToRGB'); gr.location = (800, -20)
gr.color_ramp.interpolation = 'EASE'
gr.color_ramp.elements[0].color = (1, 1, 1, 1)
gr.color_ramp.elements[1].position = 0.0125
gr.color_ramp.elements[1].color = (0, 0, 0, 1)
ghl = gr.color_ramp.elements.new(0.0035)
ghl.color = (0.42, 0.42, 0.42, 1)
L(ga.outputs[0], gr.inputs['Fac'])
gm = N('ShaderNodeTexNoise'); gm.noise_dimensions = '4D'; gm.location = (300, -820)
gm.inputs['Scale'].default_value = 0.55
gm.inputs['Detail'].default_value = 2.0
gm.inputs['Roughness'].default_value = 0.50
gm.label = 'GMRAW'
L(cmb0.outputs['Vector'], gm.inputs['Vector']); L(wC.outputs[0], gm.inputs['W'])
gmr = N('ShaderNodeValToRGB'); gmr.location = (480, -820); gmr.label = 'GATEF'
gmr.color_ramp.interpolation = 'EASE'
gmr.color_ramp.elements[0].position = 0.434
gmr.color_ramp.elements[1].position = 0.554
L(gm.outputs['Fac'], gmr.inputs['Fac'])
gg = N('ShaderNodeMath'); gg.operation = 'MULTIPLY'; gg.location = (1000, -400)
L(gr.outputs['Color'], gg.inputs[0]); L(gmr.outputs['Color'], gg.inputs[1])
gf = N('ShaderNodeMath'); gf.operation = 'MULTIPLY'; gf.inputs[1].default_value = 0.75; gf.location = (1160, -400)
gf.label = 'BOLDF'
L(gg.outputs[0], gf.inputs[0])
# ---- compose. Ground stays warm; both veins are cooler and less saturated than the
# calcite field, which is the hue break that makes it read as stone and not as cream paint.
m1 = N('ShaderNodeMix'); m1.data_type = 'RGBA'; m1.location = (760, 700)
S(m1, 'A_Color').default_value = (0.715, 0.668, 0.580, 1.0)
S(m1, 'B_Color').default_value = (0.530, 0.493, 0.425, 1.0)
L(cr.outputs['Color'], S(m1, 'Factor_Float'))
m2 = N('ShaderNodeMix'); m2.data_type = 'RGBA'; m2.location = (940, 700)
S(m2, 'B_Color').default_value = (0.505, 0.520, 0.528, 1.0)
L(O(m1), S(m2, 'A_Color')); L(mf.outputs[0], S(m2, 'Factor_Float'))
m3 = N('ShaderNodeMix'); m3.data_type = 'RGBA'; m3.location = (1120, 700)
S(m3, 'B_Color').default_value = (0.300, 0.302, 0.298, 1.0)
L(O(m2), S(m3, 'A_Color')); L(fr.outputs['Color'], S(m3, 'Factor_Float'))
m4 = N('ShaderNodeMix'); m4.data_type = 'RGBA'; m4.location = (1300, 700)
S(m4, 'B_Color').default_value = (0.192, 0.205, 0.226, 1.0)
L(O(m3), S(m4, 'A_Color')); L(gf.outputs[0], S(m4, 'Factor_Float'))
L(O(m4), bsdf.inputs['Base Color'])
mat.diffuse_color = (0.640, 0.600, 0.525, 1.0)
