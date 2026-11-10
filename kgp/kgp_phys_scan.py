# -*- coding: utf-8 -*-
r"""크렘린 대궁전 — 충돌(물리) 누락 전수 조사.

블렌더 원본을 사람 키 높이에서 수평으로 잘라 단면 선분을 얻고, 그 선분이 게임의 충돌 Part
(KGP_COL_* — col_live.json) 안에 들어가는지 5cm 간격으로 검사한다. 안 덮인 길이를 오브젝트별로
모아 우선순위 표를 만들고, 층별 평면도 PNG 를 그린다(회색=덮임, 빨강=뚫림, 하늘색=충돌 상자).

    blender.exe -b KGP_v3_textured.blend -P kgp_phys_scan.py

출력 (ovdr_export\kgp_phys)
  scan_objects.json   오브젝트별 로컬 bbox(OBB) · 월드 AABB · yaw · 재질 · 슬라이스별 미피복 길이
  scan_treads.json    계단 발판 섬(island)마다 윗면 높이·발자국 직사각형
  plan_1F.png / plan_2F.png
"""
import bpy
import bmesh
import io
import json
import math
import os
import struct
import sys
import zlib

import numpy as np

sys.path.append(r"C:\Work\blender")
import kgp_export_v3 as E          # noqa: E402

OUT = r"C:\Work\blender\ovdr_export\kgp_phys"
COL = os.path.join(OUT, "col_live.json")
X0, Z0 = 100650.0, -1400.0
FLOOR1 = 0.0
FLOOR2 = 512.0                     # 2층 카펫 윗면
SLICES = {"1F": [FLOOR1 + 40, FLOOR1 + 100, FLOOR1 + 170],
          "2F": [FLOOR2 + 40, FLOOR2 + 100, FLOOR2 + 160]}
STEP = 5.0                         # 샘플 간격(cm)
MARGIN = 15.0                      # 충돌 상자 여유(cm, 수평)
SKIP_MAT = ("water", "flame", "glow", "light")
PX = 4.0                           # 평면도 cm/px
BOUNDS = (97400.0, 103900.0, -2980.0, 2980.0)


def exportable(o):
    if o.hide_render or not o.visible_get():
        return False
    return not any(any(s in c.name for s in E.SKIP_COLL) for c in o.users_collection)


def to_engine(p):
    """(N,3) 블렌더 m -> 엔진 cm."""
    return np.stack([p[:, 0] * 100.0 + X0, p[:, 2] * 100.0, -p[:, 1] * 100.0 + Z0], axis=1)


def load_boxes():
    boxes = json.load(io.open(COL, encoding="utf-8"))
    c = np.array([b["pos"] for b in boxes], float)
    s = np.array([b["size"] for b in boxes], float)
    th = np.radians(np.array([b["rot"][1] for b in boxes], float))
    return boxes, c, s, th


def covered(pts, h, c, s, th):
    """pts (N,2) XZ 가 높이 h 에서 어떤 상자에 들어가는가."""
    ok = np.zeros(len(pts), bool)
    ylo = c[:, 1] - s[:, 1] / 2 - 5
    yhi = c[:, 1] + s[:, 1] / 2 + 5
    live = np.where((ylo <= h) & (yhi >= h))[0]
    for k in live:
        dx = pts[:, 0] - c[k, 0]
        dz = pts[:, 1] - c[k, 2]
        ct, st = math.cos(th[k]), math.sin(th[k])
        lx = dx * ct - dz * st
        lz = dx * st + dz * ct
        ok |= (np.abs(lx) <= s[k, 0] / 2 + MARGIN) & (np.abs(lz) <= s[k, 2] / 2 + MARGIN)
    return ok


def slice_tris(tri, h):
    """tri (T,3,3) 엔진 좌표. 높이 h 평면과의 교선 (M,2,2) XZ."""
    y = tri[:, :, 1] - h
    cross = (y.min(1) < 0) & (y.max(1) > 0)
    t = tri[cross]
    y = y[cross]
    segs = []
    pts = []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        yi, yj = y[:, i], y[:, j]
        m = (yi * yj) < 0
        tt = np.where(m, yi / np.where(m, yi - yj, 1.0), 0.0)
        p = t[:, i] + (t[:, j] - t[:, i]) * tt[:, None]
        pts.append((m, p[:, [0, 2]]))
    a = np.zeros((len(t), 2))
    b = np.zeros((len(t), 2))
    have_a = np.zeros(len(t), bool)
    have_b = np.zeros(len(t), bool)
    for m, p in pts:
        put_a = m & ~have_a
        a[put_a] = p[put_a]
        have_a |= put_a
        put_b = m & ~put_a & ~have_b
        b[put_b] = p[put_b]
        have_b |= put_b
    ok = have_a & have_b
    return np.stack([a[ok], b[ok]], axis=1)


