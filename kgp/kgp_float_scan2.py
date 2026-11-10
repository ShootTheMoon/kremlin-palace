# -*- coding: utf-8 -*-
r"""'아무것에도 닿지 않은 조각' 정밀 검사 (헤드리스).

모든 오브젝트를 조각(island) 단위로 나눠 전역 BVH 를 만들고, 조각마다 정점 최대 40개에서
반경 8cm 안의 면을 찾는다. 다른 조각의 면이 하나도 없으면 '떠 있음' 후보. 바닥(0)·2층(512)에
놓인 것, 물(파티클)은 뺀다. 같은 자리에 겹친 복제 조각도 따로 센다.

    blender.exe -b KGP_v3_textured.blend -P kgp_float_scan2.py
"""
import bpy
import bmesh
import io
import json
import sys
from collections import defaultdict

import numpy as np
from mathutils.bvhtree import BVHTree

sys.path.append(r"C:\Work\blender")
import kgp_export_v3 as E          # noqa: E402

OUT = r"C:\Work\blender\ovdr_export\kgp_phys\float_report2.json"
X0, Z0 = 100650.0, -1400.0
R = 0.08


def exportable(o):
    if o.hide_render or not o.visible_get():
        return False
    return not any(any(s in c.name for s in E.SKIP_COLL) for c in o.users_collection)


def eng(p):
    return [round(p[0] * 100 + X0, 1), round(p[2] * 100, 1), round(-p[1] * 100 + Z0, 1)]


def main():
    dg = bpy.context.evaluated_depsgraph_get()
    objs = [o for o in bpy.data.objects
            if o.type in ('MESH', 'CURVE', 'FONT', 'SURFACE', 'META') and exportable(o)
            and "water" not in o.name.lower()]
    V, F, fisl = [], [], []
    isl = []                    # (obj, verts np)
    for o in objs:
        me = E.eval_mesh(o, dg)
        if me is None:
            continue
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.transform(o.matrix_world)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        base = len(V)
        V.extend([v.co.copy() for v in bm.verts])
        seen = set()
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
            iid = len(isl)
            vs = sorted({v.index for g in fs for v in g.verts})
            isl.append((o.name, np.array([bm.verts[i].co[:] for i in vs])))
            for g in fs:
                F.append([base + v.index for v in g.verts])
                fisl.append(iid)
        bm.free()
        bpy.data.meshes.remove(me)
    bvh = BVHTree.FromPolygons(V, F, epsilon=0.0)
    print("@@ islands", len(isl), "faces", len(F))

    # 복제(같은 bbox) 묶음
    dup = defaultdict(list)
    for i, (n, co) in enumerate(isl):
        key = tuple(np.round(np.concatenate([co.min(0), co.max(0)]) * 100).astype(int))
        dup[key].append(i)

    floating = []
    for i, (n, co) in enumerate(isl):
        lo, hi = co.min(0), co.max(0)
        zb = lo[2] * 100
        if zb < 3 or abs(zb - 512) < 3:
            continue
        idx = np.linspace(0, len(co) - 1, min(40, len(co))).astype(int)
        free = True
        for p in co[idx]:
            for (_, _, fi, _) in bvh.find_nearest_range(p.tolist(), R):
                if fisl[fi] != i:
                    free = False
                    break
            if not free:
                break
        if free:
            floating.append({"obj": n, "island": i, "min": eng(lo), "max": eng(hi), "verts": len(co)})
    dups = [{"obj": sorted({isl[i][0] for i in v}), "n": len(v), "min": eng(isl[v[0]][1].min(0)),
             "max": eng(isl[v[0]][1].max(0))} for v in dup.values() if len(v) >= 3]
    json.dump({"floating": floating, "stacked_dups": dups}, io.open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("@@ floating", len(floating), "stacked dup groups", len(dups))


main()
