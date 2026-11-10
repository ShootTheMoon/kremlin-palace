import bpy
import sys
import os


def argval(flag, default=None):
    a = sys.argv
    if "--" in a:
        a = a[a.index("--") + 1:]
    if flag in a:
        return a[a.index(flag) + 1]
    return default


RECIPE = argval("--recipe", r"C:\Work\blender\ovdr_export\kgp_v3\_scratch\recipe_p7.py")
OUT = argval("--out", r"C:\Work\blender\ovdr_export\kgp_v3\_scratch\out\P7_water_basin.png")
SIZE = int(argval("--size", "1024"))
PROBE = argval("--probe", "")

os.makedirs(os.path.dirname(OUT), exist_ok=True)

# ---- clean scene ---------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.engine = 'CYCLES'
scn.cycles.device = 'CPU'
scn.cycles.samples = 1
scn.cycles.use_denoising = False
scn.render.bake.margin = 16
scn.render.bake.use_clear = True
scn.render.bake.use_pass_direct = False
scn.render.bake.use_pass_indirect = False
scn.render.bake.use_pass_color = True
scn.world = None

bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, 0))
ob = bpy.context.active_object
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.0)
bpy.ops.object.mode_set(mode='OBJECT')
uvl = ob.data.uv_layers.active
for i in range(len(uvl.data)):
    pass

mat = bpy.data.materials.new("P7_water_basin")
ob.data.materials.append(mat)

src = open(RECIPE, "r", encoding="utf-8").read()
g = {"bpy": bpy, "mat": mat}
exec(compile(src, RECIPE, "exec"), g)

nt = mat.node_tree
nodes = nt.nodes
links = nt.links

bsdf = None
for n in nodes:
    if n.type == 'BSDF_PRINCIPLED':
        bsdf = n
print("BSDF metallic", bsdf.inputs["Metallic"].default_value,
      "roughness", bsdf.inputs["Roughness"].default_value)

if PROBE:
    name, _, sock = PROBE.partition(":")
    pn = nodes[name]
    outs = pn.outputs[0]
    if sock:
        outs = pn.outputs[sock]
    for l in list(bsdf.inputs["Base Color"].links):
        links.remove(l)
    links.new(outs, bsdf.inputs["Base Color"])
    print("PROBE", name, outs.name)

img = bpy.data.images.new("BAKE", SIZE, SIZE, alpha=False, float_buffer=bool(PROBE))
tex = nodes.new("ShaderNodeTexImage")
tex.image = img
tex.location = (1400, -600)
nodes.active = tex
for n in nodes:
    n.select = False
tex.select = True

bpy.ops.object.select_all(action='DESELECT')
ob.select_set(True)
bpy.context.view_layer.objects.active = ob
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, use_clear=True, margin=16)

img.filepath_raw = OUT
img.file_format = 'PNG'
img.save()
print("SAVED", OUT)

# ---- stats on the linear float buffer ------------------------------------
px = list(img.pixels)
n = SIZE * SIZE
for ci, cname in ((0, "R"), (1, "G"), (2, "B")):
    v = px[ci::4]
    v.sort()
    mean = sum(v) / n
    var = sum((x - mean) ** 2 for x in v) / n
    print("LIN %s min=%.4f p01=%.4f p25=%.4f med=%.4f p75=%.4f p99=%.4f max=%.4f mean=%.4f sd=%.4f"
          % (cname, v[0], v[int(n * 0.01)], v[int(n * 0.25)], v[n // 2],
             v[int(n * 0.75)], v[int(n * 0.99)], v[-1], mean, var ** 0.5))
