mat.use_nodes = True
nt = mat.node_tree
nodes = nt.nodes
links = nt.links
nodes.clear()

TAU = 6.2831853072
NM = 0.482

# ---- seamless 4D torus coordinate built from Generated (u,v) -------------
tc = nodes.new("ShaderNodeTexCoord")
tc.location = (-2400, 0)
sep = nodes.new("ShaderNodeSeparateXYZ")
sep.location = (-2200, 0)
links.new(tc.outputs["Generated"], sep.inputs["Vector"])

au = nodes.new("ShaderNodeMath")
au.operation = 'MULTIPLY'
au.inputs[1].default_value = TAU
au.location = (-2020, 120)
links.new(sep.outputs["X"], au.inputs[0])

av = nodes.new("ShaderNodeMath")
av.operation = 'MULTIPLY'
av.inputs[1].default_value = TAU
av.location = (-2020, -120)
links.new(sep.outputs["Y"], av.inputs[0])

cu = nodes.new("ShaderNodeMath")
cu.operation = 'COSINE'
cu.location = (-1850, 240)
links.new(au.outputs[0], cu.inputs[0])
su = nodes.new("ShaderNodeMath")
su.operation = 'SINE'
su.location = (-1850, 90)
links.new(au.outputs[0], su.inputs[0])
cv = nodes.new("ShaderNodeMath")
cv.operation = 'COSINE'
cv.location = (-1850, -60)
links.new(av.outputs[0], cv.inputs[0])
sv = nodes.new("ShaderNodeMath")
sv.operation = 'SINE'
sv.location = (-1850, -210)
links.new(av.outputs[0], sv.inputs[0])

tor = nodes.new("ShaderNodeCombineXYZ")
tor.location = (-1680, 120)
links.new(cu.outputs[0], tor.inputs["X"])
links.new(su.outputs[0], tor.inputs["Y"])
links.new(cv.outputs[0], tor.inputs["Z"])

w_depth = nodes.new("ShaderNodeMath")
w_depth.operation = 'ADD'
w_depth.inputs[1].default_value = 0.0
w_depth.location = (-1680, -260)
links.new(sv.outputs[0], w_depth.inputs[0])

w_warp = nodes.new("ShaderNodeMath")
w_warp.operation = 'ADD'
w_warp.inputs[1].default_value = 3.70
w_warp.location = (-1680, -380)
links.new(sv.outputs[0], w_warp.inputs[0])

w_fine = nodes.new("ShaderNodeMath")
w_fine.operation = 'ADD'
w_fine.inputs[1].default_value = 8.15
w_fine.location = (-1680, -500)
links.new(sv.outputs[0], w_fine.inputs[0])

w_mask = nodes.new("ShaderNodeMath")
w_mask.operation = 'ADD'
w_mask.inputs[1].default_value = 12.40
w_mask.location = (-1680, -620)
links.new(sv.outputs[0], w_mask.inputs[0])

# ---- noises --------------------------------------------------------------
n_depth = nodes.new("ShaderNodeTexNoise")
n_depth.name = "N_DEPTH"
n_depth.noise_dimensions = '4D'
n_depth.inputs["Scale"].default_value = 0.50
n_depth.inputs["Detail"].default_value = 3.0
n_depth.inputs["Roughness"].default_value = 0.55
n_depth.inputs["Lacunarity"].default_value = 2.0
n_depth.inputs["Distortion"].default_value = 0.0
n_depth.location = (-1480, 300)
links.new(tor.outputs["Vector"], n_depth.inputs["Vector"])
links.new(w_depth.outputs[0], n_depth.inputs["W"])

n_warp = nodes.new("ShaderNodeTexNoise")
n_warp.name = "N_WARP"
n_warp.noise_dimensions = '4D'
n_warp.inputs["Scale"].default_value = 1.10
n_warp.inputs["Detail"].default_value = 2.0
n_warp.inputs["Roughness"].default_value = 0.50
n_warp.inputs["Lacunarity"].default_value = 2.0
n_warp.inputs["Distortion"].default_value = 0.0
n_warp.location = (-1480, 20)
links.new(tor.outputs["Vector"], n_warp.inputs["Vector"])
links.new(w_warp.outputs[0], n_warp.inputs["W"])

