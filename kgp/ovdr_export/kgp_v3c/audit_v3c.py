# -*- coding: utf-8 -*-
"""v3c 부은 뒤 전수 대조 : 저장된 .ovdrjm 을 파싱해 items / retex 와 비교.
출력 : 항목별 불일치 수 + cframe_fix_v3c.json (위치·방향이 날아간 파츠의 CFrame 복구 목록)
"""
import io, json, os, collections, math

HERE = os.path.dirname(os.path.abspath(__file__))
P = r"C:\Work\onlyonetap\onlyoneshot.ovdrjm"
sc = json.load(io.open(os.path.join(HERE, "scene_v3c.json"), encoding="utf-8"))
inst = {i["name"]: i for i in sc["instances"]}
items = []
for k in range(10):
    f = os.path.join(HERE, "items_v3c_%02d.json" % k)
    if os.path.exists(f):
        items += json.load(io.open(f, encoding="utf-8"))
retex = json.load(io.open(os.path.join(HERE, "retex_update.json"), encoding="utf-8"))

s = open(P, "rb").read().decode("utf-16-le")
if s[0] == "\ufeff":
    s = s[1:]
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
    byguid[c.get("ActorGuid")] = c

bad = collections.defaultdict(list)
fix = []
for it in items:
    name, p = it["name"], it["props"]
    cs = byname.get(name, [])
    if not cs:
        bad["missing"].append(name); continue
    if len(cs) > 1:
        bad["duplicate"].append(name)
    c = cs[-1]
    q = c["CFrame"]["Position"]; z = c["Size"]; u = c.get("UnitExtent", {})
    pos_bad = max(abs(q["X"] - p["position"][0]), abs(q["Y"] - p["position"][1]), abs(q["Z"] - p["position"][2])) > 0.6
    yaw_bad = abs(((c["CFrame"]["Orientation"]["Y"] - p["orientation"][1]) + 180) % 360 - 180) > 0.2
    if pos_bad: bad["pos"].append(name)
    if yaw_bad: bad["yaw"].append(name)
    if pos_bad or yaw_bad:
        fix.append({"guid": c["ActorGuid"], "name": name, "position": p["position"], "yaw": p["orientation"][1]})
    if max(abs(z["X"] - p["size"][0]), abs(z["Y"] - p["size"][1]), abs(z["Z"] - p["size"][2])) > 0.6:
        bad["size"].append(name)
    n = inst[name]["native_half_cm"]
    ue = (abs(u.get("X", 0)), abs(u.get("Y", 0)), abs(u.get("Z", 0)))
    if max(abs(ue[i] - n[i]) / max(n[i], 1.0) for i in range(3)) > 0.02:
        bad["unitextent"].append((name, ue, n))
    if c.get("MeshId") != p["meshId"]: bad["mesh"].append(name)
    tid = p.get("raw", {}).get("TextureId")
    if tid and c.get("TextureId") != tid: bad["texture"].append(name)
    if not c.get("DoubleSided"): bad["doublesided"].append(name)
    want_mob = p["mobility"]
    if c.get("Mobility") not in (None, want_mob) and str(c.get("Mobility")).split(".")[-1] != want_mob:
        bad["mobility"].append((name, c.get("Mobility")))

for r in retex:
    c = byguid.get(r["guid"])
    if c is None:
        bad["retex_missing"].append(r["guid"]); continue
    if c.get("MeshId") != r["props"]["MeshId"] or c.get("TextureId") != r["props"]["TextureId"]:
        bad["retex"].append(c["Name"])
    n = next(i["native_half_cm"] for i in sc["instances"] if i["name"] == c["Name"])
    u = c.get("UnitExtent", {})
    ue = (abs(u.get("X", 0)), abs(u.get("Y", 0)), abs(u.get("Z", 0)))
    if max(abs(ue[i] - n[i]) / max(n[i], 1.0) for i in range(3)) > 0.02:
        bad["retex_unitextent"].append((c["Name"], ue, n))

print("new parts expected %d | present %d" % (len(items), sum(1 for it in items if it["name"] in byname)))
for k in ("missing", "duplicate", "pos", "yaw", "size", "unitextent", "mesh", "texture", "doublesided", "mobility",
          "retex_missing", "retex", "retex_unitextent"):
    print("  %-17s %d  %s" % (k, len(bad[k]), bad[k][:2]))
print("container children:", len(cont["LuaChildren"]))
mob = collections.Counter(str(byname[it["name"]][-1].get("Mobility")) for it in items if it["name"] in byname)
print("mobility:", dict(mob))
json.dump(fix, io.open(os.path.join(HERE, "cframe_fix_v3c.json"), "w", encoding="utf-8"), indent=1)
json.dump({k: v for k, v in bad.items()}, io.open(os.path.join(HERE, "_audit_v3c.json"), "w", encoding="utf-8"), indent=1, default=list)
