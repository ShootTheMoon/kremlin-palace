# -*- coding: utf-8 -*-
r"""계단 두 팔 맨 윗단 블록의 '뒷면'(계단참 밑에서 보이는 흰 면) 실측.

맨 윗단 발판 섬(top ≈ 512)을 찾아, 한 칸 아래 발판과 반대쪽(= 계단을 오르는 방향)을 향한 수직면을
고른다. 그 면 앞 1m 에서 면 쪽으로 격자 레이를 쏴 '평평하게 드러난 범위'를 재고, 면 앞 5cm 에서
위로 레이를 쏴 계단참(다리) 밑면 높이를 잰다.

    blender.exe -b KGP_v3_textured.blend -P kgp_stair_end_measure.py
출력 : ovdr_export\kgp_stair_end\measure.json
"""
import bpy
import bmesh
import io
import json
import math
import os
import sys

from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.append(r"C:\Work\blender")
import kgp_export_v3 as E          # noqa: E402

OUT = r"C:\Work\blender\ovdr_export\kgp_stair_end"


def exportable(o):
    if o.hide_render or not o.visible_get():
        return False
    return not any(any(s in c.name for s in E.SKIP_COLL) for c in o.users_collection)


def main():
    os.makedirs(OUT, exist_ok=True)
    dg = bpy.context.evaluated_depsgraph_get()
    V, F = [], []
    for o in bpy.data.objects:
        if o.type not in ('MESH', 'CURVE', 'FONT', 'SURFACE', 'META') or not exportable(o):
            continue
        me = E.eval_mesh(o, dg)
        if me is None:
            continue
        mw = o.matrix_world
        base = len(V)
        V.extend([mw @ v.co for v in me.vertices])
        F.extend([[base + i for i in p.vertices] for p in me.polygons])
        bpy.data.meshes.remove(me)
    bvh = BVHTree.FromPolygons(V, F, epsilon=0.0)

    res = {}
    for arm in ("L", "R"):
        o = bpy.data.objects["P3 stair marble treads " + arm]
        me = E.eval_mesh(o, dg)
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.transform(o.matrix_world)
        bm.faces.ensure_lookup_table()
        seen, isl = set(), []
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
            top = max(v.co.z for g in fs for v in g.verts)
            cen = sum((v.co for g in fs for v in g.verts), Vector()) / sum(len(g.verts) for g in fs)
            isl.append((top, cen, fs))
        isl.sort(key=lambda t: t[0])
        top, cen, fs = isl[-1]
        prev = isl[-2][1]
        up = Vector((cen.x - prev.x, cen.y - prev.y, 0)).normalized()
        # 오르는 방향을 향한 수직면 중 가장 큰 것
        cand = [g for g in fs if abs(g.normal.z) < 0.1 and g.normal.dot(up) > 0.8]
        face = max(cand, key=lambda g: g.calc_area())
        n = face.normal.copy()
        n.z = 0
        n.normalize()
        fc = face.calc_center_median()
        side = Vector((-n.y, n.x, 0))                       # 면 가로 방향
        # 격자 레이 : 면 앞 1m -> -n
        pts = []
        for i in range(-40, 41):
            for k in range(0, 61):
                s = i * 0.05
                z = k * 0.1 + 0.02
                p0 = Vector((fc.x, fc.y, 0)) + side * s + n * 1.0 + Vector((0, 0, z))
                hit = bvh.ray_cast(p0, -n, 1.5)
                if hit[0] is not None and abs(hit[3] - 1.0) < 0.03:
                    pts.append((s, z))
        ss = sorted({p[0] for p in pts})
        zs = sorted({p[1] for p in pts})
        # 면 앞 5cm 에서 위로 : 천장 높이
        ceil = []
        for i in range(-10, 11):
            s = i * 0.11
            p0 = Vector((fc.x, fc.y, 0.5)) + side * s + n * 0.05
            hit = bvh.ray_cast(p0, Vector((0, 0, 1)), 10.0)
            ceil.append(round(hit[0].z, 3) if hit[0] is not None else None)
        res[arm] = {"face_center": [round(v, 4) for v in fc], "normal": [round(n.x, 4), round(n.y, 4)],
                    "side": [round(side.x, 4), round(side.y, 4)], "face_area": round(face.calc_area(), 3),
                    "flat_s_range": [ss[0], ss[-1]] if ss else None, "flat_z_range": [zs[0], zs[-1]] if zs else None,
                    "n_hits": len(pts), "ceil_z": ceil, "tread_top": round(top, 3),
                    "yaw_deg_of_side": round(math.degrees(math.atan2(side.y, side.x)), 2)}
        bm.free()
        bpy.data.meshes.remove(me)
    json.dump(res, io.open(os.path.join(OUT, "measure.json"), "w", encoding="utf-8"), indent=1)
    print("@@", json.dumps(res))


main()
