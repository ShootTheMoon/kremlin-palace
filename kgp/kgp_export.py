# -*- coding: utf-8 -*-
r"""크렘린 대궁전 -> OVERDARE 익스포트 (산곡/화성 규약 그대로).

규약: FBX 1개 = 메시 1개, <=25,000 tris, 재질 1개 = 텍스처 1장(단색 PNG),
      axis_up Y / forward -Z, FBX_SCALE_NONE, 삼각화, ASCII 이름.
      정적물은 월드좌표를 정점에 굽고, 4회 이상 재사용되는 메시는 마스터 1개 + 배치 목록.
엔진 좌표: X = bx*100 + X0, Y = bz*100, Z = -by*100 + Z0

Usage: blender -b <palace.blend> -P kgp_export.py
Out:   Desktop\blender\ovdr_export\kremlin_grand_palace_v1\
"""
import bpy, bmesh, os, sys, json, math, collections
from mathutils import Vector, Matrix

OUT = r"C:\Work\blender\ovdr_export\kremlin_grand_palace_v1"
TEX = os.path.join(OUT, "_tex")
CAP = 25000                     # tris per FBX (OVERDARE hard limit is 30,000 per file)
STATIC_RATIO = 0.5              # 정적 청크를 절반으로 (곡선 장식이 과밀해 엔진에서 무겁다)
CM = 100.0
X0, Z0 = 146000.0, -1400.0      # free corridor: Changdeokgung ends 37200, KRM_Palace starts 95800
PREFIX = "KGP"
SKIP_COLL = ("30x", "34 |", "21 |", "43 |", "LIGHTING")
MASTER_MIN_TRIS = 1500
MASTER_MIN_USERS = 4
FBX = dict(axis_up='Y', axis_forward='-Z', apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE',
           use_selection=True, object_types={'MESH'}, use_mesh_modifiers=False, mesh_smooth_type='FACE',
           path_mode='COPY', embed_textures=True, add_leaf_bones=False, bake_anim=False, use_triangles=True)
MAT_RGB = {}


def ascii_name(s):
    out = "".join(ch if (ch.isalnum() or ch == '_') else "_" for ch in s)
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_")[:48]


