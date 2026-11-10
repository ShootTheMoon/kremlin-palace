# -*- coding: utf-8 -*-
r"""라운드 2 레시피 조립기 -> recipes_r2.json

출처
  * Sapphire stone         : 라운드 2 에이전트(직접 굽고 검증: spread 199 / std 37.27 / seam 2.1·2.7)
  * Antique gilded bronze  : 라운드 1 + 비평가가 실측으로 준 램프 재배치(아래 GOLD_FIX)
  * P3 porcelain white, Wrought iron, P7 water 4종, P3 berry red, P3 topiary green
                           : 새로 씀. 라운드 1 이 기준 미달(spread 18 / 38 / 0)이었거나 타일이
                             안 이어졌다(seam 48~62).
  * 나머지                 : 라운드 1 그대로(통과).

새로 쓴 것은 전부 '4D 토러스' 좌표를 쓴다 : u,v = 2π·Generated.xy 를
(r_u·cos u, r_u·sin u, r_v·cos v, r_v·sin v) 로 보내서 4D 노이즈/보로노이를 읽는다.
u 가 0->1 로 한 바퀴 돌면 정확히 제자리라 타일 이음새가 수학적으로 없다.
축별 특징 개수 ≈ 2π · r · Scale.
"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

HELPERS = r'''
mat.use_nodes = True
nt = mat.node_tree
nodes = nt.nodes
links = nt.links
nodes.clear()
TAU = 6.2831853

def torus(ru=1.0, rv=1.0):
    tc = nodes.new('ShaderNodeTexCoord')
    sep = nodes.new('ShaderNodeSeparateXYZ')
    links.new(tc.outputs['Generated'], sep.inputs['Vector'])
    outs = []
    for ch, r in (('X', ru), ('Y', rv)):
        a = nodes.new('ShaderNodeMath'); a.operation = 'MULTIPLY'; a.inputs[1].default_value = TAU
        links.new(sep.outputs[ch], a.inputs[0])
        for op in ('COSINE', 'SINE'):
            t = nodes.new('ShaderNodeMath'); t.operation = op
            links.new(a.outputs[0], t.inputs[0])
            s = nodes.new('ShaderNodeMath'); s.operation = 'MULTIPLY'; s.inputs[1].default_value = r
            links.new(t.outputs[0], s.inputs[0])
            outs.append(s)
    c = nodes.new('ShaderNodeCombineXYZ')
    links.new(outs[0].outputs[0], c.inputs['X'])
    links.new(outs[1].outputs[0], c.inputs['Y'])
    links.new(outs[2].outputs[0], c.inputs['Z'])
    return c.outputs['Vector'], outs[3].outputs[0]

def noise4(vec, w, n_per_tile, detail=4.0, rough=0.5, dist=0.0, r=1.0):
    n = nodes.new('ShaderNodeTexNoise'); n.noise_dimensions = '4D'
    n.inputs['Scale'].default_value = n_per_tile / (TAU * r)
    n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough
    n.inputs['Distortion'].default_value = dist
    links.new(vec, n.inputs['Vector']); links.new(w, n.inputs['W'])
    return n

def voro4(vec, w, n_per_tile, feature='F1', rand=1.0, r=1.0):
    v = nodes.new('ShaderNodeTexVoronoi'); v.voronoi_dimensions = '4D'; v.feature = feature
    v.inputs['Scale'].default_value = n_per_tile / (TAU * r)
    v.inputs['Randomness'].default_value = rand
    links.new(vec, v.inputs['Vector']); links.new(w, v.inputs['W'])
    return v

def remap(sock, a, b, c=0.0, d=1.0):
    m = nodes.new('ShaderNodeMapRange'); m.clamp = True
    m.inputs['From Min'].default_value = a; m.inputs['From Max'].default_value = b
    m.inputs['To Min'].default_value = c; m.inputs['To Max'].default_value = d
    links.new(sock, m.inputs['Value'])
    return m.outputs['Result']

def mm(op, a, b=None, clamp=False):
    m = nodes.new('ShaderNodeMath'); m.operation = op; m.use_clamp = clamp
    for i, v in ((0, a), (1, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            m.inputs[i].default_value = v
        else:
            links.new(v, m.inputs[i])
    return m.outputs[0]

def sep_r(color_sock):
    s = nodes.new('ShaderNodeSeparateColor')
    links.new(color_sock, s.inputs['Color'])
    return s.outputs['Red']

def ramp(fac, stops):
    r = nodes.new('ShaderNodeValToRGB')
    el = r.color_ramp.elements
    el[0].position = stops[0][0]; el[0].color = tuple(stops[0][1]) + (1.0,)
    el[1].position = stops[-1][0]; el[1].color = tuple(stops[-1][1]) + (1.0,)
    for p, c in stops[1:-1]:
        el.new(p).color = tuple(c) + (1.0,)
    links.new(fac, r.inputs['Fac'])
    return r.outputs['Color']

def mix(fac, a, b):
    m = nodes.new('ShaderNodeMix'); m.data_type = 'RGBA'
    if isinstance(fac, (int, float)):
        m.inputs[0].default_value = fac
    else:
        links.new(fac, m.inputs[0])
    for idx, v in ((6, a), (7, b)):
        if isinstance(v, tuple):
            m.inputs[idx].default_value = v + (1.0,)
        else:
            links.new(v, m.inputs[idx])
    return m.outputs[2]

def finish(col):
    out = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.5
    links.new(col, bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
'''

# ------------------------------------------------------------------ 새로 쓴 것
PORCELAIN = r'''
vec, w = torus()
drift = noise4(vec, w, 2.5, detail=2.0, rough=0.5)
base = mix(remap(drift.outputs['Fac'], 0.38, 0.62),
           (0.865, 0.848, 0.800), (0.800, 0.830, 0.905))
pool = noise4(vec, w, 6.0, detail=3.0, rough=0.55)
col = mix(remap(pool.outputs['Fac'], 0.55, 0.68, 0.0, 0.45), base, (0.700, 0.725, 0.790))
finish(col)
'''

IRON = r'''
vec, w = torus()
facet = voro4(vec, w, 14.0, feature='F1')
base = mix(sep_r(facet.outputs['Color']), (0.028, 0.032, 0.041), (0.050, 0.055, 0.066))
dimple = remap(facet.outputs['Distance'], 0.05, 0.55, 0.0, 0.7)
base = mix(dimple, base, (0.085, 0.090, 0.102))
grain = noise4(vec, w, 40.0, detail=2.0, rough=0.5)
base = mix(remap(grain.outputs['Fac'], 0.40, 0.60, 0.0, 0.35), base, (0.018, 0.020, 0.026))
wear = noise4(vec, w, 3.0, detail=3.0, rough=0.5)
base = mix(remap(wear.outputs['Fac'], 0.56, 0.68, 0.0, 0.75), base, (0.115, 0.120, 0.132))
rust = noise4(vec, w, 16.0, detail=5.0, rough=0.6, dist=0.4)
col = mix(remap(rust.outputs['Fac'], 0.605, 0.665, 0.0, 0.8), base, (0.110, 0.056, 0.028))
finish(col)
'''

WATER = r'''
vec, w = torus()
depth = noise4(vec, w, 2.0, detail=3.0, rough=0.5)
base = mix(remap(depth.outputs['Fac'], 0.38, 0.62), (0.060, 0.190, 0.230), (0.190, 0.420, 0.460))
caus = voro4(vec, w, 7.0, feature='DISTANCE_TO_EDGE')
caus_m = remap(caus.outputs['Distance'], 0.0, 0.06, 1.0, 0.0)
breakup = remap(noise4(vec, w, 5.0, detail=2.0).outputs['Fac'], 0.40, 0.60, 0.15, 1.0)
col = mix(mm('MULTIPLY', caus_m, breakup), base, (0.600, 0.840, 0.860))
finish(col)
'''

SHEET = r'''
vec, w = torus(ru=1.0, rv=0.12)
streak = noise4(vec, w, 22.0, detail=5.0, rough=0.55, dist=0.3)
base = mix(remap(streak.outputs['Fac'], 0.36, 0.64),
           (0.260, 0.470, 0.530), (0.700, 0.880, 0.920))
riv = noise4(vec, w, 16.0, detail=2.0, rough=0.5)
col = mix(remap(riv.outputs['Fac'], 0.61, 0.70, 0.0, 0.45), base, (0.930, 0.985, 1.000))
finish(col)
'''

BERRY = r'''
vec, w = torus()
cell = voro4(vec, w, 7.0, feature='F1')
tone = sep_r(cell.outputs['Color'])
base = mix(tone, (0.300, 0.010, 0.030), (0.560, 0.035, 0.075))
# 알갱이마다 가운데는 밝고 가장자리로 갈수록 부드럽게 어두워진다 — 선을 긋지 않는다
dome = remap(cell.outputs['Distance'], 0.0, 0.55, 0.0, 1.0)
base = mix(mm('POWER', dome, 1.6), base, (0.110, 0.004, 0.012))
shine = remap(cell.outputs['Distance'], 0.0, 0.16, 0.45, 0.0)
col = mix(shine, base, (0.780, 0.220, 0.240))
finish(col)
'''

TOPIARY = r'''
vec, w = torus()
clump = noise4(vec, w, 3.0, detail=3.0, rough=0.55)
base = mix(remap(clump.outputs['Fac'], 0.38, 0.62), (0.025, 0.080, 0.028), (0.120, 0.300, 0.085))
leaf = noise4(vec, w, 28.0, detail=2.0, rough=0.5, dist=0.6)
base = mix(remap(leaf.outputs['Fac'], 0.40, 0.62, 0.0, 0.8), base, (0.200, 0.420, 0.120))
dark = noise4(vec, w, 12.0, detail=2.0, rough=0.5)
col = mix(remap(dark.outputs['Fac'], 0.58, 0.68, 0.0, 0.7), base, (0.012, 0.040, 0.014))
finish(col)
'''

CAKE = r'''
vec, w = torus()
swirl = noise4(vec, w, 4.0, detail=4.0, rough=0.55, dist=0.8)
col = ramp(remap(swirl.outputs['Fac'], 0.36, 0.64), [
    (0.00, (0.300, 0.250, 0.640)), (0.45, (0.500, 0.440, 0.850)),
    (0.80, (0.700, 0.650, 0.940)), (1.00, (0.860, 0.830, 0.980))])
sug = voro4(vec, w, 30.0, feature='F1')
col = mix(remap(sug.outputs['Distance'], 0.0, 0.06, 0.8, 0.0), col, (0.960, 0.950, 1.000))
finish(col)
'''

MIRROR = r'''
vec, w = torus()
cloud = noise4(vec, w, 1.6, detail=3.0, rough=0.5)
base = ramp(remap(cloud.outputs['Fac'], 0.36, 0.64), [
    (0.00, (0.330, 0.360, 0.410)), (0.40, (0.560, 0.600, 0.660)),
    (0.75, (0.760, 0.790, 0.840)), (1.00, (0.880, 0.900, 0.930))])
vec2, w2 = torus(ru=1.0, rv=0.35)
smear = noise4(vec2, w2, 5.0, detail=2.0, rough=0.5, r=1.0)
base = mix(remap(smear.outputs['Fac'], 0.55, 0.68, 0.0, 0.35), base, (0.900, 0.920, 0.950))
fox = voro4(vec, w, 10.0, feature='F1')
fmask = mm('MULTIPLY', remap(fox.outputs['Distance'], 0.0, 0.07, 1.0, 0.0),
           remap(noise4(vec, w, 3.0, detail=1.0).outputs['Fac'], 0.52, 0.62))
col = mix(mm('MULTIPLY', fmask, 0.75), base, (0.470, 0.430, 0.370))
finish(col)
'''

# 비평가(실측): 금 램프 8단 중 4단이 한 번도 안 찍힌다. 실제 신호 분포 위에 다시 깐다.
GOLD_FIX = r'''
for e in gd.color_ramp.elements:
    e.position = 0.24 + 0.54 * e.position
ct.inputs[1].default_value = 1.15
ct.inputs[2].default_value = 0.0
vn.color_ramp.elements[0].color = (0.08, 0.08, 0.08, 1.0)
'''

# 대리석 : 굵은 결을 옅고 차갑게. 반복 무늬가 덜 튀고, '같은 색 더 어둡게' 문제도 풀린다.
MARBLE_PATCH = [
    ("S(m3, 'B_Color').default_value = (0.200, 0.180, 0.155, 1.0)",
     "S(m3, 'B_Color').default_value = (0.360, 0.352, 0.345, 1.0)"),
    ("S(m2, 'B_Color').default_value = (0.350, 0.315, 0.270, 1.0)",
     "S(m2, 'B_Color').default_value = (0.430, 0.420, 0.410, 1.0)"),
]

NEW = {
    "P3 porcelain white":       (0.35, 512,  PORCELAIN),
    "Wrought iron":             (0.5,  512,  IRON),
    "P7 water basin":           (1.5,  512,  WATER),
    "P7 water lower bowl":      (0.6,  512,  WATER),
    "P7 water upper bowl":      (0.5,  512,  WATER),
    "P7 water overflow sheet":  (0.4,  512,  SHEET),
    "P3 berry red":             (0.06, 512,  BERRY),
    "P3 topiary green":         (0.25, 512,  TOPIARY),
    "P3 cake lavender icing":   (0.08, 512,  CAKE),
    "Palace mirror":            (1.5,  1024, MIRROR),
}


def main():
    r1 = {r["name"]: r for r in json.load(io.open(os.path.join(HERE, "recipes_r1.json"), encoding="utf-8"))}
    r2 = {r["name"]: r for r in json.load(io.open(os.path.join(HERE, "_round2_done.json"), encoding="utf-8"))}

    out = []
    for name, rec in r1.items():
        if name in NEW:
            continue
        rec = dict(rec)
        if name in r2:                                  # 에이전트가 검증한 개정판
            rec.update(code=r2[name]["code"], tile_metres=r2[name]["tile_metres"],
                       texture_px=r2[name]["texture_px"])
            rec["source"] = "round2-agent"
        elif name == "Antique gilded bronze":
            rec["code"] = rec["code"].rstrip() + "\n" + GOLD_FIX
            rec["source"] = "round1+critic-fix+r3"
        elif name == "Ivory marble":
            c = rec["code"]
            for x, y in MARBLE_PATCH:
                assert c.count(x) == 1, x
                c = c.replace(x, y)
            rec["code"] = c
            rec["source"] = "round1+r3-veins"
        else:
            rec["source"] = "round1"
        out.append(rec)
    for name, (tile, px, body) in NEW.items():
        out.append({"name": name, "tile_metres": tile, "texture_px": px,
                    "code": HELPERS + body, "source": "round2-local"})

    io.open(os.path.join(HERE, "recipes_r2.json"), "w", encoding="utf-8").write(
        json.dumps(out, ensure_ascii=False, indent=1))
    for r in out:
        print("  %-26s tile %-5s px %-5s %s" % (r["name"], r["tile_metres"], r["texture_px"], r["source"]))
    print("recipes_r2.json :", len(out))


if __name__ == "__main__":
    main()
