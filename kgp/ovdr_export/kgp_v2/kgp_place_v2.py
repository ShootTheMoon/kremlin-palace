# -*- coding: utf-8 -*-
r"""scene_v2.json + meshids_v2.json -> OVERDARE 배치 JSON.

재질 규약 (2026-09-17 결정):
  * 절차 재질 20개는 텍스처를 안 붙인다. TextureId 가 Color 를 덮어써서 색 조정이 안 먹히기 때문이다.
    대신 Color + 엔진 재질(Marble/Metal/Glass/Neon)로 간다. 화성도 텍스처 없는 파일을 이렇게 칠했다.
  * 실제 텍스처가 있는 생성 소품 2개만 Material "Basic" + Color(200,200,200) + TextureId.
    (산곡·화성·크렘린실내 세 맵이 텍스처 붙은 파츠에 쓰는 값 그대로다.)
  * 색을 바꾸려면 이 표만 고쳐 다시 돌리면 된다. 재임포트가 필요 없다.

사용:  python kgp_place_v2.py
출력:  items_v2_00.json ...
"""
import io, json, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
CHUNK = 200                       # overdare_create_instances itemsFile 한도
NAME_PREFIX = "KGP2_"             # 옛 v1 파츠와 이름이 겹치지 않게

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
    "P7_fountain_water_streams_GN":  "KGP2_WATER_jet",
    "P7_water_basin_body":           "KGP2_WATER_basin",
    "P7_water_lower_bowl_body":      "KGP2_WATER_lower",
    "P7_water_upper_bowl_body":      "KGP2_WATER_upper",
    "P7_water_overflow_sheet_lower": "KGP2_WATER_film_lo",
    "P7_water_overflow_sheet_upper": "KGP2_WATER_film_up",
}
MOVABLE = set(ROLE.values())


def main():
    sc = json.load(io.open(os.path.join(HERE, "scene_v2.json"), encoding="utf-8"))
    ids = {r["mesh"]: r for r in json.load(io.open(os.path.join(HERE, "meshids_v2.json"), encoding="utf-8"))}

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
        if min(i["size_cm"]) <= 2.0:              # 판형은 뒷면이 잘려 안 보인다
            raw["DoubleSided"] = True
        if raw:
            props["raw"] = raw
        items.append({"className": "MeshPart", "name": nm, "props": props})

    out = []
    for k in range(0, len(items), CHUNK):
        p = os.path.join(HERE, "items_v2_%02d.json" % (k // CHUNK))
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
