# -*- coding: utf-8 -*-
import json, io, sys, shutil

P = r"C:\Work\onlyonetap\onlyoneshot.ovdrjm"
BAK = r"C:\Work\onlyonetap\onlyoneshot_BEFORE_KGPV2_SCRIPTS.ovdrjm"
shutil.copyfile(P, BAK)

s = open(P, "rb").read().decode("utf-16-le")
bom = s[0] == "\ufeff"
if bom:
    s = s[1:]
d = json.loads(s)

def walk(n):
    yield n
    for c in n.get("LuaChildren", []):
        yield from walk(c)

nodes = {n.get("Name"): n for n in walk(d["Root"])
         if n.get("Name") in ("KgpFountainServer", "KgpGateServer")}

def swap(node_name, new_src):
    old = nodes[node_name]["Source"]
    a = json.dumps(old, ensure_ascii=False)
    b = json.dumps(new_src, ensure_ascii=False)
    n = s.count(a)
    if n != 1:
        raise SystemExit("ERROR %s: old source found %d times" % (node_name, n))
    return a, b

# ---------------------------------------------------------------- fountain
f_old = nodes["KgpFountainServer"]["Source"]
f_new = f_old
reps = [
 ('jets  = "KGP_S_P7_Fountain_water__nomat_00"',            'jets  = "KGP2_WATER_jet"'),
 ('film  = "KGP_S_P7_Fountain_water__P7_water_overflo_00",', 'film  = "KGP2_WATER_film_lo",\n\tfilm2 = "KGP2_WATER_film_up",'),
 ('upper = "KGP_S_P7_Fountain_water__P7_water_upper_b_00"',  'upper = "KGP2_WATER_upper"'),
 ('lower = "KGP_S_P7_Fountain_water__P7_water_lower_b_00"',  'lower = "KGP2_WATER_lower"'),
 ('basin = "KGP_S_P7_Fountain_water__P7_water_basin_00"',    'basin = "KGP2_WATER_basin"'),
]
for a, b in reps:
    if f_new.count(a) != 1:
        raise SystemExit("ERROR fountain: %r x%d" % (a, f_new.count(a)))
    f_new = f_new.replace(a, b)

film_old = ('\tlocal f = parts.film\n'
            '\tif f then\n'
            '\t\tf.part.Transparency = CFG.FILM_BASE + math.sin(t * TAU * CFG.FILM_HZ) * CFG.FILM_SWING\n'
            '\tend\n')
film_new = ('\tfor _, k in ipairs({ "film", "film2" }) do\n'
            '\t\tlocal f = parts[k]\n'
            '\t\tif f then\n'
            '\t\t\tf.part.Transparency = CFG.FILM_BASE + math.sin(t * TAU * CFG.FILM_HZ) * CFG.FILM_SWING\n'
            '\t\tend\n'
            '\tend\n')
if f_new.count(film_old) != 1:
    raise SystemExit("ERROR fountain: film block x%d" % f_new.count(film_old))
f_new = f_new.replace(film_old, film_new)

# ---------------------------------------------------------------- gate
g_new = open(r"C:\Work\blender\ovdr_export\kgp_v2\KgpGateServer_v2.lua",
             encoding="utf-8").read().replace("\r\n", "\n")

fa, fb = swap("KgpFountainServer", f_new)
ga, gb = swap("KgpGateServer", g_new)

out = s.replace(fa, fb).replace(ga, gb)
if out == s:
    raise SystemExit("ERROR: nothing replaced")

data = ("\ufeff" if bom else "") + out
open(P, "wb").write(data.encode("utf-16-le"))

# verify round-trip
chk = open(P, "rb").read().decode("utf-16-le")
if chk[0] == "\ufeff":
    chk = chk[1:]
d2 = json.loads(chk)
got = {n.get("Name"): n for n in walk(d2["Root"])
       if n.get("Name") in ("KgpFountainServer", "KgpGateServer")}
print("fountain ok:", got["KgpFountainServer"]["Source"] == f_new)
print("gate ok    :", got["KgpGateServer"]["Source"] == g_new)
print("backup:", BAK)
