# Kremlin Palace -> OVERDARE export driver (headless)
#   blender.exe --background <blend> --python krm_export.py
#
# Rules honoured (from prior OVERDARE runs):
#   - <=28,000 tris per FILE and per MESH (satisfy both; their spec contradicted itself)
#   - ONE mesh per file (importer publishes one world asset PER OBJECT and leaks a
#     transient world for each -> join everything in a file into a single object)
#   - textures <=1024, <=15 MB; .fbx only
#   - colliders NEVER in the FBX (OVERDARE has no UCX) -> engine Parts, emitted as JSON
#   - STATIC exported in WORLD coords so the map self-assembles at (0,0,0)
#   - INSTANCED masters exported in LOCAL coords + placements.csv
#   - no bpy.ops.mesh.separate / mode_set  (spins forever headless)
#   - no img.scale()/img.copy()           (null buffer headless) -> textures pre-made
#   - measure bbox from real verts, never bound_box

import bpy, bmesh, os, json, csv, math, time
from mathutils import Vector

ROOT = r"C:\Users\29\Desktop\Kremlin_Palace_Phase3\OVERDARE"
STATIC_DIR = os.path.join(ROOT, "01_STATIC")
MASTER_DIR = os.path.join(ROOT, "02_INSTANCE_MASTERS")
TEX_DIR    = os.path.join(ROOT, "03_TEXTURES")
WORK       = os.path.join(ROOT, "_work")
TRI_CAP    = 28000

for d in (STATIC_DIR, MASTER_DIR, WORK):
    os.makedirs(d, exist_ok=True)

log = []
def P(*a):
    s = " ".join(str(x) for x in a)
    log.append(s); print("[KRM]", s, flush=True)

PAL = json.load(open(os.path.join(WORK, "palette_map.json"), encoding="utf-8-sig"))

# ---------------------------------------------------------------- materials
def flat_mat(name, png):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    t = nt.nodes.new("ShaderNodeTexImage")
    img = bpy.data.images.get(os.path.basename(png))
    if img is None:
        img = bpy.data.images.load(png)
    t.image = img
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(b.outputs["BSDF"], o.inputs["Surface"])
    return m

M_PAL   = flat_mat("KRM_PALETTE",  os.path.join(TEX_DIR, "KRM_palette.png"))
M_CHAIR = flat_mat("KRM_ARMCHAIR", os.path.join(TEX_DIR, "KRM_armchair_C.png"))
M_KNIGHT= flat_mat("KRM_KNIGHT",   os.path.join(TEX_DIR, "KRM_knight_C.png"))

TRIPO = {"tripo_material_80e6d73d-33f8-4766-bd64-b25d4f764e6f": M_CHAIR,
         "tripo_material_bf5abb3c-f8fc-422c-bf4d-3c1576eb4cd8": M_KNIGHT}

def uv_for(matname):
    e = PAL.get(matname)
    return (e["u"], e["v"]) if e else (0.99, 0.01)   # magenta corner = unmapped

# ---------------------------------------------------------------- helpers
sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()

def eval_mesh(obj):
    """Evaluated mesh (modifiers applied, curves converted). Caller frees."""
    ev = obj.evaluated_get(dg)
    try:
        me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=False, depsgraph=dg)
    except Exception:
        return None
    if me is None or len(me.polygons) == 0:
        if me: bpy.data.meshes.remove(me)
        return None
    return me

def tri_count(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)

def add_to_bm(bm, uvlay, me, matrix, matslots, tripo_uv=False):
    """Append a mesh into bm, baking `matrix`, writing palette UVs."""
    vmap = []
    for v in me.vertices:
        vmap.append(bm.verts.new(matrix @ v.co))
    bm.verts.index_update()
    src_uv = me.uv_layers.active.data if (tripo_uv and me.uv_layers.active) else None
    for p in me.polygons:
        try:
            f = bm.faces.new([vmap[i] for i in p.vertices])
        except ValueError:
            continue                      # duplicate face
        f.smooth = p.use_smooth          # 원본 셰이딩 유지 (빠뜨리면 곡면이 전부 각진다)
        mi = p.material_index
        mname = matslots[mi] if mi < len(matslots) else ""
        if src_uv is not None:
            for k, l in enumerate(f.loops):
                li = p.loop_start + k
                if li < len(src_uv):
                    l[uvlay].uv = src_uv[li].uv
        else:
            u, v = uv_for(mname)
            for l in f.loops:
                l[uvlay].uv = (u, v)
    return

