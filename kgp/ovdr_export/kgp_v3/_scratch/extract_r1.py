import json, io, os
p = r"C:\Work\blender\ovdr_export\kgp_v3\_round2\Antique_gilded_bronze.json"
d = json.load(io.open(p, encoding='utf-8'))
out = r"C:\Work\blender\ovdr_export\kgp_v3\_scratch\mat_r1.py"
io.open(out, 'w', encoding='utf-8').write(d['code'])
print("wrote", out, len(d['code']))