n_fine = nodes.new("ShaderNodeTexNoise")
n_fine.name = "N_FINE"
n_fine.noise_dimensions = '4D'
n_fine.inputs["Scale"].default_value = 1.90
n_fine.inputs["Detail"].default_value = 2.0
n_fine.inputs["Roughness"].default_value = 0.50
n_fine.inputs["Lacunarity"].default_value = 2.0
n_fine.inputs["Distortion"].default_value = 0.0
n_fine.location = (-1480, -260)
links.new(tor.outputs["Vector"], n_fine.inputs["Vector"])
links.new(w_fine.outputs[0], n_fine.inputs["W"])

n_mask = nodes.new("ShaderNodeTexNoise")
n_mask.name = "N_MASK"
n_mask.noise_dimensions = '4D'
n_mask.inputs["Scale"].default_value = 0.62
n_mask.inputs["Detail"].default_value = 2.0
n_mask.inputs["Roughness"].default_value = 0.50
n_mask.inputs["Lacunarity"].default_value = 2.0
n_mask.inputs["Distortion"].default_value = 0.0
n_mask.location = (-1480, -560)
links.new(tor.outputs["Vector"], n_mask.inputs["Vector"])
links.new(w_mask.outputs[0], n_mask.inputs["W"])

# ---- ripple field A : broad swell ----------------------------------------
wavesA = ((2.0, 1.0, 0.42, 5.0, 0.00),
          (3.0, -2.0, 0.26, 4.0, 1.35),
          (-1.0, 4.0, 0.19, 3.2, 2.55),
          (5.0, 3.0, 0.13, 2.6, 4.10))
accA = None
iA = 0
for wa in wavesA:
    dp = nodes.new("ShaderNodeVectorMath")
    dp.operation = 'DOT_PRODUCT'
    dp.inputs[1].default_value = (wa[0] * TAU, wa[1] * TAU, 0.0)
    dp.location = (-1260, 460 - iA * 160)
    links.new(tc.outputs["Generated"], dp.inputs[0])
    ph = nodes.new("ShaderNodeMath")
    ph.operation = 'MULTIPLY_ADD'
    ph.inputs[1].default_value = wa[3]
    ph.inputs[2].default_value = wa[4] - wa[3] * NM
    ph.location = (-1080, 460 - iA * 160)
    links.new(n_warp.outputs[0], ph.inputs[0])
    ad = nodes.new("ShaderNodeMath")
    ad.operation = 'ADD'
    ad.location = (-900, 460 - iA * 160)
    links.new(dp.outputs["Value"], ad.inputs[0])
    links.new(ph.outputs[0], ad.inputs[1])
    sn = nodes.new("ShaderNodeMath")
    sn.operation = 'SINE'
    sn.location = (-730, 460 - iA * 160)
    links.new(ad.outputs[0], sn.inputs[0])
    mad = nodes.new("ShaderNodeMath")
    mad.operation = 'MULTIPLY_ADD'
    mad.inputs[1].default_value = wa[2]
    mad.inputs[2].default_value = 0.0
    mad.location = (-560, 460 - iA * 160)
    links.new(sn.outputs[0], mad.inputs[0])
    if accA is not None:
        links.new(accA.outputs[0], mad.inputs[2])
    accA = mad
    iA += 1

rA = nodes.new("ShaderNodeMath")
rA.name = "RIPPLE_A"
rA.operation = 'MULTIPLY_ADD'
rA.inputs[1].default_value = 0.5
rA.inputs[2].default_value = 0.5
rA.location = (-380, 460)
links.new(accA.outputs[0], rA.inputs[0])

# ---- ripple field B : fine chop that carries the caustic web -------------
wavesB = ((13.0, 7.0, 0.33, 2.6, 0.70),
          (-9.0, 16.0, 0.27, 2.2, 2.10),
          (19.0, -11.0, 0.22, 1.8, 3.55),
          (6.0, 21.0, 0.18, 1.5, 5.20))
