# -*- coding: utf-8 -*-
r"""기사상(GEN_knight_armor_LOD)을 몸의 부위대로 5조각으로 나눠 낸다.

왜 v2 의 2조각이 망가졌나 (2026-09-19 실측)
  익스포터가 면을 지운 뒤 남은 '안 쓰이는 정점'(254개·220개)을 bbox 에 넣어 조각 크기를
  잡았다. 엔진은 삼각형이 쓰는 정점만으로 크기를 잰다. 그래서 높이 100cm 짜리 반쪽이
  186·195cm 로 늘려져, 엉뚱한 중심에 놓였다. 형상 손실은 없었다.

이번 규칙
  * 큰 몸통 셸(24,342 삼각형)은 면 중심 높이로 자른다 : 받침 / 다리 / 허리 / 가슴·팔 / 어깨·머리
  * 작은 부속(방패·창·깃장식 등 61개)은 자르지 않고 통째로, 중심 높이가 속한 조각에 넣는다
  * 조각마다 안 쓰이는 정점을 지운 뒤 bbox 를 잰다 → 엔진이 재는 것과 같아진다
  * 한 파일에 메시 5개(다중 메시 FBX → 메시마다 에셋 1개). 텍스처는 v2 원본 컬러맵 재사용.

    blender.exe -b Kremlin_Grand_Palace_COMPLETE.blend -P kgp_knight_parts.py
"""
import bpy
import bmesh
import sys
import os
import json
import math
import collections
from mathutils import Matrix, Vector

sys.path.append(r"C:\Work\blender")
import kgp_export_v3 as E          # noqa: E402

OUT = r"C:\Work\blender\ovdr_export\kgp_v3\knight_fix"
STEM = "KGP3_knight_parts"
BANDS = [  # (이름, 아래 경계 z m) — 위 경계는 다음 것
    ("base", -1.0),     # 받침 바위 + 발
    ("legs", 0.25),     # 다리
    ("waist", 0.75),    # 허리·아랫몸통
    ("chest", 1.07),    # 가슴·팔
    ("head", 1.36),     # 어깨·머리·깃장식
]
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    if f.endswith(".fbx"):
        os.remove(os.path.join(OUT, f))


def band_of(z):
    idx = 0
    for i, (_, lo) in enumerate(BANDS):
        if z >= lo:
            idx = i
    return idx


dg = bpy.context.evaluated_depsgraph_get()
knights = [o for o in E.collect() if o.data.name == "GEN_knight_armor_LOD"]
me = E.eval_mesh(knights[0], dg)
print("@@ knights", len(knights), "tris", len(me.polygons))

# --- 위치로 붙어 있는 덩어리(UV 이음매로 갈라진 정점은 합쳐서 본다)
def vk(co):
    return (round(co.x, 4), round(co.y, 4), round(co.z, 4))
parent = list(range(len(me.polygons)))
def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a
owner = {}
for p in me.polygons:
    for vi in p.vertices:
        kk = vk(me.vertices[vi].co)
        if kk in owner:
            ra, rb = find(owner[kk]), find(p.index)
            if ra != rb:
                parent[ra] = rb
        else:
            owner[kk] = p.index
comp = collections.defaultdict(list)
for p in me.polygons:
    comp[find(p.index)].append(p.index)
shell = max(comp.values(), key=len)
shell_set = set(shell)

assign = {}
for faces in comp.values():
    if faces is shell:
        for f in faces:
            assign[f] = band_of(me.polygons[f].center.z)
    else:
        zc = sum(me.polygons[f].center.z for f in faces) / len(faces)
        b = band_of(zc)
        for f in faces:
            assign[f] = b
print("@@ components", len(comp), "shell", len(shell))

# --- 조각 만들기 : 면만 남기고, 안 쓰이는 정점까지 지운다
pieces = []
for bi, (bname, _) in enumerate(BANDS):
    keep = {f for f, b in assign.items() if b == bi}
    p = me.copy()
    bm = bmesh.new()
    bm.from_mesh(p)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(p)
    bm.free()
    used = set()
    for poly in p.polygons:
        used.update(poly.vertices)
    assert len(used) == len(p.vertices), "loose vertices left in %s" % bname
    mn, mx = E.bbox_local(p)
    c = (mn + mx) / 2.0
    p.transform(Matrix.Translation(-c))
    p.calc_loop_triangles()
    pieces.append({"band": bname, "mesh": p, "centre": c.copy(), "dim": (mx - mn).copy(),
                   "tris": len(p.loop_triangles), "loose_removed": len(loose)})
    print("@@ piece %-6s tris %5d  dims %s  loose removed %d"
          % (bname, len(p.loop_triangles), [round(x, 3) for x in (mx - mn)], len(loose)))

assert sum(pc["tris"] for pc in pieces) == len(me.polygons), "triangles lost"

# --- 한 파일에 5개
objs = []
for i, pc in enumerate(pieces, 1):
    nm = "KGP3K%04d" % i
    pc["name"] = nm
    ob = bpy.data.objects.new(nm, pc["mesh"])
    ob.data.name = nm
    bpy.context.scene.collection.objects.link(ob)
    objs.append(ob)
bpy.ops.object.select_all(action='DESELECT')
for ob in objs:
    ob.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
kw = dict(E.FBX)
kw.update(path_mode='STRIP', embed_textures=False)
path = os.path.join(OUT, STEM + ".fbx")
bpy.ops.export_scene.fbx(filepath=path, **kw)

# --- 기사 18체 × 5조각 배치
place = []
for o in knights:
    M = o.matrix_world
    s = M.to_scale()
    yaw = math.degrees(M.to_euler('ZXY').z)
    base = "KGP2_" + E.ascii_name(o.name)
    for pc in pieces:
        wc = M @ pc["centre"]
        d = pc["dim"]
        place.append({
            "obj": o.name, "name": base + "_" + pc["band"], "mesh": pc["name"],
            "old": [base + "_p0", base + "_p1"],
            "engine_pos": E.engine_pos(wc.x, wc.y, wc.z),
            "yaw_deg": round(((yaw + E.MESH_YAW_FIX) + 180.0) % 360.0 - 180.0, 2),
            "size_cm": [max(1.0, round(d.x * abs(s.x) * E.CM, 1)),
                        max(1.0, round(d.z * abs(s.z) * E.CM, 1)),
                        max(1.0, round(d.y * abs(s.y) * E.CM, 1))]})
json.dump({"file": STEM + ".fbx",
           "pieces": [{"mesh": pc["name"], "band": pc["band"], "tris": pc["tris"],
                       "native_half_cm": [round(pc["dim"].x * 50, 2), round(pc["dim"].z * 50, 2),
                                          round(pc["dim"].y * 50, 2)]} for pc in pieces],
           "place": place},
          open(os.path.join(OUT, "knight_parts_place.json"), "w", encoding="utf-8"), indent=1)
print("@@ exported", path, os.path.getsize(path), "bytes;", len(place), "placements")
