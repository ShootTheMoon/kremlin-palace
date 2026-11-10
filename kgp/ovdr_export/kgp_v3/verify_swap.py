import io, json, glob, os
HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = r"C:\Work\onlyonetap\onlyoneshot.ovdrjm"
ups = []
for f in sorted(glob.glob(os.path.join(HERE, "swap_v3_*.json"))):
    ups += json.load(io.open(f, encoding="utf-8"))
s = open(PRJ, "rb").read().decode("utf-16-le")
if s[0] == "\ufeff": s = s[1:]
d = json.loads(s)
def walk(n):
    yield n
    for c in n.get("LuaChildren", []) or []:
        yield from walk(c)
by = {n.get("ActorGuid"): n for n in walk(d["Root"])}
bad = []
for u in ups:
    n = by.get(u["guid"]); p = u["props"]
    if n is None: bad.append((u["guid"], "missing")); continue
    c = n["Color"]
    ok = (n["MeshId"] == p["MeshId"] and n["TextureId"] == p["TextureId"] and n["Material"] == p["Material"]
          and [round(c["R"]), round(c["G"]), round(c["B"])] == p["Color"] and bool(n["DoubleSided"]) == p["DoubleSided"]
          and ("Transparency" not in p or abs(n["Transparency"] - p["Transparency"]) < 1e-6))
    if not ok: bad.append((n["Name"], n["MeshId"], n["TextureId"], n["Material"]))
cont = next(n for n in walk(d["Root"]) if n.get("Name") == "KGP_GrandPalace")
kids = cont["LuaChildren"]
mov = sum(1 for c in kids if c.get("Mobility") == "Movable")
print("swap entries %d | matching %d | mismatched %d | container children %d | Movable %d"
      % (len(ups), len(ups) - len(bad), len(bad), len(kids), mov))
for b in bad[:6]: print("   ", b)
