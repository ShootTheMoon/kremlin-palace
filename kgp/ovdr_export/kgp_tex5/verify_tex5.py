# -*- coding: utf-8 -*-
"""저장 파일에서 교체 결과 전수 확인 : 옛 KGPTEX3_ 4종 id 를 쓰는 파츠 0, 새 id 를 쓰는 파츠 = 1,709."""
import io, json, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
plan = json.load(io.open(os.path.join(HERE, "swap_tex5_plan.json"), encoding="utf-8"))
old = set(plan["map"])
new = {"ovdrassetid://" + v: k for k, v in plan["pick"].items()}
s = open(r"C:\Work\onlyonetap\onlyoneshot.ovdrjm", "rb").read().decode("utf-16-le").lstrip("\ufeff")
d = json.loads(s)
def walk(n):
    yield n
    for c in n.get("LuaChildren", []) or []:
        yield from walk(c)
cont = next(n for n in walk(d["Root"]) if n.get("Name") == "KGP_GrandPalace")
mp = [c for c in cont["LuaChildren"] if c["InstanceType"] == "MeshPart"]
c_old = sum(1 for c in mp if c.get("TextureId") in old)
c_new = collections.Counter(new[c["TextureId"]] for c in mp if c.get("TextureId") in new)
print("MeshParts %d | still old %d | new %d %s" % (len(mp), c_old, sum(c_new.values()), dict(c_new)))
print("container children", len(cont["LuaChildren"]))