def write_fbx(obj, path):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, apply_unit_scale=True,
        global_scale=1.0, apply_scale_options='FBX_SCALE_NONE',
        axis_forward='-Z', axis_up='Y',
        object_types={'MESH'}, use_mesh_modifiers=False,
        mesh_smooth_type='FACE', path_mode='COPY', embed_textures=True,
        bake_space_transform=False)

def real_bbox(obj):
    vs = [obj.matrix_world @ v.co for v in obj.data.vertices]
    return ([round(min(p[i] for p in vs), 3) for i in range(3)],
            [round(max(p[i] for p in vs), 3) for i in range(3)])

# ---------------------------------------------------------------- DOORS
# FBX carries no animation into OVERDARE, but the engine CAN swing a door at
# runtime (CFrame.Angles + TweenService). For that the mesh origin must be the
# HINGE, so each hinged group is exported separately in hinge-local space at the
# CLOSED pose, and its children are excluded from the static/instanced passes.
DOOR_DIR = os.path.join(ROOT, "04_DOORS")
os.makedirs(DOOR_DIR, exist_ok=True)
sc.frame_set(sc.frame_start)          # closed pose
dg = bpy.context.evaluated_depsgraph_get()

hinges = [o for o in sc.objects if o.type == 'EMPTY' and
          (o.name.startswith("Entrance door hinge") or o.name.startswith("DOOR_HINGE"))]

def ancestor_hinge(o):
    p = o.parent
    while p:
        if p.type == 'EMPTY' and (p.name.startswith("Entrance door hinge")
                                  or p.name.startswith("DOOR_HINGE")):
            return p
        p = p.parent
    return None

def z_keys(h):
    if not (h.animation_data and h.animation_data.action):
        return []
    a = h.animation_data.action
    try:
        cb = a.layers[0].strips[0].channelbag(a.slots[0])
        for fc in cb.fcurves:
            if fc.data_path == "rotation_euler" and fc.array_index == 2:
                return [[int(k.co[0]), math.degrees(k.co[1])] for k in fc.keyframe_points]
    except Exception:
        pass
    return []

door_children = set()
doors_json = []
for hi, h in enumerate(sorted(hinges, key=lambda x: x.name)):
    kids = [o for o in sc.objects
            if o.type in ('MESH', 'CURVE') and o.visible_get() and ancestor_hinge(o) is h]
    if not kids:
        continue
    H_inv = h.matrix_world.inverted()
    bm = bmesh.new()
    uvlay = bm.loops.layers.uv.new("UVMap")
    tripo_any = False
    for k in kids:
        door_children.add(k.name)
        me = eval_mesh(k)
        if me is None:
            continue
        slots = [m.name if m else "" for m in me.materials]
        if any(s in TRIPO for s in slots):
            tripo_any = True
        add_to_bm(bm, uvlay, me, H_inv @ k.matrix_world, slots)
        bpy.data.meshes.remove(me)
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in h.name)[:46]
    name = "KRM_DOOR_%02d_%s" % (hi, safe)
    dm = bpy.data.meshes.new(name)
    bm.to_mesh(dm); bm.free()
    dm.materials.append(M_PAL)
    ob = bpy.data.objects.new(name, dm)
    sc.collection.objects.link(ob)
    path = os.path.join(DOOR_DIR, name + ".fbx")
    write_fbx(ob, path)
    keys = z_keys(h)
    fps = sc.render.fps
    hw = h.matrix_world.translation
    base = h.matrix_world.to_euler('XYZ')
    doors_json.append({
        "file": name + ".fbx", "hinge": h.name,
        "tris": tri_count(dm), "verts": len(dm.vertices),
        "mb": round(os.path.getsize(path) / 1e6, 3),
        "hinge_X_cm": round(hw.x * 100, 2),
        "hinge_Y_cm": round(hw.z * 100, 2),
        "hinge_Z_cm": round(hw.y * 100, 2),
        "base_yaw_deg": round(-math.degrees(base.z), 3),
        "closed_deg": 0.0,
        "open_deg": round(-keys[-1][1], 3) if keys else None,
        "open_start_s": round(keys[1][0] / fps, 3) if len(keys) > 2 else None,
        "open_end_s": round(keys[-1][0] / fps, 3) if keys else None,
        "animated_in_source": bool(keys),
        "source_keys_frame_deg": [[k[0], round(k[1], 2)] for k in keys],
    })
    P("door", name, tri_count(dm), "tris", "keys", len(keys))
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(dm)

