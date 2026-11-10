# -*- coding: utf-8 -*-
import json, re, shutil

P = r"C:\Work\onlyonetap\onlyoneshot.ovdrjm"
shutil.copyfile(P, r"C:\Work\onlyonetap\onlyoneshot_BEFORE_KGPV2_MOBILITY.ovdrjm")

s = open(P, "rb").read().decode("utf-16-le")
bom = s[0] == "\ufeff"
if bom:
    s = s[1:]
d = json.loads(s)

def find(n, t):
    if n.get("Name") == t:
        return n
    for c in n.get("LuaChildren", []):
        r = find(c, t)
        if r:
            return r

kids = find(d["Root"], "KGP_GrandPalace")["LuaChildren"]
LEAF = ("KGP2_Door_leaf_sapphire", "KGP2_Door_raised_panel_gilt", "KGP2_Door_inner_bead_gilt",
        "KGP2_Door_kick_plate_gilt", "KGP2_Door_bronze_handle")
targets = []
for c in kids:
    nm = c.get("Name", "")
    if not nm.startswith(LEAF):
        continue
    x = c["CFrame"]["Position"]["X"]
    if abs(x - 102267.9) < 40 or abs(x - 99032.1) < 40:
        targets.append(c["ActorGuid"])
print("targets:", len(targets))

MOB = re.compile(r'"Mobility"(\s*):(\s*)"Static"')
done = 0
for g in targets:
    i = s.find('"' + g + '"')
    if i < 0:
        raise SystemExit("guid not found " + g)
    if s.count('"' + g + '"') != 1:
        raise SystemExit("guid not unique " + g)
    m = MOB.search(s, i, i + 1500)
    if not m:
        raise SystemExit("Mobility not found near " + g)
    s = s[:m.start()] + '"Mobility"%s:%s"Movable"' % (m.group(1), m.group(2)) + s[m.end():]
    done += 1
print("patched:", done)

open(P, "wb").write((("\ufeff" if bom else "") + s).encode("utf-16-le"))

# verify
chk = open(P, "rb").read().decode("utf-16-le")
if chk[0] == "\ufeff":
    chk = chk[1:]
d2 = json.loads(chk)
kids2 = find(d2["Root"], "KGP_GrandPalace")["LuaChildren"]
by = {c["ActorGuid"]: c for c in kids2}
bad = [g for g in targets if by[g].get("Mobility") != "Movable"]
print("still static:", len(bad))
others = [c for c in kids2 if c.get("Mobility") == "Movable"]
print("total Movable under container:", len(others))
