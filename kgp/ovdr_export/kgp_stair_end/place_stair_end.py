# -*- coding: utf-8 -*-
r"""계단 끝 마감 장식 배치.

  python place_stair_end.py snapshot   임포트 전 에셋 id 저장
  python place_stair_end.py build      임포트 후 : 새 메시 id 해석 → items_stair_end.json (create_instances 형식)
                                       + fix_rpc.json (CFrame 이 원점으로 떨어졌을 때 복구용)
텍스처는 게임에 있는 새 사파이어(46856300) · 금(46856100) 을 쓴다. 금 소용돌이는 커브에서 온 열린 면이 있어 DoubleSided.
"""
import io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TBL = r"C:\Work\onlyonetap\UGCLocalAssetTable.json"
TEX = {"Sapphire stone": "46856300", "Antique gilded bronze": "46856100"}


def table():
    raw = open(TBL, "rb").read()
    txt = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8", "ignore")
    return json.loads(txt)["localAssetList"]


def main(mode):
    t = table()
    if mode == "snapshot":
        json.dump({"ids": sorted(t)}, io.open(os.path.join(HERE, "assets_before_stair_end.json"), "w", encoding="utf-8"))
        print("snapshot", len(t))
        return
    before = set(json.load(io.open(os.path.join(HERE, "assets_before_stair_end.json"), encoding="utf-8"))["ids"])
    spec = json.load(io.open(os.path.join(HERE, "place.json"), encoding="utf-8"))
    found = {}
    for cid, v in t.items():
        if cid in before or v.get("worldAssetType") != "STATIC_MESH":
            continue
        m = re.search(r"(KGP3EM\d{4})", v.get("name", ""))
        if m:
            found.setdefault(m.group(1), []).append((v.get("createdTime", ""), cid))
    items = []
    for r in spec["rows"]:
        if r["mesh"] not in found:
            raise SystemExit("!! 새 메시 못 찾음: " + r["mesh"])
        mid = max(found[r["mesh"]])[1]
        items.append({"className": "MeshPart", "name": r["name"], "props": {
            "meshId": "ovdrassetid://" + mid, "position": r["engine_pos"], "orientation": [0.0, r["yaw_deg"], 0.0],
            "size": r["size_cm"], "anchored": True, "castShadow": True, "canCollide": False, "canQuery": False,
            "canTouch": False, "locked": False, "mobility": "Static", "material": "Basic", "color": [200, 200, 200],
            "raw": {"TextureId": "ovdrassetid://" + TEX[r["mat"]], "DoubleSided": r["kind"] == "gold"}}})
        print("  %-28s %s -> %s" % (r["name"], r["mesh"], mid))
    io.open(os.path.join(HERE, "items_stair_end.json"), "w", encoding="utf-8").write(json.dumps(items, indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "build")