accB = None
iB = 0
for wb in wavesB:
    dp = nodes.new("ShaderNodeVectorMath")
    dp.operation = 'DOT_PRODUCT'
    dp.inputs[1].default_value = (wb[0] * TAU, wb[1] * TAU, 0.0)
    dp.location = (-1260, -260 - iB * 160)
    links.new(tc.outputs["Generated"], dp.inputs[0])
    ph = nodes.new("ShaderNodeMath")
    ph.operation = 'MULTIPLY_ADD'
    ph.inputs[1].default_value = wb[3]
    ph.inputs[2].default_value = wb[4] - wb[3] * NM
    ph.location = (-1080, -260 - iB * 160)
    links.new(n_fine.outputs[0], ph.inputs[0])
    ad = nodes.new("ShaderNodeMath")
    ad.operation = 'ADD'
    ad.location = (-900, -260 - iB * 160)
    links.new(dp.outputs["Value"], ad.inputs[0])
    links.new(ph.outputs[0], ad.inputs[1])
    sn = nodes.new("ShaderNodeMath")
    sn.operation = 'SINE'
    sn.location = (-730, -260 - iB * 160)
    links.new(ad.outputs[0], sn.inputs[0])
    mad = nodes.new("ShaderNodeMath")
    mad.operation = 'MULTIPLY_ADD'
    mad.inputs[1].default_value = wb[2]
    mad.inputs[2].default_value = 0.0
    mad.location = (-560, -260 - iB * 160)
    links.new(sn.outputs[0], mad.inputs[0])
    if accB is not None:
        links.new(accB.outputs[0], mad.inputs[2])
    accB = mad
    iB += 1

rB = nodes.new("ShaderNodeMath")
rB.name = "RIPPLE_B"
rB.operation = 'MULTIPLY_ADD'
rB.inputs[1].default_value = 0.5
rB.inputs[2].default_value = 0.5
rB.location = (-380, -260)
links.new(accB.outputs[0], rB.inputs[0])

# ---- caustic web = ridge line of field B ---------------------------------
sgn = nodes.new("ShaderNodeMath")
sgn.operation = 'MULTIPLY_ADD'
sgn.inputs[1].default_value = 2.0
sgn.inputs[2].default_value = -1.0
sgn.location = (-200, -260)
links.new(rB.outputs[0], sgn.inputs[0])
ab = nodes.new("ShaderNodeMath")
ab.operation = 'ABSOLUTE'
ab.location = (-40, -260)
links.new(sgn.outputs[0], ab.inputs[0])
ridge = nodes.new("ShaderNodeMath")
ridge.name = "RIDGE"
ridge.operation = 'SUBTRACT'
ridge.inputs[0].default_value = 1.0
ridge.location = (120, -260)
links.new(ab.outputs[0], ridge.inputs[1])

halo = nodes.new("ShaderNodeValToRGB")
halo.name = "HALO_RAMP"
halo.location = (300, -120)
halo.color_ramp.interpolation = 'B_SPLINE'
halo.color_ramp.elements[0].position = 0.685
halo.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
halo.color_ramp.elements[1].position = 0.97
halo.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
links.new(ridge.outputs[0], halo.inputs["Fac"])

core = nodes.new("ShaderNodeValToRGB")
core.name = "CORE_RAMP"
core.location = (300, -420)
core.color_ramp.interpolation = 'EASE'
core.color_ramp.elements[0].position = 0.918
core.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
core.color_ramp.elements[1].position = 0.9605
core.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
links.new(ridge.outputs[0], core.inputs["Fac"])

mask = nodes.new("ShaderNodeValToRGB")
mask.name = "MASK_RAMP"
mask.location = (-1260, -900)
mask.color_ramp.interpolation = 'B_SPLINE'
mask.color_ramp.elements[0].position = 0.428
mask.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
mask.color_ramp.elements[1].position = 0.562
mask.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
links.new(n_mask.outputs[0], mask.inputs["Fac"])

halo_m = nodes.new("ShaderNodeMath")
halo_m.name = "HALO_FAC"
halo_m.operation = 'MULTIPLY'
halo_m.inputs[1].default_value = 0.0
halo_m.location = (520, -120)
links.new(halo.outputs["Color"], halo_m.inputs[0])
links.new(mask.outputs["Color"], halo_m.inputs[1])

crest = nodes.new("ShaderNodeMath")
crest.name = "CREST"
crest.operation = 'MULTIPLY_ADD'
crest.inputs[1].default_value = 0.72
crest.inputs[2].default_value = 0.28
crest.location = (300, 620)
links.new(shade.outputs["Color"], crest.inputs[0])

halo_c = nodes.new("ShaderNodeMath")
halo_c.operation = 'MULTIPLY'
halo_c.inputs[1].default_value = 0.0
halo_c.location = (600, -20)
links.new(halo_m.outputs[0], halo_c.inputs[0])
links.new(crest.outputs[0], halo_c.inputs[1])

