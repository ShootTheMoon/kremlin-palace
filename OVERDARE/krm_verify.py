# Re-import every written FBX and measure it against manifest.json.
#   blender.exe --background --factory-startup --python krm_verify.py
import bpy, os, json
from mathutils import Vector

ROOT = r"C:\Users\29\Desktop\Kremlin_Palace_Phase3\OVERDARE"
MAN = json.load(open(os.path.join(ROOT, "manifest.json"), encoding="utf-8"))
MAN["doors"] = json.load(open(os.path.join(ROOT, "doors.json"), encoding="utf-8"))
OFFICIAL_TRI = 30000
OFFICIAL_MB = 250
TEX_MB = 15

def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def tri_of(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)

rows, fails = [], []
for sub, key in (("01_STATIC", "static"), ("02_INSTANCE_MASTERS", "masters"), ("04_DOORS", "doors")):
    for rec in MAN[key]:
        path = os.path.join(ROOT, sub, rec["file"])
        clear()
        try:
            bpy.ops.import_scene.fbx(filepath=path)
        except Exception as e:
            fails.append([rec["file"], "IMPORT_FAILED", repr(e)]); continue
        objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        tris = sum(tri_of(o.data) for o in objs)
        verts = sum(len(o.data.vertices) for o in objs)
        vs = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
        if vs:
            mn = [min(p[i] for p in vs) for i in range(3)]
            mx = [max(p[i] for p in vs) for i in range(3)]
        else:
            mn = mx = [0, 0, 0]
        mats = set()
        for o in objs:
            for m in o.data.materials:
                if m: mats.add(m.name)
        row = {"file": rec["file"], "objects": len(objs), "tris": tris, "verts": verts,
               "src_tris": rec["tris"], "materials": len(mats),
               "mb": round(os.path.getsize(path) / 1e6, 2),
               "bbox_min_cm": [round(v, 1) for v in mn], "bbox_max_cm": [round(v, 1) for v in mx]}
        if tris != rec["tris"]:
            fails.append([rec["file"], "TRI_MISMATCH", rec["tris"], tris])
        if len(objs) != 1:
            fails.append([rec["file"], "NOT_ONE_MESH", len(objs)])
        if tris > OFFICIAL_TRI:
            fails.append([rec["file"], "OVER_30K", tris])
        if row["mb"] > OFFICIAL_MB:
            fails.append([rec["file"], "OVER_250MB", row["mb"]])
        if len(mats) != 1:
            fails.append([rec["file"], "MATERIAL_COUNT", len(mats)])
        rows.append(row)

tex = []
for f in os.listdir(os.path.join(ROOT, "03_TEXTURES")):
    p = os.path.join(ROOT, "03_TEXTURES", f)
    mb = round(os.path.getsize(p) / 1e6, 3)
    tex.append([f, mb])
    if mb > TEX_MB:
        fails.append([f, "TEXTURE_OVER_15MB", mb])

summary = {
    "files_checked": len(rows),
    "total_tris": sum(r["tris"] for r in rows),
    "total_verts": sum(r["verts"] for r in rows),
    "total_mb": round(sum(r["mb"] for r in rows), 1),
    "max_tris": max(r["tris"] for r in rows) if rows else 0,
    "all_single_mesh": all(r["objects"] == 1 for r in rows),
    "all_single_material": all(r["materials"] == 1 for r in rows),
    "textures": tex,
    "FAILURES": fails,
}
json.dump({"summary": summary, "rows": rows},
          open(os.path.join(ROOT, "verify_report.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)
print("[VERIFY]", json.dumps(summary, ensure_ascii=False))
