import io
p='ivm_code.py'
s=io.open(p,encoding='utf-8').read()
rep=[
 ("cr.color_ramp.elements[0].position = 0.365","cr.color_ramp.elements[0].position = 0.415"),
 ("cr.color_ramp.elements[1].position = 0.615","cr.color_ramp.elements[1].position = 0.665"),
 ("S(m1, 'A_Color').default_value = (0.680, 0.635, 0.552, 1.0)","S(m1, 'A_Color').default_value = (0.715, 0.668, 0.580, 1.0)"),
 ("S(m1, 'B_Color').default_value = (0.505, 0.470, 0.405, 1.0)","S(m1, 'B_Color').default_value = (0.530, 0.493, 0.425, 1.0)"),
 ("S(m2, 'B_Color').default_value = (0.452, 0.466, 0.472, 1.0)","S(m2, 'B_Color').default_value = (0.505, 0.520, 0.528, 1.0)"),
 ("S(m4, 'B_Color').default_value = (0.182, 0.194, 0.214, 1.0)","S(m4, 'B_Color').default_value = (0.192, 0.205, 0.226, 1.0)"),
 ("gm.inputs['Scale'].default_value = 0.42","gm.inputs['Scale'].default_value = 0.55"),
 ("gmr.color_ramp.elements[0].position = 0.440","gmr.color_ramp.elements[0].position = 0.485"),
 ("gmr.color_ramp.elements[1].position = 0.565","gmr.color_ramp.elements[1].position = 0.610"),
 ("gf.inputs[1].default_value = 0.72","gf.inputs[1].default_value = 0.75"),
 ("mat.diffuse_color = (0.620, 0.578, 0.505, 1.0)","mat.diffuse_color = (0.640, 0.600, 0.525, 1.0)"),
 ("L(cn.outputs['Fac'], cr.inputs['Fac'])","cn.label = 'CNRAW'\nL(cn.outputs['Fac'], cr.inputs['Fac'])"),
 ("L(cmb1.outputs['Vector'], fn.inputs['Vector']); L(wD.outputs[0], fn.inputs['W'])","fn.label = 'FNRAW'\nL(cmb1.outputs['Vector'], fn.inputs['Vector']); L(wD.outputs[0], fn.inputs['W'])"),
 ("L(cmb1.outputs['Vector'], gn.inputs['Vector']); L(wE.outputs[0], gn.inputs['W'])","gn.label = 'GNRAW'\nL(cmb1.outputs['Vector'], gn.inputs['Vector']); L(wE.outputs[0], gn.inputs['W'])"),
 ("L(cmb0.outputs['Vector'], gm.inputs['Vector']); L(wC.outputs[0], gm.inputs['W'])","gm.label = 'GMRAW'\nL(cmb0.outputs['Vector'], gm.inputs['Vector']); L(wC.outputs[0], gm.inputs['W'])"),
 ("L(cmb0.outputs['Vector'], mn.inputs['Vector']); L(wB.outputs[0], mn.inputs['W'])","mn.label = 'MNRAW'\nL(cmb0.outputs['Vector'], mn.inputs['Vector']); L(wB.outputs[0], mn.inputs['W'])"),
]
for a,b in rep:
    assert s.count(a)==1, a
    s=s.replace(a,b)
io.open(p,'w',encoding='utf-8').write(s)
print("patched")