core_c = nodes.new("ShaderNodeMath")
core_c.operation = 'MULTIPLY'
core_c.inputs[1].default_value = 0.0
core_c.location = (600, -520)
links.new(core_m.outputs[0], core_c.inputs[0])
links.new(crest.outputs[0], core_c.inputs[1])

halo_s = nodes.new("ShaderNodeMath")
halo_s.operation = 'MULTIPLY'
halo_s.inputs[1].default_value = 0.42
halo_s.location = (680, -120)
links.new(halo_c.outputs[0], halo_s.inputs[0])

core_m = nodes.new("ShaderNodeMath")
core_m.name = "CORE_FAC"
core_m.operation = 'MULTIPLY'
core_m.inputs[1].default_value = 0.0
core_m.location = (520, -420)
links.new(core.outputs["Color"], core_m.inputs[0])
links.new(mask.outputs["Color"], core_m.inputs[1])

core_s = nodes.new("ShaderNodeMath")
core_s.operation = 'MULTIPLY'
core_s.inputs[1].default_value = 0.88
core_s.location = (680, -420)
links.new(core_c.outputs[0], core_s.inputs[0])

# ---- broad shading and depth ramps ---------------------------------------
shade = nodes.new("ShaderNodeValToRGB")
shade.name = "SHADE_RAMP"
shade.location = (-200, 460)
shade.color_ramp.interpolation = 'B_SPLINE'
shade.color_ramp.elements[0].position = 0.10
shade.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
shade.color_ramp.elements[1].position = 0.90
shade.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
links.new(rA.outputs[0], shade.inputs["Fac"])

depth = nodes.new("ShaderNodeValToRGB")
depth.name = "DEPTH_RAMP"
depth.location = (-1260, 900)
depth.color_ramp.interpolation = 'B_SPLINE'
depth.color_ramp.elements[0].position = 0.345
depth.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
depth.color_ramp.elements[1].position = 0.640
depth.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
links.new(n_depth.outputs[0], depth.inputs["Fac"])

# ---- colour build --------------------------------------------------------
mix_depth = nodes.new("ShaderNodeMix")
mix_depth.data_type = 'RGBA'
mix_depth.blend_type = 'MIX'
mix_depth.location = (-1000, 900)
mix_depth.inputs[6].default_value = (0.0070, 0.0265, 0.0430, 1.0)
mix_depth.inputs[7].default_value = (0.0235, 0.0850, 0.0760, 1.0)
links.new(depth.outputs["Color"], mix_depth.inputs[0])

mix_shade = nodes.new("ShaderNodeMix")
mix_shade.data_type = 'RGBA'
mix_shade.blend_type = 'MIX'
mix_shade.location = (100, 460)
mix_shade.inputs[7].default_value = (0.0780, 0.1720, 0.1780, 1.0)
links.new(mix_depth.outputs[2], mix_shade.inputs[6])
links.new(shade.outputs["Color"], mix_shade.inputs[0])

mix_halo = nodes.new("ShaderNodeMix")
mix_halo.data_type = 'RGBA'
mix_halo.blend_type = 'MIX'
mix_halo.location = (880, 200)
mix_halo.inputs[7].default_value = (0.1550, 0.2900, 0.2900, 1.0)
links.new(mix_shade.outputs[2], mix_halo.inputs[6])
links.new(halo_s.outputs[0], mix_halo.inputs[0])

mix_core = nodes.new("ShaderNodeMix")
mix_core.data_type = 'RGBA'
mix_core.blend_type = 'MIX'
mix_core.location = (1060, 0)
mix_core.inputs[7].default_value = (0.5300, 0.7400, 0.6950, 1.0)
links.new(mix_halo.outputs[2], mix_core.inputs[6])
links.new(core_s.outputs[0], mix_core.inputs[0])

bsdf = nodes.new("ShaderNodeBsdfPrincipled")
bsdf.location = (1280, 0)
bsdf.inputs["Metallic"].default_value = 0.0
bsdf.inputs["Roughness"].default_value = 0.5
bsdf.inputs["Specular IOR Level"].default_value = 0.5
bsdf.inputs["Emission Strength"].default_value = 0.0
links.new(mix_core.outputs[2], bsdf.inputs["Base Color"])

outp = nodes.new("ShaderNodeOutputMaterial")
outp.location = (1540, 0)
links.new(bsdf.outputs["BSDF"], outp.inputs["Surface"])
