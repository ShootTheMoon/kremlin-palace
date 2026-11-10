# -*- coding: utf-8 -*-
r"""크렘린 대궁전 -> OVERDARE 익스포터 v2. 감축 없음.

v1 이 잃어버린 것 세 가지를 전부 되돌린다.
  1. UV 를 (0.5,0.5) 로 뭉개던 것 -> 아예 건드리지 않는다.
  2. 정적 청크 53% 감축 -> 감축 없음. 25,000 을 넘는 메시는 깎지 않고 쪼갠다.
  3. (컬렉션 x 재질) 로 1,518개를 176 청크로 합치던 것 -> 오브젝트 단위로 낸다.

2026-09-17 프로브로 확정한 것 (Studio 에서 직접 확인):
  * FBX 하나에 메시를 여러 개 담으면 메시마다 에셋이 하나씩 생긴다.
    에셋 이름 = "<파일이름>_<오브젝트이름>". 그래서 파일 수가 441 -> 40 남짓으로 준다.
  * 메시를 전부 원점에 겹쳐 놔도 상관없다. 피벗은 메시별로 제 bbox 중심이 된다.
  * engine size(cm) = (blender x, blender z, blender y) x 100.
    Studio 가 UnitExtent 를 size/2 (Z 만 음수) 로 되돌려준다 = size 가 곧 그려지는 크기다.
    축별로 늘리므로 비균등 스케일을 그대로 넘길 수 있다.

실행:
    blender -b Kremlin_Grand_Palace_COMPLETE.blend -P kgp_export_v2.py
"""
import bpy, bmesh, collections, hashlib, json, math, os, sys
from mathutils import Matrix, Vector

# ---------------------------------------------------------------- 설정
OUT = r"C:\Work\blender\ovdr_export\kgp_v2"
PREFIX = "KGP2"                  # 에셋 이름 접두. Studio 는 같은 이름을 새 에셋으로 안 받는다
CAP = 25000                      # 파일당 삼각형. 엔진 한도는 30,000 이라 5,000 을 남긴다
MAX_MESH_PER_FILE = 24           # ★ 엔진 한도는 200 이지만 그건 임포트가 아니라 파일 한도다.
                                 #   임포터는 메시 하나마다 에셋을 만들고(쿡·썸네일·zip) 그게 메모리를
                                 #   먹는다. 삼각형이나 MB 가 아니라 "한 번에 만드는 에셋 수"가 부하다.
                                 #   v1 은 파일=에셋 1개로 45개/묶음이 안전했다. 2026-09-17 에
                                 #   메시 93개짜리 묶음을 넣다가 Studio 가 커밋 부족으로 죽었다.
CM = 100.0
X0, Z0 = 100650.0, -1400.0       # 옛 크렘린 자리. v1 은 146000 으로 뽑아 배치 때 옮겼다
MESH_YAW_FIX = 180.0             # 임포터가 메시를 세로축 180도 돌려 넣는다
TEX_MAX = 512                    # 실제 텍스처가 있는 재질만. 4096 은 임포터를 죽인다

SKIP_COLL = ("30x", "34 |", "21 |", "43 |", "LIGHTING")

FBX = dict(axis_up='Y', axis_forward='-Z', apply_unit_scale=True,
           apply_scale_options='FBX_SCALE_NONE', use_selection=True,
           object_types={'MESH'}, use_mesh_modifiers=False, mesh_smooth_type='FACE',
           add_leaf_bones=False, bake_anim=False, use_triangles=True,
           use_custom_props=False)


def ascii_name(s):
    out = "".join(ch if (ch.isalnum() or ch in "_-") else "_" for ch in s)
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_")[:40] or "x"


def tris_of(me):
    me.calc_loop_triangles()
    return len(me.loop_triangles)


def srgb255(lin):
    def f(c):
        c = max(0.0, min(1.0, c))
        return c * 12.92 if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
    return [int(round(f(c) * 255)) for c in lin[:3]]


def engine_pos(x_m, y_m, z_m):
    """blender 월드 m -> 엔진 cm. X = x*100+X0, Y = z*100, Z = -y*100+Z0."""
    return [round(x_m * CM + X0, 1), round(z_m * CM, 1), round(-y_m * CM + Z0, 1)]


