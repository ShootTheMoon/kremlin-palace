# -*- coding: utf-8 -*-
"""충돌 보강 전수 대조 : 저장 파일 vs items_static_* / items_movable / stair_update. 어긋난 것은 fix_phys.json 로."""
import io, json, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
P = r"C:\Work\onlyonetap\onlyoneshot.ovdrjm"
items = []
for f in sorted(os.listdir(HERE)):
    if f.startswith("items_static_") or f == "items_movable.json":
        items += json.load(io.open(os.path.join(HERE, f), encoding="utf-8"))
stair = json.load(io.open(os.path.join(HERE, "stair_update.json"), encoding="utf-8"))

s = open(P, "rb").read().decode("utf-16-le").lstrip("\ufeff")
d = json.loads(s)
def walk(n):
    yield n
    for c in n.get("LuaChildren", []) or []:
        yield from walk(c)
cont = next(n for n in walk(d["Root"]) if n.get("Name") == "KGP_GrandPalace")
byname = collections.defaultdict(list)
byguid = {}
for c in cont["LuaChildren"]:
    byname[c["Name"]].append(c)
    byguid[c["ActorGuid"]] = c

def yawdiff(a, b):
    return abs(((a - b) + 180) % 360 - 180)

bad = collections.defaultdict(list)
fix = []
for it in items:
    p = it["props"]
    cs = byname.get(it["name"], [])
    if not cs:
        bad["missing"].append(it["name"]); continue
    if len(cs) > 1:
        bad["duplicate"].append(it["name"])
    c = cs[-1]
    q = c["CFrame"]["Position"]; z = c["Size"]; yw = c["CFrame"]["Orientation"]["Y"]
    if max(abs(q["X"] - p["position"][0]), abs(q["Y"] - p["position"][1]), abs(q["Z"] - p["position"][2])) > 0.6 \
            or yawdiff(yw, p["orientation"][1]) > 0.2:
        bad["cframe"].append(it["name"])
        fix.append({"guid": c["ActorGuid"], "props": {"CFrame": {"ObjectType": "CFrame",
                    "Position": {"ObjectType": "Vector3", "X": p["position"][0], "Y": p["position"][1], "Z": p["position"][2]},
                    "Orientation": {"ObjectType": "Vector3", "X": 0, "Y": p["orientation"][1], "Z": 0}}}})
    if max(abs(z["X"] - p["size"][0]), abs(z["Y"] - p["size"][1]), abs(z["Z"] - p["size"][2])) > 0.6:
        bad["size"].append((it["name"], z, p["size"]))
    if c.get("Shape") != "Block": bad["shape"].append((it["name"], c.get("Shape")))
    if not c.get("CanCollide"): bad["cancollide"].append(it["name"])
    if c.get("Transparency") != 1: bad["transparency"].append(it["name"])
    if str(c.get("Mobility")) != p["mobility"]: bad["mobility"].append((it["name"], c.get("Mobility")))
for u in stair:
    c = byguid.get(u["guid"])
    q = c["CFrame"]["Position"]; z = c["Size"]; yw = c["CFrame"]["Orientation"]["Y"]
    if max(abs(q["X"] - u["pos"][0]), abs(q["Y"] - u["pos"][1]), abs(q["Z"] - u["pos"][2])) > 0.6 \
            or yawdiff(yw, u["yaw"]) > 0.2 or max(abs(z["X"] - u["size"][0]), abs(z["Y"] - u["size"][1]), abs(z["Z"] - u["size"][2])) > 0.6:
        bad["stair"].append(u["name"])
print("new parts %d | present %d" % (len(items), sum(1 for it in items if it["name"] in byname)))
for k in ("missing", "duplicate", "cframe", "size", "shape", "cancollide", "transparency", "mobility", "stair"):
    print("  %-12s %d  %s" % (k, len(bad[k]), bad[k][:3]))
print("container children:", len(cont["LuaChildren"]),
      "| collision parts:", sum(1 for c in cont["LuaChildren"] if c["InstanceType"] == "Part" and c.get("CanCollide")))
json.dump(fix, io.open(os.path.join(HERE, "fix_phys.json"), "w", encoding="utf-8"), separators=(",", ":"))
