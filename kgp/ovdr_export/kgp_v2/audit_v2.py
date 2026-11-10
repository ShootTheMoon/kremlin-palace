import json, glob, os, collections

ROOT = r"C:\Work\blender\ovdr_export\kgp_v2"
PRJ  = r"C:\Work\onlyonetap\onlyoneshot.ovdrjm"

# ---- expected -------------------------------------------------------------
exp = {}
dupes = []
n_items = 0
for f in sorted(glob.glob(os.path.join(ROOT, "items_v2_*.json"))):
    for it in json.load(open(f, encoding="utf-8")):
        n_items += 1
        nm = it["name"]
        if nm in exp:
            dupes.append(nm)
        exp[nm] = it["props"]
print("items total %d, unique names %d, duplicate names %d" % (n_items, len(exp), len(dupes)))
if dupes:
    print("  dup examples:", dupes[:10])

# ---- actual ---------------------------------------------------------------
s = open(PRJ, "rb").read().decode("utf-16-le")
if s and s[0] == "\ufeff":
    s = s[1:]
d = json.loads(s)

def find(n, target):
    if n.get("Name") == target:
        return n
    for c in n.get("LuaChildren", []):
        r = find(c, target)
        if r:
            return r
    return None

cont = find(d["Root"], "KGP_GrandPalace")
kids = cont["LuaChildren"]
print("container children: %d" % len(kids))

act = {}
act_dupes = []
for c in kids:
    nm = c.get("Name", "")
    if nm.startswith("KGP2_"):
        if nm in act:
            act_dupes.append(nm)
        act[nm] = c
print("KGP2_ parts in scene: %d (dup names %d)" % (len(act) + len(act_dupes), len(act_dupes)))

missing = sorted(set(exp) - set(act))
extra   = sorted(set(act) - set(exp))
print("missing: %d   extra: %d" % (len(missing), len(extra)))
if missing: print("  missing:", missing[:20])
if extra:   print("  extra:", extra[:20])

# ---- field comparison -----------------------------------------------------
def v3(o): return (o["X"], o["Y"], o["Z"])

TOL_POS = 0.6
TOL_SIZE = 0.6
TOL_ROT = 0.2

bad = collections.defaultdict(list)
at_origin = []
for nm, p in exp.items():
    a = act.get(nm)
    if a is None:
        continue
    ap = v3(a["CFrame"]["Position"])
    ao = v3(a["CFrame"]["Orientation"])
    asz = v3(a["Size"])
    ep, eo, esz = p["position"], p["orientation"], p["size"]

    if max(abs(ap[i] - ep[i]) for i in range(3)) > TOL_POS:
        bad["pos"].append((nm, ep, ap))
        if abs(ap[0]) < 1 and abs(ap[1]) < 1 and abs(ap[2]) < 1:
            at_origin.append(nm)
    if max(abs(asz[i] - esz[i]) for i in range(3)) > TOL_SIZE:
        bad["size"].append((nm, esz, asz))
    def dang(x, y):
        dd = (x - y) % 360.0
        return min(dd, 360.0 - dd)
    if max(dang(ao[i], eo[i]) for i in range(3)) > TOL_ROT:
        bad["rot"].append((nm, eo, ao))
    if a.get("MeshId", "") != p["meshId"]:
        bad["mesh"].append((nm, p["meshId"], a.get("MeshId", "")))
    if a.get("Material", "") != p["material"]:
        bad["material"].append((nm, p["material"], a.get("Material", "")))
    ec = p.get("color")
    if ec:
        ac = a.get("Color", {})
        if (round(ac.get("R", -1)), round(ac.get("G", -1)), round(ac.get("B", -1))) != tuple(round(x) for x in ec):
            bad["color"].append((nm, ec, (ac.get("R"), ac.get("G"), ac.get("B"))))
    if bool(a.get("Locked", False)):
        bad["locked"].append(nm)
    if a.get("Mobility") != p.get("mobility", "Static"):
        bad["mobility"].append((nm, p.get("mobility", "Static"), a.get("Mobility")))
    tex = a.get("TextureId", "")
    want_tex = p.get("raw", {}).get("TextureId", "") if isinstance(p.get("raw"), dict) else ""
    if tex != want_tex:
        bad["texture"].append((nm, want_tex, tex))

print("\n--- mismatches ---")
for k in ("pos", "size", "rot", "mesh", "material", "color", "mobility", "texture", "locked"):
    lst = bad.get(k, [])
    print("%-9s %d" % (k, len(lst)))
    for e in lst[:8]:
        print("     ", e)
print("parts at origin: %d" % len(at_origin))

json.dump({"missing": missing, "pos": [x[0] for x in bad["pos"]],
           "size": [x[0] for x in bad["size"]], "rot": [x[0] for x in bad["rot"]],
           "mesh": [x[0] for x in bad["mesh"]]},
          open(os.path.join(ROOT, "_audit_v2.json"), "w"), indent=1)
