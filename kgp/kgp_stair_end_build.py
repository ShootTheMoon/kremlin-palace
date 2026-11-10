# -*- coding: utf-8 -*-
r"""계단 두 팔 끝면(계단참 밑에서 보이는 흰 면) 마감 장식 — 만들기 · 내보내기 · 미리보기.

장식(면마다) : 사파이어 판 1.8 x 3.85 m (3cm) + 금 바깥테(6x5cm) + 금 안쪽 가는 테(2.5cm, 14cm 안)
              + 궁전 문과 같은 'Door gilt scroll' 소용돌이 위·아래 + 가운데 금 로제트.
재질별로 메시를 나눈다(사파이어 / 금) → 면 2개 x 2 = 메시 4개, 한 FBX. 텍스처는 넣지 않는다
(게임의 KGPTEX5 사파이어·금 TextureId 를 쓴다). 로컬 박스 UV (사파이어 3m, 금 2m 타일).

    blender.exe -b KGP_v3_textured.blend -P kgp_stair_end_build.py
출력 : ovdr_export\kgp_stair_end\KGP3E_stairend_00.fbx · place.json · preview_L.png · preview_R.png
"""
import bpy
import bmesh
import io
import json
import math
import os
import sys

from mathutils import Matrix, Vector

sys.path.append(r"C:\Work\blender")
import kgp_export_v3 as E          # noqa: E402
import kgp_v3_texture as T         # noqa: E402

OUT = r"C:\Work\blender\ovdr_export\kgp_stair_end"
M = json.load(io.open(os.path.join(OUT, "measure.json"), encoding="utf-8"))
R5 = r"C:\Work\blender\ovdr_export\kgp_v3\_test_r5"
STEM = "KGP3E_stairend_00"

PW, PZ0, PZ1 = 1.80, 0.35, 4.20          # 판 폭 / 아래 / 위 (m)
TILE = {"Sapphire stone": 3.0, "Antique gilded bronze": 2.0}


