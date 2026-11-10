import io
p = r"C:\Work\blender\ovdr_export\kgp_v3\_scratch\recipe_p7.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('web.color_ramp.elements[0].position = 0.80', 'web.color_ramp.elements[0].position = 0.865')
s = s.replace('web.color_ramp.elements[1].position = 0.995', 'web.color_ramp.elements[1].position = 0.958')
s = s.replace('outputs["Fac"]', 'outputs[0]')
io.open(p, "w", encoding="utf-8").write(s)
print("patched")
