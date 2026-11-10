import bpy, sys, json, math, collections
sys.path.append(r"C:\Work\blender")
import kgp_export_v3 as E
def exportable(o):
    if o.hide_render or not o.visible_get(): return False
    return not any(any(s in c.name for s in E.SKIP_COLL) for c in o.users_collection)
objs = [o for o in bpy.data.objects if o.type in ('CURVE', 'FONT', 'SURFACE', 'META') and exportable(o)]
nonyaw, negscale, nonuni = [], [], []
for o in objs:
    e = o.matrix_world.to_euler('ZXY')
    if abs(e.x) > 1e-3 or abs(e.y) > 1e-3: nonyaw.append((o.name, round(math.degrees(e.x),1), round(math.degrees(e.y),1)))
    s = o.matrix_world.to_scale()
    if min(s) < 0 or o.matrix_world.determinant() < 0: negscale.append(o.name)
    if max(s) - min(s) > 1e-3: nonuni.append(o.name)
share = collections.defaultdict(list)
for o in objs: share[o.data.name].append(o.name)
doors = [o for o in objs if any("Wing room doors" in c.name for c in o.users_collection)]
dn = collections.Counter("_".join(o.name.split(" ")[:3]) for o in doors)
st = bpy.data.objects.get("P7 fountain water streams (GN)")
dg = bpy.context.evaluated_depsgraph_get()
drop_rot = set(); drop_mats = set(); drop_scale = set()
for inst in dg.object_instances:
    if inst.is_instance and inst.parent and inst.parent.original == st:
        m = st.matrix_world.inverted() @ inst.matrix_world
        e = m.to_euler(); drop_rot.add(tuple(round(math.degrees(a)) for a in e))
        drop_scale.add(tuple(round(x, 3) for x in m.to_scale()))
        drop_mats.update(mm.name for mm in inst.object.data.materials if mm)
print("@@X " + json.dumps({
    "objects": len(objs), "non_yaw": len(nonyaw), "non_yaw_sample": nonyaw[:8],
    "neg_scale": negscale[:8], "n_neg": len(negscale), "non_uniform": len(nonuni),
    "shared_data": [(k, len(v), v[:3]) for k, v in share.items() if len(v) > 1],
    "door_curves": len(doors), "door_names": dn.most_common(15),
    "door_sample": [(o.name, [round(x, 2) for x in o.matrix_world.translation]) for o in doors[:12]],
    "drops": {"rot_variants": len(drop_rot), "scales": list(drop_scale)[:5], "mats": sorted(drop_mats)}}, ensure_ascii=False))
