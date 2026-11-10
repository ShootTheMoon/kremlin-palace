import json, glob, os

ROOT = r"C:\Work\blender\ovdr_export\kgp_v2"
PRJ  = r"C:\Work\onlyonetap\onlyoneshot.ovdrjm"

exp = {}
for f in sorted(glob.glob(os.path.join(ROOT, "items_v2_*.json"))):
    for it in json.load(open(f, encoding="utf-8")):
        exp[it["name"]] = it["props"]

s = open(PRJ, "rb").read().decode("utf-16-le")
if s and s[0] == "\ufeff": s = s[1:]
d = json.loads(s)

def find(n, t):
    if n.get("Name") == t: return n
    for c in n.get("LuaChildren", []):
        r = find(c, t)
        if r: return r
    return None

kids = find(d["Root"], "KGP_GrandPalace")["LuaChildren"]
act = {c["Name"]: c for c in kids if str(c.get("Name", "")).startswith("KGP2_")}

fix = []
for nm, p in exp.items():
    a = act[nm]
    ap = a["CFrame"]["Position"]
    ep = p["position"]
    if max(abs(ap[k] - ep[i]) for i, k in enumerate("XYZ")) > 0.6:
        fix.append({
            "guid": a["ActorGuid"],
            "props": {
                "CFrame": {
                    "ObjectType": "CFrame",
                    "Position": {"ObjectType": "Vector3", "X": ep[0], "Y": ep[1], "Z": ep[2]},
                    "Orientation": {"ObjectType": "Vector3", "X": p["orientation"][0],
                                    "Y": p["orientation"][1], "Z": p["orientation"][2]},
                }
            },
        })

print("to fix:", len(fix))
for i in range(0, len(fix), 100):
    out = os.path.join(ROOT, "fix_v2_%02d.json" % (i // 100))
    json.dump(fix[i:i + 100], open(out, "w"), indent=1)
    print(out, len(fix[i:i + 100]))