def base_colour(mat):
    if mat and mat.use_nodes:
        p = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if p:
            return srgb255(p.inputs['Base Color'].default_value)
    return [200, 200, 200]


def source_image(mat):
    """Base Color 뒤에 진짜 이미지가 있으면 돌려준다(생성 소품 2개뿐)."""
    if not (mat and mat.use_nodes):
        return None
    p = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not (p and p.inputs['Base Color'].is_linked):
        return None
    n, seen = p.inputs['Base Color'].links[0].from_node, 0
    while n and n.type != 'TEX_IMAGE' and seen < 6:
        inp = next((i for i in n.inputs if i.is_linked), None)
        n = inp.links[0].from_node if inp else None
        seen += 1
    return n.image if (n and n.type == 'TEX_IMAGE' and n.image) else None


# ---------------------------------------------------------------- 수집
def skipped(o):
    for c in o.users_collection:
        if c.name.startswith(SKIP_COLL):
            return True
    return False


def collect():
    objs = [o for o in bpy.data.objects
            if o.type == 'MESH' and not o.hide_render and not skipped(o) and o.visible_get()]
    objs.sort(key=lambda o: o.name)
    return objs


def eval_mesh(o, dg):
    """모디파이어를 적용한 로컬 좌표 메시. 레이어를 전부 살린다(v1 은 버렸다).

    ★ 여기서 삼각화까지 해 둔다. 안 하면 쪼갤 때 사각면을 1개로 세서 25,000 면 = 50,000
      삼각형이 되고 파일이 한도(30,000)를 넘는다. 2026-09-17 첫 실행에서 5개가 넘었다.
    """
    ev = o.evaluated_get(dg)
    try:
        me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
    except Exception:
        return None
    if not me.polygons:
        bpy.data.meshes.remove(me)
        return None
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    return me


# ---------------------------------------------------------------- 쪼개기
def split_faces(me, cap):
    """가장 긴 축의 중앙값으로 재귀 분할. 결정적이고 조각마다 bbox 가 좁다."""
    me.calc_loop_triangles()
    if len(me.loop_triangles) <= cap:
        return [None]
    cen = [tuple(round(v, 6) for v in p.center) for p in me.polygons]
    out, stack = [], [list(range(len(cen)))]
    while stack:
        grp = stack.pop()
        if len(grp) <= cap:
            out.append(grp)
            continue
        mn = [min(cen[i][k] for i in grp) for k in range(3)]
        mx = [max(cen[i][k] for i in grp) for k in range(3)]
        ax = max(range(3), key=lambda k: mx[k] - mn[k])
        o1, o2 = (ax + 1) % 3, (ax + 2) % 3
        grp.sort(key=lambda i: (cen[i][ax], cen[i][o1], cen[i][o2], i))
        half = len(grp) // 2
        stack.append(grp[:half])
        stack.append(grp[half:])
    out.sort(key=lambda g: (min(cen[i] for i in g), len(g)))
    return out


def piece_mesh(me, keep):
    """면 일부만 남긴 사본. 복사 후 삭제라 UV·레이어가 그대로 따라온다."""
    if keep is None:
        return me.copy()
    p = me.copy()
    bm = bmesh.new()
    bm.from_mesh(p)
    bm.faces.ensure_lookup_table()
    ks = set(keep)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in ks], context='FACES')
    bm.to_mesh(p)
    bm.free()
    return p


def bbox_local(me):
    xs = [v.co for v in me.vertices]
    mn = Vector((min(v.x for v in xs), min(v.y for v in xs), min(v.z for v in xs)))
    mx = Vector((max(v.x for v in xs), max(v.y for v in xs), max(v.z for v in xs)))
    return mn, mx


