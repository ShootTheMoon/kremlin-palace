# -*- coding: utf-8 -*-
r"""기사상(GEN_knight_armor_LOD)을 '통째로 한 조각' FBX 로 다시 낸다.

왜
  v2/v3 익스포터는 25,000 삼각형이 넘는 메시를 반으로 쪼갰다(CAP 여유분). 기사상은
  29,148 이라 둘로 잘렸는데, 트라이포 메시라 원래도 경계 엣지가 25,642 개인 '삼각형 수프'다.
  잘린 두 조각이 엔진 임포트에서 형상을 일부 잃었다 — 엔진이 기록한 크기가 FBX 보다 작다
  (아래 조각 높이 100cm vs 186cm, 위 조각은 세 축 모두 작음). 그래서 모자란 부분은 비고,
  남은 형상은 원래 크기로 늘려져 갑옷이 엉뚱하게 맞물렸다.
  엔진 한도는 30,000 이라 29,148 은 한 조각으로 들어간다. 멀쩡히 들어간 로코코 의자와 같은 길이다.

출력
  ovdr_export/kgp_v3/knight_fix/KGP3_knight_whole.fbx   (메시 1개, bbox 중심 원점)
  ovdr_export/kgp_v3/knight_fix/knight_place.json      (기사 18체 각각의 엔진 위치·크기·yaw)

    blender.exe -b Kremlin_Grand_Palace_COMPLETE.blend -P kgp_knight_whole.py
"""
import bpy
import sys
import os
import json
import math
from mathutils import Matrix, Vector

sys.path.append(r"C:\Work\blender")
import kgp_export_v3 as E          # noqa: E402  (run() 은 __main__ 일 때만 돈다)

OUT = r"C:\Work\blender\ovdr_export\kgp_v3\knight_fix"
STEM = "KGP3_knight_whole"
MESH_NAME = "KGP3K0001"
os.makedirs(OUT, exist_ok=True)

dg = bpy.context.evaluated_depsgraph_get()
knights = [o for o in E.collect() if o.data.name == "GEN_knight_armor_LOD"]
print("@@ knights", len(knights))
if not knights:
    raise SystemExit("no knights")

me = E.eval_mesh(knights[0], dg)          # 삼각화까지 된 로컬 메시(모디파이어 없음)
tris = E.tris_of(me)
print("@@ tris", tris)
if tris > 30000:
    raise SystemExit("over the 30,000 engine limit")

mn, mx = E.bbox_local(me)
c = (mn + mx) / 2.0
dim = mx - mn
me.transform(Matrix.Translation(-c))

ob = bpy.data.objects.new(MESH_NAME, me)
ob.data.name = MESH_NAME
bpy.context.scene.collection.objects.link(ob)
bpy.ops.object.select_all(action='DESELECT')
ob.select_set(True)
bpy.context.view_layer.objects.active = ob
kw = dict(E.FBX)
kw.update(path_mode='STRIP', embed_textures=False)   # 컬러맵은 v2 때 올라간 것을 그대로 쓴다
path = os.path.join(OUT, STEM + ".fbx")
bpy.ops.export_scene.fbx(filepath=path, **kw)

place = []
for o in knights:
    M = o.matrix_world
    s = M.to_scale()
    yaw = math.degrees(M.to_euler('ZXY').z)
    wc = M @ c
    size = [max(1.0, round(dim.x * abs(s.x) * E.CM, 1)),
            max(1.0, round(dim.z * abs(s.z) * E.CM, 1)),
            max(1.0, round(dim.y * abs(s.y) * E.CM, 1))]
    base = "KGP2_" + E.ascii_name(o.name)
    place.append({"obj": o.name, "keep": base + "_p0", "drop": base + "_p1",
                  "engine_pos": E.engine_pos(wc.x, wc.y, wc.z),
                  "yaw_deg": round(((yaw + E.MESH_YAW_FIX) + 180.0) % 360.0 - 180.0, 2),
                  "size_cm": size})
json.dump({"file": STEM + ".fbx", "mesh": MESH_NAME, "tris": tris,
           "native_half_cm": [round(dim.x * 50, 2), round(dim.z * 50, 2), round(dim.y * 50, 2)],
           "knights": place},
          open(os.path.join(OUT, "knight_place.json"), "w", encoding="utf-8"), indent=1)
print("@@ exported", path, "size", os.path.getsize(path))
print("@@ native half cm", [round(dim.x * 50, 2), round(dim.z * 50, 2), round(dim.y * 50, 2)])
print("@@ first", place[0])
