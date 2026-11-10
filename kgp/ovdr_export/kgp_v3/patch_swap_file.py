# -*- coding: utf-8 -*-
r"""swap_v3_NN.json 을 저장된 .ovdrjm 에 guid 단위로 국소 치환한다.

파일 전체를 다시 쓰지 않는다(Studio 포맷: 탭 들여쓰기·CRLF). 각 파츠 노드의 { } 범위 안에서만
MeshId · TextureId · Material · Color(R,G,B) · DoubleSided · Transparency 를 정규식으로 바꾸고,
하나라도 정확히 1번 매치되지 않으면 아무것도 쓰지 않고 멈춘다.

    python patch_swap_file.py 03 04 ... 15
"""
import io, json, os, re, sys, shutil, glob

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = r"C:\Work\onlyonetap\onlyoneshot.ovdrjm"
BAK = r"C:\Work\onlyonetap\onlyoneshot_BEFORE_V3_SWAP_20260918.ovdrjm"

nums = sys.argv[1:]
ups = []
for n in nums:
    ups += json.load(io.open(os.path.join(HERE, "swap_v3_%s.json" % n), encoding="utf-8"))
print("updates to patch:", len(ups))

shutil.copyfile(PRJ, BAK)
raw = open(PRJ, "rb").read().decode("utf-16-le")
bom = raw[0] == "\ufeff"
if bom:
    raw = raw[1:]

def span(s, guid):
    tok = '"' + guid + '"'
    if s.count(tok) != 1:
        raise SystemExit("guid not unique: %s (%d)" % (guid, s.count(tok)))
    i = s.index(tok)
    a = s.rindex("{", 0, i)
    depth, j, instr, esc = 0, a, False, False
    while True:
        ch = s[j]
        if instr:
            if esc: esc = False
            elif ch == "\\": esc = True
            elif ch == '"': instr = False
        else:
            if ch == '"': instr = True
            elif ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return a, j + 1
        j += 1

R_MESH = re.compile(r'("MeshId":\s*")[^"]*(")')
R_TEX = re.compile(r'("TextureId":\s*")[^"]*(")')
R_MAT = re.compile(r'("Material":\s*")[^"]*(")')
R_COL = re.compile(r'("Color":\s*\{[^{}]*?"R":\s*)[-\d.eE]+([^{}]*?"G":\s*)[-\d.eE]+([^{}]*?"B":\s*)[-\d.eE]+')
R_DS = re.compile(r'("DoubleSided":\s*)(true|false)')
R_TR = re.compile(r'("Transparency":\s*)[-\d.eE]+')

def sub1(rx, repl, text, what, guid):
    out, n = rx.subn(repl, text)
    if n != 1:
        raise SystemExit("%s matched %d times in %s" % (what, n, guid))
    return out

pieces = []
for u in ups:
    a, b = span(raw, u["guid"])
    node = raw[a:b]
    p = u["props"]
    node = sub1(R_MESH, lambda m: m.group(1) + p["MeshId"] + m.group(2), node, "MeshId", u["guid"])
    node = sub1(R_TEX, lambda m: m.group(1) + p["TextureId"] + m.group(2), node, "TextureId", u["guid"])
    node = sub1(R_MAT, lambda m: m.group(1) + p["Material"] + m.group(2), node, "Material", u["guid"])
    r, g, bb = p["Color"]
    node = sub1(R_COL, lambda m: "%s%d%s%d%s%d" % (m.group(1), r, m.group(2), g, m.group(3), bb), node, "Color", u["guid"])
    node = sub1(R_DS, lambda m: m.group(1) + ("true" if p["DoubleSided"] else "false"), node, "DoubleSided", u["guid"])
    if "Transparency" in p:
        node = sub1(R_TR, lambda m: m.group(1) + repr(float(p["Transparency"])), node, "Transparency", u["guid"])
    pieces.append((a, b, node))

pieces.sort()
out, prev = [], 0
for a, b, node in pieces:
    if a < prev:
        raise SystemExit("overlapping spans")
    out.append(raw[prev:a]); out.append(node); prev = b
out.append(raw[prev:])
txt = "".join(out)

# verify before writing
d = json.loads(txt)
def walk(n):
    yield n
    for c in n.get("LuaChildren", []) or []:
        yield from walk(c)
by = {n.get("ActorGuid"): n for n in walk(d["Root"])}
bad = 0
for u in ups:
    n = by[u["guid"]]; p = u["props"]
    c = n["Color"]
    ok = (n["MeshId"] == p["MeshId"] and n["TextureId"] == p["TextureId"] and n["Material"] == p["Material"]
          and [round(c["R"]), round(c["G"]), round(c["B"])] == p["Color"] and n["DoubleSided"] == p["DoubleSided"]
          and ("Transparency" not in p or abs(n["Transparency"] - p["Transparency"]) < 1e-6))
    bad += (not ok)
print("verified in patched text: %d ok, %d bad" % (len(ups) - bad, bad))
if bad:
    raise SystemExit("verification failed; nothing written")
open(PRJ, "wb").write((("\ufeff" if bom else "") + txt).encode("utf-16-le"))
print("written. backup:", BAK)
