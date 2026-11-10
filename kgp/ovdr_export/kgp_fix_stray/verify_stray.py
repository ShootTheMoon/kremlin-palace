# -*- coding: utf-8 -*-
"""교체 확인 : MeshId · 위치 · 크기 · UnitExtent(엔진이 잰 메시 반폭 = 파일 반폭) · TextureId 유지."""
import io, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = {r["part"]: r for r in json.load(io.open(os.path.join(HERE, "fix_stray.json"), encoding="utf-8"))["rows"]}
rpc = {u["guid"]: u for u in json.load(io.open(os.path.join(HERE, "swap_stray_rpc.json"), encoding="utf-8"))}
s = open(r"C:\Work\onlyonetap\onlyoneshot.ovdrjm", "rb").read().decode("utf-16-le").lstrip("\ufeff")
d = json.loads(s)
def walk(n):
    yield n
    for c in n.get("LuaChildren", []) or []:
        yield from walk(c)
cont = next(n for n in walk(d["Root"]) if n.get("Name") == "KGP_GrandPalace")
for c in cont["LuaChildren"]:
    if c["Name"] in spec:
        r, u = spec[c["Name"]], rpc[c["ActorGuid"]]
        p, z, ue = c["CFrame"]["Position"], c["Size"], c.get("UnitExtent", {})
        ok_mesh = c["MeshId"] == u["props"]["MeshId"]
        ok_pos = max(abs(p["X"] - r["engine_pos"][0]), abs(p["Y"] - r["engine_pos"][1]), abs(p["Z"] - r["engine_pos"][2])) < 0.6
        ok_size = max(abs(z["X"] - r["size_cm"][0]), abs(z["Y"] - r["size_cm"][1]), abs(z["Z"] - r["size_cm"][2])) < 0.6
        ue3 = [abs(ue.get(k, 0)) for k in "XYZ"]
        ok_ue = max(abs(a - b) for a, b in zip(ue3, r["native_half_cm"])) < 0.6
        print(c["Name"], "mesh", ok_mesh, "pos", ok_pos, "size", ok_size, "unitExtent", ok_ue, ue3,
              "tex", c.get("TextureId"), "ds", c.get("DoubleSided"))
