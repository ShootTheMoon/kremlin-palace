# -*- coding: utf-8 -*-
"""대궁전 2차 콜리전(물리) + 천장 마감 + 팀룸 문짝 아이템 생성."""
import io, json, os, collections

BASE = r"C:\Work\blender\ovdr_export\kremlin_grand_palace_v1"
d = json.load(io.open(os.path.join(BASE, "scene_dump.json"), encoding="utf-8"))
DX = 100650.0 - d["x0_cm"]          # 옛 크렘린 자리로 옮긴 만큼

def part(name, pos, size, yaw=0.0, **kw):
    p = {"position": [round(v, 1) for v in pos], "size": [round(v, 1) for v in size],
         "orientation": [0.0, round(yaw, 1), 0.0], "shape": "Block",
         "anchored": True, "mobility": "Static", "transparency": 1,
         "canCollide": True, "canQuery": True, "canTouch": False,
         "castShadow": False, "locked": True, "material": "Plastic"}
    p.update(kw)
    return {"className": "Part", "name": name, "props": p}

phys = []

# ── 기둥 40개. 주두 위치가 곧 기둥 축이다. 바닥부터 주두 밑까지 세운다.
cols = sorted(set((round(i["engine_pos"][0] + DX, 1), round(i["engine_pos"][2], 1),
                   round(i["engine_pos"][1], 1))
                  for i in d["instances"] if "acanthus" in i["master"]))
for n, (x, z, ytop) in enumerate(cols):
    h = ytop - 25.0                      # 주두 밑까지
    phys.append(part("KGP_COL_COLUMN_%02d" % n, [x, h / 2.0, z], [92, h, 92]))

# ── 기사상 18개 · 의자 64개. 마스터 크기를 그대로 상자로 쓴다.
def inst_boxes(master, tag, shrink=1.0):
    m = d["masters"][master]
    out = []
    for n, i in enumerate(x for x in d["instances"] if x["master"] == master):
        sc = i.get("scale", 1.0) * shrink
        s = [m["size_cm"][0] * sc, m["size_cm"][1] * i.get("scale", 1.0), m["size_cm"][2] * sc]
        p = i["engine_pos"]
        out.append(part("KGP_COL_%s_%02d" % (tag, n), [p[0] + DX, p[1], p[2]], s, i["yaw_deg"]))
    return out

phys += inst_boxes("KGP_M_GEN_knight_armor_LOD", "KNIGHT")
phys += inst_boxes("KGP_M_GEN_rococo_armchair_LOD", "CHAIR", 0.9)

# ── 티테이블. 의자 4개가 한 세트다. 세트 중심에 상판을 놓는다.
chairs = [i for i in d["instances"] if "armchair" in i["master"]]
groups, used = [], set()
for a in chairs:
    if id(a) in used:
        continue
    g = [a]; used.add(id(a))
    for b in chairs:
        if id(b) in used:
            continue
        if abs(b["engine_pos"][1] - a["engine_pos"][1]) < 5 and \
           (b["engine_pos"][0] - a["engine_pos"][0]) ** 2 + (b["engine_pos"][2] - a["engine_pos"][2]) ** 2 < 260 ** 2:
            g.append(b); used.add(id(b))
    groups.append(g)
for n, g in enumerate(groups):
    cx = sum(i["engine_pos"][0] for i in g) / len(g) + DX
    cz = sum(i["engine_pos"][2] for i in g) / len(g)
    base = min(i["engine_pos"][1] for i in g) - 56.0     # 의자 밑 = 바닥
    phys.append(part("KGP_COL_TEATABLE_%02d" % n, [cx, base + 38, cz], [150, 76, 150]))

# ── 2층 난간. 갤러리 데크에서 떨어지지 않게 안쪽 모서리를 막는다.
RAIL_H, RAIL_Y = 115.0, 512.0 + 57.5
phys += [
    part("KGP_COL_RAIL_gallery_R", [101790, RAIL_Y, 120], [22, RAIL_H, 4680]),
    part("KGP_COL_RAIL_gallery_L", [99510, RAIL_Y, 120], [22, RAIL_H, 4680]),
    part("KGP_COL_RAIL_balcony_R", [101620, RAIL_Y, 2460], [1260, RAIL_H, 22]),
    part("KGP_COL_RAIL_balcony_L", [99680, RAIL_Y, 2460], [1260, RAIL_H, 22]),
    # 계단참 앞. 가운데는 다리가 붙는 자리라 비워 둔다.
    part("KGP_COL_RAIL_landing_R", [101425, RAIL_Y, -2220], [750, RAIL_H, 22]),
    part("KGP_COL_RAIL_landing_L", [99875, RAIL_Y, -2220], [750, RAIL_H, 22]),
]

# ── 천장 마감. 지붕 구조 위에 한 장 덮어 하늘이 새지 않게 한다(충돌은 밀폐 상자가 맡는다).
caps = [
    part("KGP_CAP_Ceiling_hall", [100650, 1530, 0], [3320, 40, 5720],
         transparency=0, canCollide=False, canQuery=False, material="Basic",
         color=[181, 187, 199]),
    part("KGP_CAP_Ceiling_wing_R", [102950, 625, -2500], [1440, 40, 640],
         transparency=0, canCollide=False, canQuery=False, material="Basic",
         color=[181, 187, 199]),
    part("KGP_CAP_Ceiling_wing_L", [98350, 625, -2500], [1440, 40, 640],
         transparency=0, canCollide=False, canQuery=False, material="Basic",
         color=[181, 187, 199]),
]

# ── 팀룸 문짝. 홀↔복도 통로(폭 600 · 높이 600)를 두 짝으로 막는다.
#    경기 시작 전 닫혀 있다가 KgpGateServer 가 방 안쪽으로 90도 연다.
DOOR = dict(transparency=0, canCollide=True, canQuery=True, mobility="Movable",
            material="Wood", color=[226, 216, 196], castShadow=False, locked=False)
doors = [
    part("KGP_GATE_R_front", [102250, 297, -2350], [26, 570, 300], **DOOR),
    part("KGP_GATE_R_outer", [102250, 297, -2650], [26, 570, 300], **DOOR),
    part("KGP_GATE_L_front", [99050, 297, -2350], [26, 570, 300], **DOOR),
    part("KGP_GATE_L_outer", [99050, 297, -2650], [26, 570, 300], **DOOR),
]

CH = 45
made = []
for i in range(0, len(phys), CH):
    p = os.path.join(BASE, "_chunks", "phys_%02d.json" % (i // CH))
    json.dump(phys[i:i + CH], io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    made.append((os.path.basename(p), len(phys[i:i + CH])))
json.dump(caps + doors, io.open(os.path.join(BASE, "items_fix_00.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

kinds = collections.Counter(p["name"].split("_")[2] for p in phys)
print("물리 파츠 %d개 : %s" % (len(phys), dict(kinds)))
for nm, n in made:
    print("   ", nm, n)
print("천장 마감 %d · 문짝 %d -> items_fix_00.json" % (len(caps), len(doors)))
