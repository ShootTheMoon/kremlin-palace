# -*- coding: utf-8 -*-
r"""크렘린 대궁전 — 팀룸 벽 배열이 홀 한가운데로 넘쳐 생긴 '떠 있는 판'을 뺀 메시 4개를 다시 낸다.

원인 (2026-09-20 kgp_float_scan2 실측)
  P3 corridor L/R inner sapphire panels : 팀룸 패널 배열 끝에 160x340cm 판이 홀 가운데
      (엔진 X 100570~100730, Z -2218, Y 100~440) 로 넘쳐 나왔다. L·R 각 4겹 = 8겹이 한 자리에 겹쳐 떠 있다.
  P3 corridor L/R outer glazing        : 같은 식으로 뒤쪽 벽 앞(Z -2783)에 유리판 8겹.
처리 : 엔진 X 가 100650±200 안에 있는 조각(island)만 지우고, 안 쓰이는 정점까지 지운 뒤 v3 규칙
       (bbox 중심 원점, yaw+180, 크기 = 로컬 bbox x 스케일) 으로 한 파일에 담는다. 텍스처는 넣지 않는다
       — 게임 파츠의 TextureId 를 그대로 쓴다.

    blender.exe -b KGP_v3_textured.blend -P kgp_fix_stray.py
출력 : ovdr_export\kgp_fix_stray\KGP3S_fix_00.fbx · fix_stray.json
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

OUT = r"C:\Work\blender\ovdr_export\kgp_fix_stray"
STEM = "KGP3S_fix_00"
# outer glazing 두 개는 오브젝트 전체가 넘친 조각이고 뒤쪽 벽 면보다 5cm 안(벽 속)에 묻혀 안 보인다 → 손대지 않는다
TARGETS = ["P3 corridor L inner sapphire panels", "P3 corridor R inner sapphire panels"]
HALL_X = (100650.0 - 200.0, 100650.0 + 200.0)


def main():
    os.makedirs(OUT, exist_ok=True)
    dg = bpy.context.evaluated_depsgraph_get()
    rows, tmp = [], []
    for k, name in enumerate(TARGETS):
        o = bpy.data.objects[name]
        assert len([m for m in o.data.materials if m]) <= 1, name
        me = E.eval_mesh(o, dg)
        M = o.matrix_world
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        seen, kill, n_isl = set(), [], 0
        for f in bm.faces:
            if f.index in seen:
                continue
            stack, fs = [f], []
            seen.add(f.index)
            while stack:
                g = stack.pop()
                fs.append(g)
                for e in g.edges:
                    for h in e.link_faces:
                        if h.index not in seen:
                            seen.add(h.index)
                            stack.append(h)
            n_isl += 1
            vs = {v for g in fs for v in g.verts}
            wx = [(M @ v.co).x * 100 + E.X0 for v in vs]
            cx = (min(wx) + max(wx)) / 2
            if HALL_X[0] < cx < HALL_X[1]:
                kill.extend(fs)
        tris_before = len(bm.faces)
        bmesh.ops.delete(bm, geom=kill, context='FACES')
        loose = [v for v in bm.verts if not v.link_faces]
        if loose:
            bmesh.ops.delete(bm, geom=loose, context='VERTS')
        bm.to_mesh(me)
        bm.free()
        mn, mx = E.bbox_local(me)
        c = (mn + mx) / 2.0
        me.transform(Matrix.Translation(-c))
        s = M.to_scale()
        wc = M @ c
        yaw = math.degrees(M.to_euler('ZXY').z)
        mesh_name = "KGP3SM%04d" % (k + 1)
        dim = mx - mn
        rows.append({
            "obj": name, "part": "KGP2_" + E.ascii_name(name), "mesh": mesh_name,
            "islands": n_isl, "removed_tris": len(kill), "tris_before": tris_before, "tris": len(me.polygons),
            "engine_pos": E.engine_pos(wc.x, wc.y, wc.z),
            "yaw_deg": round(((yaw + E.MESH_YAW_FIX) + 180.0) % 360.0 - 180.0, 2),
            "size_cm": [round(dim.x * abs(s.x) * 100, 1), round(dim.z * abs(s.z) * 100, 1), round(dim.y * abs(s.y) * 100, 1)],
            "native_half_cm": [round(dim.x * 50, 2), round(dim.z * 50, 2), round(dim.y * 50, 2)]})
        me.name = mesh_name
        ob = bpy.data.objects.new(mesh_name, me)
        bpy.context.scene.collection.objects.link(ob)
        tmp.append(ob)
        print("@@", name, "islands", n_isl, "removed tris", len(kill), "->", len(me.polygons))

    bpy.ops.object.select_all(action='DESELECT')
    for ob in tmp:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = tmp[0]
    kw = dict(E.FBX)
    kw.update(path_mode='STRIP', embed_textures=False)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, STEM + ".fbx"), **kw)
    json.dump({"stem": STEM, "rows": rows}, io.open(os.path.join(OUT, "fix_stray.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("@@DONE")


main()