def sample(segs):
    if not len(segs):
        return np.zeros((0, 2))
    d = segs[:, 1] - segs[:, 0]
    L = np.hypot(d[:, 0], d[:, 1])
    n = np.maximum(1, np.ceil(L / STEP)).astype(int)
    idx = np.repeat(np.arange(len(segs)), n)
    k = np.concatenate([np.arange(v) for v in n]) + 0.5
    f = (k / np.repeat(n, n))[:, None]
    return segs[idx, 0] + d[idx] * f


def write_png(path, rgb):
    h, w, _ = rgb.shape
    raw = b"".join(b"\x00" + rgb[y].tobytes() for y in range(h))

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")
    open(path, "wb").write(png)


def to_px(xz):
    x0, x1, z0, z1 = BOUNDS
    col = ((xz[:, 0] - x0) / PX).astype(int)
    row = ((z1 - xz[:, 1]) / PX).astype(int)      # 위쪽 = +Z(정문 쪽)
    return row, col


def draw_boxes(img, c, s, th, band):
    x0, x1, z0, z1 = BOUNDS
    H, W, _ = img.shape
    for k in range(len(c)):
        if c[k, 1] + s[k, 1] / 2 < band[0] or c[k, 1] - s[k, 1] / 2 > band[1]:
            continue
        r = math.hypot(s[k, 0], s[k, 2]) / 2
        cmin = max(0, int((c[k, 0] - r - x0) / PX)); cmax = min(W - 1, int((c[k, 0] + r - x0) / PX))
        rmin = max(0, int((z1 - c[k, 2] - r) / PX)); rmax = min(H - 1, int((z1 - c[k, 2] + r) / PX))
        if cmin > cmax or rmin > rmax:
            continue
        cc, rr = np.meshgrid(np.arange(cmin, cmax + 1), np.arange(rmin, rmax + 1))
        X = x0 + (cc + 0.5) * PX
        Z = z1 - (rr + 0.5) * PX
        dx, dz = X - c[k, 0], Z - c[k, 2]
        ct, st = math.cos(th[k]), math.sin(th[k])
        lx = dx * ct - dz * st
        lz = dx * st + dz * ct
        m = (np.abs(lx) <= s[k, 0] / 2) & (np.abs(lz) <= s[k, 2] / 2)
        sub = img[rmin:rmax + 1, cmin:cmax + 1]
        sub[m] = (sub[m] * 0.5 + np.array([120, 190, 255]) * 0.5).astype(np.uint8)


