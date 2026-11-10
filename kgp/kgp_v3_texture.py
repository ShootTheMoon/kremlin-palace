# -*- coding: utf-8 -*-
"""
KGP v3 — 재질에 실제 표면 무늬를 넣고, 타일 텍스처로 구워서, UV 를 깔아준다.

왜 필요한가
-----------
v2 는 22개 재질 중 19개가 블렌더에서도 '단색'이었다. 금장(오브젝트 850개)은 노이즈가
Roughness 에만 물려 있어서 EEVEE 에서만 금으로 보였고, 반사가 없는 게임 엔진에서는
그냥 베이지 덩어리가 됐다. 그래서 순서가 이렇다 :

  1) apply_recipes()  — Base Color 에 진짜 무늬를 그려 넣는다(에이전트가 설계한 노드 트리)
  2) bake_tiles()     — 재질마다 타일 한 장을 굽는다(DIFFUSE/COLOR, 조명 없음)
  3) box_uv_all()     — 메시마다 로컬 박스 투영으로 UV 를 깐다(재질별 타일 크기 m)
  4) relink_baked()   — 구운 이미지를 Base Color 에 물린다(익스포터가 이걸 찾아간다)

메시 데이터블록이 1,518 오브젝트에 430개뿐이라 UV 는 '로컬' 좌표로 깐다. 월드로 깔면
공유 데이터블록 하나에 서로 다른 UV 가 필요해져서 메시가 1,518개로 불어난다.
"""

import bpy
import bmesh
import os
import json
import math

OUT_TEX = r"C:\Work\blender\ovdr_export\kgp_v3\_tex"
SKIP_COLL = ("30x", "34 |", "21 |", "43 |", "LIGHTING")

# ★ 이미 제대로 된 UV 와 컬러맵을 가진 재질. 굽지도 말고 UV 도 건드리지 말 것.
#   생성 소품(기사상·로코코 의자) 2종이다. 박스 투영을 씌우면 캐릭터 UV 가 날아가고,
#   평면에 구우면 원본 2048 텍스처가 타일 한 장으로 뭉개진다.
def keep_as_is(mat_name):
    return mat_name.startswith("tripo_material_")



# ---------------------------------------------------------------- 공통
def exported_objects():
    out = []
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or not ob.visible_get():
            continue
        if any(any(s in c.name for s in SKIP_COLL) for c in ob.users_collection):
            continue
        out.append(ob)
    return out


def exported_materials():
    mats = {}
    for ob in exported_objects():
        for sl in ob.material_slots:
            if sl.material:
                mats.setdefault(sl.material.name, 0)
                mats[sl.material.name] += 1
    return mats


# ---------------------------------------------------------------- 1) 레시피 적용
def apply_recipes(recipes):
    """recipes: [{name, code, tile_metres, texture_px}, ...]"""
    done, failed = [], []
    for r in recipes:
        mat = bpy.data.materials.get(r["name"])
        if mat is None:
            failed.append((r["name"], "material not found"))
            continue
        try:
            ns = {"bpy": bpy, "mat": mat, "math": math}
            exec(r["code"], ns, ns)
            done.append(r["name"])
        except Exception as e:                       # noqa: BLE001
            failed.append((r["name"], "%s: %s" % (type(e).__name__, e)))
    return {"applied": done, "failed": failed}


# ---------------------------------------------------------------- 2) 타일 굽기
def _bake_scene():
    sc = bpy.data.scenes.get("KGP_BAKE") or bpy.data.scenes.new("KGP_BAKE")
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 1
    sc.cycles.use_denoising = False
    sc.render.bake.use_pass_direct = False
    sc.render.bake.use_pass_indirect = False
    sc.render.bake.use_pass_color = True
    sc.render.bake.margin = 16
    sc.render.bake.use_clear = True
    return sc


