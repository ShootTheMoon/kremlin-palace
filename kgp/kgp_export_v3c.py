# -*- coding: utf-8 -*-
r"""크렘린 대궁전 — v3 가 빠뜨린 것들을 추가로 낸다 (v3c).

빠진 이유 (2026-09-19 실측)
  v2/v3 익스포터의 collect() 가 type == 'MESH' 만 모았다. 궁전 장식의 상당수가 커브로
  만들어져 있어서 511개가 통째로 빠졌다 — 2층 측면 갤러리 난간, 벽 패널·파사드·돔 금장
  소용돌이, 샹들리에 팔·체인·크리스털 줄, 기사 복도 격자, 티 테이블 금장 상감, 문짝 금장
  소용돌이 100개 등. 고유 삼각형 1,363,604.
  분수 물줄기의 물방울 392개는 지오메트리 노드 인스턴스라 new_from_object 에 안 잡혔다.

이 스크립트가 내는 것
  1) 커브(CURVE/FONT/SURFACE/META) 511개 — 평가된 메시로 바꿔, 재질 타일 크기로 박스 UV
  2) 물방울 392개를 물줄기 오브젝트의 로컬 공간에 합친 메시 1개 (→ KGP2_WATER_drops)
  3) 베리·토피어리 — 텍스처를 다시 구웠으므로 새 에셋으로 (메시는 같음)

규칙 (v3 와 같음 + 이번 수정)
  * 조각을 자를 때마다 '안 쓰이는 정점'을 지운다 — 엔진은 삼각형이 쓰는 정점만으로 크기를 잰다.
  * 커브 511개는 전부 yaw 만 돌아 있고 음수·비균등 스케일이 없다(실측) → v3 배치 규칙 그대로.
  * 문짝 위에 붙은 소용돌이는 이름을 KGP2_Door_leaf_scroll_* 로, Movable 로 낸다 → 문 스크립트가 같이 돌린다.

    blender.exe -b KGP_v3_textured.blend -P kgp_export_v3c.py
"""
import bpy
import bmesh
import collections
import io
import json
import math
import os
import sys
from mathutils import Matrix, Vector

sys.path.append(r"C:\Work\blender")
import kgp_export_v3 as E          # noqa: E402
import kgp_v3_texture as T         # noqa: E402

OUT = r"C:\Work\blender\ovdr_export\kgp_v3c"
PREFIX = "KGP3C"
CAP = 25000
MAX_MESH_PER_FILE = 24
RECIPES = r"C:\Work\blender\ovdr_export\kgp_v3\recipes_r2.json"
TILE = {r["name"]: float(r["tile_metres"]) for r in json.load(io.open(RECIPES, encoding="utf-8"))}
STREAMS = "P7 fountain water streams (GN)"
RETEX = ("P3 berry red", "P3 topiary green")

# 문짝(안쪽 통로 문) — kgp_v3 배치 기준 엔진 좌표
LEAF_X = (102267.9, 99032.1)
LEAF_Z = (-2640.0, -2300.0)
LEAF_Y = (0.0, 440.0)


def exportable(o):
    if o.hide_render or not o.visible_get():
        return False
    return not any(any(s in c.name for s in E.SKIP_COLL) for c in o.users_collection)


def clean(me, keep=None):
    """keep 면만 남긴 사본. 안 쓰이는 정점까지 지운다."""
    p = me.copy()
    bm = bmesh.new()
    bm.from_mesh(p)
    bm.faces.ensure_lookup_table()
    if keep is not None:
        ks = set(keep)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in ks], context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(p)
    bm.free()
    return p


def droplet_mesh(dg):
    st = bpy.data.objects[STREAMS]
    inv = st.matrix_world.inverted()
    verts, faces = [], []
    mat = None
    n = 0
    for inst in dg.object_instances:
        if not (inst.is_instance and inst.parent and inst.parent.original == st):
            continue
        src = inst.object.data
        m = inv @ inst.matrix_world
        base = len(verts)
        verts.extend(tuple(m @ v.co) for v in src.vertices)
        faces.extend(tuple(base + i for i in poly.vertices) for poly in src.polygons)
        if mat is None and src.materials:
            mat = src.materials[0]
        n += 1
    me = bpy.data.meshes.new("KGP_drops")
    me.from_pydata(verts, [], faces)
    me.update()
    if mat:
        me.materials.append(mat)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    return me, n, st


