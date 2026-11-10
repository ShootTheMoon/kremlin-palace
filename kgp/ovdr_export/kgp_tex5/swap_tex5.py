# -*- coding: utf-8 -*-
r"""라운드 5 텍스처 교체표 만들기.

  python swap_tex5.py snapshot   임포트 전 에셋 id 목록 저장 (assets_before_tex5.json)
  python swap_tex5.py build      임포트 후 : 새 KGPTEX5_* 텍스처 id 를 찾고,
                                 옛 KGPTEX3_<같은 재질> 텍스처를 쓰는 파츠 전부의 TextureId 교체표를 만든다
                                 -> swap_tex5_NN.json (100개씩, overdare_instance_update 형식)

옛 텍스처는 FBX 마다 따로 올라가 같은 재질이라도 id 가 여러 개다 → 이름으로 전부 모은다.
"""
import io
import json
import os
import re
import sys
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
TBL = r"C:\Work\onlyonetap\UGCLocalAssetTable.json"
PRJ = r"C:\Work\onlyonetap\onlyoneshot.ovdrjm"
MATS = ["Antique_gilded_bronze", "Sapphire_stone", "Ivory_marble", "Blue_grey_marble"]
STAMP = re.compile(r"_\d{14}$")


def table():
    raw = open(TBL, "rb").read()
    txt = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8", "ignore")
    return json.loads(txt)["localAssetList"]


def main(mode):
    t = table()
    if mode == "snapshot":
        json.dump({"ids": sorted(t)}, io.open(os.path.join(HERE, "assets_before_tex5.json"), "w", encoding="utf-8"))
        print("snapshot", len(t))
        return
    before = set(json.load(io.open(os.path.join(HERE, "assets_before_tex5.json"), encoding="utf-8"))["ids"])
    new, old = {}, collections.defaultdict(set)
    for cid, v in t.items():
        if v.get("worldAssetType") != "TEXTURE":
            continue
        nm = STAMP.sub("", v.get("name", ""))
        for m in MATS:
            if nm == "KGPTEX5_" + m and cid not in before:
                new.setdefault(m, []).append((v.get("createdTime", ""), cid))
            elif nm == "KGPTEX3_" + m:
                old[m].add(cid)
    missing = [m for m in MATS if m not in new]
    for m in MATS:
        print("  %-24s new %-22s old ids %d" % (m, [c for _, c in sorted(new.get(m, []))], len(old[m])))
    if missing:
        print("!! 새 텍스처를 못 찾음:", missing)
        sys.exit(1)
    pick = {m: max(new[m])[1] for m in MATS}
    to_new = {("ovdrassetid://" + c): "ovdrassetid://" + pick[m] for m in MATS for c in old[m]}

    s = open(PRJ, "rb").read().decode("utf-16-le").lstrip("\ufeff")
    d = json.loads(s)

    def walk(n):
        yield n
        for c in n.get("LuaChildren", []) or []:
            yield from walk(c)
    cont = next(n for n in walk(d["Root"]) if n.get("Name") == "KGP_GrandPalace")
    upd, per = [], collections.Counter()
    for c in cont["LuaChildren"]:
        if c.get("InstanceType") == "MeshPart" and c.get("TextureId") in to_new:
            upd.append({"guid": c["ActorGuid"], "props": {"TextureId": to_new[c["TextureId"]]}})
            per[c["TextureId"]] += 1
    for f in os.listdir(HERE):
        if f.startswith("swap_tex5_") and f.endswith(".json"):
            os.remove(os.path.join(HERE, f))
    for k in range(0, len(upd), 100):
        io.open(os.path.join(HERE, "swap_tex5_%02d.json" % (k // 100)), "w", encoding="utf-8").write(
            json.dumps(upd[k:k + 100], separators=(",", ":")))
    json.dump({"pick": pick, "map": to_new, "count": len(upd)},
              io.open(os.path.join(HERE, "swap_tex5_plan.json"), "w", encoding="utf-8"), indent=1)
    print("교체 대상 파츠 %d · 묶음 %d" % (len(upd), (len(upd) + 99) // 100))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "build")