def tris_of(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def srgb255(lin):
    out = []
    for c in lin[:3]:
        s = 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
        out.append(int(round(max(0.0, min(1.0, s)) * 255)))
    return out


def source_image(src_mat):
    """The Base Color image of a material, if it has one (the generated props do)."""
    if not (src_mat and src_mat.use_nodes):
        return None
    p = next((n for n in src_mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not p or not p.inputs['Base Color'].is_linked:
        return None
    n = p.inputs['Base Color'].links[0].from_node
    seen = 0
    while n and n.type != 'TEX_IMAGE' and seen < 6:     # walk back through mix/ramp nodes
        inp = next((i for i in n.inputs if i.is_linked), None)
        n = inp.links[0].from_node if inp else None
        seen += 1
    return n.image if (n and n.type == 'TEX_IMAGE' and n.image) else None


def flat_material(src_mat):
    """One FBX-safe material per source material: the real Base Color image when the
    material has one (generated knight/armchair), otherwise a solid 8x8 PNG of its base
    colour. The palace shaders are procedural (veins, emission, refraction) and none of
    that survives FBX, so colour travels as a texture plus the MeshPart Color."""
    name = ascii_name(src_mat.name if src_mat else "nomat")
    existing = bpy.data.materials.get("KGPMAT_" + name)
    if existing:
        return existing, MAT_RGB[name]
    rgb = (0.8, 0.8, 0.8)
    if src_mat and src_mat.use_nodes:
        p = next((n for n in src_mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if p:
            rgb = tuple(p.inputs['Base Color'].default_value)[:3]
    elif src_mat:
        rgb = tuple(src_mat.diffuse_color)[:3]
    path = os.path.join(TEX, name + ".png")
    src_img = source_image(src_mat)
    if not os.path.exists(path):
        if src_img:                                     # keep the real texture, fitted to 512
            img = src_img.copy()
            w, h = img.size
            if max(w, h) > 512:
                s = 512.0 / max(w, h)
                img.scale(max(1, int(w * s)), max(1, int(h * s)))
            rgb = (0.78, 0.78, 0.78)                    # let the texture carry the colour
        else:
            img = bpy.data.images.new("KGPTEX_" + name, 8, 8, alpha=False)
            img.pixels = (list(rgb) + [1.0]) * 64
        img.filepath_raw = path
        img.file_format = 'PNG'
        img.save()
        bpy.data.images.remove(img)
    elif src_img:
        rgb = (0.78, 0.78, 0.78)
    disk = bpy.data.images.get(name + "_kgp") or bpy.data.images.load(path)
    disk.name = name + "_kgp"
    m = bpy.data.materials.new("KGPMAT_" + name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = disk
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    MAT_RGB[name] = srgb255(rgb)
    return m, MAT_RGB[name]


def eval_mesh(o, dg):
    ev = o.evaluated_get(dg)
    try:
        me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=False, depsgraph=dg)
    except Exception:
        return None
    if me is None:
        return None
    if not me.polygons:
        bpy.data.meshes.remove(me)
        return None
    return me


def uv_and_material(me, mat):
    me.materials.clear()
    me.materials.append(mat)
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    for d in me.uv_layers[0].data:
        d.uv = (0.5, 0.5)


def export_mesh(me, folder, name):
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    for x in list(bpy.context.selected_objects):
        x.select_set(False)
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    d = os.path.join(OUT, folder)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, name + ".fbx")
    bpy.ops.export_scene.fbx(filepath=path, **FBX)
    bpy.data.objects.remove(o)
    return path


def bbox_of(me):
    xs = [v.co for v in me.vertices]
    mn = [min(v[i] for v in xs) for i in range(3)]
    mx = [max(v[i] for v in xs) for i in range(3)]
    return mn, mx


def decimate_mesh(me, cap):
    n = tris_of(me)
    if n <= cap:
        return n
    o = bpy.data.objects.new("tmp_dec", me)
    bpy.context.scene.collection.objects.link(o)
    m = o.modifiers.new("dec", 'DECIMATE')
    m.decimate_type = 'COLLAPSE'
    m.ratio = (cap * 0.94) / n
    m.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg)
    bpy.data.objects.remove(o)
    me.clear_geometry()
    bm = bmesh.new()
    bm.from_mesh(new)
    bm.to_mesh(me)
    bm.free()
    bpy.data.meshes.remove(new)
    return tris_of(me)


def engine_pos(x_m, y_m, z_m):
    return [round(x_m * CM + X0, 1), round(z_m * CM, 1), round(-y_m * CM + Z0, 1)]


# ------------------------------------------------------------------ collision slabs (engine Parts)
def collision_items():
    """MeshPart carries no collision in OVERDARE, so every walkable surface is a transparent Part.
    Written in Blender metres here and converted with the same transform as the meshes."""
    out = []

    def slab(name, cx, cy, cz_top, sx, sy, thick=0.5, yaw=0.0):
        out.append({"name": name,
                    "engine_pos": engine_pos(cx, cy, cz_top - thick / 2),
                    "size_cm": [round(sx * CM, 1), round(thick * CM, 1), round(sy * CM, 1)],
                    "yaw_deg": round(yaw, 2)})

    def wall(name, cx, cy, z0, z1, sx, sy):
        out.append({"name": name,
                    "engine_pos": engine_pos(cx, cy, (z0 + z1) / 2),
                    "size_cm": [round(sx * CM, 1), round((z1 - z0) * CM, 1), round(sy * CM, 1)],
                    "yaw_deg": 0.0})

    # ground floors
    slab("FLOOR_hall", 0, -14, 0.0, 32, 56)
    for s in (1, -1):
        slab("FLOOR_wing_%s" % ('R' if s > 0 else 'L'), s * 23, 11, 0.0, 14, 6)
    # gallery decks, rear landing, entrance balconies, stair-top bridge
    for s in (1, -1):
        tag = 'R' if s > 0 else 'L'
        slab("DECK_gallery_%s" % tag, s * 13.7, -15.2, 5.12, 4.6, 46.8)
        slab("DECK_balcony_%s" % tag, s * 9.7, -40.3, 5.12, 12.6, 3.4)
    slab("DECK_landing", 0, 11.1, 5.12, 23, 5.8)
    for i in range(5):
        a = math.radians(150 + 12 * i)
        slab("DECK_bridge_%d" % i, 4.5 * math.sin(a), 4 - 4.5 * math.cos(a), 5.12, 2.6, 1.4,
             yaw=math.degrees(a))
    # twin horseshoe stairs: one slab per tread, following the arc
    PHI0, PHI1, N, H = math.radians(30), math.radians(150), 30, 5.12
    for s in (1, -1):
        for i in range(N):
            phi = PHI0 + (PHI1 - PHI0) * (i + 0.5) / N
            r = 4.5
            slab("STAIR_%s_%02d" % ('R' if s > 0 else 'L', i),
                 s * r * math.sin(phi), 4 - r * math.cos(phi), (i + 1) * H / N, 2.4, 0.42, 0.34,
                 yaw=math.degrees(-s * phi))
    # perimeter walls (hall, forehall, wings) - portal doorways stay open
    wall("WALL_rear", 0, 14, 0, 12, 32, 0.45)
    wall("WALL_front", 0, -42, 0, 12, 32, 0.5)
    for s in (1, -1):
        tag = 'R' if s > 0 else 'L'
        wall("WALL_side_%s_a" % tag, s * 16, -25.9, 0, 12, 0.45, 32.2)   # y -42..-9.8
        wall("WALL_side_%s_b" % tag, s * 16, -0.9, 0, 12, 0.45, 17.8)    # y -9.8..8 (portal opens at 8..14)
        wall("WALL_wing_front_%s" % tag, s * 23, 8, 0, 6, 14, 0.3)
        wall("WALL_wing_outer_%s" % tag, s * 23, 14, 0, 6, 14, 0.3)
        wall("WALL_wing_end_%s" % tag, s * 30, 11, 0, 6, 0.3, 6)
    # fountain basin ring
    for k in range(8):
        a = 2 * math.pi * k / 8
        out.append({"name": "COL_fountain_%d" % k,
                    "engine_pos": engine_pos(2.2 * math.cos(a), 4 + 2.2 * math.sin(a), 0.35),
                    "size_cm": [180.0, 70.0, 60.0],
                    "yaw_deg": round(math.degrees(-a), 2)})
    return out


def run():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(TEX, exist_ok=True)
    sc = bpy.context.scene
    sc.frame_set(1)
    dg = bpy.context.evaluated_depsgraph_get()

    objs = []
    for o in sc.objects:
        if o.type not in {'MESH', 'CURVE'}:
            continue
        cn = o.users_collection[0].name if o.users_collection else ''
        if cn.startswith(SKIP_COLL) or o.hide_render:
            continue
        objs.append(o)

    users = collections.Counter(o.data.name for o in objs)
    masters, statics = {}, []
    for o in objs:
        if users[o.data.name] >= MASTER_MIN_USERS:
            masters.setdefault(o.data.name, []).append(o)
        else:
            statics.append(o)

    dump = {"schema": "kgp-v1/sgk-rules", "x0_cm": X0, "z0_cm": Z0, "container": "KGP_GrandPalace",
            "statics": [], "masters": {}, "instances": [], "collision": collision_items()}

    master_files = 0
    for key, insts in sorted(masters.items()):
        me = eval_mesh(insts[0], dg)
        if me is None:
            continue
        if tris_of(me) < MASTER_MIN_TRIS:
            statics.extend(insts)
            bpy.data.meshes.remove(me)
            continue
        src_mat = insts[0].data.materials[0] if getattr(insts[0].data, 'materials', None) and len(insts[0].data.materials) else None
        mat, rgb = flat_material(src_mat)
        mn, mx = bbox_of(me)
        centre = Vector(((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, (mn[2] + mx[2]) / 2))
        me.transform(Matrix.Translation(-centre))
        cap = 6000 if 'armchair' in key else (10000 if 'knight' in key else CAP)
        n = decimate_mesh(me, cap)
        uv_and_material(me, mat)
        stem = "%s_M_%s" % (PREFIX, ascii_name(key))
        export_mesh(me, "10_MASTERS", stem)
        dump["masters"][stem] = {"file": "10_MASTERS/%s.fbx" % stem, "tris": n, "colour": rgb,
                                 "size_cm": [round((mx[0] - mn[0]) * CM, 1), round((mx[2] - mn[2]) * CM, 1), round((mx[1] - mn[1]) * CM, 1)],
                                 "centre_offset_m": [round(v, 4) for v in centre]}
        for o in insts:
            wc = o.matrix_world @ centre
            dump["instances"].append({"master": stem, "name": ascii_name(o.name),
                                      "engine_pos": engine_pos(wc.x, wc.y, wc.z),
                                      "yaw_deg": round(math.degrees(o.matrix_world.to_euler('ZXY').z), 2),
                                      "scale": round(o.matrix_world.to_scale().x, 4)})
        bpy.data.meshes.remove(me)
        master_files += 1

    groups = collections.defaultdict(list)
    for o in statics:
        me = eval_mesh(o, dg)
        if me is None:
            continue
        me.transform(o.matrix_world)
        mats = getattr(o.data, 'materials', None)
        src_mat = mats[0] if mats and len(mats) else None
        zone = ascii_name((o.users_collection[0].name if o.users_collection else 'misc').split('|')[-1])[:18]
        groups[(zone, ascii_name(src_mat.name if src_mat else 'nomat'))].append((me, src_mat))

    static_files = 0

    def flush(chunk, zone, matname, src_mat, idx):
        if not chunk:
            return 0
        bm = bmesh.new()
        for m in chunk:
            bm.from_mesh(m)
        me = bpy.data.meshes.new("chunk")
        bm.to_mesh(me)
        bm.free()
        # Ornament scrollwork is curve geometry and very dense; half of it reads the same
        # in engine and keeps the whole map near the budget the other maps run at.
        n = decimate_mesh(me, min(CAP, max(2500, int(tris_of(me) * STATIC_RATIO))))
        mat, rgb = flat_material(src_mat)
        uv_and_material(me, mat)
        stem = "%s_S_%s_%s_%02d" % (PREFIX, zone, matname[:16], idx)
        export_mesh(me, "01_SHELL", stem)
        mn, mx = bbox_of(me)
        c = [(mn[i] + mx[i]) / 2 for i in range(3)]
        dump["statics"].append({"file": "01_SHELL/%s.fbx" % stem, "name": stem, "tris": n, "colour": rgb,
                                "engine_pos": engine_pos(c[0], c[1], c[2]),
                                "size_cm": [round((mx[0] - mn[0]) * CM, 1), round((mx[2] - mn[2]) * CM, 1), round((mx[1] - mn[1]) * CM, 1)]})
        bpy.data.meshes.remove(me)
        return 1

    for (zone, matname), entries in sorted(groups.items()):
        entries.sort(key=lambda e: (bbox_of(e[0])[0][1], bbox_of(e[0])[0][0]))
        src_mat = entries[0][1]
        chunk, acc, idx = [], 0, 0
        for me, _m in entries:
            t = tris_of(me)
            if acc + t > CAP and chunk:
                static_files += flush(chunk, zone, matname, src_mat, idx)
                idx += 1
                chunk, acc = [], 0
            chunk.append(me)
            acc += t
        static_files += flush(chunk, zone, matname, src_mat, idx)
        for me, _m in entries:
            bpy.data.meshes.remove(me)

    json.dump(dump, open(os.path.join(OUT, "scene_dump.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    total_tris = sum(s["tris"] for s in dump["statics"]) + sum(m["tris"] for m in dump["masters"].values())
    print("@@KGP masters=%d statics=%d instances=%d collision=%d unique_tris=%d"
          % (master_files, static_files, len(dump["instances"]), len(dump["collision"]), total_tris))


if __name__ == "__main__":
    run()
