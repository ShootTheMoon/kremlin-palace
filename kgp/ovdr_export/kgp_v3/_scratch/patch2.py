import io
p = r"C:\Work\blender\ovdr_export\kgp_v3\_scratch\recipe_p7.py"
s = io.open(p, encoding="utf-8").read()

def rep(a, b):
    global s
    assert a in s, a[:70]
    s = s.replace(a, b, 1)

# finer caustic net, gentler warp
rep("""wavesB = ((7.0, 4.0, 0.33, 3.4, 0.70),
          (-5.0, 9.0, 0.27, 2.8, 2.10),
          (11.0, -6.0, 0.22, 2.2, 3.55),
          (3.0, 12.0, 0.18, 1.8, 5.20))""",
    """wavesB = ((13.0, 7.0, 0.33, 2.6, 0.70),
          (-9.0, 16.0, 0.27, 2.2, 2.10),
          (19.0, -11.0, 0.22, 1.8, 3.55),
          (6.0, 21.0, 0.18, 1.5, 5.20))""")

# narrower halo, narrower core
rep("halo.color_ramp.elements[0].position = 0.62", "halo.color_ramp.elements[0].position = 0.685")
rep("core.color_ramp.elements[0].position = 0.905", "core.color_ramp.elements[0].position = 0.918")
rep("core.color_ramp.elements[1].position = 0.962", "core.color_ramp.elements[1].position = 0.9605")

# stronger, broader density mask
rep("n_mask.inputs[\"Scale\"].default_value = 0.85", "n_mask.inputs[\"Scale\"].default_value = 0.62")
rep("mask.color_ramp.elements[0].position = 0.405", "mask.color_ramp.elements[0].position = 0.428")
rep("mask.color_ramp.elements[1].position = 0.575", "mask.color_ramp.elements[1].position = 0.562")

# weaker halo strength
rep("halo_s.inputs[1].default_value = 0.52", "halo_s.inputs[1].default_value = 0.42")

# colours: bluer, calmer
rep("mix_depth.inputs[6].default_value = (0.0090, 0.0330, 0.0470, 1.0)",
    "mix_depth.inputs[6].default_value = (0.0070, 0.0265, 0.0430, 1.0)")
rep("mix_depth.inputs[7].default_value = (0.0270, 0.0890, 0.0860, 1.0)",
    "mix_depth.inputs[7].default_value = (0.0235, 0.0850, 0.0760, 1.0)")
rep("mix_shade.inputs[7].default_value = (0.0950, 0.1900, 0.1820, 1.0)",
    "mix_shade.inputs[7].default_value = (0.0780, 0.1720, 0.1780, 1.0)")
rep("mix_halo.inputs[7].default_value = (0.2450, 0.4000, 0.3750, 1.0)",
    "mix_halo.inputs[7].default_value = (0.1550, 0.2900, 0.2900, 1.0)")
rep("mix_core.inputs[7].default_value = (0.6400, 0.8100, 0.7350, 1.0)",
    "mix_core.inputs[7].default_value = (0.5300, 0.7400, 0.6950, 1.0)")

# crest modulation: caustics brighter on the swell crests
rep("""halo_s = nodes.new("ShaderNodeMath")""",
    """crest = nodes.new("ShaderNodeMath")
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

halo_s = nodes.new("ShaderNodeMath")""")
rep("links.new(halo_m.outputs[0], halo_s.inputs[0])", "links.new(halo_c.outputs[0], halo_s.inputs[0])")
rep("links.new(core_m.outputs[0], core_s.inputs[0])", "links.new(core_c.outputs[0], core_s.inputs[0])")

io.open(p, "w", encoding="utf-8").write(s)
print("patched v3")
