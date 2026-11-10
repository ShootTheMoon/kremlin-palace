import bpy
mat = bpy.data.materials.new("T")
mat.use_nodes = True
nt = mat.node_tree
n = nt.nodes.new("ShaderNodeMix")
n.data_type = 'RGBA'
print("MIX INPUTS")
for i,s in enumerate(n.inputs):
    print(i, repr(s.name), s.type, "enabled=", s.enabled)
print("MIX OUTPUTS")
for i,s in enumerate(n.outputs):
    print(i, repr(s.name), s.type, "enabled=", s.enabled)
nz = nt.nodes.new("ShaderNodeTexNoise")
nz.noise_dimensions = '4D'
print("NOISE INPUTS")
for i,s in enumerate(nz.inputs):
    print(i, repr(s.name), s.type, "enabled=", s.enabled)
print("noise type", nz.noise_type, "normalize", nz.normalize)
vm = nt.nodes.new("ShaderNodeVectorMath")
vm.operation = 'DOT_PRODUCT'
print("VECMATH IN", [s.name for s in vm.inputs], "OUT", [(s.name,s.enabled) for s in vm.outputs])
m = nt.nodes.new("ShaderNodeMath")
m.operation = 'MULTIPLY_ADD'
print("MATH IN", [(i,s.name) for i,s in enumerate(m.inputs)])
bsdf = nt.nodes["Principled BSDF"]
print("BSDF has Specular IOR Level:", 'Specular IOR Level' in bsdf.inputs)
print("bpy", bpy.app.version_string)
