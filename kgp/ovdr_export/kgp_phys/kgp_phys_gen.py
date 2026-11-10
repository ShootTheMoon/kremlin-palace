# -*- coding: utf-8 -*-
r"""크렘린 대궁전 — 충돌(물리) 2차 보강 생성기.

입력 : scan_objects.json · scan_treads.json (kgp_phys_scan.py) · col_live.json (게임의 현재 충돌)
출력
  stair_update.json      기존 KGP_COL_STAIR_* 60개를 제자리 수정 (회전이 26~94° 틀어져 있었다)
                         → 발판마다 바닥부터 발판 윗면까지 꽉 찬 블록 (블렌더 발판이 원래 그렇다)
  items_static_NN.json   새 Static 충돌 Part (계단 난간 · 계단 기둥 · 문 옆 벽/인방 · 분수 · 소품 군집)
  items_movable.json     팀룸 문짝 충돌 4개 (Movable, 이름이 KGP2_Door_leaf_sapphire 로 시작 → 문 스크립트가 같이 돌린다)
  plan_new_1F.png / plan_new_2F.png   기존(하늘) + 새 상자(초록) + 계단 수정(주황)
  gen_report.txt

회전 규약 : Part yaw θ 에서 로컬 X 축 = 월드 (cos θ, 0, -sin θ). (화성 문짝으로 실측 검증된 Roblox 규약)
"""
import io
import json
import math
import os
import struct
import zlib
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OBJ = json.load(io.open(os.path.join(HERE, "scan_objects.json"), encoding="utf-8"))
TREADS = json.load(io.open(os.path.join(HERE, "scan_treads.json"), encoding="utf-8"))
COL = json.load(io.open(os.path.join(HERE, "col_live.json"), encoding="utf-8"))
LEAVES = json.load(io.open(os.path.join(HERE, "gate_leaves.json"), encoding="utf-8"))

FOUNTAIN = (100650.0, -1800.0)
FLOOR = {"1F": 0.0, "2F": 512.0}
BASE = dict(anchored=True, transparency=1, canCollide=True, canQuery=True, canTouch=False,
            castShadow=False, locked=True, material="Plastic", shape="Block")
EXCL = ("stair", "newel", "Door ", "fountain", "P7 ", "angel", "tea ", "WATER", "chandelier",
        "Wing ceiling", "portal lintel", "Rug", "rug", "carpet", "runner", "inlay", "floor", "tiles")


def yaw_for_axis(ax, az):
    """로컬 X 축이 월드 (ax, az) 를 향하게 하는 yaw(도)."""
    return round(math.degrees(math.atan2(-az, ax)), 2)


def part(name, pos, size, yaw, mobility="Static"):
    p = dict(BASE)
    p.update(position=[round(float(v), 1) for v in pos], size=[round(float(v), 1) for v in size],
             orientation=[0.0, float(yaw), 0.0], mobility=mobility)
    return {"className": "Part", "name": name, "props": p}


def min_rect(xz, pad):
    pts = np.unique(np.round(np.asarray(xz, float), 1), axis=0)
    best = None
    for a in np.radians(np.arange(0.0, 90.0, 1.0)):
        u = np.array([math.cos(a), math.sin(a)])
        v = np.array([-math.sin(a), math.cos(a)])
        pu, pv = pts @ u, pts @ v
        area = (np.ptp(pu) + 2 * pad) * (np.ptp(pv) + 2 * pad)
        if best is None or area < best[0]:
            c = (pu.max() + pu.min()) / 2 * u + (pv.max() + pv.min()) / 2 * v
            best = (area, c, np.ptp(pu) + 2 * pad, np.ptp(pv) + 2 * pad, u)
    return best[1:]


