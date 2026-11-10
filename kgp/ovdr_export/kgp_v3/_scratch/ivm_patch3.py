import io
p='ivm_code.py'
s=io.open(p,encoding='utf-8').read()
rep=[
 ("fs.inputs[1].default_value = 0.4855","fs.inputs[1].default_value = 0.4784"),
 ("gs.inputs[1].default_value = 0.4800","gs.inputs[1].default_value = 0.4817"),
 ("gmr.color_ramp.elements[0].position = 0.485","gmr.color_ramp.elements[0].position = 0.434"),
 ("gmr.color_ramp.elements[1].position = 0.610","gmr.color_ramp.elements[1].position = 0.554"),
]
for a,b in rep:
    assert s.count(a)==1, a
    s=s.replace(a,b)
io.open(p,'w',encoding='utf-8').write(s)
print("patched3")
