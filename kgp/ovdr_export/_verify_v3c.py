import bpy, json, glob, os
from mathutils import Vector
spec = json.load(open(r"C:\Work\blender\ovdr_export\kgp_v3c\scene_v3c.json", encoding="utf-8"))
nat = {}
for i in spec["instances"]:
    nat.setdefault(i["mesh"], i["native_half_cm"])
res = {"meshes": 0, "loose": 0, "no_uv": [], "mismatch": [], "over30k": []}
for f in sorted(glob.glob(r"C:\Work\blender\ovdr_export\kgp_v3c\10_MESH\*.fbx")):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=f)
    tris = 0
    for o in bpy.context.scene.objects:
        if o.type != 'MESH': continue
        me = o.data
        res["meshes"] += 1
        used = set()
        for p in me.polygons: used.update(p.vertices)
        res["loose"] += len(me.vertices) - len(used)
        if not me.uv_layers: res["no_uv"].append(o.name)
        vs = [o.matrix_world @ me.vertices[i].co for i in used]
        mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
        mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
        d = mx - mn
        half = [d.x * 50, d.z * 50, d.y * 50]
        n = nat.get(o.name)
        if n is None or max(abs(a - b) for a, b in zip(half, n)) > 0.1:
            res["mismatch"].append((o.name, [round(x, 2) for x in half], n))
        me.calc_loop_triangles(); tris += len(me.loop_triangles)
    if tris > 30000: res["over30k"].append((os.path.basename(f), tris))
print("@@R " + json.dumps(res))
