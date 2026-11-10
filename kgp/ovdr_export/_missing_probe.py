import bpy, sys, json, collections
sys.path.append(r"C:\Work\blender")
import kgp_export_v3 as E
exported = {o.name for o in E.collect()}
dg = bpy.context.evaluated_depsgraph_get()
miss = collections.defaultdict(lambda: {"n": 0, "tris": 0, "kind": set(), "coll": set(), "src": set()})
seen_mesh_tris = {}
def tris_of_eval(ob):
    key = ob.data.name if hasattr(ob, "data") and ob.data else ob.name
    if key in seen_mesh_tris: return seen_mesh_tris[key]
    try:
        me = ob.to_mesh()
        me.calc_loop_triangles(); t = len(me.loop_triangles)
        ob.to_mesh_clear()
    except Exception:
        t = 0
    seen_mesh_tris[key] = t
    return t
total_inst = 0
for inst in dg.object_instances:
    ob = inst.object
    if ob.type not in ('MESH', 'CURVE', 'SURFACE', 'FONT', 'META', 'CURVES', 'POINTCLOUD'):
        continue
    orig = ob.original
    parent = inst.parent.original if inst.is_instance and inst.parent else None
    if not inst.is_instance and orig.name in exported:
        continue
    # skip things inside skipped collections (source hidden originals, cameras etc.)
    host = parent if parent else orig
    if any(any(s in c.name for s in E.SKIP_COLL) for c in host.users_collection):
        continue
    if not inst.show_self:
        continue
    if host.hide_render or not host.visible_get():
        continue
    total_inst += 1
    key = (host.name if parent else orig.name)
    m = miss[key]
    m["n"] += 1
    m["tris"] += tris_of_eval(ob)
    m["kind"].add(("instance:" + (parent.type if parent else "?") + "->" + ob.type) if inst.is_instance else ("object:" + ob.type))
    m["coll"].update(c.name for c in host.users_collection)
    m["src"].add(orig.name)
rows = sorted(({"host": k, "n": v["n"], "tris": v["tris"], "kind": sorted(v["kind"]), "coll": sorted(v["coll"]),
               "src": sorted(v["src"])[:4]} for k, v in miss.items()), key=lambda r: -r["tris"])
print("@@M " + json.dumps({"missing_instances": total_inst, "hosts": len(rows),
                          "tris": sum(r["tris"] for r in rows), "rows": rows[:60]}, ensure_ascii=False))
