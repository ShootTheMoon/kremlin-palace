import io, json, collections
native = json.load(io.open("_fbx_native_half.json", encoding="utf-8"))          # token -> [hx,hy,hz] cm
ids = json.load(io.open("meshids_v3.json", encoding="utf-8"))
tok_of = {("ovdrassetid://" + r["meshId"]): r["mesh"] for r in ids}
P = r"C:\Work\onlyonetap\onlyoneshot.ovdrjm"
s = open(P, "rb").read().decode("utf-16-le")
if s[0] == "\ufeff": s = s[1:]
d = json.loads(s)
def walk(n):
    yield n
    for c in n.get("LuaChildren", []) or []:
        yield from walk(c)
cont = next(n for n in walk(d["Root"]) if n.get("Name") == "KGP_GrandPalace")
bad, ok, per_tok = [], 0, collections.defaultdict(list)
for c in cont["LuaChildren"]:
    if c["InstanceType"] != "MeshPart":
        continue
    tok = tok_of.get(c["MeshId"])
    if not tok or tok not in native:
        bad.append((c["Name"], "no token", c["MeshId"])); continue
    u = c["UnitExtent"]; n = native[tok]
    ue = (abs(u["X"]), abs(u["Y"]), abs(u["Z"]))
    err = max(abs(ue[i] - n[i]) / max(n[i], 1.0) for i in range(3))
    if err > 0.02:
        bad.append((c["Name"], tok, ue, tuple(n), round(err, 3)))
        per_tok[tok].append(c["Name"])
    else:
        ok += 1
print("MeshParts OK: %d   UnitExtent != FBX native: %d   (distinct meshes affected: %d)" % (ok, len(bad), len(per_tok)))
for tok, names in sorted(per_tok.items(), key=lambda kv: -len(kv[1])):
    ex = next(b for b in bad if b[1] == tok)
    print("  %-10s parts %-3d  engine %-28s fbx %-28s  e.g. %s" % (tok, len(names), tuple(round(x,1) for x in ex[2]), ex[3], names[0]))
json.dump({"bad": bad, "per_tok": per_tok}, io.open("_unit_audit.json", "w", encoding="utf-8"), indent=1, default=list)
