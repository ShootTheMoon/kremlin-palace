# -*- coding: utf-8 -*-
r"""크렘린 대궁전 — '공중에 뜬 조각' 전수 조사 (헤드리스).

오브젝트마다 연결 조각(island)으로 나누고 두 가지를 본다.
  A) 따로 노는 조각 : 같은 오브젝트의 다른 조각들과 멀리 떨어진 조각 (배열 모디파이어가 넘친 경우 등)
  B) 받침 없는 조각 : 조각 밑면 아래로 수직 레이를 쏴서 30cm 안에 아무 면도 없고, 바닥(0 / 2층 512)에서도 뜬 것
결과 : ovdr_export\kgp_phys\float_report.json + 콘솔 요약

    blender.exe -b KGP_v3_textured.blend -P kgp_float_scan.py
"""
import bpy
import bmesh
import io
import json
import math
import os
import sys

import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.append(r"C:\Work\blender")
import kgp_export_v3 as E          # noqa: E402

OUT = r"C:\Work\blender\ovdr_export\kgp_phys\float_report.json"
X0, Z0 = 100650.0, -1400.0
FOCUS = ("P3 corridor L inner sapphire panels", "P3 corridor R inner sapphire panels")


def exportable(o):
    if o.hide_render or not o.visible_get():
        return False
    return not any(any(s in c.name for s in E.SKIP_COLL) for c in o.users_collection)


def eng(p):
    return [round(p[0] * 100 + X0, 1), round(p[2] * 100, 1), round(-p[1] * 100 + Z0, 1)]


def islands(bm):
    bm.faces.ensure_lookup_table()
    seen, out = set(), []
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
        out.append(fs)
    return out


def main():
    dg = bpy.context.evaluated_depsgraph_get()
    objs = [o for o in bpy.data.objects
            if o.type in ('MESH', 'CURVE', 'FONT', 'SURFACE', 'META') and exportable(o)]
    # 월드 전체 BVH (받침 검사용)
    allv, allf = [], []
    per = []
    for o in objs:
        me = E.eval_mesh(o, dg)
        if me is None:
            continue
        mw = o.matrix_world
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.transform(mw)
        bm.verts.ensure_lookup_table()
        base = len(allv)
        allv.extend([v.co.copy() for v in bm.verts])
        allf.extend([[base + v.index for v in f.verts] for f in bm.faces])
        isl = []
        for fs in islands(bm):
            vs = {v for f in fs for v in f.verts}
            co = np.array([v.co[:] for v in vs])
            isl.append({"lo": co.min(0), "hi": co.max(0), "nf": len(fs)})
        per.append((o, isl))
        bm.free()
        bpy.data.meshes.remove(me)
    bvh = BVHTree.FromPolygons(allv, allf, epsilon=0.0)
    print("@@ objects", len(per), "faces", len(allf))

    rep = {"focus": [], "outlier": [], "unsupported": []}
    for o, isl in per:
        if o.name in FOCUS:
            for k, s in enumerate(isl):
                rep["focus"].append({"obj": o.name, "i": k, "min": eng(s["lo"]), "max": eng(s["hi"]), "faces": s["nf"]})
        if len(isl) >= 2:
            cen = np.array([(s["lo"] + s["hi"]) / 2 for s in isl])
            ext = np.array([np.linalg.norm(s["hi"] - s["lo"]) for s in isl])
            for k, s in enumerate(isl):
                d = np.linalg.norm(cen - cen[k], axis=1)
                d[k] = 1e9
                nn = d.min()
                typical = np.median(np.sort(np.linalg.norm(cen[:, None] - cen[None], axis=2), axis=1)[:, 1]) if len(isl) > 2 else 0
                if nn > max(4.0, 4 * typical, 2 * ext[k]):
                    rep["outlier"].append({"obj": o.name, "i": k, "min": eng(s["lo"]), "max": eng(s["hi"]),
                                           "faces": s["nf"], "nn_m": round(float(nn), 2), "typical_m": round(float(typical), 2)})
        for k, s in enumerate(isl):
            lo, hi = s["lo"], s["hi"]
            bottom = lo[2] * 100
            if bottom < 25 or abs(bottom - 512) < 25 or hi[2] * 100 > 1150:
                continue                                   # 바닥에 놓였거나 천장부
            hit = 0
            for fx in (0.25, 0.5, 0.75):
                for fy in (0.25, 0.5, 0.75):
                    p = Vector((lo[0] + (hi[0] - lo[0]) * fx, lo[1] + (hi[1] - lo[1]) * fy, lo[2] - 0.005))
                    r = bvh.ray_cast(p, Vector((0, 0, -1)), 0.30)
                    if r[0] is not None:
                        hit += 1
            # 옆으로 붙은 것(벽 장식 등)도 받침으로 본다 : bbox 를 5cm 키워 다른 면과 닿는지
            if hit == 0:
                c = Vector(((lo + hi) / 2).tolist())
                touch = 0
                for dv in (Vector((1, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, -1, 0)), Vector((0, 0, 1))):
                    half = Vector(((hi - lo) / 2).tolist())
                    reach = abs(half.dot(dv)) + 0.08
                    r = bvh.ray_cast(c + dv * (reach - 0.079), dv, 0.08)
                    if r[0] is not None:
                        touch += 1
                if touch == 0:
                    rep["unsupported"].append({"obj": o.name, "i": k, "min": eng(lo), "max": eng(hi), "faces": s["nf"]})
    json.dump(rep, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("@@ focus islands", len(rep["focus"]), "outliers", len(rep["outlier"]), "unsupported", len(rep["unsupported"]))


main()