def bake_tiles(specs, out_dir=OUT_TEX):
    """specs: [{name, texture_px}, ...] -> {mat: png path}

    재질마다 평면 하나를 만들어 UV 0..1 로 펴고 DIFFUSE/COLOR 를 굽는다.
    레시피가 Generated/Object 좌표를 쓰므로 평면의 0..1 이 곧 타일 한 장이다.
    """
    os.makedirs(out_dir, exist_ok=True)
    prev = bpy.context.window.scene
    sc = _bake_scene()
    bpy.context.window.scene = sc

    made = {}
    errors = []
    for spec in specs:
        name = spec["name"]
        px = int(spec.get("texture_px") or 512)
        if keep_as_is(name):
            continue
        mat = bpy.data.materials.get(name)
        if mat is None or not mat.use_nodes:
            errors.append((name, "no material / no nodes"))
            continue

        safe = "".join(ch if (ch.isalnum() or ch in "._-") else "_" for ch in name)[:48]
        img_name = "KGPTEX3_" + safe
        img = bpy.data.images.get(img_name)
        if img and (img.size[0] != px or img.size[1] != px):
            bpy.data.images.remove(img)
            img = None
        if img is None:
            img = bpy.data.images.new(img_name, px, px, alpha=False, float_buffer=False)
        img.colorspace_settings.name = 'sRGB'

        me = bpy.data.meshes.new("KGP_BAKE_PLANE")
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
        bm.to_mesh(me)
        bm.free()
        me.uv_layers.new(name="UVMap")
        # 평면 하나짜리라 UV 를 손으로 0..1 로 박는다
        uv = me.uv_layers[0]
        corner = {(-0.5, -0.5): (0.0, 0.0), (0.5, -0.5): (1.0, 0.0),
                  (0.5, 0.5): (1.0, 1.0), (-0.5, 0.5): (0.0, 1.0)}
        for loop in me.loops:
            v = me.vertices[loop.vertex_index].co
            key = (round(v.x, 3), round(v.y, 3))
            uv.data[loop.index].uv = corner.get(key, (0.0, 0.0))

        ob = bpy.data.objects.new("KGP_BAKE_OBJ", me)
        sc.collection.objects.link(ob)
        ob.data.materials.append(mat)

        nt = mat.node_tree
        tgt = nt.nodes.new("ShaderNodeTexImage")
        tgt.image = img
        tgt.select = True
        nt.nodes.active = tgt

        for o in sc.collection.objects:
            o.select_set(False)
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob

        try:
            bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'},
                                use_clear=True, margin=16)
            path = os.path.join(out_dir, img_name + ".png")
            img.filepath_raw = path
            img.file_format = 'PNG'
            img.save()
            made[name] = path
        except Exception as e:                       # noqa: BLE001
            errors.append((name, "%s: %s" % (type(e).__name__, e)))
        finally:
            nt.nodes.remove(tgt)
            bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.meshes.remove(me)

    bpy.context.window.scene = prev
    return {"baked": made, "errors": errors}


# ---------------------------------------------------------------- 3) UV 박스 투영
def box_uv_mesh(me, tile_m):
    """로컬 좌표 박스 투영. 면 법선의 우세축을 골라 나머지 두 축을 UV 로 쓴다."""
    if tile_m <= 0:
        tile_m = 1.0
    inv = 1.0 / tile_m
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    me.uv_layers.active = uv
    data = uv.data
    for poly in me.polygons:
        n = poly.normal
        ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if az >= ax and az >= ay:            # 바닥/천장
                u, v = co.x, co.y
            elif ax >= ay:                        # 좌우 벽
                u, v = co.y, co.z
            else:                                 # 앞뒤 벽
                u, v = co.x, co.z
            data[li].uv = (u * inv, v * inv)
    return len(me.polygons)


def box_uv_all(tile_by_mat, default_tile=2.0):
    """메시 데이터블록마다 한 번씩. 타일 크기는 그 메시의 첫 재질을 따른다."""
    seen, kept = {}, set()
    for ob in exported_objects():
        me = ob.data
        if me.name in seen or me.name in kept:
            continue
        mnames = [sl.material.name for sl in ob.material_slots if sl.material]
        if any(keep_as_is(m) for m in mnames):
            kept.add(me.name)
            continue
        mname = mnames[0] if mnames else None
        tile = tile_by_mat.get(mname, default_tile)
        seen[me.name] = box_uv_mesh(me, tile)
    return {"meshes": len(seen), "faces": sum(seen.values()), "kept_own_uv": len(kept)}


# ---------------------------------------------------------------- 4) 구운 걸 다시 물리기
def relink_baked(baked):
    """구운 이미지를 Base Color 로. 익스포터의 source_image() 가 이걸 찾아간다."""
    out = []
    for name, path in baked.items():
        mat = bpy.data.materials.get(name)
        if mat is None:
            continue
        img = None
        for i in bpy.data.images:
            if i.filepath_raw == path or i.name == os.path.splitext(os.path.basename(path))[0]:
                img = i
                break
        if img is None:
            img = bpy.data.images.load(path)
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out_node = nt.nodes.new("ShaderNodeOutputMaterial")
        out_node.location = (400, 0)
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (120, 0)
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        tex.location = (-220, 0)
        uvm = nt.nodes.new("ShaderNodeUVMap")
        uvm.uv_map = "UVMap"
        uvm.location = (-460, 0)
        nt.links.new(uvm.outputs["UV"], tex.inputs["Vector"])
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        nt.links.new(bsdf.outputs["BSDF"], out_node.inputs["Surface"])
        bsdf.inputs["Metallic"].default_value = 0.0
        bsdf.inputs["Roughness"].default_value = 0.5
        out.append(name)
    return out
