# -*- coding: utf-8 -*-
r"""떠 있는 판 제거본(KGP3S_fix_00.fbx) 교체.

  python swap_stray.py snapshot   임포트 전 에셋 id 저장
  python swap_stray.py build      임포트 후 : 새 메시 id 해석 → swap_stray_rpc.json (MeshId·CFrame·Size, 제자리)
"""
import io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TBL = r"C:\Work\onlyonetap\UGCLocalAssetTable.json"
PRJ = r"C:\Work\onlyonetap\onlyoneshot.ovdrjm"
STAMP = re.compile(r"_\d{14}$")


def table():
    raw = open(TBL, "rb").read()
    txt = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8", "ignore")
    return json.loads(txt)["localAssetList"]


def main(mode):
    t = table()
    if mode == "snapshot":
        json.dump({"ids": sorted(t)}, io.open(os.path.join(HERE, "assets_before_stray.json"), "w", encoding="utf-8"))
        print("snapshot", len(t))
        return
    before = set(json.load(io.open(os.path.join(HERE, "assets_before_stray.json"), encoding="utf-8"))["ids"])
    spec = json.load(io.open(os.path.join(HERE, "fix_stray.json"), encoding="utf-8"))
    found = {}
    for cid, v in t.items():
        if cid in before or v.get("worldAssetType") != "STATIC_MESH":
            continue
        m = re.search(r"(KGP3SM\d{4})", v.get("name", ""))
        if m:
            found.setdefault(m.group(1), []).append((v.get("createdTime", ""), cid))
    s = open(PRJ, "rb").read().decode("utf-16-le").lstrip("\ufeff")
    d = json.loads(s)

    def walk(n):
        yield n
        for c in n.get("LuaChildren", []) or []:
            yield from walk(c)
    cont = next(n for n in walk(d["Root"]) if n.get("Name") == "KGP_GrandPalace")
    live = {c["Name"]: c for c in cont["LuaChildren"]}
    V = lambda a: {"ObjectType": "Vector3", "X": a[0], "Y": a[1], "Z": a[2]}
    out = []
    for r in spec["rows"]:
        if r["mesh"] not in found:
            raise SystemExit("!! 새 메시 못 찾음: " + r["mesh"])
        mid = max(found[r["mesh"]])[1]
        c = live[r["part"]]
        out.append({"guid": c["ActorGuid"], "props": {
            "MeshId": "ovdrassetid://" + mid,
            "CFrame": {"ObjectType": "CFrame", "Position": V(r["engine_pos"]), "Orientation": V([0, r["yaw_deg"], 0])},
            "Size": V(r["size_cm"])}})
        print("  %-44s %s -> %s  (%d건)" % (r["part"], c.get("MeshId"), mid, len(found[r["mesh"]])))
    json.dump(out, io.open(os.path.join(HERE, "swap_stray_rpc.json"), "w", encoding="utf-8"), separators=(",", ":"))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "build")
