import bpy, sys, json, collections
sys.path.append(r"C:\Work\blender")
import kgp_export_v3 as E
dg = bpy.context.evaluated_depsgraph_get()
def exportable(o):
    if o.hide_render or not o.visible_get(): return False
    return not any(any(s in c.name for s in E.SKIP_COLL) for c in o.users_collection)
# 1) non-mesh geometry objects that render
objs = [o for o in bpy.data.objects if o.type in ('CURVE', 'FONT', 'SURFACE', 'META') and exportable(o)]
datas = collections.Counter(o.data.name for o in objs)
rows = []
tri_by_data = {}
for o in objs:
    ev = o.evaluated_get(dg)
    try:
        me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
    except Exception:
        me = None
    t = 0; uv = []; mats = []
    if me:
        me.calc_loop_triangles(); t = len(me.loop_triangles)
        uv = [u.name for u in me.uv_layers]
        mats = [m.name for m in me.materials if m]
        bpy.data.meshes.remove(me)
    tri_by_data[o.data.name] = t
    rows.append({"obj": o.name, "type": o.type, "data": o.data.name, "tris": t, "uv": uv, "mats": mats,
                 "coll": o.users_collection[0].name if o.users_collection else ""})
# 2) GN / particle instances on exported mesh objects
exported = {o.name for o in E.collect()}
gn = collections.Counter(); gn_tris = collections.Counter()
for inst in dg.object_instances:
    if inst.is_instance and inst.parent and inst.parent.original.name in exported and inst.object.type == 'MESH':
        gn[inst.parent.original.name] += 1
        try:
            m = inst.object.data; m.calc_loop_triangles(); gn_tris[inst.parent.original.name] += len(m.loop_triangles)
        except Exception: pass
out = {"curve_objects": len(rows), "unique_curve_data": len(datas), "world_tris": sum(r["tris"] for r in rows),
       "unique_tris": sum(tri_by_data.values()),
       "shared_data": {k: v for k, v in datas.items() if v > 1},
       "no_uv": sum(1 for r in rows if not r["uv"]),
       "by_coll": collections.Counter(r["coll"] for r in rows).most_common(),
       "by_mat": collections.Counter(m for r in rows for m in r["mats"]).most_common(),
       "over_25k": [(r["obj"], r["tris"]) for r in rows if r["tris"] > 25000],
       "gn": [(k, v, gn_tris[k]) for k, v in gn.items()],
       "rows": rows}
json.dump(out, open(r"C:\Work\blender\ovdr_export\_missing_inv.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("@@DONE")