def islands(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    seen = set()
    out = []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack = [f]
        seen.add(f.index)
        vs = set()
        while stack:
            g = stack.pop()
            for v in g.verts:
                vs.add(v.index)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        out.append(sorted(vs))
    bm.free()
    return out


def min_rect(xz):
    """볼록 껍질의 최소 넓이 직사각형 -> (cx, cz, w_along, d_across, angle_rad of w axis)."""
    pts = np.unique(np.round(xz, 2), axis=0)
    if len(pts) < 3:
        c = pts.mean(0)
        return float(c[0]), float(c[1]), 1.0, 1.0, 0.0
    best = None
    for a in np.radians(np.arange(0.0, 180.0, 0.5)):
        u = np.array([math.cos(a), math.sin(a)])
        v = np.array([-math.sin(a), math.cos(a)])
        pu, pv = pts @ u, pts @ v
        area = (pu.max() - pu.min()) * (pv.max() - pv.min())
        if best is None or area < best[0]:
            cu, cv = (pu.max() + pu.min()) / 2, (pv.max() + pv.min()) / 2
            c = cu * u + cv * v
            best = (area, float(c[0]), float(c[1]), float(pu.max() - pu.min()), float(pv.max() - pv.min()), float(a))
    return best[1:]


def main():
    os.makedirs(OUT, exist_ok=True)
    boxes, bc, bs, bth = load_boxes()
    dg = bpy.context.evaluated_depsgraph_get()
    objs = [o for o in bpy.data.objects
            if o.type in ('MESH', 'CURVE', 'FONT', 'SURFACE', 'META') and exportable(o)]
    objs.sort(key=lambda o: o.name)
    print("@@ objects", len(objs))

    H = int((BOUNDS[3] - BOUNDS[2]) / PX) + 1
    W = int((BOUNDS[1] - BOUNDS[0]) / PX) + 1
    imgs = {k: np.full((H, W, 3), 255, np.uint8) for k in SLICES}
    for k in SLICES:
        band = (min(SLICES[k]) - 60, max(SLICES[k]) + 60)
        draw_boxes(imgs[k], bc, bs, bth, band)

    rows, treads = [], []
    for n, o in enumerate(objs):
        mats = [sl.material.name for sl in o.material_slots if sl.material]
        if any(any(s in m.lower() for s in SKIP_MAT) for m in mats) or "WATER" in o.name.upper():
            continue
        me = E.eval_mesh(o, dg)
        if me is None:
            continue
        nv = len(me.vertices)
        loc = np.empty(nv * 3)
        me.vertices.foreach_get("co", loc)
        loc = loc.reshape(-1, 3)
        tri_idx = np.empty(len(me.polygons) * 3, dtype=np.int64)
        me.polygons.foreach_get("vertices", tri_idx)
        tri_idx = tri_idx.reshape(-1, 3)
        mw = np.array(o.matrix_world)
        wv = loc @ mw[:3, :3].T + mw[:3, 3]
        ev = to_engine(wv)
        tri = ev[tri_idx]

        lo, hi = loc.min(0), loc.max(0)
        sc = np.array(o.matrix_world.to_scale())
        cen_l = (lo + hi) / 2
        cen_w = to_engine((mw[:3, :3] @ cen_l + mw[:3, 3])[None])[0]
        yaw = math.degrees(o.matrix_world.to_euler().z)
        ext = (hi - lo) * np.abs(sc)
        rec = {"name": o.name, "type": o.type, "mats": mats, "tris": int(len(tri_idx)),
               "yaw": round(yaw, 2),
               "obb_center": [round(float(v), 1) for v in cen_w],
               "obb_size": [round(float(ext[0] * 100), 1), round(float(ext[2] * 100), 1), round(float(ext[1] * 100), 1)],
               "aabb_min": [round(float(v), 1) for v in ev.min(0)],
               "aabb_max": [round(float(v), 1) for v in ev.max(0)],
               "uncovered": {}, "sliced": {}}

        for k, hs in SLICES.items():
            unc_pts = []
            tot = 0.0
            for h in hs:
                segs = slice_tris(tri, h)
                if not len(segs):
                    continue
                pts = sample(segs)
                ok = covered(pts, h, bc, bs, bth)
                tot += len(pts) * STEP
                r, c = to_px(pts)
                m = (r >= 0) & (r < H) & (c >= 0) & (c < W)
                imgs[k][r[m & ok], c[m & ok]] = (90, 90, 90)
                imgs[k][r[m & ~ok], c[m & ~ok]] = (230, 30, 30)
                if (~ok).any():
                    unc_pts.append(pts[~ok])
            if tot:
                rec["sliced"][k] = round(tot)
            if unc_pts:
                u = np.concatenate(unc_pts)
                g = np.unique(np.round(u / 5.0).astype(int), axis=0) * 5
                rec["uncovered"][k] = {"cm": round(len(u) * STEP),
                                       "min": [round(float(v)) for v in u.min(0)],
                                       "max": [round(float(v)) for v in u.max(0)],
                                       "pts": g.tolist()}

        if "stair" in o.name.lower() and "tread" in o.name.lower():
            for vs in islands(me):
                p = ev[vs]
                cx, cz, wa, da, ang = min_rect(p[:, [0, 2]])
                treads.append({"obj": o.name, "top": round(float(p[:, 1].max()), 1),
                               "bottom": round(float(p[:, 1].min()), 1),
                               "cx": round(cx, 1), "cz": round(cz, 1), "w": round(wa, 1), "d": round(da, 1),
                               "ang_deg": round(math.degrees(ang), 2), "nverts": len(vs)})
        bpy.data.meshes.remove(me)
        rows.append(rec)
        if n % 100 == 0:
            print("@@", n, o.name)

    json.dump(rows, io.open(os.path.join(OUT, "scan_objects.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(treads, io.open(os.path.join(OUT, "scan_treads.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for k, img in imgs.items():
        write_png(os.path.join(OUT, "plan_%s.png" % k), img)
    print("@@ done", len(rows), "objects,", len(treads), "tread islands")


main()
