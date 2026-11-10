# -*- coding: utf-8 -*-
r"""scene_v3.json + meshids_v3.json -> OVERDARE 배치 JSON.

v3 재질 규약 — 다른 맵 세 개(화성·산곡·크렘린실내)와 같아졌다:
  * 22개 재질 전부 실제 타일 텍스처를 갖는다. 그래서 전부 Material "Basic" +
    Color(200,200,200) + TextureId 로 나간다. v2 는 텍스처가 2개뿐이라 나머지를
    엔진 재질(Marble/Metal/...) + 단색으로 때웠고, 그게 "다 대리석 같다"의 원인이었다.
  * 투명도는 유리·물에만 남긴다. TextureId 는 Color 를 덮지만 Transparency 는 안 덮는다.
  * DoubleSided 는 두께가 아니라 '열린 메시'로 판단한다(아래 주석 참고).

사용:  python kgp_place_v3.py
출력:  items_v3_00.json ...
"""
import io, json, os, collections

OPEN = {}

HERE = os.path.dirname(os.path.abspath(__file__))
CHUNK = 200                       # overdare_create_instances itemsFile 한도
NAME_PREFIX = "KGP3_"             # 옛 v1 파츠와 이름이 겹치지 않게

# 재질 -> (엔진 재질, 투명도). 색은 블렌더에서 잰 값을 그대로 쓴다.
MAT = {
    "Antique gilded bronze":   ("Metal",   0.0),
    "Ivory marble":            ("Marble",  0.0),
    "Sapphire stone":          ("Marble",  0.0),
    "Blue grey marble":        ("Marble",  0.0),
    "P3 pale marble tile":     ("Marble",  0.0),
    "Palace mirror":           ("Metal",   0.0),
    "Wrought iron":            ("Metal",   0.0),
    "Pale azure glazing":      ("Glass",   0.35),
    "P3 window daylight glass":("Glass",   0.50),
    "Royal blue velvet":       ("Plastic", 0.0),   # Fabric 은 엔진에 없다
    "P3 topiary green":        ("Plastic", 0.0),
    "P3 berry red":            ("Plastic", 0.0),
    "P3 cake lavender icing":  ("Plastic", 0.0),
    "P3 porcelain white":      ("Marble",  0.0),
    "Candle light":            ("Neon",    0.0),
    "P3 skylight sky":         ("Neon",    0.0),
    "P7 water basin":          ("Glass",   0.40),
    "P7 water lower bowl":     ("Glass",   0.40),
    "P7 water upper bowl":     ("Glass",   0.40),
    "P7 water overflow sheet": ("Glass",   0.62),
    "nomat":                   ("Neon",    0.45),   # 분수 제트 + 물방울
}
WATER_COLOUR = {
    "P7 water basin": [140, 210, 235], "P7 water lower bowl": [140, 210, 235],
    "P7 water upper bowl": [140, 210, 235], "P7 water overflow sheet": [205, 238, 250],
    "nomat": [214, 242, 255],
}
# 스크립트가 이름으로 붙잡는 것들. 이름을 고정해 둔다.
ROLE = {
    "P7_fountain_water_streams_GN":  "KGP3_WATER_jet",
    "P7_water_basin_body":           "KGP3_WATER_basin",
    "P7_water_lower_bowl_body":      "KGP3_WATER_lower",
    "P7_water_upper_bowl_body":      "KGP3_WATER_upper",
    "P7_water_overflow_sheet_lower": "KGP3_WATER_film_lo",
    "P7_water_overflow_sheet_upper": "KGP3_WATER_film_up",
}
MOVABLE = set(ROLE.values())


def main():
    sc = json.load(io.open(os.path.join(HERE, "scene_v3.json"), encoding="utf-8"))
    global OPEN
    OPEN = {r["obj"]: r["open_edges"]
            for r in json.load(io.open(os.path.join(HERE, "_mesh_openness.json"), encoding="utf-8"))}
    ids = {r["mesh"]: r for r in json.load(io.open(os.path.join(HERE, "meshids_v3.json"), encoding="utf-8"))}

    items, missing, seen = [], [], collections.Counter()
    for i in sc["instances"]:
        rec = ids.get(i["mesh"])
        if not rec:
            missing.append(i["mesh"])
            continue
        mat = i["mat"]
        emat, transp = MAT.get(mat, ("Basic", 0.0))
        colour = i["colour"]
        tex = rec.get("textureId")
        if tex:                                   # 텍스처가 있으면 house 규약대로
            emat, colour = "Basic", [200, 200, 200]
        colour = WATER_COLOUR.get(mat, colour)

        nm = ROLE.get(i["name"])
        if not nm:
            nm = NAME_PREFIX + i["name"]
            seen[nm] += 1
            if seen[nm] > 1:                      # 같은 이름이 또 나오면 번호를 붙인다
                nm = "%s_%02d" % (nm, seen[nm])
        props = {
            "meshId": "ovdrassetid://" + str(rec["meshId"]),
            "material": emat, "color": colour,
            "position": i["engine_pos"], "orientation": [0.0, i["yaw_deg"], 0.0],
            "size": i["size_cm"],
            "anchored": True,
            "mobility": "Movable" if nm in MOVABLE else "Static",
            "castShadow": True,
            "canCollide": False, "canQuery": False, "canTouch": False, "locked": False,
        }
        if transp:
            props["transparency"] = transp
        raw = {}
        if tex:
            raw["TextureId"] = "ovdrassetid://" + str(tex)
        if OPEN.get(i.get("obj"), 0) > 0 or min(i["size_cm"]) <= 2.0:
            # ★ v2 는 '두께 2cm 이하'만 양면으로 했다. 그래서 천장이 뚫려 보였다 :
            #   천장판·돔은 30~100cm 두께인데 아랫면이 아예 없는 껍데기(경계 엣지 592개)라
            #   엔진이 뒷면을 잘라내면 그대로 하늘이 보인다. 열린 메시는 전부 양면으로 낸다.
            raw["DoubleSided"] = True
        if raw:
            props["raw"] = raw
        items.append({"className": "MeshPart", "name": nm, "props": props})

    out = []
    for k in range(0, len(items), CHUNK):
        p = os.path.join(HERE, "items_v3_%02d.json" % (k // CHUNK))
        json.dump(items[k:k + CHUNK], io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        out.append((os.path.basename(p), len(items[k:k + CHUNK])))
    for nm, n in out:
        print("%-22s %4d" % (nm, n))
    print("총 %d개 · 이름 중복 %d · 메시 없음 %d"
          % (len(items), sum(v - 1 for v in seen.values() if v > 1), len(missing)))
    print("Movable(물) %d · 텍스처 %d · 반투명 %d · DoubleSided %d"
          % (sum(1 for i in items if i["props"]["mobility"] == "Movable"),
             sum(1 for i in items if i["props"].get("raw", {}).get("TextureId")),
             sum(1 for i in items if "transparency" in i["props"]),
             sum(1 for i in items if i["props"].get("raw", {}).get("DoubleSided"))))
    if missing:
        print("!! 메시 못 찾음:", missing[:5])


if __name__ == "__main__":
    main()