def box(bm, x0, x1, y0, y1, z0, z1):
    vs = [bm.verts.new(v) for v in [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                    (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        bm.faces.new([vs[i] for i in f])


def disk(bm, cx, cz, r, y0, y1, seg=24):
    b0 = [bm.verts.new((cx + r * math.cos(2 * math.pi * i / seg), y0, cz + r * math.sin(2 * math.pi * i / seg))) for i in range(seg)]
    b1 = [bm.verts.new((cx + r * math.cos(2 * math.pi * i / seg), y1, cz + r * math.sin(2 * math.pi * i / seg))) for i in range(seg)]
    bm.faces.new(b0)
    bm.faces.new(list(reversed(b1)))
    for i in range(seg):
        j = (i + 1) % seg
        bm.faces.new([b0[i], b0[j], b1[j], b1[i]])


def scroll_template():
    """'Door gilt scroll' 메시를 로컬 좌표로 : 가장 긴 축 -> x, 가장 얇은 축 -> y, 가운데 원점."""
    o = bpy.data.objects["Door gilt scroll"]
    dg = bpy.context.evaluated_depsgraph_get()
    me = E.eval_mesh(o, dg)
    co = [v.co.copy() for v in me.vertices]
    lo = Vector((min(c[i] for c in co) for i in range(3)))
    hi = Vector((max(c[i] for c in co) for i in range(3)))
    dim = hi - lo
    order = sorted(range(3), key=lambda i: -dim[i])          # 긴 축, 중간, 얇은 축
    cen = (lo + hi) / 2
    pts = [((c - cen)[order[0]], (c - cen)[order[2]], (c - cen)[order[1]]) for c in co]
    faces = [list(p.vertices) for p in me.polygons]
    w = dim[order[0]]
    bpy.data.meshes.remove(me)
    return pts, faces, w


def add_scroll(bm, tpl, cx, cz, width, y_back, flip=False, mirror=False):
    pts, faces, w = tpl
    s = width / w
    thick = max(abs(p[1]) for p in pts) * 2 * s
    vs = [bm.verts.new((cx + (-p[0] if mirror else p[0]) * s, y_back - thick / 2 + p[1] * s,
                        cz + (-p[2] if flip else p[2]) * s)) for p in pts]
    rev = flip != mirror
    for f in faces:
        try:
            bm.faces.new([vs[i] for i in (reversed(f) if rev else f)])
        except ValueError:
            pass


def build_side(arm, tpl):
    m = M[arm]
    fc = Vector(m["face_center"])
    n = Vector((m["normal"][0], m["normal"][1], 0))
    side = Vector((m["side"][0], m["side"][1], 0))
    s_mid = (m["flat_s_range"][0] + m["flat_s_range"][1]) / 2.0
    origin = Vector((fc.x, fc.y, 0.0)) + side * s_mid
    yaw = math.atan2(side.y, side.x)
    W = Matrix.Translation(origin) @ Matrix.Rotation(yaw, 4, 'Z')    # 로컬 X=면 가로, -Y=바깥

    sap = bmesh.new()
    box(sap, -PW / 2, PW / 2, -0.03, 0.0, PZ0, PZ1)

    gold = bmesh.new()
    t, d0, d1 = 0.06, -0.07, -0.02
    box(gold, -PW / 2 - t / 2, PW / 2 + t / 2, d0, d1, PZ1 - t / 2, PZ1 + t / 2)
    box(gold, -PW / 2 - t / 2, PW / 2 + t / 2, d0, d1, PZ0 - t / 2, PZ0 + t / 2)
    box(gold, -PW / 2 - t / 2, -PW / 2 + t / 2, d0, d1, PZ0 - t / 2, PZ1 + t / 2)
    box(gold, PW / 2 - t / 2, PW / 2 + t / 2, d0, d1, PZ0 - t / 2, PZ1 + t / 2)
    ins, tt, e0, e1 = 0.14, 0.025, -0.045, -0.03
    ix0, ix1, iz0, iz1 = -PW / 2 + ins, PW / 2 - ins, PZ0 + ins, PZ1 - ins
    box(gold, ix0, ix1, e0, e1, iz1 - tt, iz1)
    box(gold, ix0, ix1, e0, e1, iz0, iz0 + tt)
    box(gold, ix0, ix0 + tt, e0, e1, iz0, iz1)
    box(gold, ix1 - tt, ix1, e0, e1, iz0, iz1)
    # 정문처럼 좌우 대칭 한 쌍 (위·아래)
    for sx, mir in ((-0.25, False), (0.25, True)):
        add_scroll(gold, tpl, sx, iz1 - 0.28, 0.46, -0.03, mirror=mir)
        add_scroll(gold, tpl, sx, iz0 + 0.28, 0.46, -0.03, flip=True, mirror=mir)
    zc = (PZ0 + PZ1) / 2
    disk(gold, 0.0, zc, 0.13, -0.05, -0.03)
    disk(gold, 0.0, zc, 0.07, -0.075, -0.05)
    for a in range(8):
        ang = a * math.pi / 4
        disk(gold, 0.20 * math.cos(ang), zc + 0.20 * math.sin(ang), 0.035, -0.055, -0.03, seg=12)

    out = []
    for kind, bm, mat in (("sapphire", sap, "Sapphire stone"), ("gold", gold, "Antique gilded bronze")):
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        me = bpy.data.meshes.new("tmp")
        bm.to_mesh(me)
        bm.free()
        lo, hi = E.bbox_local(me)
        c = (lo + hi) / 2
        me.transform(Matrix.Translation(-c))
        T.box_uv_mesh(me, TILE[mat])
        me.materials.append(bpy.data.materials[mat])
        wc = W @ c
        dim = hi - lo
        out.append({"arm": arm, "kind": kind, "mat": mat, "me": me, "world": W @ Matrix.Translation(c),
                    "engine_pos": E.engine_pos(wc.x, wc.y, wc.z),
                    "yaw_deg": round(((math.degrees(yaw) + E.MESH_YAW_FIX) + 180.0) % 360.0 - 180.0, 2),
                    "size_cm": [round(dim.x * 100, 1), round(dim.z * 100, 1), round(dim.y * 100, 1)],
                    "native_half_cm": [round(dim.x * 50, 2), round(dim.z * 50, 2), round(dim.y * 50, 2)],
                    "tris": len(me.polygons)})
    return out


def preview(objs):
    # 새 r5 텍스처로 바꿔 끼워 게임과 같은 색으로 본다
    for mat, png in (("Sapphire stone", "KGPTEX3_Sapphire_stone.png"), ("Antique gilded bronze", "KGPTEX3_Antique_gilded_bronze.png"),
                     ("Ivory marble", "KGPTEX3_Ivory_marble.png"), ("Blue grey marble", "KGPTEX3_Blue_grey_marble.png")):
        m = bpy.data.materials.get(mat)
        if m and m.use_nodes:
            for nd in m.node_tree.nodes:
                if nd.type == 'TEX_IMAGE' and nd.image:
                    nd.image = bpy.data.images.load(os.path.join(R5, png), check_existing=True)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'FLAT'
    sc.display.shading.color_type = 'TEXTURE'
    sc.render.resolution_x, sc.render.resolution_y = 1280, 800
    cam = bpy.data.objects.new("PrevCam", bpy.data.cameras.new("PrevCam"))
    sc.collection.objects.link(cam)
    cam.data.lens = 18
    sc.camera = cam

    def eng2bl(x, y, z):
        return Vector(((x - 100650) / 100.0, -(z + 1400) / 100.0, y / 100.0))
    for tag, pos, tgt in (("user", (100480, 170, -2650), (100560, 200, -1800)),
                          ("close", (100650, 170, -2600), (100420, 230, -2230))):
        p, q = eng2bl(*pos), eng2bl(*tgt)
        cam.location = p
        cam.rotation_euler = (q - p).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(OUT, "preview_%s.png" % tag)
        bpy.ops.render.render(write_still=True)


def main():
    tpl = scroll_template()
    parts = build_side("L", tpl) + build_side("R", tpl)
    tmp = []
    for k, p in enumerate(parts):
        name = "KGP3EM%04d" % (k + 1)
        p["mesh"] = name
        p["me"].name = name
        ob = bpy.data.objects.new(name, p["me"])
        bpy.context.scene.collection.objects.link(ob)
        tmp.append(ob)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in tmp:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = tmp[0]
    kw = dict(E.FBX)
    kw.update(path_mode='STRIP', embed_textures=False)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, STEM + ".fbx"), **kw)
    rows = []
    for p in parts:
        rows.append({k: p[k] for k in ("arm", "kind", "mat", "mesh", "engine_pos", "yaw_deg", "size_cm", "native_half_cm", "tris")})
        rows[-1]["name"] = "KGP2_StairEnd_%s_%s" % (p["arm"], p["kind"])
    json.dump({"stem": STEM, "rows": rows}, io.open(os.path.join(OUT, "place.json"), "w", encoding="utf-8"), indent=1)
    for ob, p in zip(tmp, parts):
        ob.matrix_world = p["world"]              # 미리보기용 제자리
    preview(tmp)
    for r in rows:
        print("@@", r)
    print("@@DONE")


main()