def main():
    report = []
    static, movable, stair_upd = [], [], []

    # ---------------------------------------------------------------- 1. 계단 블록 (제자리 수정)
    by_arm = defaultdict(list)
    for t in TREADS:
        a = t["ang_deg"] if t["w"] > t["d"] else t["ang_deg"] + 90.0
        ax, az = math.cos(math.radians(a)), math.sin(math.radians(a))
        if (t["cx"] - FOUNTAIN[0]) * ax + (t["cz"] - FOUNTAIN[1]) * az < 0:
            ax, az = -ax, -az                               # 바깥(분수 반대)을 향하게
        t.update(ux=ax, uz=az, width=max(t["w"], t["d"]), depth=min(t["w"], t["d"]))
        by_arm["L" if "treads L" in t["obj"] else "R"].append(t)
    slabs = {c["name"]: c for c in COL if c["name"].startswith("KGP_COL_STAIR_")}
    used = set()
    for arm, ts in by_arm.items():
        ts.sort(key=lambda t: t["top"])
        for t in ts:
            best = min((s for s in slabs.values() if s["name"] not in used and "_%s_" % arm in s["name"]),
                       key=lambda s: math.hypot(s["pos"][0] - t["cx"], s["pos"][2] - t["cz"]))
            d = math.hypot(best["pos"][0] - t["cx"], best["pos"][2] - t["cz"])
            assert d < 2.0, (best["name"], d)
            used.add(best["name"])
            yaw = yaw_for_axis(t["ux"], t["uz"])
            top = t["top"]
            stair_upd.append({"guid": best["guid"], "name": best["name"],
                              "pos": [t["cx"], top / 2.0, t["cz"]], "yaw": yaw,
                              "size": [round(t["width"] + 32.0, 1), round(top, 1), 44.0]})
    report.append("계단 블록 제자리 수정 %d (발판 %d)" % (len(stair_upd), len(TREADS)))

    # ---------------------------------------------------------------- 2. 계단 난간 (발판 2개씩, 안·밖)
    n_rail = 0
    for arm, ts in by_arm.items():
        for k in range(0, len(ts), 2):
            pair = ts[k:k + 2]
            for side, sgn in (("in", -1.0), ("out", 1.0)):
                e = [np.array([t["cx"] + sgn * t["ux"] * (t["width"] / 2 + 10.0),
                               t["cz"] + sgn * t["uz"] * (t["width"] / 2 + 10.0)]) for t in pair]
                mid = sum(e) / len(e)
                ux = sum(t["ux"] for t in pair); uz = sum(t["uz"] for t in pair)
                n = math.hypot(ux, uz); ux, uz = ux / n, uz / n
                L = (np.linalg.norm(e[-1] - e[0]) if len(e) > 1 else 0.0) + 44.0
                H = max(t["top"] for t in pair) + 100.0
                static.append(part("KGP_COL_RAIL_stair_%s_%s_%02d" % (arm, side, k // 2),
                                   (mid[0], H / 2, mid[1]), (14.0, H, L), yaw_for_axis(ux, uz)))
                n_rail += 1
    report.append("계단 난간 %d" % n_rail)

    # ---------------------------------------------------------------- 3. 계단 기둥(newel) 4
    newel = [o for o in OBJ if o["name"].startswith("P3 newel")]
    groups = []
    for o in newel:
        c = ((o["aabb_min"][0] + o["aabb_max"][0]) / 2, (o["aabb_min"][2] + o["aabb_max"][2]) / 2)
        g = next((g for g in groups if math.hypot(g["c"][0] - c[0], g["c"][1] - c[1]) < 40), None)
        if g is None:
            groups.append({"c": c, "lo": list(o["aabb_min"]), "hi": list(o["aabb_max"])})
        else:
            g["lo"] = [min(a, b) for a, b in zip(g["lo"], o["aabb_min"])]
            g["hi"] = [max(a, b) for a, b in zip(g["hi"], o["aabb_max"])]
    for i, g in enumerate(sorted(groups, key=lambda g: g["c"])):
        lo, hi = g["lo"], g["hi"]
        static.append(part("KGP_COL_NEWEL_%d" % i, [(a + b) / 2 for a, b in zip(lo, hi)],
                           [hi[0] - lo[0] + 4, hi[1] - lo[1], hi[2] - lo[2] + 4], 0.0))
    report.append("계단 기둥 %d" % len(groups))

    # ---------------------------------------------------------------- 4. 팀룸 문 옆 벽 · 인방 (좌우 3개씩)
    for side, xc in (("R", 102250.0), ("L", 99050.0)):
        static.append(part("KGP_COL_GATEWALL_%s_back" % side, (xc, 300.0, (-2800.0 - 2636.0) / 2),
                           (74.0, 600.0, 164.0), 0.0))
        static.append(part("KGP_COL_GATEWALL_%s_front" % side, (xc, 300.0, (-2304.0 - 2200.0) / 2),
                           (74.0, 600.0, 104.0), 0.0))
        static.append(part("KGP_COL_GATEWALL_%s_lintel" % side, (xc, (440.0 + 1200.0) / 2, -2500.0),
                           (46.0, 760.0, 600.0), 0.0))
    report.append("문 옆 벽·인방 6")

    # ---------------------------------------------------------------- 5. 문짝 충돌 4 (Movable)
    for lf in LEAVES:
        key = ("R" if lf["pos"][0] > 100650 else "L") + ("_back" if lf["pos"][2] < -2470 else "_front")
        movable.append(part("KGP2_Door_leaf_sapphire_COL_%s" % key, lf["pos"],
                            (lf["size"][0], lf["size"][1], 24.0), lf["yaw"], mobility="Movable"))
    report.append("문짝 충돌 %d (Movable)" % len(movable))

    # ---------------------------------------------------------------- 6. 분수 가운데
    fx, fz = FOUNTAIN
    static.append(part("KGP_COL_FOUNTAIN_core", (fx, 75.0, fz), (100.0, 150.0, 100.0), 0.0))
    static.append(part("KGP_COL_FOUNTAIN_spire", (fx, 380.0, fz), (60.0, 380.0, 60.0), 0.0))
    for i, yw in enumerate((0.0, 45.0, 90.0, 135.0)):
        static.append(part("KGP_COL_FOUNTAIN_bowl_lo_%d" % i, (fx, 169.0, fz), (284.0, 44.0, 118.0), yw))
    for i, yw in enumerate((0.0, 90.0)):
        static.append(part("KGP_COL_FOUNTAIN_bowl_up_%d" % i, (fx, 272.0, fz), (164.0, 40.0, 68.0), yw))
    report.append("분수 가운데 8")

    # ---------------------------------------------------------------- 7. 나머지 소품 — 안 덮인 점 군집
    decks = [c for c in COL if "DECK" in c["name"]]

    def over_deck(x, z):
        for c in decks:
            th = math.radians(c["rot"][1])
            dx, dz = x - c["pos"][0], z - c["pos"][2]
            lx = dx * math.cos(th) - dz * math.sin(th)
            lz = dx * math.sin(th) + dz * math.cos(th)
            if abs(lx) <= c["size"][0] / 2 + 60 and abs(lz) <= c["size"][2] / 2 + 60:
                return True
        return False

    CELL = 10.0
    for fl in ("1F", "2F"):
        cells = defaultdict(set)
        pts = defaultdict(list)
        for oi, o in enumerate(OBJ):
            u = o["uncovered"].get(fl)
            if not u or any(s in o["name"] for s in EXCL):
                continue
            for x, z in u["pts"]:
                if fl == "2F" and not over_deck(x, z):
                    continue
                k = (int(x // CELL), int(z // CELL))
                cells[k].add(oi)
                pts[k].append((x, z))
        seen, comps = set(), []
        for k in cells:
            if k in seen:
                continue
            stack, comp = [k], []
            seen.add(k)
            while stack:
                c = stack.pop()
                comp.append(c)
                for dx in (-2, -1, 0, 1, 2):
                    for dz in (-2, -1, 0, 1, 2):
                        n = (c[0] + dx, c[1] + dz)
                        if n in cells and n not in seen:
                            seen.add(n)
                            stack.append(n)
            comps.append(comp)
        made = 0
        for ci, comp in enumerate(sorted(comps, key=lambda c: min(c))):
            if len(comp) < 2:
                continue
            ois = set().union(*(cells[c] for c in comp))
            xz = [p for c in comp for p in pts[c]]
            cen, w, d, u = min_rect(xz, 6.0)
            lo = max(FLOOR[fl], min(OBJ[i]["aabb_min"][1] for i in ois))
            if lo < FLOOR[fl] + 30:
                lo = FLOOR[fl]
            hi = min(max(OBJ[i]["aabb_max"][1] for i in ois), FLOOR[fl] + 320.0)
            if hi - lo < 10:
                continue
            names = sorted({OBJ[i]["name"] for i in ois})
            tag = "".join(ch if ch.isalnum() else "_" for ch in names[0])[:28]
            nm = "KGP_COL_PROP_%s_%03d_%s" % (fl, made, tag)
            static.append(part(nm, (cen[0], (lo + hi) / 2, cen[1]), (w, hi - lo, d), yaw_for_axis(u[0], u[1])))
            made += 1
            flag = "  !!큼" if w * d > 40000 else ""
            report.append("%s  %4.0fx%4.0fx%4.0f  @(%6.0f,%5.0f,%6.0f)  %s%s" % (
                nm, w, hi - lo, d, cen[0], (lo + hi) / 2, cen[1], ", ".join(names)[:110], flag))
        report.append("== %s 소품 군집 %d" % (fl, made))

    # ---------------------------------------------------------------- 출력
    json.dump(stair_upd, io.open(os.path.join(HERE, "stair_update.json"), "w", encoding="utf-8"), indent=1)
    json.dump(movable, io.open(os.path.join(HERE, "items_movable.json"), "w", encoding="utf-8"), indent=1)
    for f in os.listdir(HERE):
        if f.startswith("items_static_"):
            os.remove(os.path.join(HERE, f))
    for k in range(0, len(static), 100):
        json.dump(static[k:k + 100], io.open(os.path.join(HERE, "items_static_%02d.json" % (k // 100)), "w",
                                             encoding="utf-8"), indent=1)
    report.insert(0, "새 Static %d · 새 Movable %d · 계단 제자리 %d" % (len(static), len(movable), len(stair_upd)))
    io.open(os.path.join(HERE, "gen_report.txt"), "w", encoding="utf-8").write("\n".join(report))
    draw(static, movable, stair_upd)
    print("\n".join(report[:12]))
    print("... (gen_report.txt)")


# -------------------------------------------------------------------- 평면도
PX = 4.0
BOUNDS = (97400.0, 103900.0, -2980.0, 2980.0)


def write_png(path, rgb):
    h, w, _ = rgb.shape
    raw = b"".join(b"\x00" + rgb[y].tobytes() for y in range(h))

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")
    open(path, "wb").write(png)


def fill_box(img, pos, size, yaw, colr, alpha):
    x0, x1, z0, z1 = BOUNDS
    H, W, _ = img.shape
    r = math.hypot(size[0], size[2]) / 2
    cmin = max(0, int((pos[0] - r - x0) / PX)); cmax = min(W - 1, int((pos[0] + r - x0) / PX))
    rmin = max(0, int((z1 - pos[2] - r) / PX)); rmax = min(H - 1, int((z1 - pos[2] + r) / PX))
    if cmin > cmax or rmin > rmax:
        return
    cc, rr = np.meshgrid(np.arange(cmin, cmax + 1), np.arange(rmin, rmax + 1))
    X = x0 + (cc + 0.5) * PX
    Z = z1 - (rr + 0.5) * PX
    th = math.radians(yaw)
    dx, dz = X - pos[0], Z - pos[2]
    lx = dx * math.cos(th) - dz * math.sin(th)
    lz = dx * math.sin(th) + dz * math.cos(th)
    m = (np.abs(lx) <= size[0] / 2) & (np.abs(lz) <= size[2] / 2)
    sub = img[rmin:rmax + 1, cmin:cmax + 1]
    sub[m] = (sub[m] * (1 - alpha) + np.array(colr) * alpha).astype(np.uint8)


def draw(static, movable, stair_upd):
    H = int((BOUNDS[3] - BOUNDS[2]) / PX) + 1
    W = int((BOUNDS[1] - BOUNDS[0]) / PX) + 1
    for fl, band in (("1F", (20, 250)), ("2F", (530, 760))):
        img = np.full((H, W, 3), 255, np.uint8)
        for c in COL:
            if c["name"].startswith("KGP_COL_STAIR_") or "SEAL" in c["name"] or "FLOOR" in c["name"]:
                continue
            if c["pos"][1] + c["size"][1] / 2 < band[0] or c["pos"][1] - c["size"][1] / 2 > band[1]:
                continue
            fill_box(img, c["pos"], c["size"], c["rot"][1], (120, 190, 255), 0.6)
        for s in stair_upd:
            if s["size"][1] >= band[0] - 150:
                fill_box(img, s["pos"], s["size"], s["yaw"], (255, 150, 40), 0.55)
        for it in static + movable:
            p = it["props"]
            if p["position"][1] + p["size"][1] / 2 < band[0] or p["position"][1] - p["size"][1] / 2 > band[1]:
                continue
            fill_box(img, p["position"], p["size"], p["orientation"][1],
                     (220, 40, 200) if p["mobility"] == "Movable" else (30, 170, 60), 0.7)
        write_png(os.path.join(HERE, "plan_new_%s.png" % fl), img)


main()
