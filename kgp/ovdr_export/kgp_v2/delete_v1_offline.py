# -*- coding: utf-8 -*-
import json, shutil, collections

P = r"C:\Work\onlyonetap\onlyoneshot.ovdrjm"
BAK = r"C:\Work\onlyonetap\onlyoneshot_BEFORE_V1_DELETE_20260917.ovdrjm"
shutil.copyfile(P, BAK)

raw = open(P, "rb").read().decode("utf-16-le")
bom = raw[0] == "\ufeff"
if bom:
    raw = raw[1:]
d = json.loads(raw)

def find(n, t):
    if n.get("Name") == t:
        return n
    for c in n.get("LuaChildren", []):
        r = find(c, t)
        if r:
            return r

kids = find(d["Root"], "KGP_GrandPalace")["LuaChildren"]
print("before:", len(kids))

rec = {r["guid"] for r in json.load(open(
    r"C:\Work\blender\ovdr_export\kgp_v2\_v1_meshparts.json", encoding="utf-8"))}

kill = [c for c in kids
        if (c.get("InstanceType") == "MeshPart" and not c.get("Name", "").startswith("KGP2_"))
        or c.get("Name", "").startswith("KGP_GATE")]
killset = {c["ActorGuid"] for c in kill}
keep = [c for c in kids if c["ActorGuid"] not in killset]

print("to delete:", len(kill), dict(collections.Counter(c["InstanceType"] for c in kill)))
print("recorded-338 fully covered:", rec <= killset, "| beyond record:", len(killset - rec))
print("keep:", len(keep), dict(collections.Counter(c["InstanceType"] for c in keep)))
assert len([c for c in keep if c["InstanceType"] == "MeshPart"]) == 1547
assert all(c["Name"].startswith("KGP2_") for c in keep if c["InstanceType"] == "MeshPart")

json.dump(sorted((c["ActorGuid"], c["Name"]) for c in kill),
          open(r"C:\Work\blender\ovdr_export\kgp_v2\_deleted_v1.json", "w"), indent=1)

# ---- locate each node's exact text span ----------------------------------
def obj_span(s, guid):
    tok = '"' + guid + '"'
    if s.count(tok) != 1:
        raise SystemExit("guid not unique: " + guid)
    i = s.index(tok)
    start = s.rindex("{", 0, i)
    depth, j, n = 0, start, len(s)
    instr = esc = False
    while j < n:
        ch = s[j]
        if instr:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                instr = False
        else:
            if ch == '"':
                instr = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return start, j + 1
        j += 1
    raise SystemExit("unbalanced for " + guid)

spans = []
for c in kill:
    a, b = obj_span(raw, c["ActorGuid"])
    # swallow the separating comma, before if possible else after
    p = a - 1
    while p >= 0 and raw[p] in " \t\r\n":
        p -= 1
    if p >= 0 and raw[p] == ",":
        a = p
    else:
        q = b
        while q < len(raw) and raw[q] in " \t\r\n":
            q += 1
        if q < len(raw) and raw[q] == ",":
            b = q + 1
    spans.append((a, b))

spans.sort()
for k in range(1, len(spans)):
    if spans[k][0] < spans[k - 1][1]:
        raise SystemExit("overlapping spans")

out, prev = [], 0
for a, b in spans:
    out.append(raw[prev:a])
    prev = b
out.append(raw[prev:])
txt = "".join(out)
print("bytes removed:", len(raw) - len(txt))

# ---- verify before writing ----------------------------------------------
d2 = json.loads(txt)
k2 = find(d2["Root"], "KGP_GrandPalace")["LuaChildren"]
print("after:", len(k2), dict(collections.Counter(c["InstanceType"] for c in k2)))
assert len(k2) == len(keep)
assert [c["ActorGuid"] for c in k2] == [c["ActorGuid"] for c in keep]
# everything outside the container must be untouched
d["Root"] and None
import copy
ref = copy.deepcopy(d)
find(ref["Root"], "KGP_GrandPalace")["LuaChildren"] = keep
assert ref == d2, "document differs outside the deleted nodes"

open(P, "wb").write((("\ufeff" if bom else "") + txt).encode("utf-16-le"))
print("written OK, backup:", BAK)