def main():
    os.makedirs(os.path.join(OUT, "10_MESH"), exist_ok=True)
    tex_dir = os.path.join(OUT, "_tex")
    os.makedirs(tex_dir, exist_ok=True)
    for f in os.listdir(os.path.join(OUT, "10_MESH")):
        os.remove(os.path.join(OUT, "10_MESH", f))

    dg = bpy.context.evaluated_depsgraph_get()
    curves = sorted([o for o in bpy.data.objects
                     if o.type in ('CURVE', 'FONT', 'SURFACE', 'META') and exportable(o)],
                    key=lambda o: o.name)
    retex = sorted([o for o in E.collect()
                    if any(sl.material and sl.material.name in RETEX for sl in o.material_slots)],
                   key=lambda o: o.name)
    print("@@ curves", len(curves), "retex objects", len(retex))

    # ---- (source object, key base) 목록. 커브는 데이터 이름으로 묶는다(40개 공유 2종)
    work = [(o, "CURVE::" + o.data.name) for o in curves] + [(o, "RETEX::" + o.data.name) for o in retex]

    prepared = {}
    obj_keys = collections.defaultdict(list)
    for o, kb in work:
        me0 = None
        mats = [sl.material for sl in o.material_slots] or [None]
        for slot, mat in enumerate(mats):
            key = (kb, mat.name if mat else "nomat", slot)
            obj_keys[o.name].append(key)
            if key in prepared:
                continue
            if me0 is None:
                me0 = E.eval_mesh(o, dg)
                if me0 is None:
                    print("@@ !! 폴리곤 없음:", o.name)
                    break
            keep = [i for i, p in enumerate(me0.polygons) if p.material_index == slot] if len(mats) > 1 else None
            if keep == []:
                continue
            base = clean(me0, keep)
            if kb.startswith("CURVE::"):
                T.box_uv_mesh(base, TILE.get(mat.name if mat else "", 2.0))
            groups = E.split_faces(base, CAP)
            if len(groups) == 1 and groups[0] is None:
                pieces = [base]
            else:
                pieces = [clean(base, g) for g in groups]
                bpy.data.meshes.remove(base)
            prepared[key] = {"pieces": pieces, "mat": mat}
        if me0 is not None:
            bpy.data.meshes.remove(me0)

    # ---- 물방울
    dme, ndrops, st = droplet_mesh(dg)
    dmat = dme.materials[0] if dme.materials else None
    dkey = ("GN::drops", dmat.name if dmat else "nomat", 0)
    groups = E.split_faces(dme, CAP)
    prepared[dkey] = {"pieces": [dme] if (len(groups) == 1 and groups[0] is None)
                      else [clean(dme, g) for g in groups], "mat": dmat}
    obj_keys[STREAMS + "::drops"].append(dkey)
    print("@@ droplets", ndrops, "tris", E.tris_of(dme), "pieces", len(prepared[dkey]["pieces"]))

    # ---- 조각을 제 bbox 중심으로
    for rec in prepared.values():
        rec["dims"] = []
        for p in rec["pieces"]:
            used = set()
            for poly in p.polygons:
                used.update(poly.vertices)
            assert len(used) == len(p.vertices), "loose verts left"
            mn, mx = E.bbox_local(p)
            c = (mn + mx) / 2.0
            p.transform(Matrix.Translation(-c))
            rec["dims"].append({"centre": [c.x, c.y, c.z], "dim": [mx.x - mn.x, mx.y - mn.y, mx.z - mn.z],
                                "tris": E.tris_of(p)})

    # ---- 텍스처 : 구운 이미지가 물린 재질
    bymat = collections.defaultdict(list)
    for key, rec in prepared.items():
        for i in range(len(rec["pieces"])):
            bymat[rec["mat"].name if rec["mat"] else "nomat"].append((key, i))
    tex_of = {}
    for mname in bymat:
        mat = next((prepared[k]["mat"] for k, _ in bymat[mname] if prepared[k]["mat"]), None)
        img = E.source_image(mat) if mat else None
        if img:
            if mname in RETEX:
                # 같은 이름이면 Studio 가 새 에셋으로 안 받을 수 있다 → 이름을 새로 한다
                import shutil
                src = bpy.path.abspath(img.filepath_raw)
                safe = "".join(ch if (ch.isalnum() or ch in "._-") else "_" for ch in mname)[:48]
                dst = os.path.join(tex_dir, "KGPTEX3B_" + safe + ".png")
                shutil.copyfile(src, dst)
                img.name = "KGPTEX3B_" + safe
                img.filepath_raw = dst
                img.reload()
            tex_of[mname] = img.filepath_raw or img.name
    EMBED = {m for m in tex_of if m in RETEX}   # 나머지는 v3 때 올라간 텍스처를 그대로 쓴다

    # ---- 파일 (한 파일 = 한 재질, ≤25,000 삼각형, ≤24 메시)
    mesh_id, files, n = {}, [], 0
    for mname in sorted(bymat):
        entries = sorted(bymat[mname], key=lambda kp: (kp[0][0], kp[0][2], kp[1]))
        bucket, acc, idx = [], 0, 0

        def flush(bucket, idx):
            if not bucket:
                return
            stem = "%s_%s_%02d" % (PREFIX, E.ascii_name(mname)[:18], idx)
            tmp = []
            for (key, pi) in bucket:
                me = prepared[key]["pieces"][pi].copy()
                nm = mesh_id[(key, pi)]
                ob = bpy.data.objects.new(nm, me)
                ob.data.name = nm
                bpy.context.scene.collection.objects.link(ob)
                tmp.append(ob)
            bpy.ops.object.select_all(action='DESELECT')
            for ob in tmp:
                ob.select_set(True)
            bpy.context.view_layer.objects.active = tmp[0]
            kw = dict(E.FBX)
            if mname in EMBED:
                kw.update(path_mode='COPY', embed_textures=True)
            else:
                kw.update(path_mode='STRIP', embed_textures=False)
            bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, "10_MESH", stem + ".fbx"), **kw)
            files.append({"file": stem + ".fbx", "stem": stem, "mat": mname,
                          "meshes": [mesh_id[k] for k in bucket],
                          "tris": sum(prepared[k]["dims"][p]["tris"] for k, p in bucket)})
            for ob in tmp:
                me = ob.data
                bpy.data.objects.remove(ob, do_unlink=True)
                bpy.data.meshes.remove(me)

        for (key, pi) in entries:
            t = prepared[key]["dims"][pi]["tris"]
            if bucket and (acc + t > CAP or len(bucket) >= MAX_MESH_PER_FILE):
                flush(bucket, idx)
                idx += 1
                bucket, acc = [], 0
            n += 1
            mesh_id[(key, pi)] = "%sM%04d" % (PREFIX, n)
            bucket.append((key, pi))
            acc += t
        flush(bucket, idx)

    # ---- 배치표
    inst, seen = [], collections.Counter()
    srcs = [(o, o.name, o.matrix_world) for o, _ in work] + [(st, STREAMS + "::drops", st.matrix_world)]
    for o, oname, M in srcs:
        s = M.to_scale()
        yaw = math.degrees(M.to_euler('ZXY').z)
        for key in obj_keys.get(oname, []):
            rec = prepared.get(key)
            if not rec:
                continue
            multi = len(rec["dims"]) > 1
            for pi, dim in enumerate(rec["dims"]):
                wc = M @ Vector(dim["centre"])
                pos = E.engine_pos(wc.x, wc.y, wc.z)
                size = [max(1.0, round(dim["dim"][0] * abs(s.x) * E.CM, 1)),
                        max(1.0, round(dim["dim"][2] * abs(s.z) * E.CM, 1)),
                        max(1.0, round(dim["dim"][1] * abs(s.y) * E.CM, 1))]
                role = "static"
                if key[0] == "GN::drops":
                    name = "KGP2_WATER_drops" + ("_p%d" % pi if multi else "")
                    role = "water"
                else:
                    base = E.ascii_name(o.name)
                    name = "KGP2_" + base + ("_p%d" % pi if multi else "")
                    if o.name.startswith("Door gilt scroll") or o.name.startswith("Door handle stem"):
                        on_leaf = (any(abs(pos[0] - x) <= 20 for x in LEAF_X)
                                   and LEAF_Z[0] <= pos[2] <= LEAF_Z[1] and LEAF_Y[0] <= pos[1] <= LEAF_Y[1])
                        if on_leaf:
                            if o.name.startswith("Door handle stem"):
                                name = "KGP2_Door_leaf_stem_" + base.replace("Door_handle_stem", "").strip("_")
                            else:
                                name = "KGP2_Door_leaf_scroll_" + base.replace("Door_gilt_scroll", "").strip("_")
                            role = "door_leaf"
                    if key[0].startswith("RETEX::"):
                        role = "retex"
                seen[name] += 1
                if seen[name] > 1:
                    name = "%s_%02d" % (name, seen[name])
                inst.append({"name": name, "obj": o.name, "role": role, "mesh": mesh_id[(key, pi)],
                             "mat": key[1], "engine_pos": pos,
                             "yaw_deg": round(((yaw + E.MESH_YAW_FIX) + 180.0) % 360.0 - 180.0, 2),
                             "size_cm": size, "tris": dim["tris"],
                             "native_half_cm": [round(dim["dim"][0] * 50, 2), round(dim["dim"][2] * 50, 2),
                                                round(dim["dim"][1] * 50, 2)]})

    world = sum(i["tris"] for i in inst)
    uniq = sum(d["tris"] for r in prepared.values() for d in r["dims"])
    json.dump({"schema": "kgp-v3c", "files": files, "instances": inst,
               "textures": {k: os.path.basename(v) for k, v in tex_of.items()},
               "unique_tris": uniq, "world_tris": world},
              io.open(os.path.join(OUT, "scene_v3c.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    roles = collections.Counter(i["role"] for i in inst)
    print("@@ files", len(files), "meshes", len(mesh_id), "instances", len(inst), "roles", dict(roles))
    print("@@ unique tris", uniq, "world tris", world, "files over 30k", sum(1 for f in files if f["tris"] > 30000))
    print("@@ textures", sorted(tex_of), "embedded", sorted(EMBED))
    print("@@DONE")


main()
