import io, json, collections
spec = json.load(io.open("knight_parts_place.json", encoding="utf-8"))
native = {p["mesh"]: p["native_half_cm"] for p in spec["pieces"]}
items = {i["name"]: i for i in json.load(io.open("knight_parts_items.json", encoding="utf-8"))}
P = r"C:\Work\onlyonetap\onlyoneshot.ovdrjm"
s = open(P, "rb").read().decode("utf-16-le")
if s[0] == "\ufeff": s = s[1:]
d = json.loads(s)
def walk(n):
    yield n
    for c in n.get("LuaChildren", []) or []:
        yield from walk(c)
cont = next(n for n in walk(d["Root"]) if n.get("Name") == "KGP_GrandPalace")
live = {c["Name"]: c for c in cont["LuaChildren"]}
mesh_of = {k["name"]: k["mesh"] for k in spec["place"]}
bad = collections.defaultdict(list)
for name, it in items.items():
    c = live.get(name)
    if c is None: bad["missing"].append(name); continue
    p = it["props"]; q = c["CFrame"]["Position"]; z = c["Size"]; u = c.get("UnitExtent", {})
    if max(abs(q["X"]-p["position"][0]), abs(q["Y"]-p["position"][1]), abs(q["Z"]-p["position"][2])) > 0.6: bad["pos"].append(name)
    if abs(((c["CFrame"]["Orientation"]["Y"] - p["orientation"][1]) + 180) % 360 - 180) > 0.2: bad["yaw"].append(name)
    if max(abs(z["X"]-p["size"][0]), abs(z["Y"]-p["size"][1]), abs(z["Z"]-p["size"][2])) > 0.6: bad["size"].append(name)
    n = native[mesh_of[name]]
    ue = (abs(u.get("X", 0)), abs(u.get("Y", 0)), abs(u.get("Z", 0)))
    if max(abs(ue[i] - n[i]) for i in range(3)) > 0.5: bad["unitextent"].append((name, ue, n))
    if c.get("MeshId") != p["meshId"]: bad["mesh"].append(name)
    if c.get("TextureId") != p["raw"]["TextureId"]: bad["texture"].append(name)
    if not c.get("DoubleSided"): bad["doublesided"].append(name)
old_left = [n for n in live if n.startswith("KGP2_") and "GEN_knight" in n and (n.endswith("_p0") or n.endswith("_p1"))]
print("new knight parts expected 90 | present %d" % sum(1 for n in items if n in live))
for k in ("missing", "pos", "yaw", "size", "unitextent", "mesh", "texture", "doublesided"):
    print("  %-11s %d  %s" % (k, len(bad[k]), bad[k][:2]))
print("old _p0/_p1 knight parts left:", len(old_left))
print("container children:", len(cont["LuaChildren"]))
