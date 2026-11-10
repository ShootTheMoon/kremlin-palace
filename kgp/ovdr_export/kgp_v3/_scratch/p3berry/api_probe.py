import bpy
print("BLENDER", bpy.app.version_string)
mat = bpy.data.materials.new('T')
mat.use_nodes = True
nt = mat.node_tree
v = nt.nodes.new('ShaderNodeTexVoronoi')
print("VORONOI dims enum:", [e.identifier for e in v.bl_rna.properties['voronoi_dimensions'].enum_items])
print("VORONOI features:", [e.identifier for e in v.bl_rna.properties['feature'].enum_items])
v.voronoi_dimensions = '4D'
print("VOR 4D inputs:", [(i.name, i.type) for i in v.inputs])
print("VOR 4D outputs:", [(o.name, o.type) for o in v.outputs])
n = nt.nodes.new('ShaderNodeTexNoise')
print("NOISE dims:", [e.identifier for e in n.bl_rna.properties['noise_dimensions'].enum_items])
n.noise_dimensions = '4D'
print("NOISE 4D inputs:", [(i.name, i.type) for i in n.inputs])
print("NOISE 4D outputs:", [(o.name, o.type) for o in n.outputs])
vm = nt.nodes.new('ShaderNodeVectorMath')
print("VECMATH ops:", [e.identifier for e in vm.bl_rna.properties['operation'].enum_items])