# ---------------------------------------------------------------- 실행
def run():
    os.makedirs(OUT, exist_ok=True)
    mesh_dir = os.path.join(OUT, "10_MESH")
    tex_dir = os.path.join(OUT, "_tex")
    os.makedirs(mesh_dir, exist_ok=True)
    os.makedirs(tex_dir, exist_ok=True)

    dg = bpy.context.evaluated_depsgraph_get()
    objs = collect()
    print("@@ objects", len(objs))

    # --- 검사 : 전부 yaw 뿐인지, 뒤집힌 것이 없는지
    bad_rot, bad_det = [], []
    for o in objs:
        e = o.matrix_world.to_euler('ZXY')
        if abs(e.x) > 1e-3 or abs(e.y) > 1e-3:
            bad_rot.append((o.name, round(math.degrees(e.x), 2), round(math.degrees(e.y), 2)))
        if o.matrix_world.to_3x3().determinant() <= 0:
            bad_det.append(o.name)
    if bad_rot:
        print("@@ !! yaw 가 아닌 회전:", bad_rot[:10], "총", len(bad_rot))
    if bad_det:
        print("@@ !! 뒤집힌 스케일:", bad_det[:10], "총", len(bad_det))

    # --- 데이터블록 x 재질 -> 조각. 모디파이어가 붙은 것은 따로 센다
    prepared = {}          # key -> {"pieces":[mesh], "mat":mat}
    obj_key = {}           # object -> (key, n_pieces)
    for o in objs:
        mods = [m for m in o.modifiers if m.show_viewport]
        key_base = ("MOD::" + o.name) if mods else o.data.name
        mats = [m for m in o.data.materials if m] or [None]
        for slot, mat in enumerate(mats):
            key = (key_base, mat.name if mat else "nomat", slot)
            if key in prepared:
                continue
            me = eval_mesh(o, dg)
            if me is None:
                print("@@ !! 폴리곤 없음, 건너뜀:", o.name)
                continue
            if len(mats) > 1:      # 재질 슬롯별로 면을 가른다
                keep = [i for i, p in enumerate(me.polygons) if p.material_index == slot]
                if not keep:
                    bpy.data.meshes.remove(me)
                    continue
                cut = piece_mesh(me, keep)
                bpy.data.meshes.remove(me)
                me = cut
            groups = split_faces(me, CAP)
            pieces = [piece_mesh(me, g) for g in groups]
            if not (len(groups) == 1 and groups[0] is None):
                bpy.data.meshes.remove(me)
            prepared[key] = {"pieces": pieces, "mat": mat}
        obj_key[o.name] = [( (key_base, (m.name if m else "nomat"), s) )
                           for s, m in enumerate(mats)]

    # --- 조각을 제 bbox 중심으로 옮기고 크기를 기록
    info = {}
    for key, rec in prepared.items():
        rec["dims"] = []
        for p in rec["pieces"]:
            mn, mx = bbox_local(p)
            c = (mn + mx) / 2.0
            p.transform(Matrix.Translation(-c))
            rec["dims"].append({"centre": [c.x, c.y, c.z],
                                "dim": [mx.x - mn.x, mx.y - mn.y, mx.z - mn.z],
                                "tris": tris_of(p)})
        info[key] = rec

    total_unique = sum(d["tris"] for r in info.values() for d in r["dims"])
    print("@@ unique pieces", sum(len(r["pieces"]) for r in info.values()),
          "unique tris", total_unique)

    # --- 재질별로 파일에 담는다 (한 파일 = 한 재질, 메시 여러 개)
    bymat = collections.defaultdict(list)
    for key, rec in info.items():
        for i in range(len(rec["pieces"])):
            bymat[rec["mat"].name if rec["mat"] else "nomat"].append((key, i))

    # 텍스처 : 실제 이미지가 있는 재질만 뽑는다
    tex_of = {}
    for mname in bymat:
        mat = next((info[k]["mat"] for k, _ in bymat[mname] if info[k]["mat"]), None)
        img = source_image(mat) if mat else None
        if img:
            cp = img.copy()
            w, h = cp.size
            if max(w, h) > TEX_MAX:
                s = float(TEX_MAX) / max(w, h)
                cp.scale(max(1, int(w * s)), max(1, int(h * s)))
            tp = os.path.join(tex_dir, "KGPTEX_" + ascii_name(mname)[:24] + ".png")
            cp.filepath_raw = tp
            cp.file_format = 'PNG'
            cp.save()
            tex_of[mname] = tp

    mesh_id = {}            # (key, piece) -> 메시 오브젝트 이름 (에셋 이름의 꼬리)
    files = []
    n = 0
    for mname in sorted(bymat):
        bucket, acc, idx = [], 0, 0
        entries = sorted(bymat[mname], key=lambda kp: (kp[0][0], kp[0][2], kp[1]))

        def flush(bucket, idx):
            if not bucket:
                return
            stem = "%s_%s_%02d" % (PREFIX, ascii_name(mname)[:18], idx)
            tmp = []
            for (key, pi) in bucket:
                me = info[key]["pieces"][pi].copy()
                nm = mesh_id[(key, pi)]
                ob = bpy.data.objects.new(nm, me)
                ob.data.name = nm
                bpy.context.scene.collection.objects.link(ob)
                tmp.append(ob)
            bpy.ops.object.select_all(action='DESELECT')
            for ob in tmp:
                ob.select_set(True)
            bpy.context.view_layer.objects.active = tmp[0]
            kw = dict(FBX)
            if mname in tex_of:
                kw.update(path_mode='COPY', embed_textures=True)
            else:
                kw.update(path_mode='STRIP', embed_textures=False)
            path = os.path.join(mesh_dir, stem + ".fbx")
            bpy.ops.export_scene.fbx(filepath=path, **kw)
            files.append({"file": stem + ".fbx", "stem": stem, "mat": mname,
                          "meshes": [mesh_id[k] for k in bucket],
                          "tris": sum(info[k]["dims"][p]["tris"] for k, p in bucket)})
            for ob in tmp:
                me = ob.data
                bpy.data.objects.remove(ob, do_unlink=True)
                bpy.data.meshes.remove(me)

        for (key, pi) in entries:
            t = info[key]["dims"][pi]["tris"]
            if bucket and (acc + t > CAP or len(bucket) >= MAX_MESH_PER_FILE):
                flush(bucket, idx)
                idx += 1
                bucket, acc = [], 0
            n += 1
            mesh_id[(key, pi)] = "%sM%04d" % (PREFIX, n)
            bucket.append((key, pi))
            acc += t
        flush(bucket, idx)

    print("@@ files", len(files))

    # --- 배치표
    inst = []
    for o in objs:
        M = o.matrix_world
        s = M.to_scale()
        yaw = math.degrees(M.to_euler('ZXY').z)
        for key in obj_key.get(o.name, []):
            rec = info.get(key)
            if not rec:
                continue
            for pi, dim in enumerate(rec["dims"]):
                c = Vector(dim["centre"])
                wc = M @ c
                size = [max(1.0, round(dim["dim"][0] * abs(s.x) * CM, 1)),
                        max(1.0, round(dim["dim"][2] * abs(s.z) * CM, 1)),
                        max(1.0, round(dim["dim"][1] * abs(s.y) * CM, 1))]
                inst.append({
                    "name": ascii_name(o.name) + ("_p%d" % pi if len(rec["dims"]) > 1 else ""),
                    "obj": o.name,
                    "coll": (o.users_collection[0].name if o.users_collection else ""),
                    "mesh": mesh_id[(key, pi)],
                    "mat": key[1],
                    "engine_pos": engine_pos(wc.x, wc.y, wc.z),
                    "yaw_deg": round(((yaw + MESH_YAW_FIX) + 180.0) % 360.0 - 180.0, 2),
                    "size_cm": size,
                    "colour": base_colour(rec["mat"]),
                    "tris": dim["tris"]})

    world_tris = sum(i["tris"] for i in inst)
    dump = {"schema": "kgp-v2", "x0_cm": X0, "z0_cm": Z0, "container": "KGP_GrandPalace",
            "files": files, "instances": inst,
            "textures": {k: os.path.basename(v) for k, v in tex_of.items()},
            "unique_tris": total_unique, "world_tris": world_tris}
    with open(os.path.join(OUT, "scene_v2.json"), "w", encoding="utf-8") as f:
        json.dump(dump, f, ensure_ascii=False, indent=1)

    xs = [i["engine_pos"][0] for i in inst]
    ys = [i["engine_pos"][1] for i in inst]
    zs = [i["engine_pos"][2] for i in inst]
    print("@@ instances %d  world_tris %d" % (len(inst), world_tris))
    print("@@ centre range X %.0f..%.0f  Y %.0f..%.0f  Z %.0f..%.0f"
          % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
    over = [f for f in files if f["tris"] > 30000]
    print("@@ files over 30k tris:", len(over))
    print("@@ textures:", list(tex_of.keys()))
    print("@@DONE")


if __name__ == "__main__":
    run()