json.dump(doors_json, open(os.path.join(ROOT, "doors.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)
P("doors", len(doors_json), "excluded children", len(door_children))

# ---------------------------------------------------------------- collect
vis = [o for o in sc.objects
       if o.type in ('MESH', 'CURVE') and o.visible_get() and not o.hide_render
       and o.name not in door_children]
static, instanced = [], {}
for o in vis:
    key = o.data.name
    if o.type == 'MESH' and o.data.users > 1:
        instanced.setdefault(key, []).append(o)
    else:
        static.append(o)
P("visible", len(vis), "| static objs", len(static), "| instance masters", len(instanced))

# ---------------------------------------------------------------- STATIC
t0 = time.time()
buckets, cur, cur_tris = [], [], 0
prepared = []
for o in static:
    me = eval_mesh(o)
    if me is None:
        continue
    t = tri_count(me)
    slots = [m.name if m else "" for m in me.materials]
    prepared.append((o.name, me, o.matrix_world.copy(), slots, t))

def split_oversize(nm, me, mw, slots, cap):
    """Split a single mesh that exceeds `cap` into spatial chunks.
    Faces are sorted along the longest world axis and cut into runs — original
    geometry is preserved (never decimate; a collapse shatters ornament)."""
    faces = []
    for p in me.polygons:
        c = mw @ p.center
        faces.append((c, p.vertices[:], p.material_index, len(p.vertices) - 2, p.use_smooth))
    ext = [max(f[0][i] for f in faces) - min(f[0][i] for f in faces) for i in range(3)]
    ax = ext.index(max(ext))
    faces.sort(key=lambda f: f[0][ax])
    out, run, run_t = [], [], 0
    for f in faces:
        if run_t + f[3] > cap and run:
            out.append(run); run, run_t = [], 0
        run.append(f); run_t += f[3]
    if run:
        out.append(run)
    chunks = []
    for ci, run in enumerate(out):
        vidx = sorted({i for f in run for i in f[1]})
        remap = {v: k for k, v in enumerate(vidx)}
        cm = bpy.data.meshes.new("%s__c%02d" % (nm[:40], ci))
        verts = [me.vertices[i].co.copy() for i in vidx]
        polys = [[remap[i] for i in f[1]] for f in run]
        cm.from_pydata(verts, [], polys)
        cm.update()
        for m in me.materials:
            cm.materials.append(m)
        for k, f in enumerate(run):
            if k < len(cm.polygons):
                cm.polygons[k].material_index = f[2]
                cm.polygons[k].use_smooth = f[4]
        chunks.append(("%s#%02d" % (nm, ci), cm, mw, slots, tri_count(cm)))
    return chunks

expanded = []
for rec in prepared:
    if rec[4] > TRI_CAP:
        parts = split_oversize(rec[0], rec[1], rec[2], rec[3], TRI_CAP)
        P("split", rec[0], rec[4], "tris ->", len(parts), "chunks")
        expanded.extend(parts)
    else:
        expanded.append(rec)
prepared = expanded

prepared.sort(key=lambda r: r[0])
for rec in prepared:
    if cur_tris + rec[4] > TRI_CAP and cur:
        buckets.append(cur); cur, cur_tris = [], 0
    cur.append(rec); cur_tris += rec[4]
if cur:
    buckets.append(cur)
P("static buckets", len(buckets), "prep", round(time.time() - t0, 1), "s")

manifest = {"static": [], "masters": [], "tri_cap": TRI_CAP}
for bi, bucket in enumerate(buckets):
    bm = bmesh.new()
    uvlay = bm.loops.layers.uv.new("UVMap")
    for (nm, me, mw, slots, t) in bucket:
        add_to_bm(bm, uvlay, me, mw, slots)
    name = "KRM_STATIC_%03d" % bi
    out_me = bpy.data.meshes.new(name)
    bm.to_mesh(out_me); bm.free()
    out_me.materials.append(M_PAL)
    ob = bpy.data.objects.new(name, out_me)
    sc.collection.objects.link(ob)
    tris = tri_count(out_me)
    path = os.path.join(STATIC_DIR, name + ".fbx")
    write_fbx(ob, path)
    mn, mx = real_bbox(ob)
    manifest["static"].append({"file": name + ".fbx", "tris": tris,
                               "verts": len(out_me.vertices),
                               "parts": [r[0] for r in bucket],
                               "bbox_min_m": mn, "bbox_max_m": mx,
                               "mb": round(os.path.getsize(path) / 1e6, 2)})
    P("static", name, tris, "tris", len(out_me.vertices), "verts")
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(out_me)

for (_, me, _, _, _) in prepared:
    try: bpy.data.meshes.remove(me)
    except Exception: pass

# ---------------------------------------------------------------- INSTANCED
placements = []
for mi, (mesh_name, objs) in enumerate(sorted(instanced.items())):
    src = objs[0]
    me = eval_mesh(src)
    if me is None:
        continue
    slots = [m.name if m else "" for m in me.materials]
    is_tripo = any(s in TRIPO for s in slots)
    # local space, recentred on geometry XY centre with Z at the base
    vs = [v.co.copy() for v in me.vertices]
    cx = (min(v.x for v in vs) + max(v.x for v in vs)) / 2
    cy = (min(v.y for v in vs) + max(v.y for v in vs)) / 2
    zmin = min(v.z for v in vs)
    from mathutils import Matrix
    recentre = Matrix.Translation(Vector((-cx, -cy, -zmin)))
    bm = bmesh.new()
    uvlay = bm.loops.layers.uv.new("UVMap")
    add_to_bm(bm, uvlay, me, recentre, slots, tripo_uv=is_tripo)
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in mesh_name)[:48]
    name = "KRM_M%02d_%s" % (mi, safe)
    out_me = bpy.data.meshes.new(name)
    bm.to_mesh(out_me); bm.free()
    out_me.materials.append(TRIPO[slots[0]] if is_tripo and slots[0] in TRIPO else M_PAL)
    ob = bpy.data.objects.new(name, out_me)
    sc.collection.objects.link(ob)
    tris = tri_count(out_me)
    path = os.path.join(MASTER_DIR, name + ".fbx")
    write_fbx(ob, path)
    manifest["masters"].append({"file": name + ".fbx", "mesh": mesh_name, "tris": tris,
                                "verts": len(out_me.vertices), "instances": len(objs),
                                "textured": is_tripo,
                                "mb": round(os.path.getsize(path) / 1e6, 2)})
    P("master", name, tris, "tris x", len(objs), "instances")
    for o in objs:
        mw = o.matrix_world
        loc = mw.translation
        # the master was recentred, so re-apply the same offset in world space
        off = mw.to_3x3() @ Vector((cx, cy, zmin))
        wx, wy, wz = loc.x + off.x, loc.y + off.y, loc.z + off.z
        eul = mw.to_euler('XYZ')
        placements.append({
            "master": name, "object": o.name,
            "X_cm": round(wx * 100, 2), "Y_cm": round(wz * 100, 2), "Z_cm": round(wy * 100, 2),
            "yaw_deg": round(-math.degrees(eul.z), 3),
            "pitch_deg": round(math.degrees(eul.x), 3), "roll_deg": round(math.degrees(eul.y), 3),
            "scale_x": round(o.scale.x, 5), "scale_y": round(o.scale.y, 5), "scale_z": round(o.scale.z, 5)})
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(out_me)
    bpy.data.meshes.remove(me)

with open(os.path.join(ROOT, "placements.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(placements[0].keys()))
    w.writeheader(); w.writerows(placements)

manifest["totals"] = {
    "static_files": len(manifest["static"]),
    "static_tris": sum(r["tris"] for r in manifest["static"]),
    "master_files": len(manifest["masters"]),
    "master_tris": sum(r["tris"] for r in manifest["masters"]),
    "placements": len(placements),
    "over_margin_28k": [r["file"] for r in manifest["static"] + manifest["masters"] if r["tris"] > TRI_CAP],
    "over_OFFICIAL_30k": [r["file"] for r in manifest["static"] + manifest["masters"] if r["tris"] > 30000],
    "max_tris_in_a_file": max(r["tris"] for r in manifest["static"] + manifest["masters"]),
    "total_mb": round(sum(r["mb"] for r in manifest["static"] + manifest["masters"]), 1),
}
json.dump(manifest, open(os.path.join(ROOT, "manifest.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)
open(os.path.join(WORK, "export_log.txt"), "w", encoding="utf-8").write("\n".join(log))
P("DONE", json.dumps(manifest["totals"], ensure_ascii=False))
