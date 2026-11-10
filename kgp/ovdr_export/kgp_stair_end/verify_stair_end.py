# -*- coding: utf-8 -*-
"""계단 끝 장식 4개 확인 : 개수(중복 없음) · 위치 · yaw · 크기 · UnitExtent · TextureId · Mobility. 어긋나면 fix_rpc.json."""
import io, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
items = {i["name"]: i for i in json.load(io.open(os.path.join(HERE, "items_stair_end.json"), encoding="utf-8"))}
spec = {r["name"]: r for r in json.load(io.open(os.path.join(HERE, "place.json"), encoding="utf-8"))["rows"]}
s = open(r"C:\Work\onlyonetap\onlyoneshot.ovdrjm", "rb").read().decode("utf-16-le").lstrip("\ufeff")
d = json.loads(s)
def walk(n):
    yield n
    for c in n.get("LuaChildren", []) or []:
        yield from walk(c)
cont = next(n for n in walk(d["Root"]) if n.get("Name") == "KGP_GrandPalace")
fix = []
for name, it in items.items():
    cs = [c for c in cont["LuaChildren"] if c["Name"] == name]
    if len(cs) != 1:
        print(name, "count", len(cs)); continue
    c, p, r = cs[0], it["props"], spec[name]
    q, z, ue = c["CFrame"]["Position"], c["Size"], c.get("UnitExtent", {})
    yw = c["CFrame"]["Orientation"]["Y"]
    pos_ok = max(abs(q["X"] - p["position"][0]), abs(q["Y"] - p["position"][1]), abs(q["Z"] - p["position"][2])) < 0.6
    yaw_ok = abs(((yw - p["orientation"][1]) + 180) % 360 - 180) < 0.2
    size_ok = max(abs(z["X"] - p["size"][0]), abs(z["Y"] - p["size"][1]), abs(z["Z"] - p["size"][2])) < 0.6
    ue_ok = max(abs(abs(ue.get(k, 0)) - v) for k, v in zip("XYZ", r["native_half_cm"])) < 0.6
    print("%-26s pos %s yaw %s size %s unitExtent %s tex %s mob %s ds %s" % (
        name, pos_ok, yaw_ok, size_ok, ue_ok, c.get("TextureId") == p["raw"]["TextureId"], c.get("Mobility"), c.get("DoubleSided")))
    if not (pos_ok and yaw_ok):
        fix.append({"guid": c["ActorGuid"], "props": {"CFrame": {"ObjectType": "CFrame",
                    "Position": {"ObjectType": "Vector3", "X": p["position"][0], "Y": p["position"][1], "Z": p["position"][2]},
                    "Orientation": {"ObjectType": "Vector3", "X": 0, "Y": p["orientation"][1], "Z": 0}}}})
print("container children", len(cont["LuaChildren"]), "| fix needed", len(fix))
json.dump(fix, io.open(os.path.join(HERE, "fix_rpc.json"), "w", encoding="utf-8"), separators=(",", ":"))
